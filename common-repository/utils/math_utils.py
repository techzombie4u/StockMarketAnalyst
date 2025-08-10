
"""
Mathematical Utilities
"""

import numpy as np
from typing import List, Optional, Union

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division with default fallback"""
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100

def calculate_moving_average(values: List[float], window: int) -> List[float]:
    """Calculate simple moving average"""
    if len(values) < window:
        return [np.mean(values)] * len(values)
    
    result = []
    for i in range(len(values)):
        if i < window - 1:
            result.append(np.mean(values[:i+1]))
        else:
            result.append(np.mean(values[i-window+1:i+1]))
    
    return result

def calculate_volatility(prices: List[float], window: int = 30) -> float:
    """Calculate rolling volatility (standard deviation of returns)"""
    if len(prices) < 2:
        return 0.0
    
    # Calculate returns
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] != 0:
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
    
    if len(returns) < window:
        return np.std(returns) * np.sqrt(252) * 100  # Annualized volatility
    
    # Rolling volatility
    recent_returns = returns[-window:]
    return np.std(recent_returns) * np.sqrt(252) * 100

def normalize_score(value: float, min_val: float, max_val: float, 
                   target_min: float = 0.0, target_max: float = 100.0) -> float:
    """Normalize a value to a target range"""
    if max_val == min_val:
        return target_min
    
    normalized = (value - min_val) / (max_val - min_val)
    return target_min + normalized * (target_max - target_min)

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(value, max_val))

def round_to_precision(value: float, precision: int = 2) -> float:
    """Round to specified decimal places"""
    try:
        return round(float(value), precision)
    except (TypeError, ValueError):
        return 0.0

def calculate_compound_return(returns: List[float]) -> float:
    """Calculate compound return from a list of periodic returns"""
    if not returns:
        return 0.0
    
    compound = 1.0
    for ret in returns:
        compound *= (1 + ret / 100)
    
    return (compound - 1) * 100

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 5.0) -> float:
    """Calculate Sharpe ratio"""
    if not returns or len(returns) < 2:
        return 0.0
    
    excess_returns = [r - risk_free_rate for r in returns]
    mean_excess = np.mean(excess_returns)
    std_excess = np.std(excess_returns)
    
    if std_excess == 0:
        return 0.0
    
    return mean_excess / std_excess

def calculate_max_drawdown(values: List[float]) -> float:
    """Calculate maximum drawdown from a series of values"""
    if len(values) < 2:
        return 0.0
    
    peak = values[0]
    max_dd = 0.0
    
    for value in values:
        if value > peak:
            peak = value
        else:
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)
    
    return max_dd * 100
