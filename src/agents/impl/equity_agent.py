
"""
Equity Agent Implementation  
"""

from typing import Dict, Any
from ..core.contracts import AgentOutput

DEFAULT_SCHEMA = {
    "verdict": "string",
    "confidence": "number",
    "rationale": "string",
    "insights": "array", 
    "actions": "array"
}

def build_inputs(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build inputs for equity agent"""
    return {
        "predictions_snapshot": context.get("predictions", []),
        "kpi_snapshot": context.get("kpis", {}),
        "market_context": context.get("market_data", {}),
        "sector_trends": context.get("sector_analysis", {})
    }

def postprocess(output: AgentOutput) -> AgentOutput:
    """Post-process equity agent output"""
    # Ensure equity-specific actions
    if not output.actions:
        output.actions = ["Monitor price levels", "Review fundamentals"]
        
    return output
