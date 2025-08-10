
"""
AI Verdict Generator (Stub Implementation)
Generates AI verdicts and confidence scores for stocks
"""

import random
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

AI_VERDICTS = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]

def ai_verdict_stub(symbol: str, score: float = None, volume: float = None, 
                   trend: str = None) -> Tuple[str, float]:
    """
    Generate AI verdict and confidence (stub implementation)
    
    Args:
        symbol: Stock symbol
        score: Current composite score
        volume: Trading volume
        trend: Trend indicator
    
    Returns:
        Tuple of (verdict, confidence_percentage)
    """
    try:
        # Use score to influence verdict (higher score = more bullish)
        if score is None:
            score = random.uniform(40, 90)
        
        # Map score to verdict with some randomness
        if score >= 85:
            verdict_weights = [0.6, 0.3, 0.1, 0.0, 0.0]  # Strong Buy heavy
        elif score >= 75:
            verdict_weights = [0.3, 0.5, 0.2, 0.0, 0.0]  # Buy heavy
        elif score >= 60:
            verdict_weights = [0.1, 0.3, 0.5, 0.1, 0.0]  # Hold heavy
        elif score >= 45:
            verdict_weights = [0.0, 0.1, 0.3, 0.5, 0.1]  # Sell heavy
        else:
            verdict_weights = [0.0, 0.0, 0.1, 0.3, 0.6]  # Strong Sell heavy
        
        # Select verdict based on weights
        verdict = random.choices(AI_VERDICTS, weights=verdict_weights)[0]
        
        # Generate confidence based on score consistency
        base_confidence = min(95, max(60, score + random.uniform(-15, 15)))
        
        # Add symbol-based consistency (same symbol should have similar confidence)
        symbol_seed = sum(ord(c) for c in symbol) % 100
        confidence = min(95, max(60, base_confidence + (symbol_seed - 50) * 0.2))
        
        return verdict, round(confidence, 1)
        
    except Exception as e:
        logger.error(f"Error generating AI verdict for {symbol}: {e}")
        return "Hold", 70.0

def get_verdict_color(verdict: str) -> str:
    """Get CSS class for verdict color"""
    color_map = {
        "Strong Buy": "verdict-strong-buy",
        "Buy": "verdict-buy", 
        "Hold": "verdict-hold",
        "Sell": "verdict-sell",
        "Strong Sell": "verdict-strong-sell"
    }
    return color_map.get(verdict, "verdict-hold")
