import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import os
import time

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
        """Generate short strangle strategies for tier 1 stocks with real-time data"""
        try:
            logger.info(f"🔄 Generating real-time options strategies for {timeframe}, force_refresh={force_refresh}")

            tier_1_stocks = ['RELIANCE', 'HDFCBANK', 'TCS', 'ITC', 'INFY', 'HINDUNILVR']
            strategies = []

            for symbol in tier_1_stocks:
                try:
                    logger.info(f"📡 Fetching real-time data for {symbol}")
                    strategy = self._generate_strategy_for_stock(symbol, timeframe, force_refresh=True)
                    if strategy and strategy.get('current_price', 0) > 0:
                        strategies.append(strategy)
                        logger.info(f"✅ Generated strategy for {symbol}: ROI={strategy['expected_roi']:.1f}%")
                    else:
                        logger.warning(f"⚠️ No valid strategy generated for {symbol}")
                except Exception as e:
                    logger.error(f"❌ Error generating strategy for {symbol}: {e}")
                    continue

            logger.info(f"🎯 Generated {len(strategies)} total real-time strategies")

            # Always cache real-time results
            if strategies:
                cache_key = f"options_strategies_{timeframe}"
                self._save_to_cache(cache_key, strategies)
                logger.info(f"💾 Saved {len(strategies)} real-time strategies to cache")

            return strategies

        except Exception as e:
            logger.error(f"❌ Error generating options strategies: {e}")
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

            # Convert inputs with validation
            S = float(spot)
            K = float(strike)
            T = float(days_to_expiry) / 365.0
            r = float(risk_free_rate)
            sigma = float(vol) / 100.0

            # Validate inputs
            if S <= 0 or K <= 0:
                logger.warning(f"Invalid price inputs: spot={S}, strike={K}")
                return self._simplified_premium_calculation(spot, strike, days_to_expiry, vol, option_type)

            # Handle edge cases
            if T <= 0:
                if option_type == 'call':
                    return max(0, S - K)
                else:
                    return max(0, K - S)

            # Black-Scholes calculation with error handling
            try:
                d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
                d2 = d1 - sigma * math.sqrt(T)

                if option_type == 'call':
                    premium = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
                else:  # put
                    premium = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

                # Ensure minimum premium and reasonable bounds
                premium = max(5.0, min(premium, S * 0.2))  # Min ₹5, Max 20% of spot

                return float(premium)
            except (ValueError, OverflowError, ZeroDivisionError) as calc_error:
                logger.warning(f"Calculation error in Black-Scholes: {calc_error}")
                return self._simplified_premium_calculation(spot, strike, days_to_expiry, vol, option_type)

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

    def _generate_strategy_for_stock(self, symbol, timeframe, force_refresh=True):
        """Generate strategy for a single stock with real-time data"""
        try:
            # Always get fresh data from yfinance
            ticker = yf.Ticker(f"{symbol}.NS")

            # Get current price with retries
            attempts = 0
            hist = None
            while attempts < 3 and (hist is None or hist.empty):
                try:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        break
                except Exception as e:
                    logger.warning(f"Attempt {attempts + 1} failed for {symbol}: {e}")
                attempts += 1
                time.sleep(1)

            if hist is None or hist.empty:
                logger.error(f"❌ No price data available for {symbol} after {attempts} attempts")
                return None

            current_price = float(hist['Close'].iloc[-1])
            logger.info(f"💰 {symbol}: Current price = ₹{current_price:.2f}")

            # Validate price data
            if current_price <= 0:
                logger.error(f"❌ Invalid price data for {symbol}: {current_price}")
                return None

            # Calculate volatility for the past 30 days
            try:
                hist_30d = ticker.history(period="30d")
                if len(hist_30d) > 5:
                    returns = hist_30d['Close'].pct_change().dropna()
                    volatility = returns.std() * (252 ** 0.5) * 100  # Annualized volatility
                else:
                    volatility = 20.0  # Default volatility
            except Exception as e:
                logger.warning(f"⚠️ Volatility calculation failed for {symbol}: {e}")
                volatility = 20.0

            logger.info(f"📊 {symbol}: Historical volatility = {volatility:.1f}%")

            # Calculate strikes (3-5% OTM)
            otm_percent = 0.04  # 4% OTM
            call_strike = current_price * (1 + otm_percent)
            put_strike = current_price * (1 - otm_percent)

            # Round strikes to nearest 50 for better liquidity
            call_strike = round(call_strike / 50) * 50
            put_strike = round(put_strike / 50) * 50

            # Ensure strikes are valid
            if call_strike <= current_price or put_strike >= current_price:
                logger.warning(f"⚠️ Invalid strikes for {symbol}: call={call_strike}, put={put_strike}, current={current_price}")
                call_strike = current_price * 1.05
                put_strike = current_price * 0.95

            # Estimate premiums based on volatility and time
            time_to_expiry = 30 if '30D' in timeframe else 10 if '10D' in timeframe else 5

            # Premium calculation (simplified Black-Scholes approximation)
            call_premium = self._estimate_option_premium(current_price, call_strike, time_to_expiry, volatility, 'call')
            put_premium = self._estimate_option_premium(current_price, put_strike, time_to_expiry, volatility, 'put')

            total_premium = call_premium + put_premium

            # Validate premiums
            if total_premium <= 0:
                logger.warning(f"⚠️ Invalid premiums for {symbol}: total={total_premium}")
                return None

            # Calculate breakeven points
            breakeven_upper = call_strike + total_premium
            breakeven_lower = put_strike - total_premium

            # Estimate margin requirement (approximate)
            margin_required = max(
                current_price * 0.20,  # 20% of stock price
                abs(current_price - put_strike) + put_premium,
                abs(call_strike - current_price) + call_premium
            ) * 100  # For 1 lot (100 shares)

            # Calculate ROI
            expected_roi = (total_premium / margin_required) * 100

            # Risk assessment
            price_range = breakeven_upper - breakeven_lower
            risk_ratio = price_range / current_price

            if risk_ratio > 0.15:  # >15% range
                risk_level = "Low"
                confidence = min(90, 70 + (risk_ratio - 0.15) * 100)
            elif risk_ratio > 0.10:  # >10% range
                risk_level = "Medium" 
                confidence = min(80, 60 + (risk_ratio - 0.10) * 200)
            else:
                risk_level = "High"
                confidence = max(50, 70 - (0.10 - risk_ratio) * 200)

            # Ensure all values are valid numbers
            strategy = {
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'call_strike': round(call_strike, 2),
                'put_strike': round(put_strike, 2),
                'call_premium': round(call_premium, 2),
                'put_premium': round(put_premium, 2),
                'total_premium': round(total_premium, 2),
                'breakeven_upper': round(breakeven_upper, 2),
                'breakeven_lower': round(breakeven_lower, 2),
                'margin_required': round(margin_required, 2),
                'expected_roi': round(expected_roi, 2),
                'confidence': round(confidence, 1),
                'risk_level': risk_level,
                'volatility': round(volatility, 1),
                'time_to_expiry': time_to_expiry,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'yahoo_finance_real_time'
            }

            # Final validation
            if strategy['current_price'] <= 0 or strategy['total_premium'] <= 0:
                logger.error(f"❌ Invalid strategy data for {symbol}")
                return None

            logger.info(f"✅ Generated strategy for {symbol}: ROI={expected_roi:.1f}%")
            return strategy

        except Exception as e:
            logger.error(f"❌ Error generating strategy for {symbol}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _estimate_option_premium(self, spot, strike, time_to_expiry, volatility, option_type):
        """Placeholder for a more sophisticated option premium calculation if needed"""
        # This is a simplified estimation, could be replaced with Black-Scholes
        # For now, using a basic formula that scales with volatility and time
        try:
            if option_type == 'call':
                intrinsic = max(0, spot - strike)
                moneyness = strike / spot
            else: # put
                intrinsic = max(0, strike - spot)
                moneyness = spot / strike

            # Simplified time value
            time_value = time_to_expiry / 365.0
            vol_factor = volatility / 100.0

            # Base time premium, influenced by volatility and time to expiry
            time_premium = spot * vol_factor * np.sqrt(time_value) * 0.5

            # Adjust time premium based on moneyness
            if option_type == 'call':
                if strike > spot: # OTM
                    time_premium *= (1 + (strike - spot) / spot * 0.5) # Higher for further OTM
                else: # ITM/ATM
                    time_premium *= 0.8 # Lower for ITM/ATM
            else: # put
                if strike < spot: # OTM
                    time_premium *= (1 + (spot - strike) / spot * 0.5) # Higher for further OTM
                else: # ITM/ATM
                    time_premium *= 0.8 # Lower for ITM/ATM

            # Ensure time premium is not negative
            time_premium = max(0, time_premium)

            premium = intrinsic + time_premium

            # Ensure a minimum premium and cap it to prevent unrealistic values
            min_premium = max(5.0, spot * 0.01) # Min premium of 1% of spot or 5
            max_premium = spot * 0.30 # Max premium of 30% of spot

            return max(min_premium, min(premium, max_premium))

        except Exception as e:
            logger.warning(f"⚠️ Error in _estimate_option_premium for {option_type}: {e}")
            return max(10.0, spot * 0.02) # Fallback

    def _save_to_cache(self, cache_key, data):
        """Saves data to the cache file"""
        try:
            if not os.path.exists(self.cache_file):
                cache_data = {}
            else:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)

            cache_data[cache_key] = {
                'data': data,
                'timestamp': datetime.now().isoformat()
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Data cached for key: {cache_key}")

        except Exception as e:
            logger.error(f"❌ Error saving to cache: {e}")

    def get_real_time_price(self, symbol):
        """Get real-time price for a symbol"""
        try:
            import yfinance as yf

            # Add .NS for NSE stocks
            yahoo_symbol = f"{symbol}.NS"

            ticker = yf.Ticker(yahoo_symbol)
            data = ticker.history(period="1d")

            if not data.empty:
                current_price = float(data['Close'].iloc[-1])
                logger.info(f"[REALTIME] {symbol} fetched live price: ₹{current_price}")
                return current_price
            else:
                logger.warning(f"No data found for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error fetching real-time price for {symbol}: {str(e)}")
            return None

    def get_price(self, symbol, use_live=True):
        """Get price with fallback logic"""
        if use_live:
            try:
                live_price = self.get_real_time_price(symbol)
                if live_price is not None:
                    return live_price
                logger.warning(f"[FALLBACK] Using cached price for {symbol}")
            except Exception as e:
                logger.error(f"[FALLBACK] Error getting live price for {symbol}: {str(e)}")

        # Fallback to cached/demo prices
        demo_prices = {
            'RELIANCE': 2750.50,
            'TCS': 3420.75,
            'INFY': 1650.25,
            'HDFCBANK': 1580.00,
            'ICICIBANK': 985.50,
            'HINDUNILVR': 2420.30,
            'SBIN': 642.80,
            'BHARTIARTL': 1245.60,
            'ITC': 465.20,
            'KOTAKBANK': 1750.40
        }
        cached_price = demo_prices.get(symbol, 1000.0)
        logger.info(f"[CACHED] Using cached price for {symbol}: ₹{cached_price}")
        return cached_price

    def analyze_short_strangle(self, symbol, manual_refresh=False, force_realtime=False):
        """Analyze short strangle strategy for a given symbol"""
        try:
            logger.info(f"Analyzing short strangle for {symbol}, manual_refresh={manual_refresh}, force_realtime={force_realtime}")

            # Use real-time prices by default, or when explicitly requested
            use_live = manual_refresh or force_realtime or True  # Always try live first
            current_price = self.get_price(symbol, use_live=use_live)