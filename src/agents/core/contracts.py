
"""
Agent Framework Contracts and Data Structures
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentInput:
    """Structured input for AI agents"""
    context: Dict[str, Any]
    kpi: Optional[Dict[str, Any]] = None
    predictions: Optional[List[Dict[str, Any]]] = None
    timeframe: Optional[str] = None
    product: Optional[str] = None
    market_date: Optional[str] = None
    pinned: Optional[List[str]] = None
    config_overrides: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'context': self.context,
            'kpi': self.kpi,
            'predictions': self.predictions,
            'timeframe': self.timeframe,
            'product': self.product,
            'market_date': self.market_date,
            'pinned': self.pinned,
            'config_overrides': self.config_overrides
        }

@dataclass 
class AgentOutput:
    """Structured output from AI agents"""
    verdict: str
    confidence: float
    reasons: List[str]
    insights: List[str] = None
    actions: List[str] = None
    risk_flags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []
        if self.actions is None:
            self.actions = []
        if self.risk_flags is None:
            self.risk_flags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'verdict': self.verdict,
            'confidence': self.confidence,
            'reasons': self.reasons,
            'insights': self.insights,
            'actions': self.actions,
            'risk_flags': self.risk_flags,
            'metadata': self.metadata
        }

@dataclass
class AgentSpec:
    """Agent specification from configuration"""
    name: str
    enabled: bool
    purpose: str
    inputs: List[str]
    outputs: List[str]
    constraints: Dict[str, Any]
    safety: Dict[str, Any]
    run_policy: str
    
    @classmethod
    def from_config(cls, name: str, config: Dict[str, Any]) -> 'AgentSpec':
        """Create AgentSpec from configuration dictionary"""
        return cls(
            name=name,
            enabled=config.get('enabled', True),
            purpose=config.get('purpose', ''),
            inputs=config.get('inputs', []),
            outputs=config.get('outputs', []),
            constraints=config.get('constraints', {}),
            safety=config.get('safety', {}),
            run_policy=config.get('run_policy', 'manual_only')
        )

class AgentError(Exception):
    """Base exception for agent errors"""
    pass

class AgentTimeoutError(AgentError):
    """Agent execution timeout error"""
    pass

class AgentRateLimitError(AgentError):
    """Agent rate limit exceeded error"""
    pass

class AgentValidationError(AgentError):
    """Agent input/output validation error"""
    pass
