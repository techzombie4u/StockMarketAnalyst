
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os

logger = logging.getLogger(__name__)

class ShortStrangleEngine:
    """Engine for generating short strangle options strategies with real-time data"""
    
    def __init__(self):
        self.tier1_stocks = [
            'RELIANCE.NS', 'HDFCBANK.NS', 'TCS.NS', 'ITC.NS', 
            'INFY.NS', 'HINDUNILVR.NS'
        ]
        self.cache_file = 'data/tracking/options_signals.json'
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
    def generate_strategies(self, timeframe='30D', force_refresh=False):
        """Generate short strangle strategies with real-time Yahoo Finance data"""
        try:
            logger.info(f"🔄 Generating real-time options strategies for {timeframe}, force_refresh={force_refresh}")
            
            strategies = []
            
            for symbol_ns in self.tier1_stocks:
                try:
                    # Clean symbol for display
                    symbol = symbol_ns.replace('.NS', '')
                    
                    # Get real-time data from Yahoo Finance
                    logger.info(f"📡 Fetching real-time data for {symbol}")
                    stock = yf.Ticker(symbol_ns)
                    
                    # Get current price with multiple fallbacks
                    current_price = self._get_current_price(stock, symbol_ns)
                    if not current_price:
                        logger.warning(f"⚠️ Could not get price data for {symbol}")
                        continue
                    
                    logger.info(f"💰 {symbol}: Current price = ₹{current_price:.2f}")
                    
                    # Get historical volatility
                    historical_vol = self._calculate_historical_volatility(stock, symbol)
                    
                    # Calculate strategy parameters
                    strategy = self._calculate_strangle_strategy(symbol, current_price, timeframe, historical_vol)
                    if strategy:
                        strategies.append(strategy)
                        logger.info(f"✅ Generated strategy for {symbol}: ROI={strategy['expected_roi']:.1f}%")
                    
                except Exception as e:
                        logger.error(f"❌ Error processing {symbol}: {e}")
                        continue
            
            logger.info(f"🎯 Generated {len(strategies)} total real-time strategies")
            
            # Save to cache
            self._save_strategies_to_cache(strategies, timeframe)
            
            return strategies
            
        except Exception as e:
            logger.error(f"❌ Error generating strategies: {e}")
            return []
    
    def _get_current_price(self, stock, symbol_ns):
        """Get current price with multiple fallbacks"""
        try:
            # Method 1: Try info
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
            
            if current_price and current_price > 0:
                return float(current_price)
            
            # Method 2: Try recent history
            hist = stock.history(period='5d')
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                if current_price > 0:
                    return current_price
            
            # Method 3: Try 1 day history
            hist_1d = stock.history(period='1d', interval='1m')
            if not hist_1d.empty:
                current_price = float(hist_1d['Close'].iloc[-1])
                if current_price > 0:
                    return current_price
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol_ns}: {e}")
            return None
    
    def _calculate_historical_volatility(self, stock, symbol):
        """Calculate historical volatility for the stock"""
        try:
            # Get 60 days of historical data
            hist = stock.history(period='60d')
            
            if len(hist) < 10:
                logger.warning(f"⚠️ Insufficient data for volatility calculation for {symbol}")
                return 25.0  # Default volatility
            
            # Calculate daily returns
            returns = hist['Close'].pct_change().dropna()
            
            if len(returns) < 5:
                return 25.0
            
            # Calculate annualized volatility
            daily_vol = returns.std()
            annualized_vol = daily_vol * np.sqrt(252) * 100  # Convert to percentage
            
            # Clamp between reasonable bounds
            volatility = max(10.0, min(80.0, annualized_vol))
            
            logger.info(f"📊 {symbol}: Historical volatility = {volatility:.1f}%")
            return volatility
            
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate volatility for {symbol}: {e}")
            return 25.0  # Default fallback
    
    def _calculate_strangle_strategy(self, symbol, current_price, timeframe, historical_vol):
        """Calculate short strangle strategy parameters with real data"""
        try:
            # Strategy parameters based on timeframe
            if timeframe == '5D':
                otm_percent = 0.025  # 2.5% OTM
                days_to_expiry = 5
                risk_free_rate = 0.065  # 6.5% risk-free rate (India)
            elif timeframe == '10D':
                otm_percent = 0.035  # 3.5% OTM
                days_to_expiry = 10
                risk_free_rate = 0.065
            else:  # 30D
                otm_percent = 0.05  # 5% OTM
                days_to_expiry = 30
                risk_free_rate = 0.065
            
            # Calculate strikes
            call_strike = current_price * (1 + otm_percent)
            put_strike = current_price * (1 - otm_percent)
            
            # Calculate implied volatility (typically higher than historical)
            implied_vol = historical_vol * 1.15  # IV premium
            
            # Calculate option premiums using simplified Black-Scholes
            call_premium = self._calculate_option_premium(
                current_price, call_strike, days_to_expiry, implied_vol, risk_free_rate, 'call'
            )
            put_premium = self._calculate_option_premium(
                current_price, put_strike, days_to_expiry, implied_vol, risk_free_rate, 'put'
            )
            
            total_premium = call_premium + put_premium
            
            # Calculate breakeven points
            breakeven_upper = call_strike + total_premium
            breakeven_lower = put_strike - total_premium
            breakeven_range_pct = ((breakeven_upper - breakeven_lower) / current_price) * 100
            
            # Calculate margin requirement (SPAN + Exposure margin for Indian markets)
            margin_required = self._calculate_margin_requirement(current_price, call_strike, put_strike, total_premium)
            
            # Calculate ROI
            expected_roi = (total_premium / (margin_required / 100)) * 100
            
            # Calculate annualized ROI
            annual_factor = 365 / days_to_expiry
            annualized_roi = expected_roi * annual_factor
            
            # Determine confidence and risk level based on real metrics
            confidence = self._calculate_confidence_score(symbol, breakeven_range_pct, implied_vol, historical_vol)
            risk_level, risk_color = self._determine_risk_level(expected_roi, confidence, implied_vol)
            
            strategy_data = {
                'symbol': str(symbol),
                'current_price': float(current_price),
                'call_strike': float(call_strike),
                'put_strike': float(put_strike),
                'call_premium': float(call_premium),
                'put_premium': float(put_premium),
                'total_premium': float(total_premium),
                'breakeven_upper': float(breakeven_upper),
                'breakeven_lower': float(breakeven_lower),
                'breakeven_range_pct': float(breakeven_range_pct),
                'margin_required': float(margin_required),
                'expected_roi': float(expected_roi),
                'annualized_roi': float(annualized_roi),
                'confidence': float(confidence),
                'implied_volatility': float(implied_vol),
                'historical_volatility': float(historical_vol),
                'risk_level': str(risk_level),
                'risk_color': str(risk_color),
                'days_to_expiry': int(days_to_expiry),
                'timeframe': str(timeframe),
                'last_updated': datetime.now().isoformat(),
                'data_source': 'yahoo_finance_realtime'
            }
            
            return strategy_data
            
        except Exception as e:
            logger.error(f"❌ Error calculating strategy for {symbol}: {e}")
            return None
    
    def _calculate_option_premium(self, spot, strike, days_to_expiry, vol, risk_free_rate, option_type):
        """Calculate option premium using simplified Black-Scholes model"""
        try:
            from scipy.stats import norm
            import math
            
            # Convert inputs
            S = float(spot)
            K = float(strike)
            T = float(days_to_expiry) / 365.0
            r = float(risk_free_rate)
            sigma = float(vol) / 100.0
            
            # Handle edge cases
            if T <= 0:
                if option_type == 'call':
                    return max(0, S - K)
                else:
                    return max(0, K - S)
            
            # Black-Scholes calculation
            d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            if option_type == 'call':
                premium = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            else:  # put
                premium = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            
            # Ensure minimum premium and reasonable bounds
            premium = max(5.0, min(premium, S * 0.2))  # Min ₹5, Max 20% of spot
            
            return float(premium)
            
        except ImportError:
            # Fallback calculation without scipy
            logger.warning("scipy not available, using simplified premium calculation")
            return self._simplified_premium_calculation(spot, strike, days_to_expiry, vol, option_type)
        except Exception as e:
            logger.warning(f"⚠️ Error in Black-Scholes calculation: {e}")
            return self._simplified_premium_calculation(spot, strike, days_to_expiry, vol, option_type)
    
    def _simplified_premium_calculation(self, spot, strike, days_to_expiry, vol, option_type):
        """Simplified option premium calculation as fallback"""
        try:
            time_value = days_to_expiry / 365.0
            volatility = vol / 100.0
            
            # Intrinsic value
            if option_type == 'call':
                intrinsic = max(0, spot - strike)
                moneyness = strike / spot
            else:  # put
                intrinsic = max(0, strike - spot)
                moneyness = spot / strike
            
            # Time value (simplified)
            time_premium = spot * volatility * np.sqrt(time_value) * 0.4
            
            # Adjust for moneyness
            if moneyness > 1.05:  # Deep OTM
                time_premium *= 0.7
            elif moneyness < 0.95:  # ITM
                time_premium *= 1.2
            
            premium = intrinsic + time_premium
            
            # Ensure reasonable bounds
            return max(5.0, min(premium, spot * 0.15))
            
        except Exception as e:
            logger.warning(f"⚠️ Error in simplified premium calculation: {e}")
            return max(10.0, spot * 0.02)  # Absolute fallback
    
    def _calculate_margin_requirement(self, spot_price, call_strike, put_strike, total_premium):
        """Calculate margin requirement for short strangle in Indian markets"""
        try:
            # SPAN margin calculation (simplified)
            # For Indian markets: typically 10-20% of underlying value
            spot_margin_rate = 0.15  # 15% of spot price
            base_margin = spot_price * 100 * spot_margin_rate  # Per lot (assuming 100 shares)
            
            # Exposure margin (additional 3-5% in Indian markets)
            exposure_margin = spot_price * 100 * 0.04  # 4%
            
            # Total margin = SPAN + Exposure - Premium received
            total_margin = base_margin + exposure_margin - (total_premium * 100)
            
            # Ensure minimum margin
            minimum_margin = spot_price * 100 * 0.10  # At least 10%
            
            return max(minimum_margin, total_margin)
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating margin: {e}")
            return spot_price * 100 * 0.20  # 20% fallback
    
    def _calculate_confidence_score(self, symbol, breakeven_range_pct, implied_vol, historical_vol):
        """Calculate confidence score based on real market metrics"""
        try:
            base_confidence = 65.0
            
            # Adjust based on breakeven range
            if breakeven_range_pct > 20:
                base_confidence += 20
            elif breakeven_range_pct > 15:
                base_confidence += 15
            elif breakeven_range_pct > 10:
                base_confidence += 10
            elif breakeven_range_pct > 8:
                base_confidence += 5
            
            # Adjust based on volatility stability
            vol_ratio = implied_vol / historical_vol if historical_vol > 0 else 1.0
            if 0.9 <= vol_ratio <= 1.1:  # Stable volatility
                base_confidence += 10
            elif vol_ratio > 1.5:  # Very high IV
                base_confidence -= 15
            
            # Stock-specific adjustments based on liquidity and stability
            tier1_adjustments = {
                'RELIANCE': 8,    # High liquidity
                'TCS': 10,        # Very stable
                'HDFCBANK': 9,    # Banking sector leader
                'ITC': 5,         # FMCG stability
                'INFY': 7,        # IT sector stability
                'HINDUNILVR': 6   # FMCG stability
            }
            base_confidence += tier1_adjustments.get(symbol, 0)
            
            # Clamp between reasonable bounds
            return max(45.0, min(95.0, base_confidence))
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating confidence: {e}")
            return 75.0
    
    def _determine_risk_level(self, expected_roi, confidence, implied_vol):
        """Determine risk level based on real metrics"""
        try:
            # Multi-factor risk assessment
            if confidence >= 85 and expected_roi >= 12 and implied_vol < 35:
                return 'Safe', 'success'
            elif confidence >= 75 and expected_roi >= 8 and implied_vol < 50:
                return 'Moderate', 'warning'
            elif confidence >= 65 and expected_roi >= 5:
                return 'Moderate', 'warning'
            else:
                return 'High', 'danger'
                
        except Exception as e:
            logger.warning(f"⚠️ Error determining risk level: {e}")
            return 'Moderate', 'warning'
    
    def _save_strategies_to_cache(self, strategies, timeframe):
        """Save strategies to cache file"""
        try:
            cache_data = {
                timeframe: {
                    'strategies': strategies,
                    'last_updated': datetime.now().isoformat(),
                    'total_opportunities': len(strategies),
                    'data_source': 'yahoo_finance_realtime'
                }
            }
            
            # Load existing cache and update
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r') as f:
                        existing_data = json.load(f)
                        existing_data.update(cache_data)
                        cache_data = existing_data
                except Exception as e:
                    logger.warning(f"⚠️ Could not load existing cache: {e}")
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"💾 Saved {len(strategies)} real-time strategies to cache")
            
        except Exception as e:
            logger.error(f"❌ Error saving to cache: {e}")
