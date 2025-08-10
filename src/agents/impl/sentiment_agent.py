
"""
Sentiment Agent Implementation
"""

from typing import Dict, Any
from ..core.contracts import AgentOutput

DEFAULT_SCHEMA = {
    "verdict": "string",
    "confidence": "number",
    "insights": "array", 
    "risk_flags": "array"
}

def build_inputs(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build inputs for sentiment agent"""
    return {
        "sentiment_aggregates": context.get("sentiment_data", {}),
        "news_summary": context.get("news_headlines", []),
        "market_context": context.get("market_data", {}),
        "social_signals": context.get("social_sentiment", {})
    }

def postprocess(output: AgentOutput) -> AgentOutput:
    """Post-process sentiment agent output"""
    # Add sentiment-specific insights
    if not output.insights:
        output.insights = ["Monitor sentiment shifts", "Track news impact"]
        
    return output
