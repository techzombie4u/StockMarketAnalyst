
"""
Communication Agent Implementation
"""

from typing import Dict, Any
from ..core.contracts import AgentOutput

DEFAULT_SCHEMA = {
    "verdict": "string",
    "confidence": "number",
    "insights": "array",
    "actions": "array"
}

def build_inputs(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build inputs for communication agent"""
    return {
        "kpi_snapshot": context.get("kpis", {}),
        "predictions": context.get("predictions", []),
        "market_context": context.get("market_data", {}),
        "performance_summary": context.get("performance", {})
    }

def postprocess(output: AgentOutput) -> AgentOutput:
    """Post-process communication agent output"""
    # Add communication-focused insights
    if not output.insights:
        output.insights = ["Update stakeholders", "Prepare performance report"]
        
    return output
