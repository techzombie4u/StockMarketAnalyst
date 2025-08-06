
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
        
    def generate_strategies(self, timeframe='30D', force_refresh=False):
        """Generate short strangle strategies with real-time Yahoo Finance data"""
        try:
            logger.info(f"🔄 Generating options strategies for {timeframe}, force_refresh={force_refresh}")
            
            strategies = []
            
            for symbol_ns in self.tier1_stocks:
                try:
                    # Clean symbol for display
                    symbol = symbol_ns.replace('.NS', '')
                    
                    # Get real-time data from Yahoo Finance
                    logger.info(f"📡 Fetching real-time data for {symbol}")
                    stock = yf.Ticker(symbol_ns)
                    
                    # Get current price
                    info = stock.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    
                    if not current_price:
                        # Fallback to recent history
                        hist = stock.history(period='1d')
                        if not hist.empty:
                            current_price = float(hist['Close'].iloc[-1])
                        else:
                            logger.warning(f"⚠️ No price data for {symbol}")
                            continue
                    
                    current_price = float(current_price)
                    logger.info(f"💰 {symbol}: Current price = ₹{current_price:.2f}")
                    
                    # Calculate strategy parameters
                    strategy = self._calculate_strangle_strategy(symbol, current_price, timeframe)
                    if strategy:
                        strategies.append(strategy)
                        logger.info(f"✅ Generated strategy for {symbol}: ROI={strategy['expected_roi']:.1f}%")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {symbol}: {e}")
                    continue
            
            logger.info(f"🎯 Generated {len(strategies)} total strategies")
            
            # Save to cache
            self._save_strategies_to_cache(strategies, timeframe)
            
            return strategies
            
        except Exception as e:
            logger.error(f"❌ Error generating strategies: {e}")
            return []
    
    def _calculate_strangle_strategy(self, symbol, current_price, timeframe):
        """Calculate short strangle strategy parameters"""
        try:
            # Strategy parameters based on timeframe
            if timeframe == '5D':
                otm_percent = 0.02  # 2% OTM
                days_to_expiry = 5
                annual_factor = 365 / 5
            elif timeframe == '10D':
                otm_percent = 0.03  # 3% OTM
                days_to_expiry = 10
                annual_factor = 365 / 10
            else:  # 30D
                otm_percent = 0.05  # 5% OTM
                days_to_expiry = 30
                annual_factor = 365 / 30
            
            # Calculate strikes
            call_strike = current_price * (1 + otm_percent)
            put_strike = current_price * (1 - otm_percent)
            
            # Estimate premiums (simplified model)
            iv = self._estimate_implied_volatility(symbol)
            call_premium = self._estimate_option_premium(current_price, call_strike, days_to_expiry, iv, 'call')
            put_premium = self._estimate_option_premium(current_price, put_strike, days_to_expiry, iv, 'put')
            
            total_premium = call_premium + put_premium
            
            # Calculate breakeven points
            breakeven_upper = call_strike + total_premium
            breakeven_lower = put_strike - total_premium
            breakeven_range_pct = ((breakeven_upper - breakeven_lower) / current_price) * 100
            
            # Estimate margin requirement (simplified)
            margin_required = max(
                0.2 * current_price * 100,  # 20% of underlying value
                (call_strike - current_price + call_premium) * 100 if call_strike > current_price else call_premium * 100
            )
            
            # Calculate ROI
            expected_roi = (total_premium / (margin_required / 100)) * 100
            annualized_roi = expected_roi * annual_factor
            
            # Determine confidence and risk level
            confidence = self._calculate_confidence(symbol, breakeven_range_pct, iv)
            risk_level = self._determine_risk_level(expected_roi, confidence, iv)
            
            # Ensure all values are properly formatted numbers
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
                'implied_volatility': float(iv),
                'risk_level': str(risk_level),
                'risk_color': 'success' if risk_level == 'Safe' else 'warning' if risk_level == 'Moderate' else 'danger',
                'days_to_expiry': int(days_to_expiry),
                'timeframe': str(timeframe),
                'last_updated': datetime.now().isoformat()
            }
            
            return strategy_data
            
        except Exception as e:
            logger.error(f"❌ Error calculating strategy for {symbol}: {e}")
            return None
    
    def _estimate_implied_volatility(self, symbol):
        """Estimate implied volatility for the stock"""
        try:
            # Historical volatility as proxy for IV
            symbol_ns = f"{symbol}.NS"
            stock = yf.Ticker(symbol_ns)
            hist = stock.history(period='30d')
            
            if len(hist) < 10:
                return 25.0  # Default IV
            
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
            
            # Adjust for typical IV premium
            iv = volatility * 1.2  # IV typically higher than historical vol
            
            # Clamp between reasonable bounds
            return max(15.0, min(60.0, iv))
            
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate IV for {symbol}: {e}")
            return 25.0  # Default fallback
    
    def _estimate_option_premium(self, spot, strike, days_to_expiry, iv, option_type):
        """Simplified Black-Scholes option pricing"""
        try:
            # Simplified option pricing model
            time_value = days_to_expiry / 365.0
            volatility = iv / 100.0
            
            # Intrinsic value
            if option_type == 'call':
                intrinsic = max(0, spot - strike)
            else:  # put
                intrinsic = max(0, strike - spot)
            
            # Time value (simplified)
            time_premium = (volatility * spot * np.sqrt(time_value)) * 0.4
            
            premium = intrinsic + time_premium
            
            # Ensure minimum premium
            return max(5.0, premium)
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating premium: {e}")
            return 10.0  # Default premium
    
    def _calculate_confidence(self, symbol, breakeven_range_pct, iv):
        """Calculate confidence level for the strategy"""
        try:
            base_confidence = 70.0
            
            # Adjust based on breakeven range
            if breakeven_range_pct > 15:
                base_confidence += 15
            elif breakeven_range_pct > 10:
                base_confidence += 10
            elif breakeven_range_pct > 8:
                base_confidence += 5
            
            # Adjust based on volatility
            if iv < 20:
                base_confidence += 10  # Low vol = higher confidence
            elif iv > 40:
                base_confidence -= 10  # High vol = lower confidence
            
            # Stock-specific adjustments
            tier1_bonus = {
                'RELIANCE': 5, 'TCS': 8, 'HDFCBANK': 8,
                'ITC': 3, 'INFY': 6, 'HINDUNILVR': 4
            }
            base_confidence += tier1_bonus.get(symbol, 0)
            
            return max(50.0, min(95.0, base_confidence))
            
        except Exception as e:
            logger.warning(f"⚠️ Error calculating confidence: {e}")
            return 75.0
    
    def _determine_risk_level(self, expected_roi, confidence, iv):
        """Determine risk level for the strategy"""
        try:
            if confidence >= 85 and expected_roi >= 15 and iv < 30:
                return 'Safe'
            elif confidence >= 75 and expected_roi >= 10:
                return 'Moderate'
            else:
                return 'High'
        except:
            return 'Moderate'
    
    def _save_strategies_to_cache(self, strategies, timeframe):
        """Save strategies to cache file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            cache_data = {
                timeframe: {
                    'strategies': strategies,
                    'last_updated': datetime.now().isoformat(),
                    'total_opportunities': len(strategies)
                }
            }
            
            # Load existing cache
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r') as f:
                        existing_data = json.load(f)
                        existing_data.update(cache_data)
                        cache_data = existing_data
                except:
                    pass
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"💾 Saved {len(strategies)} strategies to cache")
            
        except Exception as e:
            logger.error(f"❌ Error saving to cache: {e}")
"""
Short Strangle Options Strategy Engine
"""

import logging
import yfinance as yf
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ShortStrangleEngine:
    """Engine for generating short strangle options strategies"""
    
    def __init__(self):
        self.tier1_stocks = ['RELIANCE.NS', 'HDFCBANK.NS', 'TCS.NS', 'ITC.NS', 'INFY.NS']
    
    def generate_strategies(self, timeframe='30D', force_refresh=False):
        """Generate short strangle strategies"""
        try:
            strategies = []
            
            for symbol_ns in self.tier1_stocks:
                try:
                    symbol = symbol_ns.replace('.NS', '')
                    
                    # Get stock data
                    stock = yf.Ticker(symbol_ns)
                    info = stock.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                    
                    if not current_price:
                        hist = stock.history(period='1d')
                        if not hist.empty:
                            current_price = float(hist['Close'].iloc[-1])
                        else:
                            continue
                    
                    current_price = float(current_price)
                    
                    # Calculate strategy parameters
                    if timeframe == '5D':
                        otm_percent = 0.02
                        days_to_expiry = 5
                    elif timeframe == '10D':
                        otm_percent = 0.03
                        days_to_expiry = 10
                    else:  # 30D
                        otm_percent = 0.05
                        days_to_expiry = 30
                    
                    # Calculate strikes and premiums
                    call_strike = current_price * (1 + otm_percent)
                    put_strike = current_price * (1 - otm_percent)
                    call_premium = max(5.0, current_price * 0.02)
                    put_premium = max(5.0, current_price * 0.02)
                    total_premium = call_premium + put_premium
                    
                    # Calculate breakeven points
                    breakeven_upper = call_strike + total_premium
                    breakeven_lower = put_strike - total_premium
                    
                    # Calculate other metrics
                    margin_required = max(20000, current_price * 100 * 0.2)
                    expected_roi = (total_premium / (margin_required / 100)) * 100
                    confidence = min(95.0, 75.0 + (10 if symbol in ['RELIANCE', 'TCS', 'HDFCBANK'] else 0))
                    
                    strategy = {
                        'symbol': symbol,
                        'current_price': current_price,
                        'call_strike': call_strike,
                        'put_strike': put_strike,
                        'call_premium': call_premium,
                        'put_premium': put_premium,
                        'total_premium': total_premium,
                        'breakeven_upper': breakeven_upper,
                        'breakeven_lower': breakeven_lower,
                        'margin_required': margin_required,
                        'expected_roi': expected_roi,
                        'confidence': confidence,
                        'risk_level': 'Medium',
                        'days_to_expiry': days_to_expiry
                    }
                    
                    strategies.append(strategy)
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    continue
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error generating strategies: {e}")
            return []
