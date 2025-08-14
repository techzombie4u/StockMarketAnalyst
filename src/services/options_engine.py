
import math
import datetime as dt
from typing import Dict, Any, List
from src.live_data.provider import LiveProvider, Chain, LiveDataError

def nearest_expiry_for_window(expiries: List[str], days_target: int) -> str:
    """Choose the expiry whose (expiry - today).days is closest to days_target"""
    today = dt.date.today()
    
    def days_diff(e):
        y, m, d = map(int, e.split("-"))
        return abs((dt.date(y, m, d) - today).days - days_target)
    
    if not expiries:
        raise LiveDataError("No expiries available")
    
    return sorted(expiries, key=days_diff)[0]

def select_atm_strangle(chain: Chain) -> Dict[str, Any]:
    """Select ATM strangle strategy with real calculations"""
    spot = chain.spot
    step = chain.step or 100.0
    
    # Find ATM strike
    atm = round(spot / step) * step
    
    # Pick call = next step above ATM, put = next step below ATM
    call_strike = atm + step
    put_strike = atm - step
    
    def find_quote(quotes, strike):
        """Find quote at specific strike and calculate mid price"""
        for q in quotes:
            if abs(q.strike - strike) < 1e-6:
                mid = (q.bid + q.ask) / 2 if (q.bid and q.ask and q.bid > 0 and q.ask > 0) else (q.bid or q.ask or 0)
                return q, mid
        return None, 0
    
    call_q, call_mid = find_quote(chain.calls, call_strike)
    put_q, put_mid = find_quote(chain.puts, put_strike)
    
    if not call_q or not put_q:
        # Try to find closest strikes if exact ATM not available
        call_strikes = sorted([q.strike for q in chain.calls if q.strike > spot])
        put_strikes = sorted([q.strike for q in chain.puts if q.strike < spot], reverse=True)
        
        if call_strikes and put_strikes:
            call_strike = call_strikes[0]
            put_strike = put_strikes[0]
            call_q, call_mid = find_quote(chain.calls, call_strike)
            put_q, put_mid = find_quote(chain.puts, put_strike)
        
        if not call_q or not put_q:
            raise LiveDataError(f"Cannot find suitable strangle strikes for {chain.symbol}")
    
    # Calculate strategy metrics
    net_credit = call_mid + put_mid
    
    # Average IV
    iv = 0.0
    if call_q.iv and put_q.iv:
        iv = (call_q.iv + put_q.iv) / 2
    elif call_q.iv or put_q.iv:
        iv = call_q.iv or put_q.iv
    
    # Theta (positive for short positions)
    theta_day = -(call_q.theta + put_q.theta) if (call_q.theta and put_q.theta) else 0
    
    # Breakevens
    be_min = put_strike - net_credit
    be_max = call_strike + net_credit
    
    # Estimate margin (exchange-specific, this is indicative)
    est_margin = max(0.2 * spot, 0.15 * spot * 1.5)  # Conservative estimate
    
    # ROI on margin
    roi_on_margin = (net_credit / est_margin * 100) if est_margin > 0 else 0
    
    # Market stability based on IV
    if iv < 20:
        market_stability = "Low"
    elif iv < 35:
        market_stability = "Medium"
    else:
        market_stability = "High"
    
    # Max loss heuristic (2σ approach)
    if iv < 20:
        max_loss_2s = "Low"
    elif iv < 35:
        max_loss_2s = "Moderate"
    else:
        max_loss_2s = "High"
    
    # IV rank (simplified - would need historical data for accurate calculation)
    iv_rank = min(100, max(0, iv * 2.5))  # Rough approximation
    
    # Breakout probability (simplified calculation based on strikes vs spot)
    range_width = be_max - be_min
    prob_factor = range_width / spot if spot > 0 else 0
    breakout_prob = min(0.5, prob_factor * 0.3)  # Conservative estimate
    
    return {
        "spot": round(spot, 2),
        "call": call_strike,
        "put": put_strike,
        "net_credit": round(net_credit, 2),
        "theta_day": round(theta_day, 2),
        "roi_on_margin": round(roi_on_margin, 1),
        "breakeven_min": round(be_min, 2),
        "breakeven_max": round(be_max, 2),
        "iv": round(iv, 1),
        "iv_rank": round(iv_rank, 1),
        "market_stability": market_stability,
        "max_loss_2s": max_loss_2s,
        "breakout_prob": breakout_prob
    }

def get_dte_from_timeframe(timeframe: str) -> int:
    """Convert timeframe to target DTE"""
    timeframe_map = {
        "45D": 45,
        "30D": 30,
        "21D": 21,
        "14D": 14,
        "10D": 10,
        "7D": 7
    }
    return timeframe_map.get(timeframe, 30)
