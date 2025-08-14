import math
import datetime as dt
from typing import Dict, Any, List
from src.live_data.provider import LiveProvider, Chain, LiveDataError

# Create the main options blueprint
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

options_bp = Blueprint('options_bp', __name__)

class OptionsEngine:
    """Options calculation and analysis engine"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_option_metrics(self, symbol, spot_price, strike, option_type, dte):
        """Calculate basic option metrics"""
        try:
            # Simple Black-Scholes approximation
            moneyness = spot_price / strike if option_type == 'CE' else strike / spot_price
            time_factor = max(0.01, dte / 365.0)

            # Basic pricing
            if option_type == 'CE':
                intrinsic = max(0, spot_price - strike)
                time_value = spot_price * 0.02 * math.sqrt(time_factor) * moneyness
            else:
                intrinsic = max(0, strike - spot_price)
                time_value = spot_price * 0.018 * math.sqrt(time_factor) * (2 - moneyness)

            premium = intrinsic + time_value

            return {
                'premium': round(premium, 2),
                'intrinsic': round(intrinsic, 2),
                'time_value': round(time_value, 2),
                'moneyness': round(moneyness, 3)
            }

        except Exception as e:
            self.logger.error(f"Error calculating option metrics: {e}")
            return {
                'premium': 0,
                'intrinsic': 0,
                'time_value': 0,
                'moneyness': 1.0
            }

    def generate_options_chain(self, symbol, spot_price):
        """Generate options chain data"""
        try:
            # Generate expiry dates (next 3 Thursdays)
            expiries = []
            current_date = datetime.now()
            for i in range(3):
                # Find next Thursday
                days_ahead = (3 - current_date.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                next_thursday = current_date + timedelta(days=days_ahead + (i * 7))
                expiries.append(next_thursday.strftime('%Y-%m-%d'))

            # Generate strikes around spot price
            strikes = []
            base_strike = round(spot_price / 50) * 50  # Round to nearest 50
            for i in range(-10, 11):  # ±10 strikes
                strikes.append(base_strike + (i * 50))

            # Generate CE and PE prices
            ce_prices = {}
            pe_prices = {}

            for expiry in expiries:
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                dte = (expiry_date - current_date).days

                ce_prices[expiry] = {}
                pe_prices[expiry] = {}

                for strike in strikes:
                    ce_metrics = self.calculate_option_metrics(symbol, spot_price, strike, 'CE', dte)
                    pe_metrics = self.calculate_option_metrics(symbol, spot_price, strike, 'PE', dte)

                    ce_prices[expiry][str(strike)] = ce_metrics['premium']
                    pe_prices[expiry][str(strike)] = pe_metrics['premium']

            # Calculate IV and IV Rank based on symbol
            symbol_hash = hash(symbol) % 100
            iv = 18 + (symbol_hash % 20)  # 18-38%
            iv_rank = 30 + (symbol_hash % 40)  # 30-70%

            # Get lot size
            lot_sizes = {
                'RELIANCE': 505, 'TCS': 300, 'HDFCBANK': 550, 'INFY': 300,
                'ICICIBANK': 1375, 'WIPRO': 3000, 'LT': 225, 'MARUTI': 100
            }
            lot_size = lot_sizes.get(symbol, 1000)

            return {
                'lot_size': lot_size,
                'expiries': expiries,
                'strikes': strikes,
                'ce_prices': ce_prices,
                'pe_prices': pe_prices,
                'iv': iv,
                'iv_rank': iv_rank
            }

        except Exception as e:
            self.logger.error(f"Error generating options chain for {symbol}: {e}")
            return None

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