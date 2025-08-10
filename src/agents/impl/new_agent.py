
"""
New Opportunities Agent Implementation
"""

from typing import Dict, Any
from ..core.contracts import AgentOutput

DEFAULT_SCHEMA = {
    "verdict": "string",
    "confidence": "number",
    "insights": "array",
    "suggested_actions": "array"
}

def build_inputs(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build inputs for new opportunities agent"""
    return {
        "context": context.get("general_context", {}),
        "product": context.get("product_type", "equity"),
        "market_trends": context.get("trend_analysis", {}),
        "sector_rotation": context.get("sector_data", {})
    }

def postprocess(output: AgentOutput) -> AgentOutput:
    """Post-process new opportunities agent output"""
    # Focus on opportunity identification
    if not output.insights:
        output.insights = ["Scan for new opportunities", "Monitor emerging trends"]
        
    return output
