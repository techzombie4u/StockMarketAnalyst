
# src/agents/builtin_agents.py
from typing import Dict, Any
import time, random

def run_new_ai_analyzer() -> Dict[str, Any]:
    # minimal dummy output used by tests; keep deterministic fields
    return {
        "agent": "new_ai_analyzer",
        "timestamp": int(time.time()),
        "summary": "AI analyzer completed",
        "metrics": {"score": round(random.uniform(0.6, 0.9), 2)},
        "success": True
    }

def run_sentiment_analyzer() -> Dict[str, Any]:
    return {
        "agent": "sentiment_analyzer",
        "timestamp": int(time.time()),
        "summary": "Sentiment analyzer completed",
        "metrics": {"bullish_pct": round(random.uniform(45, 65), 1)},
        "success": True
    }
