
"""
Mathematical utility functions
"""

from typing import Union, Optional
import numpy as np

def safe_divide(a: Union[int, float], b: Union[int, float], default: Union[int, float] = 0) -> Union[int, float]:
    """Safely divide two numbers, returning default if division by zero"""
    try:
        if b == 0:
            return default
        return a / b
    except (TypeError, ZeroDivisionError):
        return default

def safe_percentage(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """Calculate percentage safely"""
    try:
        if denominator == 0:
            return default
        return (numerator / denominator) * 100
    except (TypeError, ZeroDivisionError):
        return default

def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

def calculate_rsi(prices: list, period: int = 14) -> Optional[float]:
    """Calculate RSI (Relative Strength Index)"""
    try:
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    except Exception:
        return None
