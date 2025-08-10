
"""
Agent Registry - Loads and manages agent configurations
"""

import os
import yaml
import logging
from typing import Dict, List, Optional
from ..core.contracts import AgentSpec
from ...common_repository.config.feature_flags import feature_flags
from ...common_repository.utils.ratelimit import rate_limiter

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Manages agent configurations and specifications"""
    
    def __init__(self):
        self.specs: Dict[str, AgentSpec] = {}
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load agents configuration from YAML"""
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), 
                '../../common_repository/config/agents.yaml'
            )
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = yaml.safe_load(f)
                
                # Load agent specs
                agents_config = self.config.get('agents', {})
                for name, agent_config in agents_config.items():
                    self.specs[name] = AgentSpec.from_config(name, agent_config)
                    
                    # Set rate limits
                    qpm_limit = feature_flags.get_flag_value('agents_rate_limit_qpm', 6)
                    rate_limiter.set_limit(name, qpm_limit)
                
                logger.info(f"Loaded {len(self.specs)} agent specifications")
            else:
                logger.warning(f"Agents config file not found: {config_path}")
                self._load_default_config()
                
        except Exception as e:
            logger.error(f"Error loading agent config: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration when YAML is not available"""
        default_agents = ['dev', 'trainer', 'equity', 'options', 'comm', 'new', 'sentiment']
        
        for name in default_agents:
            self.specs[name] = AgentSpec(
                name=name,
                enabled=True,
                purpose=f"Default {name} agent",
                inputs=['context'],
                outputs=['verdict', 'confidence', 'reasons'],
                constraints={'latency_ms': 10000, 'token_cap': 1000},
                safety={'disallow_pii': True},
                run_policy='manual_only'
            )
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent names"""
        enabled = []
        
        for name, spec in self.specs.items():
            # Check both config and feature flags
            config_enabled = spec.enabled
            flag_key = f'enable_agent_{name}'
            flag_enabled = feature_flags.is_enabled(flag_key)
            
            if config_enabled and flag_enabled:
                enabled.append(name)
        
        return enabled
    
    def get_agent_spec(self, name: str) -> Optional[AgentSpec]:
        """Get agent specification by name"""
        return self.specs.get(name)
    
    def is_agent_enabled(self, name: str) -> bool:
        """Check if agent is enabled"""
        spec = self.get_agent_spec(name)
        if not spec:
            return False
            
        flag_key = f'enable_agent_{name}'
        return spec.enabled and feature_flags.is_enabled(flag_key)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.config.get('llm', {
            'provider': 'mistral',
            'model': 'mistral-medium',
            'temperature': 0.1,
            'max_tokens': 2000
        })

# Global registry instance
agent_registry = AgentRegistry()
