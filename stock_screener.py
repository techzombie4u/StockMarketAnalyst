"""
Stock Market Analyst - Enhanced Data Collection and Scoring Module

This module handles:
1. Enhanced technical indicators (RSI, EMA, Bollinger Bands)
2. Rolling statistics and lagged features
3. Multiple data sources for better reliability
4. Improved scoring algorithm with advanced features

Note: This is for personal use only. Respect website terms of service.
"""

import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedStockScreener:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Complete Nifty 50 stocks list
        self.nifty50_symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
            'ICICIBANK', 'BHARTIARTL', 'SBIN', 'LT', 'ITC',
            'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'ASIANPAINT', 'MARUTI',
            'SUNPHARMA', 'ULTRACEMCO', 'TITAN', 'NESTLEIND', 'BAJFINANCE',
            'WIPRO', 'ONGC', 'NTPC', 'POWERGRID', 'TECHM',
            'M&M', 'TATAMOTORS', 'BAJAJFINSV', 'DRREDDY', 'JSWSTEEL',
            'COALINDIA', 'TATASTEEL', 'HDFCLIFE', 'SBILIFE', 'GRASIM',
            'BRITANNIA', 'APOLLOHOSP', 'CIPLA', 'DIVISLAB', 'HEROMOTOCO',
            'ADANIENT', 'EICHERMOT', 'HINDALCO', 'UPL', 'INDUSINDBK',
            'BAJAJ-AUTO', 'BPCL', 'TATACONSUM', 'SHRIRAMFIN', 'LTIM'
        ]

        # Use all Nifty 50 stocks for comprehensive screening
        self.watchlist = self.nifty50_symbols

        self.bulk_deals = []
        self.fundamentals = {}
        self.technical_data = {}

        # Data source configurations
        self.data_sources = {
            'yahoo': {'priority': 1, 'timeout': 10},
            'screener': {'priority': 2, 'timeout': 15},
            'moneycontrol': {'priority': 3, 'timeout': 12},
            'nse': {'priority': 4, 'timeout': 8},
            'bse': {'priority': 5, 'timeout': 10}
        }

    def calculate_enhanced_technical_indicators(self, symbol: str) -> Dict:
        """Calculate enhanced technical indicators with multiple timeframes"""
        try:
            # Try multiple data sources for price data
            hist_data = self._fetch_price_data_multiple_sources(symbol)

            if hist_data is None or hist_data.empty:
                logger.warning(f"No price data found for {symbol}")
                return {}

            # Ensure we have enough data points
            if hist_data is None or hist_data.empty or len(hist_data) < 50:
                logger.warning(f"Insufficient data for {symbol}: {len(hist_data) if hist_data is not None else 0} days")
                return {}

            indicators = {}

            # 1. Enhanced ATR calculation (multiple periods)
            indicators.update(self._calculate_atr_indicators(hist_data))

            # 2. RSI (Relative Strength Index)
            indicators.update(self._calculate_rsi_indicators(hist_data))

            # 3. EMA (Exponential Moving Averages)
            indicators.update(self._calculate_ema_indicators(hist_data))

            # 4. Bollinger Bands
            indicators.update(self._calculate_bollinger_bands(hist_data))

            # 5. Volume indicators
            indicators.update(self._calculate_volume_indicators(hist_data))

            # 6. Momentum and trend indicators
            indicators.update(self._calculate_momentum_indicators(hist_data))

            # 7. Rolling statistics
            indicators.update(self._calculate_rolling_statistics(hist_data))

            # 8. Lagged features
            indicators.update(self._calculate_lagged_features(hist_data))

            # 9. Volatility measures
            indicators.update(self._calculate_volatility_measures(hist_data))

            # Current price and basic info
            current_price_val = hist_data['Close'].iloc[-1]
            indicators['current_price'] = float(current_price_val) if not pd.isna(current_price_val) else 0
            indicators['data_quality_score'] = self._assess_data_quality(hist_data)

            return indicators

        except Exception as e:
            logger.error(f"Error calculating enhanced indicators for {symbol}: {str(e)}")
            return {}

    def _fetch_price_data_multiple_sources(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch price data from multiple sources with fallback"""

        # Primary source: Yahoo Finance (most reliable)
        try:
            ticker = f"{symbol}.NS"
            hist_data = yf.download(ticker, period="1y", progress=False)
            if hist_data is not None and not hist_data.empty and len(hist_data) > 30:
                logger.debug(f"Yahoo Finance data successful for {symbol}")
                return hist_data
        except Exception as e:
            logger.warning(f"Yahoo Finance failed for {symbol}: {str(e)}")

        # Fallback sources (placeholder implementations)
        # In a real implementation, you would add NSE, BSE, Moneycontrol APIs

        # For now, try Yahoo Finance with different periods as fallback
        fallback_periods = ["6mo", "3mo", "2mo"]
        for period in fallback_periods:
            try:
                ticker = f"{symbol}.NS"
                hist_data = yf.download(ticker, period=period, progress=False)
                if hist_data is not None and not hist_data.empty and len(hist_data) > 20:
                    logger.info(f"Yahoo Finance fallback ({period}) successful for {symbol}")
                    return hist_data
            except Exception:
                continue

        logger.error(f"All data sources failed for {symbol}")
        return None

    def _calculate_atr_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate ATR for multiple periods"""
        indicators = {}

        try:
            high_low = data['High'] - data['Low']
            high_close = (data['High'] - data['Close'].shift()).abs()
            low_close = (data['Low'] - data['Close'].shift()).abs()
            
            # Calculate true range using numpy maximum for element-wise comparison
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))

            # Multiple ATR periods
            for period in [7, 14, 21]:
                atr = true_range.rolling(window=period).mean()
                atr_val = atr.iloc[-1] if len(atr) > 0 else 0
                indicators[f'atr_{period}'] = float(atr_val) if not pd.isna(atr_val) else 0

            # ATR-based volatility
            current_price = data['Close'].iloc[-1] if len(data['Close']) > 0 else 0
            indicators['atr_volatility'] = (indicators['atr_14'] / current_price * 100) if current_price > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")

        return indicators

    def _calculate_rsi_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate RSI for multiple periods"""
        indicators = {}

        try:
            close_prices = data['Close']

            for period in [14, 21]:
                delta = close_prices.diff()
                gain = delta.where(delta > 0, 0)
                loss = (-delta).where(delta < 0, 0)
                
                avg_gain = gain.rolling(window=period).mean()
                avg_loss = loss.rolling(window=period).mean()
                
                # Avoid division by zero
                rs = avg_gain / (avg_loss + 1e-10)
                rsi = 100 - (100 / (1 + rs))

                rsi_val = rsi.iloc[-1] if len(rsi) > 0 else 50
                indicators[f'rsi_{period}'] = float(rsi_val) if not pd.isna(rsi_val) else 50

            # RSI signal interpretation
            rsi_14 = indicators.get('rsi_14', 50)
            if rsi_14 < 30:
                indicators['rsi_signal'] = 'oversold'
            elif rsi_14 > 70:
                indicators['rsi_signal'] = 'overbought'
            else:
                indicators['rsi_signal'] = 'neutral'

        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")

        return indicators

    def _calculate_ema_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate Exponential Moving Averages"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Multiple EMA periods
            ema_periods = [5, 12, 21, 50]
            for period in ema_periods:
                ema = close_prices.ewm(span=period).mean()
                ema_val = ema.iloc[-1] if len(ema) > 0 else 0
                indicators[f'ema_{period}'] = float(ema_val) if not pd.isna(ema_val) else 0

            # EMA crossover signals
            current_price = close_prices.iloc[-1] if len(close_prices) > 0 else 0
            indicators['price_above_ema_12'] = float(current_price) > float(indicators.get('ema_12', 0))
            indicators['price_above_ema_21'] = float(current_price) > float(indicators.get('ema_21', 0))
            indicators['ema_12_above_21'] = float(indicators.get('ema_12', 0)) > float(indicators.get('ema_21', 0))

            # EMA trend strength
            ema_5 = indicators.get('ema_5', 0)
            ema_21 = indicators.get('ema_21', 0)
            indicators['ema_trend_strength'] = ((ema_5 - ema_21) / ema_21 * 100) if ema_21 > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")

        return indicators

    def _calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict:
        """Calculate Bollinger Bands"""
        indicators = {}

        try:
            close_prices = data['Close']
            period = 20
            std_dev = 2

            # Calculate Bollinger Bands
            bb_middle = close_prices.rolling(window=period).mean()
            bb_std = close_prices.rolling(window=period).std()
            bb_upper = bb_middle + (bb_std * std_dev)
            bb_lower = bb_middle - (bb_std * std_dev)

            bb_upper_val = bb_upper.iloc[-1]
            bb_middle_val = bb_middle.iloc[-1]
            bb_lower_val = bb_lower.iloc[-1]
            
            indicators['bb_upper'] = float(bb_upper_val) if not pd.isna(bb_upper_val) else 0
            indicators['bb_middle'] = float(bb_middle_val) if not pd.isna(bb_middle_val) else 0
            indicators['bb_lower'] = float(bb_lower_val) if not pd.isna(bb_lower_val) else 0

            # Current price position in Bollinger Bands
            current_price = close_prices.iloc[-1]
            bb_width = indicators['bb_upper'] - indicators['bb_lower']
            indicators['bb_position'] = ((current_price - indicators['bb_lower']) / bb_width * 100) if bb_width > 0 else 50

            # Bollinger Band squeeze indicator
            indicators['bb_width'] = bb_width / indicators['bb_middle'] * 100 if indicators['bb_middle'] > 0 else 0

            # Signal interpretation
            if current_price > indicators['bb_upper']:
                indicators['bb_signal'] = 'above_upper'
            elif current_price < indicators['bb_lower']:
                indicators['bb_signal'] = 'below_lower'
            else:
                indicators['bb_signal'] = 'within_bands'

        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")

        return indicators

    def _calculate_volume_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate volume-based indicators"""
        indicators = {}

        try:
            volume = data['Volume']
            close_prices = data['Close']

            # Volume moving averages
            vol_ma_10 = volume.rolling(window=10).mean().iloc[-1]
            vol_ma_20 = volume.rolling(window=20).mean().iloc[-1]
            indicators['volume_ma_10'] = float(vol_ma_10) if not pd.isna(vol_ma_10) else 0
            indicators['volume_ma_20'] = float(vol_ma_20) if not pd.isna(vol_ma_20) else 0

            # Current volume vs average
            current_volume = volume.iloc[-1]
            indicators['volume_ratio_10'] = current_volume / indicators['volume_ma_10'] if indicators['volume_ma_10'] > 0 else 1

            # Price-Volume trend
            price_change = close_prices.pct_change()
            volume_change = volume.pct_change()
            pv_correlation = price_change.rolling(window=20).corr(volume_change)
            pv_corr_val = pv_correlation.iloc[-1]
            indicators['price_volume_correlation'] = float(pv_corr_val) if not pd.isna(pv_corr_val) else 0

            # On Balance Volume (OBV)
            close_diff = close_prices.diff()
            volume_direction = np.where(close_diff > 0, volume, 
                                      np.where(close_diff < 0, -volume, 0))
            obv = volume_direction.cumsum()
            indicators['obv'] = float(obv.iloc[-1]) if not pd.isna(obv.iloc[-1]) else 0
            indicators['obv_trend'] = float(obv.iloc[-1] - obv.iloc[-11]) if len(obv) > 10 and not pd.isna(obv.iloc[-1]) and not pd.isna(obv.iloc[-11]) else 0

        except Exception as e:
            logger.error(f"Error calculating volume indicators: {str(e)}")

        return indicators

    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate momentum and trend indicators"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Multiple timeframe momentum
            for period in [2, 5, 10, 20]:
                momentum = close_prices.pct_change(periods=period)
                momentum_val = momentum.iloc[-1]
                indicators[f'momentum_{period}d'] = float(momentum_val) if not pd.isna(momentum_val) else 0

            # MACD (Moving Average Convergence Divergence)
            ema_12 = close_prices.ewm(span=12).mean()
            ema_26 = close_prices.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            macd_histogram = macd_line - signal_line

            macd_val = macd_line.iloc[-1]
            signal_val = signal_line.iloc[-1]
            histogram_val = macd_histogram.iloc[-1]
            
            indicators['macd'] = float(macd_val) if not pd.isna(macd_val) else 0
            indicators['macd_signal'] = float(signal_val) if not pd.isna(signal_val) else 0
            indicators['macd_histogram'] = float(histogram_val) if not pd.isna(histogram_val) else 0
            indicators['macd_bullish'] = indicators['macd'] > indicators['macd_signal']

            # Rate of Change
            if len(close_prices) > 10:
                current_price = close_prices.iloc[-1]
                past_price = close_prices.iloc[-11]
                roc_10 = ((current_price - past_price) / past_price * 100) if past_price > 0 else 0
            else:
                roc_10 = 0
            indicators['roc_10'] = roc_10

        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {str(e)}")

        return indicators

    def _calculate_rolling_statistics(self, data: pd.DataFrame) -> Dict:
        """Calculate rolling statistical measures"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Rolling statistics for multiple windows
            for window in [5, 10, 20]:
                rolling_data = close_prices.rolling(window=window)

                mean_val = rolling_data.mean().iloc[-1]
                std_val = rolling_data.std().iloc[-1]
                min_val = rolling_data.min().iloc[-1]
                max_val = rolling_data.max().iloc[-1]
                
                indicators[f'rolling_mean_{window}'] = float(mean_val) if not pd.isna(mean_val) else 0
                indicators[f'rolling_std_{window}'] = float(std_val) if not pd.isna(std_val) else 0
                indicators[f'rolling_min_{window}'] = float(min_val) if not pd.isna(min_val) else 0
                indicators[f'rolling_max_{window}'] = float(max_val) if not pd.isna(max_val) else 0

                # Position within rolling range
                current_price = close_prices.iloc[-1]
                rolling_min = indicators[f'rolling_min_{window}']
                rolling_max = indicators[f'rolling_max_{window}']
                range_width = rolling_max - rolling_min

                if range_width > 0:
                    indicators[f'price_position_{window}'] = ((current_price - rolling_min) / range_width * 100)
                else:
                    indicators[f'price_position_{window}'] = 50

            # Coefficient of variation (volatility relative to mean)
            for window in [10, 20]:
                mean_val = indicators[f'rolling_mean_{window}']
                std_val = indicators[f'rolling_std_{window}']
                indicators[f'coeff_variation_{window}'] = (std_val / mean_val * 100) if mean_val > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating rolling statistics: {str(e)}")

        return indicators

    def _calculate_lagged_features(self, data: pd.DataFrame) -> Dict:
        """Calculate lagged price features"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Lagged price features
            for lag in [1, 2, 3, 5, 10]:
                if len(close_prices) > lag:
                    lagged_price = close_prices.iloc[-(lag+1)]
                    current_price = close_prices.iloc[-1]

                    indicators[f'price_lag_{lag}'] = float(lagged_price) if not pd.isna(lagged_price) else 0
                    indicators[f'return_lag_{lag}'] = ((current_price - lagged_price) / lagged_price * 100) if lagged_price > 0 and not pd.isna(lagged_price) else 0

            # Lagged volume features
            volume = data['Volume']
            for lag in [1, 2, 5]:
                if len(volume) > lag:
                    lagged_vol = volume.iloc[-(lag+1)]
                    indicators[f'volume_lag_{lag}'] = float(lagged_vol) if not pd.isna(lagged_vol) else 0

                    # Volume change from lag
                    current_volume = volume.iloc[-1]
                    lagged_volume = volume.iloc[-(lag+1)]
                    if lagged_volume > 0 and not pd.isna(lagged_volume) and not pd.isna(current_volume):
                        indicators[f'volume_change_lag_{lag}'] = ((current_volume - lagged_volume) / lagged_volume * 100)
                    else:
                        indicators[f'volume_change_lag_{lag}'] = 0

            # Sequential return patterns
            returns = close_prices.pct_change()
            if len(returns) >= 5:
                recent_returns = returns.tail(5).dropna().values
                if len(recent_returns) > 0:
                    indicators['returns_pattern'] = {
                        'consecutive_positive': int(np.sum(recent_returns > 0)),
                        'consecutive_negative': int(np.sum(recent_returns < 0)),
                        'avg_return_5d': float(np.mean(recent_returns))
                    }

        except Exception as e:
            logger.error(f"Error calculating lagged features: {str(e)}")

        return indicators

    def _calculate_volatility_measures(self, data: pd.DataFrame) -> Dict:
        """Calculate various volatility measures"""
        indicators = {}

        try:
            close_prices = data['Close']
            returns = close_prices.pct_change().dropna()

            # Historical volatility (annualized)
            for window in [10, 20, 30]:
                if len(returns) >= window:
                    vol = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
                    vol_val = vol.iloc[-1]
                    indicators[f'hist_volatility_{window}'] = float(vol_val) if not pd.isna(vol_val) else 0

            # Parkinson's volatility (using high-low)
            try:
                high_low_ratio = (data['High'] / data['Low']).apply(np.log)
                high_low_clean = high_low_ratio.dropna()
                if len(high_low_clean) > 0:
                    parkinson_vol = np.sqrt(np.mean(high_low_clean**2) / (4 * np.log(2))) * np.sqrt(252)
                    indicators['parkinson_volatility'] = float(parkinson_vol) if not pd.isna(parkinson_vol) else 0
                else:
                    indicators['parkinson_volatility'] = 0
            except:
                indicators['parkinson_volatility'] = 0

            # Garman-Klass volatility (more accurate)
            try:
                if len(data) >= 20:
                    log_hl = (data['High'] / data['Low']).apply(np.log)
                    log_co = (data['Close'] / data['Open']).apply(np.log)
                    log_hl_clean = log_hl.dropna()
                    log_co_clean = log_co.dropna()
                    
                    if len(log_hl_clean) > 0 and len(log_co_clean) > 0:
                        gk_component = 0.5 * log_hl_clean**2 - (2*np.log(2)-1) * log_co_clean**2
                        gk_vol = np.sqrt(np.mean(gk_component.dropna())) * np.sqrt(252)
                        indicators['garman_klass_volatility'] = float(gk_vol) if not pd.isna(gk_vol) else 0
                    else:
                        indicators['garman_klass_volatility'] = 0
                else:
                    indicators['garman_klass_volatility'] = 0
            except:
                indicators['garman_klass_volatility'] = 0

            # Volatility regime detection
            current_vol = indicators.get('hist_volatility_20', 0)
            long_term_vol = indicators.get('hist_volatility_30', 0)

            if long_term_vol > 0:
                if current_vol > long_term_vol * 1.2:
                    indicators['volatility_regime'] = 'high'
                elif current_vol < long_term_vol * 0.8:
                    indicators['volatility_regime'] = 'low'
                else:
                    indicators['volatility_regime'] = 'normal'
            else:
                indicators['volatility_regime'] = 'normal'

        except Exception as e:
            logger.error(f"Error calculating volatility measures: {str(e)}")

        return indicators

    def _assess_data_quality(self, data: pd.DataFrame) -> float:
        """Assess the quality of the data"""
        try:
            quality_score = 0

            # Data completeness
            if len(data) >= 100:
                quality_score += 30
            elif len(data) >= 50:
                quality_score += 20
            elif len(data) >= 20:
                quality_score += 10

            # Volume data availability
            if 'Volume' in data.columns:
                volume_sum = data['Volume'].sum()
                if volume_sum > 0:
                    quality_score += 20

            # Price consistency
            price_changes = data['Close'].pct_change().dropna()
            if len(price_changes) > 0:
                extreme_changes = np.sum(np.abs(price_changes) > 0.20)  # More than 20% daily change
                if extreme_changes / len(price_changes) < 0.05:  # Less than 5% extreme changes
                    quality_score += 25
                elif extreme_changes / len(price_changes) < 0.10:
                    quality_score += 15

            # Data recency
            if hasattr(data.index[-1], 'date'):
                days_old = (datetime.now().date() - data.index[-1].date()).days
                if days_old <= 3:
                    quality_score += 25
                elif days_old <= 7:
                    quality_score += 15
                elif days_old <= 30:
                    quality_score += 5

            return min(quality_score, 100)

        except Exception:
            return 50  # Default quality score

    def scrape_screener_data(self, symbol: str) -> Dict:
        """Enhanced scrape fundamental data from Screener.in with better error handling"""
        try:
            url = f"https://www.screener.in/company/{symbol}/consolidated/"
            response = self.session.get(url, timeout=15)

            fallback_data = {
                'pe_ratio': None,
                'revenue_growth': 5.0,
                'earnings_growth': 3.0,
                'promoter_buying': False,
                'debt_to_equity': None,
                'roe': None,
                'current_ratio': None,
                'data_source': 'fallback'
            }

            if response.status_code != 200:
                logger.warning(f"Failed to fetch data for {symbol}: {response.status_code}")
                return fallback_data

            soup = BeautifulSoup(response.content, 'html.parser')

            result = fallback_data.copy()
            result['data_source'] = 'screener'

            # Enhanced PE ratio extraction
            pe_ratio = self._extract_pe_ratio(soup, symbol)
            if pe_ratio:
                result['pe_ratio'] = pe_ratio

            # Enhanced financial metrics extraction
            result.update(self._extract_financial_metrics(soup))

            # Enhanced growth data extraction
            result.update(self._extract_growth_data(soup))

            return result

        except Exception as e:
            logger.error(f"Error scraping {symbol}: {str(e)}")
            return {
                'pe_ratio': None,
                'revenue_growth': 5.0,
                'earnings_growth': 3.0,
                'promoter_buying': False,
                'debt_to_equity': None,
                'roe': None,
                'current_ratio': None,
                'data_source': 'error'
            }

    def _extract_pe_ratio(self, soup: BeautifulSoup, symbol: str) -> Optional[float]:
        """Enhanced PE ratio extraction"""
        try:
            # Multiple selectors for PE ratio
            pe_selectors = [
                'span:contains("Stock P/E")',
                'span:contains("P/E")',
                'td:contains("Stock P/E")',
                'td:contains("P/E Ratio")',
                '.number'
            ]

            for selector in pe_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        # Look for number in various locations
                        for candidate in [element, element.find_next_sibling(), 
                                        element.parent.find_next('span', class_='number') if element.parent else None]:
                            if candidate and candidate.text:
                                text = candidate.text.strip()
                                try:
                                    pe_value = float(text.replace(',', '').replace('%', ''))
                                    if 0 < pe_value < 500:
                                        return pe_value
                                except ValueError:
                                    continue
                except Exception:
                    continue

            # Fallback to yfinance
            try:
                ticker = f"{symbol}.NS"
                stock_info = yf.Ticker(ticker).info
                if 'trailingPE' in stock_info and stock_info['trailingPE']:
                    pe_value = float(stock_info['trailingPE'])
                    if 0 < pe_value < 500:
                        return pe_value
            except Exception:
                pass

            return None

        except Exception as e:
            logger.error(f"Error extracting PE ratio: {str(e)}")
            return None

    def _extract_financial_metrics(self, soup: BeautifulSoup) -> Dict:
        """Extract additional financial metrics"""
        metrics = {}

        try:
            # Look for debt-to-equity, ROE, current ratio, etc.
            metric_mappings = {
                'debt_to_equity': ['Debt to equity', 'D/E', 'Debt/Equity'],
                'roe': ['ROE', 'Return on equity', 'Return on Equity'],
                'current_ratio': ['Current ratio', 'Current Ratio']
            }

            for metric, search_terms in metric_mappings.items():
                value = self._extract_metric_value(soup, search_terms)
                if value is not None:
                    metrics[metric] = value

        except Exception as e:
            logger.error(f"Error extracting financial metrics: {str(e)}")

        return metrics

    def _extract_growth_data(self, soup: BeautifulSoup) -> Dict:
        """Enhanced growth data extraction"""
        growth_data = {
            'revenue_growth': 5.0,
            'earnings_growth': 3.0,
            'promoter_buying': False
        }

        try:
            # Look for quarterly results table
            tables = soup.find_all('table', {'class': 'data-table'})

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        row_text = cells[0].text.lower()

                        # Revenue growth
                        if any(term in row_text for term in ['sales', 'revenue', 'income']):
                            growth = self._calculate_growth_from_cells(cells[1:3])
                            if growth is not None:
                                growth_data['revenue_growth'] = growth

                        # Earnings growth
                        elif any(term in row_text for term in ['net profit', 'earnings', 'pat']):
                            growth = self._calculate_growth_from_cells(cells[1:3])
                            if growth is not None:
                                growth_data['earnings_growth'] = growth

            # Check for promoter buying
            page_text = soup.get_text().lower()
            if any(term in page_text for term in ['promoter', 'buying', 'increase in holding']):
                growth_data['promoter_buying'] = True

        except Exception as e:
            logger.error(f"Error extracting growth data: {str(e)}")

        return growth_data

    def _extract_metric_value(self, soup: BeautifulSoup, search_terms: List[str]) -> Optional[float]:
        """Extract a specific metric value from soup"""
        try:
            for term in search_terms:
                elements = soup.find_all(text=lambda text: text and term.lower() in text.lower())
                for element in elements:
                    parent = element.parent
                    if parent:
                        # Look for number in the same row
                        row = parent.find_parent('tr')
                        if row:
                            number_element = row.find('span', class_='number') or row.find(text=lambda t: t and any(c.isdigit() for c in t))
                            if number_element:
                                try:
                                    value = float(str(number_element).replace(',', '').replace('%', ''))
                                    return value
                                except ValueError:
                                    continue
            return None
        except Exception:
            return None

    def _calculate_growth_from_cells(self, cells: List) -> Optional[float]:
        """Calculate growth rate from table cells"""
        try:
            if len(cells) >= 2:
                current_text = cells[0].text.replace(',', '').replace('%', '').strip()
                previous_text = cells[1].text.replace(',', '').replace('%', '').strip()

                current = float(current_text)
                previous = float(previous_text)

                if previous != 0:
                    growth = ((current - previous) / abs(previous)) * 100
                    return growth

        except (ValueError, IndexError, AttributeError):
            pass

        return None

    def enhanced_score_and_rank(self, stocks_data: Dict) -> List[Dict]:
        """Enhanced scoring algorithm with new technical indicators"""
        scored_stocks = []

        # Calculate median PE for normalization
        pe_ratios = [
            data.get('fundamentals', {}).get('pe_ratio')
            for data in stocks_data.values()
            if data.get('fundamentals', {}).get('pe_ratio') is not None and data.get('fundamentals', {}).get('pe_ratio') > 0
        ]
        median_pe = np.median(pe_ratios) if pe_ratios else 20

        bulk_deal_symbols = {deal['symbol'] for deal in self.bulk_deals}

        for symbol, data in stocks_data.items():
            fundamentals = data.get('fundamentals', {})
            technical = data.get('technical', {})

            # Start with base score
            score = 30

            # 1. Enhanced bulk deal scoring
            score += self._score_bulk_deals(symbol, bulk_deal_symbols)

            # 2. Enhanced fundamental scoring
            score += self._score_fundamentals(fundamentals, median_pe)

            # 3. Enhanced technical scoring with new indicators
            score += self._score_technical_indicators(technical)

            # 4. Data quality bonus
            data_quality = technical.get('data_quality_score', 50)
            score += (data_quality - 50) / 10  # Max 5 points bonus for perfect data

            # 5. Volatility adjustment
            volatility_score = self._score_volatility(technical)
            score += volatility_score

            # Normalize score to 0-100
            normalized_score = max(25, min(100, score))

            # Calculate enhanced predictions
            predictions = self._calculate_enhanced_predictions(technical, normalized_score)

            # Risk assessment
            risk_assessment = self._assess_risk(technical, fundamentals)

            stock_result = {
                'symbol': symbol,
                'score': round(normalized_score, 1),
                'adjusted_score': round(normalized_score * risk_assessment['risk_factor'], 1),
                'confidence': self._calculate_confidence(technical, fundamentals),
                'current_price': technical.get('current_price', 0),
                'risk_level': risk_assessment['risk_level'],
                'market_cap': self._estimate_market_cap(symbol),
                'pe_ratio': fundamentals.get('pe_ratio'),
                'pe_description': self.get_pe_description(fundamentals.get('pe_ratio')),
                'revenue_growth': round(fundamentals.get('revenue_growth', 0), 1),
                'technical_summary': self._generate_technical_summary(technical),
                'fundamentals': fundamentals,
                'technical': technical,
                **predictions
            }

            scored_stocks.append(stock_result)

        # Sort by adjusted score
        scored_stocks.sort(key=lambda x: x['adjusted_score'], reverse=True)

        return scored_stocks[:20]

    def _score_bulk_deals(self, symbol: str, bulk_deal_symbols: set) -> float:
        """Enhanced bulk deal scoring"""
        score_boost = 0

        symbol_deals = [deal for deal in self.bulk_deals if deal['symbol'] == symbol]
        if symbol_deals:
            for deal in symbol_deals:
                deal_type = deal.get('type', 'Other')
                percentage = deal.get('percentage', 0)

                # Base bulk deal bonus
                score_boost += 20

                # Type-based scoring
                type_bonuses = {
                    'FII': 15,
                    'DII': 12,
                    'Promoter': 18,
                    'Buy': 8
                }
                score_boost += type_bonuses.get(deal_type, 5)

                # Size-based bonus
                if percentage >= 2.0:
                    score_boost += 8
                elif percentage >= 1.0:
                    score_boost += 4

        return score_boost

    def _score_fundamentals(self, fundamentals: Dict, median_pe: float) -> float:
        """Enhanced fundamental scoring"""
        score_boost = 0

        # PE ratio scoring
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio and pe_ratio > 0:
            score_boost += 5  # Points for having PE data
            if pe_ratio < median_pe * 1.2:
                score_boost += 8
            if pe_ratio < 15:
                score_boost += 5  # Additional bonus for very low PE

        # Growth scoring
        revenue_growth = fundamentals.get('revenue_growth', 0) or 0
        earnings_growth = fundamentals.get('earnings_growth', 0) or 0

        if revenue_growth > 15 or earnings_growth > 15:
            score_boost += 12
        elif revenue_growth > 5 or earnings_growth > 5:
            score_boost += 6

        # Additional financial metrics
        roe = fundamentals.get('roe')
        if roe and roe > 15:
            score_boost += 5

        debt_to_equity = fundamentals.get('debt_to_equity')
        if debt_to_equity and debt_to_equity < 0.5:
            score_boost += 3

        # Promoter buying
        if fundamentals.get('promoter_buying', False):
            score_boost += 15

        return score_boost

    def _score_technical_indicators(self, technical: Dict) -> float:
        """Score based on enhanced technical indicators"""
        score_boost = 0

        # RSI scoring
        rsi_14 = technical.get('rsi_14', 50)
        if 30 <= rsi_14 <= 70:  # Neutral zone
            score_boost += 5
        elif 25 <= rsi_14 <= 35:  # Oversold (good for buying)
            score_boost += 8

        # EMA trend scoring
        if technical.get('ema_12_above_21', False):
            score_boost += 6
        if technical.get('price_above_ema_12', False):
            score_boost += 4

        # Bollinger Bands scoring
        bb_signal = technical.get('bb_signal', 'within_bands')
        if bb_signal == 'below_lower':  # Potential oversold
            score_boost += 6
        elif bb_signal == 'within_bands':
            score_boost += 3

        # MACD scoring
        if technical.get('macd_bullish', False):
            score_boost += 5

        # Volume scoring
        volume_ratio = technical.get('volume_ratio_10', 1)
        if volume_ratio > 1.5:  # High volume
            score_boost += 4
        elif volume_ratio > 1.2:
            score_boost += 2

        # Momentum scoring
        momentum_5d = technical.get('momentum_5d', 0)
        if momentum_5d > 0.02:  # Positive momentum
            score_boost += 6
        elif momentum_5d > 0:
            score_boost += 3

        return score_boost

    def _score_volatility(self, technical: Dict) -> float:
        """Score based on volatility measures"""
        volatility_regime = technical.get('volatility_regime', 'normal')

        if volatility_regime == 'low':
            return 5  # Low volatility is good
        elif volatility_regime == 'normal':
            return 2
        else:  # high volatility
            return -3

    def _calculate_enhanced_predictions(self, technical: Dict, score: float) -> Dict:
        """Calculate enhanced predictions using multiple indicators"""

        current_price = technical.get('current_price', 0)
        if current_price <= 0:
            return {
                'predicted_price': 0,
                'predicted_gain': 0,
                'confidence_level': 'low',
                'time_horizon': 15
            }

        # Base prediction from score
        base_gain = score / 5

        # Technical adjustments
        technical_adjustment = 0

        # RSI adjustment
        rsi_14 = technical.get('rsi_14', 50)
        if rsi_14 < 35:  # Oversold
            technical_adjustment += 2
        elif rsi_14 > 65:  # Overbought
            technical_adjustment -= 1

        # EMA trend adjustment
        ema_trend_strength = technical.get('ema_trend_strength', 0)
        technical_adjustment += max(-2, min(3, ema_trend_strength))

        # MACD adjustment
        if technical.get('macd_bullish', False):
            technical_adjustment += 1

        # Volume adjustment
        volume_ratio = technical.get('volume_ratio_10', 1)
        if volume_ratio > 1.5:
            technical_adjustment += 1

        # Final prediction
        predicted_gain = base_gain + technical_adjustment
        predicted_price = current_price * (1 + predicted_gain / 100)

        # Calculate time horizon based on score and predicted gain
        if predicted_gain > 15:
            time_horizon = 8
        elif predicted_gain > 10:
            time_horizon = 12
        elif predicted_gain > 5:
            time_horizon = 18
        else:
            time_horizon = 25

        # Confidence level
        data_quality = technical.get('data_quality_score', 50)
        if data_quality > 80:
            confidence_level = 'high'
        elif data_quality > 60:
            confidence_level = 'medium'
        else:
            confidence_level = 'low'

        return {
            'predicted_price': round(predicted_price, 2),
            'predicted_gain': round(predicted_gain, 1),
            'confidence_level': confidence_level,
            'time_horizon': time_horizon
        }

    def _assess_risk(self, technical: Dict, fundamentals: Dict) -> Dict:
        """Comprehensive risk assessment"""
        risk_score = 0

        # Volatility risk
        volatility_regime = technical.get('volatility_regime', 'normal')
        volatility_scores = {'low': 0, 'normal': 1, 'high': 3}
        risk_score += volatility_scores.get(volatility_regime, 1)

        # PE ratio risk
        pe_ratio = fundamentals.get('pe_ratio')
        if pe_ratio:
            if pe_ratio > 50:
                risk_score += 2
            elif pe_ratio > 30:
                risk_score += 1

        # Debt risk
        debt_to_equity = fundamentals.get('debt_to_equity')
        if debt_to_equity:
            if debt_to_equity > 1.0:
                risk_score += 2
            elif debt_to_equity > 0.5:
                risk_score += 1

        # Technical risk
        bb_signal = technical.get('bb_signal', 'within_bands')
        if bb_signal == 'above_upper':
            risk_score += 1

        # Risk level and factor
        if risk_score <= 1:
            risk_level = 'Low'
            risk_factor = 1.0
        elif risk_score <= 3:
            risk_level = 'Medium'
            risk_factor = 0.95
        else:
            risk_level = 'High'
            risk_factor = 0.85

        return {
            'risk_level': risk_level,
            'risk_factor': risk_factor,
            'risk_score': risk_score
        }

    def _calculate_confidence(self, technical: Dict, fundamentals: Dict) -> int:
        """Calculate overall confidence score"""
        confidence = 50  # Base confidence

        # Data quality
        data_quality = technical.get('data_quality_score', 50)
        confidence += (data_quality - 50) / 2

        # Fundamental data availability
        if fundamentals.get('pe_ratio') is not None:
            confidence += 10
        if fundamentals.get('revenue_growth') != 5.0:  # Not default value
            confidence += 10
        if fundamentals.get('roe') is not None:
            confidence += 5

        # Technical indicator consistency
        consistency_score = 0

        # RSI and price position consistency
        rsi_14 = technical.get('rsi_14', 50)
        bb_position = technical.get('bb_position', 50)
        if (rsi_14 < 40 and bb_position < 40) or (rsi_14 > 60 and bb_position > 60):
            consistency_score += 10

        # EMA and MACD consistency
        if technical.get('ema_12_above_21', False) and technical.get('macd_bullish', False):
            consistency_score += 10

        confidence += consistency_score

        return int(max(0, min(100, confidence)))

    def _generate_technical_summary(self, technical: Dict) -> str:
        """Generate a summary of technical indicators"""
        summary_parts = []

        # RSI summary
        rsi_14 = technical.get('rsi_14', 50)
        if rsi_14 < 30:
            summary_parts.append("Oversold (RSI)")
        elif rsi_14 > 70:
            summary_parts.append("Overbought (RSI)")
        else:
            summary_parts.append("Neutral (RSI)")

        # Trend summary
        if technical.get('ema_12_above_21', False):
            summary_parts.append("Uptrend (EMA)")
        else:
            summary_parts.append("Downtrend (EMA)")

        # Bollinger Bands summary
        bb_signal = technical.get('bb_signal', 'within_bands')
        bb_summaries = {
            'above_upper': 'Above Upper BB',
            'below_lower': 'Below Lower BB',
            'within_bands': 'Within BB Range'
        }
        summary_parts.append(bb_summaries.get(bb_signal, 'BB Neutral'))

        # Volume summary
        volume_ratio = technical.get('volume_ratio_10', 1)
        if volume_ratio > 1.5:
            summary_parts.append("High Volume")
        elif volume_ratio < 0.8:
            summary_parts.append("Low Volume")
        else:
            summary_parts.append("Normal Volume")

        return " | ".join(summary_parts)

    def _estimate_market_cap(self, symbol: str) -> str:
        """Estimate market cap category"""
        large_caps = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK']
        mid_caps = ['TITAN', 'ASIANPAINT', 'ULTRACEMCO', 'BAJFINANCE', 'HCLTECH']

        if symbol in large_caps:
            return "Large Cap"
        elif symbol in mid_caps:
            return "Mid Cap"
        else:
            return "Small Cap"

    def get_pe_description(self, pe_ratio: float) -> str:
        """Convert PE ratio to user-friendly description"""
        if pe_ratio is None or pe_ratio <= 0:
            return "Not Available"
        elif pe_ratio < 10:
            return "Very Low"
        elif pe_ratio < 15:
            return "Below Average"
        elif pe_ratio <= 20:
            return "At Par"
        elif pe_ratio <= 30:
            return "Above Average"
        elif pe_ratio <= 50:
            return "High"
        else:
            return "Very High"

    def scrape_bulk_deals(self) -> List[Dict]:
        """Scrape bulk deals with enhanced error handling"""
        try:
            url = "https://trendlyne.com/equity/bulk-block-deals/today/"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = self.session.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch bulk deals: {response.status_code}")
                return self._get_fallback_bulk_deals()

            soup = BeautifulSoup(response.content, 'html.parser')
            deals = []

            tables = soup.find_all('table', {'class': 'table'})

            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header row

                for row in rows:
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 6:
                        try:
                            symbol = cells[0].get_text(strip=True).upper()
                            client_name = cells[1].get_text(strip=True)
                            deal_type = cells[2].get_text(strip=True)
                            quantity_text = cells[3].get_text(strip=True)
                            price_text = cells[4].get_text(strip=True)
                            percentage_text = cells[5].get_text(strip=True)

                            percentage = 0.0
                            if '%' in percentage_text:
                                percentage = float(percentage_text.replace('%', '').strip())

                            deal_category = self._classify_deal_type(client_name, deal_type)

                            if symbol in self.nifty50_symbols and percentage >= 0.5:
                                deals.append({
                                    'symbol': symbol,
                                    'type': deal_category,
                                    'percentage': percentage,
                                    'client': client_name,
                                    'deal_type': deal_type,
                                    'quantity': quantity_text,
                                    'price': price_text
                                })

                        except (ValueError, IndexError) as e:
                            logger.debug(f"Error parsing bulk deal row: {str(e)}")
                            continue

            significant_deals = self._filter_significant_deals(deals)
            logger.info(f"Found {len(significant_deals)} significant bulk deals")

            return significant_deals

        except Exception as e:
            logger.error(f"Error scraping bulk deals: {str(e)}")
            return self._get_fallback_bulk_deals()

    def _classify_deal_type(self, client_name: str, deal_type: str) -> str:
        """Classify deal type based on client name and deal type"""
        client_lower = client_name.lower()

        if any(term in client_lower for term in ['fii', 'foreign', 'offshore']):
            return 'FII'
        elif any(term in client_lower for term in ['dii', 'mutual', 'insurance']):
            return 'DII'
        elif any(term in client_lower for term in ['promoter', 'group']):
            return 'Promoter'
        elif 'buy' in deal_type.lower():
            return 'Buy'
        elif 'sell' in deal_type.lower():
            return 'Sell'
        else:
            return 'Other'

    def _filter_significant_deals(self, deals: List[Dict]) -> List[Dict]:
        """Filter and deduplicate significant deals"""
        significant_deals = []
        seen_combinations = set()

        for deal in deals:
            combo = (deal['symbol'], deal['type'], deal['percentage'])
            if combo not in seen_combinations:
                significant_deals.append(deal)
                seen_combinations.add(combo)

        return significant_deals

    def _get_fallback_bulk_deals(self) -> List[Dict]:
        """Fallback bulk deals when scraping fails"""
        logger.info("Using fallback bulk deals data")
        return [{
            'symbol': 'RELIANCE',
            'type': 'FII',
            'percentage': 0.8
        }, {
            'symbol': 'TCS',
            'type': 'Promoter', 
            'percentage': 1.2
        }]

    def run_enhanced_screener(self) -> List[Dict]:
        """Main enhanced screening function"""
        logger.info("Starting enhanced stock screening process...")

        # Step 1: Scrape bulk deals
        self.bulk_deals = self.scrape_bulk_deals()
        time.sleep(2)

        # Step 2: Collect enhanced data for watchlist
        stocks_data = {}

        for i, symbol in enumerate(self.watchlist):
            logger.info(f"Processing {symbol} ({i+1}/{len(self.watchlist)})")

            # Scrape enhanced fundamentals
            fundamentals = self.scrape_screener_data(symbol)

            # Calculate enhanced technical indicators
            technical = self.calculate_enhanced_technical_indicators(symbol)

            if fundamentals or technical:
                stocks_data[symbol] = {
                    'fundamentals': fundamentals,
                    'technical': technical
                }

            # Rate limiting
            time.sleep(1.5)

        # Step 3: Enhanced scoring and ranking
        top_stocks = self.enhanced_score_and_rank(stocks_data)

        # Step 4: Try ML predictions if available
        try:
            from predictor import enrich_with_ml_predictions
            enhanced_stocks = enrich_with_ml_predictions(top_stocks)
            logger.info("✅ ML predictions added successfully")
            return enhanced_stocks
        except Exception as e:
            logger.warning(f"⚠️ ML predictions failed, using enhanced scoring: {str(e)}")
            return top_stocks
    
    def is_market_hours(self) -> bool:
        """Check if the current time is within market hours (9 AM - 4 PM IST)"""
        now_utc = datetime.utcnow()
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset
        
        start_time = now_ist.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = now_ist.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return start_time <= now_ist <= end_time

    def run_screening(self, force=False):
        """Main screening process"""
        try:
            logger.info("🔍 Starting stock screening process...")

            # Check if market is open (unless forced)
            if not force and not self.is_market_hours():
                logger.info("⏰ Market is closed. Screening will run only during market hours (9 AM - 4 PM IST).")
                return False

            results = self.run_enhanced_screener()
            return results

        except Exception as e:
            logger.error(f"Error during screening: {str(e)}")
            return []


# Compatibility layer - create an instance that matches the old interface
class StockScreener(EnhancedStockScreener):
    """Compatibility wrapper for the enhanced screener"""

    def __init__(self):
        super().__init__()

    def run_screener(self) -> List[Dict]:
        """Compatibility method that calls the enhanced screener"""
        return self.run_enhanced_screener()

    def calculate_technical_indicators(self, symbol: str) -> Dict:
        """Compatibility method for technical indicators"""
        enhanced_indicators = self.calculate_enhanced_technical_indicators(symbol)

        # Return subset for backward compatibility
        return {
            'atr_14': enhanced_indicators.get('atr_14', 0),
            'current_price': enhanced_indicators.get('current_price', 0),
            'momentum_ratio': enhanced_indicators.get('momentum_2d', 0),
            'volatility': enhanced_indicators.get('atr_volatility', 0)
        }

    def score_and_rank(self, stocks_data: Dict) -> List[Dict]:
        """Compatibility method for scoring"""
        return self.enhanced_score_and_rank(stocks_data)


def main():
    """Test function"""
    screener = StockScreener()
    results = screener.run_screener()

    print(json.dumps(results[:3], indent=2))  # Print first 3 results


if __name__ == "__main__":
    main()