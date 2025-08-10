
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_id: str, name: str, description: str = ""):
        self.agent_id = agent_id
        self.name = name
        self.description = description
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """Execute the agent and return results"""
        pass
    
    def get_verdict_from_llm(self, context: str) -> Dict[str, Any]:
        """Common LLM integration for getting AI verdicts"""
        try:
            # Import here to avoid circular imports
            from src.common_repository.utils.ai_verdict import get_ai_verdict
            
            # Use existing AI verdict pipeline
            verdict_data = get_ai_verdict(context)
            
            return {
                "verdict": verdict_data.get("verdict", "HOLD"),
                "confidence": verdict_data.get("confidence", 0.5),
                "reasoning": verdict_data.get("reasoning", "")
            }
        except Exception as e:
            return {
                "verdict": "HOLD",
                "confidence": 0.5,
                "reasoning": f"Error getting LLM verdict: {str(e)}"
            }
