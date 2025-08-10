
"""
LLM Client Interface and Adapters
"""

import json
import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from LLM"""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, str]:
        """Get provider information"""
        pass

class MockLLMClient(LLMClient):
    """Mock LLM client for testing and development"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.call_count = 0
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response"""
        self.call_count += 1
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Generate structured mock response
        mock_response = {
            "verdict": "HOLD",
            "confidence": 75.5,
            "reasons": [
                "Market conditions are neutral",
                "Technical indicators show mixed signals",
                "No significant catalysts identified"
            ],
            "insights": [
                "Consider monitoring for breakout patterns",
                "Volume trends suggest consolidation phase"
            ],
            "actions": [
                "Monitor key support/resistance levels",
                "Review position sizing if applicable"
            ],
            "risk_flags": [],
            "metadata": {
                "model_version": "mock-v1.0",
                "processing_time_ms": 100,
                "token_count": len(prompt) // 4
            }
        }
        
        return json.dumps(mock_response, indent=2)
    
    def get_provider_info(self) -> Dict[str, str]:
        """Get mock provider information"""
        return {
            'provider': 'mock',
            'model': 'mock-model',
            'version': '1.0.0'
        }

class MistralClient(LLMClient):
    """Mistral AI client (stub for future implementation)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = None  # Will be loaded from environment
        self.base_url = config.get('api_base', 'https://api.mistral.ai/v1')
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from Mistral AI"""
        # For now, fall back to mock until real implementation
        logger.info("Using mock response - Mistral integration not yet implemented")
        mock_client = MockLLMClient(self.config)
        return mock_client.generate(prompt, **kwargs)
    
    def get_provider_info(self) -> Dict[str, str]:
        return {
            'provider': 'mistral',
            'model': self.config.get('model', 'mistral-medium'),
            'version': '1.0.0'
        }

def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """Factory function to create appropriate LLM client"""
    provider = config.get('provider', 'mock').lower()
    
    if provider == 'mock':
        return MockLLMClient(config)
    elif provider == 'mistral':
        return MistralClient(config)
    else:
        logger.warning(f"Unknown provider {provider}, using mock client")
        return MockLLMClient(config)
