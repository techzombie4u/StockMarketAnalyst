
"""
Agent Runner - Executes agents with safety and rate limiting
"""

import json
import logging
import time
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

from .contracts import AgentInput, AgentOutput, AgentError, AgentTimeoutError, AgentRateLimitError
from .registry import agent_registry
from .providers.llm_client import create_llm_client
from ...common_repository.security.safety import safety_manager
from ...common_repository.utils.ratelimit import rate_limiter
from ...common_repository.config.feature_flags import feature_flags

logger = logging.getLogger(__name__)

class AgentRunner:
    """Executes AI agents with safety, rate limiting, and validation"""
    
    def __init__(self):
        self.llm_client = None
        self.initialize_llm()
        
    def initialize_llm(self):
        """Initialize LLM client"""
        try:
            llm_config = agent_registry.get_llm_config()
            self.llm_client = create_llm_client(llm_config)
            logger.info(f"Initialized LLM client: {self.llm_client.get_provider_info()}")
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}")
    
    def run_agent(self, agent_name: str, agent_input: AgentInput) -> AgentOutput:
        """Run an agent with full safety and validation pipeline"""
        start_time = time.time()
        
        try:
            # 1. Validate agent exists and is enabled
            if not agent_registry.is_agent_enabled(agent_name):
                raise AgentError(f"Agent {agent_name} is not enabled")
            
            spec = agent_registry.get_agent_spec(agent_name)
            if not spec:
                raise AgentError(f"Agent {agent_name} not found")
            
            # 2. Check rate limits
            if not rate_limiter.is_allowed(agent_name):
                raise AgentRateLimitError(f"Rate limit exceeded for {agent_name}")
            
            # 3. Sanitize and validate input
            sanitized_input = self._sanitize_input(agent_input, spec)
            
            # 4. Safety checks
            if not safety_manager.check_safety(sanitized_input.to_dict(), spec.safety):
                raise AgentError("Input failed safety checks")
            
            # 5. Build prompt payload
            prompt_payload = self._build_prompt(agent_name, sanitized_input, spec)
            
            # 6. Execute with timeout
            timeout = spec.constraints.get('latency_ms', 10000) / 1000.0
            response = self._execute_with_timeout(prompt_payload, timeout)
            
            # 7. Parse and validate output
            agent_output = self._parse_output(response, spec)
            
            # 8. Add metadata
            agent_output.metadata.update({
                'agent_name': agent_name,
                'execution_time_ms': int((time.time() - start_time) * 1000),
                'input_hash': self._hash_input(agent_input),
                'timestamp': datetime.now().isoformat(),
                'provider_info': self.llm_client.get_provider_info() if self.llm_client else {}
            })
            
            return agent_output
            
        except Exception as e:
            logger.error(f"Error running agent {agent_name}: {e}")
            # Return error response
            return AgentOutput(
                verdict="ERROR",
                confidence=0.0,
                reasons=[f"Agent execution failed: {str(e)}"],
                metadata={
                    'error': True,
                    'error_type': type(e).__name__,
                    'execution_time_ms': int((time.time() - start_time) * 1000)
                }
            )
    
    def _sanitize_input(self, agent_input: AgentInput, spec) -> AgentInput:
        """Sanitize agent input according to spec"""
        try:
            input_dict = agent_input.to_dict()
            
            # Apply redactions from spec
            redactions = spec.constraints.get('redactions', [])
            sanitized_dict = safety_manager.sanitize_input(input_dict, redactions)
            
            # Apply token limits
            token_cap = spec.constraints.get('token_cap', 1000)
            sanitized_dict = safety_manager.truncate_tokens(sanitized_dict, token_cap)
            
            # Reconstruct AgentInput
            return AgentInput(**sanitized_dict)
            
        except Exception as e:
            logger.error(f"Error sanitizing input: {e}")
            return agent_input
    
    def _build_prompt(self, agent_name: str, agent_input: AgentInput, spec) -> str:
        """Build prompt payload for LLM"""
        try:
            prompt_parts = [
                f"You are an AI agent named '{agent_name}' with the following purpose:",
                spec.purpose,
                "",
                "Your task is to analyze the provided data and return a JSON response with the following structure:",
                json.dumps({
                    "verdict": "string (BUY/SELL/HOLD/ANALYZE/ERROR)",
                    "confidence": "number (0-100)",
                    "reasons": ["list of reasoning points"],
                    "insights": ["list of insights"],
                    "actions": ["list of suggested actions"],
                    "risk_flags": ["list of identified risks"]
                }, indent=2),
                "",
                "Input data:",
                json.dumps(agent_input.to_dict(), indent=2),
                "",
                "Provide your analysis as valid JSON only:"
            ]
            
            return "\n".join(prompt_parts)
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            return f"Analyze: {json.dumps(agent_input.to_dict())}"
    
    def _execute_with_timeout(self, prompt: str, timeout: float) -> str:
        """Execute LLM call with timeout"""
        try:
            if not self.llm_client:
                raise AgentError("LLM client not initialized")
            
            start_time = time.time()
            response = self.llm_client.generate(prompt)
            
            if time.time() - start_time > timeout:
                raise AgentTimeoutError(f"Agent execution exceeded timeout of {timeout}s")
                
            return response
            
        except AgentTimeoutError:
            raise
        except Exception as e:
            logger.error(f"Error in LLM execution: {e}")
            raise AgentError(f"LLM execution failed: {e}")
    
    def _parse_output(self, response: str, spec) -> AgentOutput:
        """Parse LLM response into AgentOutput"""
        try:
            # Try to parse as JSON
            if response.startswith('{') or response.startswith('['):
                data = json.loads(response)
            else:
                # Extract JSON from response if wrapped in text
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    data = json.loads(json_str)
                else:
                    # Fallback for non-JSON responses
                    data = {
                        'verdict': 'ANALYZE',
                        'confidence': 50.0,
                        'reasons': ['Response could not be parsed as JSON'],
                        'insights': [response[:200] + '...' if len(response) > 200 else response]
                    }
            
            # Validate required fields
            verdict = data.get('verdict', 'ANALYZE')
            confidence = float(data.get('confidence', 50.0))
            reasons = data.get('reasons', ['No specific reasons provided'])
            
            # Ensure confidence is in valid range
            confidence = max(0.0, min(100.0, confidence))
            
            return AgentOutput(
                verdict=verdict,
                confidence=confidence,
                reasons=reasons,
                insights=data.get('insights', []),
                actions=data.get('actions', []),
                risk_flags=data.get('risk_flags', []),
                metadata=data.get('metadata', {})
            )
            
        except Exception as e:
            logger.error(f"Error parsing agent output: {e}")
            return AgentOutput(
                verdict="ERROR",
                confidence=0.0,
                reasons=[f"Failed to parse response: {str(e)}"],
                insights=[response[:200] + '...' if len(response) > 200 else response]
            )
    
    def _hash_input(self, agent_input: AgentInput) -> str:
        """Generate hash of input for tracking"""
        try:
            input_str = json.dumps(agent_input.to_dict(), sort_keys=True)
            return hashlib.md5(input_str.encode()).hexdigest()
        except:
            return "unknown"

# Global runner instance
agent_runner = AgentRunner()
