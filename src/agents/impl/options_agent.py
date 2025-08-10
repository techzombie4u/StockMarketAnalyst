
"""
Options Agent Implementation
"""

from typing import Dict, Any
from ..core.contracts import AgentOutput

DEFAULT_SCHEMA = {
    "verdict": "string",
    "confidence": "number", 
    "rationale": "string",
    "risk_flags": "array",
    "actions": "array"
}

def build_inputs(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build inputs for options agent"""
    return {
        "options_chain": context.get("options_data", {}),
        "predictions_snapshot": context.get("predictions", []),
        "market_context": context.get("market_data", {}),
        "volatility": context.get("volatility_metrics", {})
    }

def postprocess(output: AgentOutput) -> AgentOutput:
    """Post-process options agent output"""
    # Add options-specific risk flags
    if not output.risk_flags:
        output.risk_flags = ["Monitor time decay", "Check volatility changes"]
        
    return output
