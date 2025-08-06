
"""
Short Strangle Options Strategy Engine
Implements low-risk monthly passive income strategy using Tier 1 stocks
"""

import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf

logger = logging.getLogger(__name__)

class ShortStrangleEngine:
    """Engine for calculating short strangle opportunities"""
    
    # Tier 1 stocks specifically chosen for passive income
    TIER_1_STOCKS = {
        'RELIANCE.NS': {'name': 'RELIANCE', 'sector': 'Energy', 'iv_range': (18, 25)},
        'HDFCBANK.NS': {'name': 'HDFC BANK', 'sector': 'Banking', 'iv_range': (15, 22)},
        'TCS.NS': {'name': 'TCS', 'sector': 'IT', 'iv_range': (12, 18)},
        'ITC.NS': {'name': 'ITC', 'sector': 'FMCG', 'iv_range': (15, 20)},
        'INFY.NS': {'name': 'INFY', 'sector': 'IT', 'iv_range': (16, 23)},
        'HINDUNILVR.NS': {'name': 'HUL', 'sector': 'FMCG', 'iv_range': (12, 18)}
    }
    
    def __init__(self):
        self.options_file = "data/tracking/options_signals.json"
        
    def calculate_implied_volatility(self, symbol: str, price_data: Dict) -> float:
        """Calculate estimated IV based on historical volatility"""
        try:
            if 'historical_volatility' in price_data:
                hv = price_data['historical_volatility']
                # IV typically 1.2-1.5x HV for these stocks
                iv_multiplier = 1.3
                estimated_iv = hv * iv_multiplier
                
                # Cap IV within realistic ranges for Tier 1 stocks
                stock_info = self.TIER_1_STOCKS.get(symbol, {})
                iv_range = stock_info.get('iv_range', (15, 25))
                return max(iv_range[0], min(iv_range[1], estimated_iv))
            
            # Fallback to sector-based IV estimates
            stock_info = self.TIER_1_STOCKS.get(symbol, {})
            iv_range = stock_info.get('iv_range', (15, 25))
            return (iv_range[0] + iv_range[1]) / 2
            
        except Exception as e:
            logger.warning(f"IV calculation failed for {symbol}: {e}")
            return 18.0  # Conservative default
    
    def calculate_option_premium(self, spot: float, strike: float, days_to_expiry: int, 
                                iv: float, option_type: str) -> float:
        """
        Simplified Black-Scholes estimation for option premium
        Using realistic assumptions for Indian options market
        """
        try:
            # Risk-free rate (approximate Indian T-bill rate)
            r = 0.065
            
            # Time to expiry in years
            t = days_to_expiry / 365.0
            
            # Volatility as decimal
            vol = iv / 100.0
            
            # Moneyness
            moneyness = spot / strike if option_type == 'call' else strike / spot
            
            # Simplified premium calculation based on time value and intrinsic value
            time_value = spot * vol * math.sqrt(t) * 0.4  # Approximation factor
            
            if option_type == 'call':
                intrinsic = max(0, spot - strike)
            else:  # put
                intrinsic = max(0, strike - spot)
            
            premium = intrinsic + time_value
            
            # Adjust for moneyness (OTM options have lower premiums)
            if moneyness < 1:  # OTM
                premium *= (0.3 + 0.7 * moneyness)
            
            # Minimum premium for liquidity
            return max(premium, spot * 0.001)  # At least 0.1% of spot
            
        except Exception as e:
            logger.warning(f"Premium calculation failed: {e}")
            # Fallback: percentage-based estimation
            otm_distance = abs(spot - strike) / spot
            return spot * (0.01 + otm_distance * 0.02)
    
    def calculate_margin_requirement(self, spot: float, call_strike: float, 
                                   put_strike: float, call_premium: float, 
                                   put_premium: float) -> float:
        """Calculate margin requirement for short strangle"""
        try:
            # Indian brokers typically require:
            # Max(Call margin, Put margin) + Premium received
            
            # Call margin: 20% of spot + call premium - OTM amount
            call_otm = max(0, call_strike - spot)
            call_margin = 0.20 * spot + call_premium - call_otm
            
            # Put margin: 20% of strike + put premium - OTM amount  
            put_otm = max(0, spot - put_strike)
            put_margin = 0.20 * put_strike + put_premium - put_otm
            
            # Total margin is max of both legs
            base_margin = max(call_margin, put_margin)
            
            # Add buffer for volatility
            total_margin = base_margin * 1.1
            
            return max(total_margin, spot * 0.15)  # Minimum 15% of spot
            
        except Exception as e:
            logger.warning(f"Margin calculation failed: {e}")
            return spot * 0.25  # Conservative fallback
    
    def get_real_time_price(self, symbol: str) -> float:
        """Fetch real-time price from Yahoo Finance with multiple fallbacks"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Try 1-minute data first (most recent)
            try:
                hist_1m = ticker.history(period="1d", interval="1m")
                if not hist_1m.empty and len(hist_1m) > 0:
                    price = float(hist_1m['Close'].iloc[-1])
                    if price > 0:
                        logger.info(f"Real-time 1m price for {symbol}: ₹{price:.2f}")
                        return price
            except Exception as e:
                logger.warning(f"1-minute data failed for {symbol}: {e}")
            
            # Fallback to 5-minute data
            try:
                hist_5m = ticker.history(period="1d", interval="5m")
                if not hist_5m.empty and len(hist_5m) > 0:
                    price = float(hist_5m['Close'].iloc[-1])
                    if price > 0:
                        logger.info(f"Real-time 5m price for {symbol}: ₹{price:.2f}")
                        return price
            except Exception as e:
                logger.warning(f"5-minute data failed for {symbol}: {e}")
            
            # Fallback to daily data
            try:
                hist_daily = ticker.history(period="5d")
                if not hist_daily.empty and len(hist_daily) > 0:
                    price = float(hist_daily['Close'].iloc[-1])
                    if price > 0:
                        logger.info(f"Daily price for {symbol}: ₹{price:.2f}")
                        return price
            except Exception as e:
                logger.warning(f"Daily data failed for {symbol}: {e}")
            
            # Final fallback - try ticker info
            try:
                info = ticker.info
                if info and 'currentPrice' in info:
                    price = float(info['currentPrice'])
                    if price > 0:
                        logger.info(f"Info price for {symbol}: ₹{price:.2f}")
                        return price
            except Exception as e:
                logger.warning(f"Ticker info failed for {symbol}: {e}")
                
        except Exception as e:
            logger.error(f"Complete price fetch failed for {symbol}: {e}")
        
        logger.error(f"❌ Could not fetch any price data for {symbol}")
        return None

    def calculate_strangle_metrics(self, symbol: str, current_price: float, 
                                 predictions: Dict, timeframe: str = '30D') -> Dict:
        """Calculate all metrics for a short strangle strategy"""
        try:
            # Get real-time price instead of cached price
            real_price = self.get_real_time_price(symbol)
            if real_price:
                current_price = real_price
                logger.info(f"Using real-time price for {symbol}: ₹{current_price:.2f}")
            else:
                logger.warning(f"Could not fetch real-time price for {symbol}, using cached: ₹{current_price:.2f}")

            # Get prediction confidence
            pred_key = f'pred_{timeframe.lower()}'
            confidence = predictions.get('confidence', 75.0)
            predicted_change = predictions.get(pred_key, 0.0)
            
            # Strike selection based on timeframe and volatility
            if timeframe == '5D':
                otm_percentage = 0.02  # 2% OTM for short term
                days_to_expiry = 5
            elif timeframe == '10D':
                otm_percentage = 0.03  # 3% OTM
                days_to_expiry = 10
            else:  # 30D
                otm_percentage = 0.04  # 4% OTM for monthly
                days_to_expiry = 30
            
            # Calculate strikes
            call_strike = current_price * (1 + otm_percentage)
            put_strike = current_price * (1 - otm_percentage)
            
            # Round strikes to nearest 0.5 or 1.0 based on price level
            if current_price > 1000:
                strike_increment = 10
            elif current_price > 500:
                strike_increment = 5
            else:
                strike_increment = 2.5
                
            call_strike = round(call_strike / strike_increment) * strike_increment
            put_strike = round(put_strike / strike_increment) * strike_increment
            
            # Calculate IV and premiums
            iv = self.calculate_implied_volatility(symbol, predictions)
            call_premium = self.calculate_option_premium(current_price, call_strike, 
                                                       days_to_expiry, iv, 'call')
            put_premium = self.calculate_option_premium(current_price, put_strike, 
                                                      days_to_expiry, iv, 'put')
            
            total_premium = call_premium + put_premium
            
            # Calculate breakeven points
            breakeven_upper = call_strike + total_premium
            breakeven_lower = put_strike - total_premium
            breakeven_range_pct = ((breakeven_upper - breakeven_lower) / current_price) * 100
            
            # Calculate margin and ROI
            margin_required = self.calculate_margin_requirement(current_price, call_strike, 
                                                              put_strike, call_premium, put_premium)
            roi_percentage = (total_premium / margin_required) * 100
            
            # Annualized ROI
            annualized_roi = roi_percentage * (365 / days_to_expiry)
            
            # Risk assessment
            if breakeven_range_pct >= 6:
                risk_level = 'Safe'
                risk_color = 'success'
            elif breakeven_range_pct >= 4:
                risk_level = 'Moderate' 
                risk_color = 'warning'
            else:
                risk_level = 'Risky'
                risk_color = 'danger'
            
            # Strategy classification based on ROI and risk
            if roi_percentage >= 25 and risk_level == 'Safe':
                strategy_type = 'aggressive'
            elif roi_percentage >= 15 and risk_level in ['Safe', 'Moderate']:
                strategy_type = 'moderate'
            else:
                strategy_type = 'conservative'
            
            return {
                'symbol': self.TIER_1_STOCKS.get(symbol, {}).get('name', symbol.replace('.NS', '')),
                'current_price': round(current_price, 2),
                'call_strike': round(call_strike, 2),
                'put_strike': round(put_strike, 2),
                'call_premium': round(call_premium, 2),
                'put_premium': round(put_premium, 2),
                'total_premium': round(total_premium, 2),
                'breakeven_upper': round(breakeven_upper, 2),
                'breakeven_lower': round(breakeven_lower, 2),
                'breakeven_range_pct': round(breakeven_range_pct, 2),
                'margin_required': round(margin_required, 0),
                'expected_roi': round(roi_percentage, 2),
                'annualized_roi': round(annualized_roi, 2),
                'confidence': round(confidence, 1),
                'implied_volatility': round(iv, 1),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'strategy_type': strategy_type,
                'timeframe': timeframe,
                'days_to_expiry': days_to_expiry,
                'sector': self.TIER_1_STOCKS.get(symbol, {}).get('sector', 'Unknown'),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating strangle metrics for {symbol}: {e}")
            return None
    
    def generate_all_strategies(self, stock_data: List[Dict], timeframe: str = '30D') -> List[Dict]:
        """Generate strangle strategies for all Tier 1 stocks"""
        strategies = []
        
        for stock in stock_data:
            try:
                symbol_yahoo = None
                stock_symbol = stock.get('symbol', '')
                
                # Map to Yahoo Finance symbols
                for yf_symbol, info in self.TIER_1_STOCKS.items():
                    if info['name'] == stock_symbol or stock_symbol in info['name']:
                        symbol_yahoo = yf_symbol
                        break
                
                if not symbol_yahoo:
                    continue
                
                # Get real-time price first, fallback to cached price
                real_price = self.get_real_time_price(symbol_yahoo)
                current_price = real_price if real_price else stock.get('current_price', 0)
                
                if current_price <= 0:
                    logger.warning(f"No valid price found for {stock_symbol}")
                    continue
                
                # Create predictions dict from stock data
                predictions = {
                    'confidence': stock.get('confidence', 75.0),
                    'pred_5d': stock.get('pred_5d', 0.0),
                    'pred_10d': stock.get('pred_1mo', 0.0) * 0.33,  # Approximate 10d from 1mo
                    'pred_30d': stock.get('pred_1mo', 0.0),
                    'historical_volatility': self._estimate_volatility(stock)
                }
                
                strategy = self.calculate_strangle_metrics(symbol_yahoo, current_price, 
                                                         predictions, timeframe)
                if strategy:
                    strategies.append(strategy)
                    
            except Exception as e:
                logger.warning(f"Failed to generate strategy for {stock.get('symbol', 'unknown')}: {e}")
                continue
        
        # Sort by ROI descending
        strategies.sort(key=lambda x: x.get('expected_roi', 0), reverse=True)
        
        # Save to file
        self._save_strategies(strategies, timeframe)
        
        return strategies
    
    def _estimate_volatility(self, stock: Dict) -> float:
        """Estimate historical volatility from stock data"""
        try:
            # Use technical indicators as proxy for volatility
            rsi = stock.get('rsi', 50)
            
            # Higher RSI deviation from 50 suggests higher volatility
            rsi_deviation = abs(rsi - 50) / 50
            base_volatility = 15 + (rsi_deviation * 10)
            
            return min(30, max(10, base_volatility))
            
        except Exception:
            return 18.0  # Default volatility
    
    def _save_strategies(self, strategies: List[Dict], timeframe: str):
        """Save strategies to JSON file"""
        try:
            import os
            os.makedirs(os.path.dirname(self.options_file), exist_ok=True)
            
            # Load existing data
            try:
                with open(self.options_file, 'r') as f:
                    all_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                all_data = {}
            
            # Update with new strategies
            all_data[timeframe] = {
                'strategies': strategies,
                'last_updated': datetime.now().isoformat(),
                'total_opportunities': len(strategies),
                'high_confidence_count': len([s for s in strategies if s.get('confidence', 0) >= 80])
            }
            
            with open(self.options_file, 'w') as f:
                json.dump(all_data, f, indent=2, default=str)
                
            logger.info(f"Saved {len(strategies)} strategies for {timeframe}")
            
        except Exception as e:
            logger.error(f"Failed to save strategies: {e}")
    
    def load_strategies(self, timeframe: str = '30D') -> Dict:
        """Load strategies from JSON file"""
        try:
            with open(self.options_file, 'r') as f:
                all_data = json.load(f)
            return all_data.get(timeframe, {'strategies': [], 'total_opportunities': 0})
        except (FileNotFoundError, json.JSONDecodeError):
            return {'strategies': [], 'total_opportunities': 0, 'high_confidence_count': 0}
    
    def generate_demo_strategies(self, timeframe: str = '30D') -> List[Dict]:
        """Generate demo strategies as fallback with real-time prices"""
        demo_strategies = []
        
        logger.info(f"Generating demo strategies for {timeframe} with real-time price fetching")
        
        # Create demo data for each Tier 1 stock with fallback prices
        base_prices = {
            'RELIANCE': 2800,
            'HDFC BANK': 1650, 
            'TCS': 3950,
            'ITC': 465,
            'INFY': 1720,
            'HUL': 2420
        }
        
        for symbol, base_price in base_prices.items():
            try:
                # Map to correct Yahoo Finance symbol
                yf_symbol = f"{symbol.replace(' ', '')}.NS" if symbol != 'HDFC BANK' else 'HDFCBANK.NS'
                
                logger.info(f"Demo strategy: Fetching price for {symbol} ({yf_symbol})")
                
                # Try to get real-time price, fallback to base price
                real_price = self.get_real_time_price(yf_symbol)
                current_price = real_price if real_price and real_price > 0 else base_price
                
                if real_price:
                    logger.info(f"✅ Demo: Using real-time price for {symbol}: ₹{current_price:.2f}")
                else:
                    logger.warning(f"⚠️ Demo: Using fallback price for {symbol}: ₹{current_price:.2f}")
                
                # Enhanced predictions for demo
                predictions = {
                    'confidence': 82.0 if real_price else 75.0,  # Higher confidence for real-time data
                    'pred_5d': 2.3 if real_price else 2.0,
                    'pred_10d': 4.8 if real_price else 4.2,
                    'pred_30d': 9.5 if real_price else 8.5,
                    'historical_volatility': 18.5
                }
                
                strategy = self.calculate_strangle_metrics(yf_symbol, current_price, predictions, timeframe)
                if strategy:
                    # Mark as demo but with real-time data if available
                    strategy['data_quality'] = 'real_time' if real_price else 'demo_fallback'
                    demo_strategies.append(strategy)
                    logger.info(f"✅ Demo strategy created for {symbol}: ROI {strategy.get('expected_roi', 0):.1f}%")
                    
            except Exception as e:
                logger.error(f"❌ Error creating demo strategy for {symbol}: {e}")
                continue
        
        logger.info(f"Generated {len(demo_strategies)} demo strategies")
        return demo_strategies
