
"""
Options calculation engine with deterministic Black-Scholes implementation
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class Greeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float = 0.0

@dataclass
class OptionPosition:
    position_id: str
    symbol: str
    strategy_type: str
    entry_date: str
    status: str  # "open" | "closed"
    pnl: float
    current_value: float
    roi_pct: float
    margin: float
    payoff: Dict[str, List[float]]  # {"x": [], "y": []}
    greeks: Dict[str, float]
    call_strike: float = 0.0
    put_strike: float = 0.0
    credit: float = 0.0
    breakeven_low: float = 0.0
    breakeven_high: float = 0.0

class OptionsEngine:
    def __init__(self):
        self.positions_file = "data/persistent/options_positions.json"
        self.risk_free_rate = 0.065  # 6.5% for Indian markets
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.positions_file), exist_ok=True)

    def norm_cdf(self, x: float) -> float:
        """Cumulative distribution function for standard normal distribution"""
        # Approximation using error function
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    def norm_pdf(self, x: float) -> float:
        """Probability density function for standard normal distribution"""
        return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

    def black_scholes_price(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Calculate Black-Scholes option price"""
        try:
            if T <= 0:
                return max(0, S - K) if option_type == 'call' else max(0, K - S)
            
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            if option_type == 'call':
                price = S * self.norm_cdf(d1) - K * math.exp(-r * T) * self.norm_cdf(d2)
            else:  # put
                price = K * math.exp(-r * T) * self.norm_cdf(-d2) - S * self.norm_cdf(-d1)
            
            return max(0.01, price)  # Minimum price of 1 paisa
            
        except (ValueError, OverflowError, ZeroDivisionError):
            # Fallback to intrinsic value
            if option_type == 'call':
                return max(0.01, S - K)
            else:
                return max(0.01, K - S)

    def calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Greeks:
        """Calculate option Greeks using Black-Scholes model"""
        try:
            if T <= 0:
                return Greeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)
            
            d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            if option_type == 'call':
                delta = self.norm_cdf(d1)
                rho = K * T * math.exp(-r * T) * self.norm_cdf(d2) / 100
            else:  # put
                delta = -self.norm_cdf(-d1)
                rho = -K * T * math.exp(-r * T) * self.norm_cdf(-d2) / 100
            
            gamma = self.norm_pdf(d1) / (S * sigma * math.sqrt(T))
            theta = -(S * self.norm_pdf(d1) * sigma / (2 * math.sqrt(T)) + 
                     r * K * math.exp(-r * T) * self.norm_cdf(d2 if option_type == 'call' else -d2)) / 365
            vega = S * self.norm_pdf(d1) * math.sqrt(T) / 100
            
            return Greeks(
                delta=round(delta, 4),
                gamma=round(gamma, 6),
                theta=round(theta, 4),
                vega=round(vega, 4),
                rho=round(rho, 4)
            )
            
        except (ValueError, OverflowError, ZeroDivisionError):
            return Greeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)

    def calculate_strangle_metrics(self, symbol: str, spot: float, call_strike: float, put_strike: float, 
                                 days_to_expiry: int, implied_vol: float = 0.25) -> Dict[str, Any]:
        """Calculate complete strangle strategy metrics"""
        try:
            T = days_to_expiry / 365.0
            
            # Calculate option prices
            call_price = self.black_scholes_price(spot, call_strike, T, self.risk_free_rate, implied_vol, 'call')
            put_price = self.black_scholes_price(spot, put_strike, T, self.risk_free_rate, implied_vol, 'put')
            
            # Strategy metrics
            credit = call_price + put_price
            breakeven_low = put_strike - credit
            breakeven_high = call_strike + credit
            
            # Margin calculation (simplified SPAN + exposure)
            margin = max(credit * 0.2, spot * 0.1)  # 20% of credit or 10% of spot
            roi_pct = (credit / margin) * 100.0 if margin > 0 else 0.0
            
            # Calculate combined Greeks
            call_greeks = self.calculate_greeks(spot, call_strike, T, self.risk_free_rate, implied_vol, 'call')
            put_greeks = self.calculate_greeks(spot, put_strike, T, self.risk_free_rate, implied_vol, 'put')
            
            # Short strangle Greeks (negative because we're selling)
            combined_greeks = Greeks(
                delta=-(call_greeks.delta + put_greeks.delta),
                gamma=-(call_greeks.gamma + put_greeks.gamma),
                theta=-(call_greeks.theta + put_greeks.theta),
                vega=-(call_greeks.vega + put_greeks.vega),
                rho=-(call_greeks.rho + put_greeks.rho)
            )
            
            # Probability of Profit (approximation using ±1σ coverage)
            one_sigma_move = spot * implied_vol * math.sqrt(T)
            prob_range_low = spot - one_sigma_move
            prob_range_high = spot + one_sigma_move
            
            # PoP if price stays between breakevens
            if prob_range_low > breakeven_low and prob_range_high < breakeven_high:
                pop = 0.68  # ~68% if within 1σ
            elif prob_range_low > breakeven_low or prob_range_high < breakeven_high:
                pop = 0.50  # Partial coverage
            else:
                pop = 0.32  # Outside 1σ range
            
            # Generate payoff diagram
            payoff = self.generate_payoff_diagram(spot, call_strike, put_strike, credit)
            
            return {
                'symbol': symbol,
                'spot_price': round(spot, 2),
                'call_strike': round(call_strike, 2),
                'put_strike': round(put_strike, 2),
                'call_price': round(call_price, 2),
                'put_price': round(put_price, 2),
                'credit': round(credit, 2),
                'breakeven_low': round(breakeven_low, 2),
                'breakeven_high': round(breakeven_high, 2),
                'margin': round(margin, 2),
                'roi_pct': round(roi_pct, 2),
                'probability_profit': round(pop, 3),
                'days_to_expiry': days_to_expiry,
                'implied_volatility': implied_vol,
                'greeks': {
                    'delta': combined_greeks.delta,
                    'gamma': combined_greeks.gamma,
                    'theta': combined_greeks.theta,
                    'vega': combined_greeks.vega,
                    'rho': combined_greeks.rho
                },
                'payoff': payoff
            }
            
        except Exception as e:
            logger.error(f"Error calculating strangle metrics for {symbol}: {e}")
            return self._get_default_metrics(symbol, spot)

    def generate_payoff_diagram(self, spot: float, call_strike: float, put_strike: float, credit: float) -> Dict[str, List[float]]:
        """Generate payoff diagram data points"""
        try:
            # Price range: ±20% from spot
            price_range = spot * 0.4
            min_price = max(1, spot - price_range)
            max_price = spot + price_range
            
            x_points = []
            y_points = []
            
            # Generate 50 points for smooth curve
            for i in range(51):
                price = min_price + (max_price - min_price) * i / 50
                
                # Short strangle P&L
                call_pnl = min(0, call_strike - price) if price > call_strike else 0
                put_pnl = min(0, price - put_strike) if price < put_strike else 0
                total_pnl = credit + call_pnl + put_pnl
                
                x_points.append(round(price, 2))
                y_points.append(round(total_pnl, 2))
            
            return {'x': x_points, 'y': y_points}
            
        except Exception as e:
            logger.error(f"Error generating payoff diagram: {e}")
            # Return simple 3-point diagram
            return {
                'x': [put_strike, spot, call_strike],
                'y': [0, credit, 0]
            }

    def save_position(self, position_data: Dict[str, Any]) -> str:
        """Save a new position and return position ID"""
        try:
            positions = self.load_positions()
            
            position_id = f"POS_{len(positions) + 1}_{int(datetime.now().timestamp())}"
            
            position = OptionPosition(
                position_id=position_id,
                symbol=position_data.get('symbol', ''),
                strategy_type=position_data.get('strategy_type', 'short_strangle'),
                entry_date=datetime.now().isoformat(),
                status='open',
                pnl=0.0,
                current_value=position_data.get('credit', 0.0),
                roi_pct=position_data.get('roi_pct', 0.0),
                margin=position_data.get('margin', 0.0),
                payoff=position_data.get('payoff', {'x': [], 'y': []}),
                greeks=position_data.get('greeks', {}),
                call_strike=position_data.get('call_strike', 0.0),
                put_strike=position_data.get('put_strike', 0.0),
                credit=position_data.get('credit', 0.0),
                breakeven_low=position_data.get('breakeven_low', 0.0),
                breakeven_high=position_data.get('breakeven_high', 0.0)
            )
            
            positions.append(position.__dict__)
            
            with open(self.positions_file, 'w') as f:
                json.dump(positions, f, indent=2)
            
            return position_id
            
        except Exception as e:
            logger.error(f"Error saving position: {e}")
            return ""

    def load_positions(self) -> List[Dict[str, Any]]:
        """Load all positions from storage"""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading positions: {e}")
            return []

    def get_positions(self, status: str = None) -> List[Dict[str, Any]]:
        """Get positions filtered by status"""
        positions = self.load_positions()
        
        if status and status != 'all':
            positions = [p for p in positions if p.get('status', '').lower() == status.lower()]
        
        return positions

    def update_position_pnl(self, position_id: str, current_spot: float) -> bool:
        """Update position P&L based on current market price"""
        try:
            positions = self.load_positions()
            
            for position in positions:
                if position['position_id'] == position_id:
                    # Recalculate current value and P&L
                    call_strike = position.get('call_strike', 0)
                    put_strike = position.get('put_strike', 0)
                    credit = position.get('credit', 0)
                    
                    # Current option values (simplified)
                    call_value = max(0, current_spot - call_strike) if current_spot > call_strike else 0
                    put_value = max(0, put_strike - current_spot) if current_spot < put_strike else 0
                    current_value = call_value + put_value
                    
                    # P&L for short position
                    pnl = credit - current_value
                    position['pnl'] = round(pnl, 2)
                    position['current_value'] = round(current_value, 2)
                    
                    break
            
            with open(self.positions_file, 'w') as f:
                json.dump(positions, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating position P&L: {e}")
            return False

    def _get_default_metrics(self, symbol: str, spot: float) -> Dict[str, Any]:
        """Return default metrics on calculation error"""
        return {
            'symbol': symbol,
            'spot_price': spot,
            'call_strike': spot * 1.05,
            'put_strike': spot * 0.95,
            'call_price': spot * 0.02,
            'put_price': spot * 0.02,
            'credit': spot * 0.04,
            'breakeven_low': spot * 0.91,
            'breakeven_high': spot * 1.09,
            'margin': spot * 0.1,
            'roi_pct': 40.0,
            'probability_profit': 0.65,
            'days_to_expiry': 30,
            'implied_volatility': 0.25,
            'greeks': {'delta': 0.0, 'gamma': 0.0, 'theta': -0.5, 'vega': 0.0, 'rho': 0.0},
            'payoff': {'x': [spot * 0.8, spot, spot * 1.2], 'y': [0, spot * 0.04, 0]}
        }

# Global instance
options_engine = OptionsEngine()
