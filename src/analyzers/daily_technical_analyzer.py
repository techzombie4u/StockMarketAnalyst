"""
Daily Technical Analysis Module

Enhanced technical analysis using daily OHLC data instead of intraday data
for more stable and reliable indicators suitable for longer timeframes.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import talib if available, otherwise mock it
try:
    import talib
except ImportError:
    # Mock talib if it's not installed
    class MockTA:
        def CDLDOJI(self, open, high, low, close): return pd.Series([0] * len(close))
        def CDLHAMMER(self, open, high, low, close): return pd.Series([0] * len(close))
        def CDLENGULFING(self, open, high, low, close): return pd.Series([0] * len(close))
        def CDLSHOOTINGSTAR(self, open, high, low, close): return pd.Series([0] * len(close))
    talib = MockTA()


logger = logging.getLogger(__name__)

class DailyTechnicalAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_expiry = timedelta(hours=6)  # Cache daily data for 6 hours

    def fetch_daily_ohlc_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Fetch daily OHLC data from Yahoo Finance"""
        try:
            cache_key = f"{symbol}_{period}"
            now = datetime.now()

            # Check cache first
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if now - cached_time < self.cache_expiry:
                    logger.debug(f"Using cached daily data for {symbol}")
                    return cached_data

            # Fetch fresh data
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)

            # Get daily OHLC data
            hist_data = stock.history(period=period, interval="1d")

            if hist_data is None or hist_data.empty:
                logger.warning(f"No daily OHLC data found for {symbol}")
                return None

            # Clean and prepare data
            hist_data = hist_data.dropna()

            if len(hist_data) < 50:
                logger.warning(f"Insufficient daily data for {symbol}: {len(hist_data)} days")
                return None

            # Cache the data
            self.cache[cache_key] = (hist_data.copy(), now)

            logger.info(f"Fetched daily OHLC data for {symbol}: {len(hist_data)} days")
            return hist_data

        except Exception as e:
            logger.error(f"Error fetching daily OHLC data for {symbol}: {str(e)}")
            return None

    def calculate_daily_technical_indicators(self, symbol: str) -> Dict:
        """Calculate comprehensive technical indicators using daily OHLC data"""
        try:
            # Fetch daily OHLC data
            daily_data = self.fetch_daily_ohlc_data(symbol)

            if daily_data is None or daily_data.empty:
                return {}

            indicators = {}

            # Basic price data
            high = daily_data['High']
            low = daily_data['Low']
            close = daily_data['Close']
            open_price = daily_data['Open']
            volume = daily_data['Volume']

            current_price = float(close.iloc[-1])
            indicators['current_price'] = current_price

            # 1. Moving Averages (Daily)
            indicators.update(self._calculate_moving_averages(close))

            # 2. Trend Analysis
            indicators.update(self._calculate_trend_indicators(close, high, low))

            # 3. Momentum Indicators
            indicators.update(self._calculate_momentum_indicators(close, high, low))

            # 4. Volatility Indicators
            indicators.update(self._calculate_volatility_indicators(close, high, low, open_price))

            # 5. Volume Analysis
            indicators.update(self._calculate_volume_indicators(close, volume))

            # 6. Support/Resistance Levels
            indicators.update(self._calculate_support_resistance(high, low, close))

            # 7. Pattern Recognition
            indicators.update(self._detect_chart_patterns(high, low, close, open_price))

            # 8. Strength Indicators
            indicators.update(self._calculate_strength_indicators(close, high, low, volume))

            # 9. Daily Momentum
            indicators.update(self._calculate_daily_momentum(close))

            # 10. Risk Metrics
            indicators.update(self._calculate_risk_metrics(close))

            # 11. Advanced Predictive Features
            try:
                indicators.update(self._calculate_market_microstructure(daily_data))
            except AttributeError:
                # Add basic microstructure indicators as fallback
                indicators.update({
                    'bid_ask_spread': 0.0,
                    'market_impact': 0.0,
                    'liquidity_ratio': 1.0
                })

            # 12. Seasonality and Cyclical Patterns
            indicators.update(self._calculate_temporal_patterns(daily_data))

            # 13. Cross-Asset Correlations
            indicators.update(self._calculate_market_regime_indicators())

            indicators['data_quality'] = 'daily_ohlc'
            indicators['timeframe'] = 'daily'
            indicators['data_points'] = len(daily_data)

            return indicators

        except Exception as e:
            logger.error(f"Error calculating daily technical indicators for {symbol}: {str(e)}")
            return {}

    def _calculate_moving_averages(self, close: pd.Series) -> Dict:
        """Calculate various moving averages"""
        indicators = {}

        try:
            # Simple Moving Averages
            periods = [5, 10, 20, 50, 100, 200]
            for period in periods:
                if len(close) >= period:
                    sma = close.rolling(window=period).mean()
                    indicators[f'sma_{period}'] = float(sma.iloc[-1])

                    # Price vs SMA
                    price_vs_sma = ((close.iloc[-1] - sma.iloc[-1]) / sma.iloc[-1]) * 100
                    indicators[f'price_vs_sma_{period}'] = round(price_vs_sma, 2)

            # Exponential Moving Averages
            ema_periods = [12, 26, 50]
            for period in ema_periods:
                if len(close) >= period:
                    ema = close.ewm(span=period).mean()
                    indicators[f'ema_{period}'] = float(ema.iloc[-1])

            # Golden Cross / Death Cross signals
            if 'sma_50' in indicators and 'sma_200' in indicators:
                indicators['golden_cross'] = indicators['sma_50'] > indicators['sma_200']
                indicators['death_cross'] = indicators['sma_50'] < indicators['sma_200']

            # Price position relative to key MAs
            current_price = close.iloc[-1]
            if 'sma_20' in indicators:
                indicators['above_sma_20'] = current_price > indicators['sma_20']
            if 'sma_50' in indicators:
                indicators['above_sma_50'] = current_price > indicators['sma_50']
            if 'sma_200' in indicators:
                indicators['above_sma_200'] = current_price > indicators['sma_200']

        except Exception as e:
            logger.error(f"Error calculating moving averages: {str(e)}")

        return indicators

    def _calculate_trend_indicators(self, close: pd.Series, high: pd.Series, low: pd.Series) -> Dict:
        """Calculate trend strength and direction indicators"""
        indicators = {}

        try:
            # ADX (Average Directional Index)
            indicators.update(self._calculate_adx(high, low, close))

            # Parabolic SAR
            indicators.update(self._calculate_parabolic_sar(high, low, close))

            # Ichimoku components
            indicators.update(self._calculate_ichimoku(high, low, close))

            # Trend strength score
            trend_score = 0

            # Check various trend conditions
            if len(close) >= 20:
                # Price above/below 20-day SMA
                sma_20 = close.rolling(window=20).mean()
                if close.iloc[-1] > sma_20.iloc[-1]:
                    trend_score += 2

                # Rising/falling SMA
                if sma_20.iloc[-1] > sma_20.iloc[-5]:
                    trend_score += 1
                elif sma_20.iloc[-1] < sma_20.iloc[-5]:
                    trend_score -= 1

            # Higher highs / Lower lows
            if len(high) >= 10:
                recent_high = high.tail(10).max()
                prev_high = high.iloc[-20:-10].max() if len(high) >= 20 else high.iloc[0]
                if recent_high > prev_high:
                    trend_score += 1
                elif recent_high < prev_high:
                    trend_score -= 1

            indicators['trend_strength_score'] = trend_score

            # Trend classification
            if trend_score >= 3:
                indicators['trend_direction'] = 'strong_uptrend'
            elif trend_score >= 1:
                indicators['trend_direction'] = 'uptrend'
            elif trend_score <= -3:
                indicators['trend_direction'] = 'strong_downtrend'
            elif trend_score <= -1:
                indicators['trend_direction'] = 'downtrend'
            else:
                indicators['trend_direction'] = 'sideways'

        except Exception as e:
            logger.error(f"Error calculating trend indicators: {str(e)}")

        return indicators

    def _calculate_momentum_indicators(self, close: pd.Series, high: pd.Series, low: pd.Series) -> Dict:
        """Calculate momentum oscillators"""
        indicators = {}

        try:
            # RSI (14-day)
            if len(close) >= 15:
                delta = close.diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                rs = avg_gain / (avg_loss + 1e-10)
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi_14'] = float(rsi.iloc[-1])

                # RSI signals
                if indicators['rsi_14'] < 30:
                    indicators['rsi_signal'] = 'oversold'
                elif indicators['rsi_14'] > 70:
                    indicators['rsi_signal'] = 'overbought'
                else:
                    indicators['rsi_signal'] = 'neutral'

            # Stochastic Oscillator
            if len(close) >= 14:
                lowest_low = low.rolling(window=14).min()
                highest_high = high.rolling(window=14).max()
                k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
                d_percent = k_percent.rolling(window=3).mean()

                indicators['stoch_k'] = float(k_percent.iloc[-1])
                indicators['stoch_d'] = float(d_percent.iloc[-1])

                # Stochastic signals
                if indicators['stoch_k'] < 20:
                    indicators['stoch_signal'] = 'oversold'
                elif indicators['stoch_k'] > 80:
                    indicators['stoch_signal'] = 'overbought'
                else:
                    indicators['stoch_signal'] = 'neutral'

            # MACD
            if len(close) >= 26:
                ema_12 = close.ewm(span=12).mean()
                ema_26 = close.ewm(span=26).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=9).mean()
                histogram = macd_line - signal_line

                indicators['macd'] = float(macd_line.iloc[-1])
                indicators['macd_signal'] = float(signal_line.iloc[-1])
                indicators['macd_histogram'] = float(histogram.iloc[-1])
                indicators['macd_bullish'] = indicators['macd'] > indicators['macd_signal']

            # Rate of Change (ROC)
            periods = [5, 10, 20]
            for period in periods:
                if len(close) > period:
                    roc = ((close.iloc[-1] - close.iloc[-period-1]) / close.iloc[-period-1]) * 100
                    indicators[f'roc_{period}'] = round(roc, 2)

            # Williams %R
            if len(close) >= 14:
                highest_high = high.rolling(window=14).max()
                lowest_low = low.rolling(window=14).min()
                williams_r = -100 * ((highest_high.iloc[-1] - close.iloc[-1]) /
                                   (highest_high.iloc[-1] - lowest_low.iloc[-1]))
                indicators['williams_r'] = round(williams_r, 2)

        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {str(e)}")

        return indicators

    def _calculate_volatility_indicators(self, close: pd.Series, high: pd.Series,
                                       low: pd.Series, open_price: pd.Series) -> Dict:
        """Calculate volatility-based indicators"""
        indicators = {}

        try:
            # Average True Range (ATR)
            if len(close) >= 15:
                high_low = high - low
                high_close = (high - close.shift()).abs()
                low_close = (low - close.shift()).abs()
                true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

                for period in [14, 21]:
                    atr = true_range.rolling(window=period).mean()
                    indicators[f'atr_{period}'] = float(atr.iloc[-1])

                # ATR-based volatility percentage
                atr_volatility_pct = (indicators['atr_14'] / close.iloc[-1]) * 100
                indicators['atr_volatility_pct'] = round(atr_volatility_pct, 2)

            # Bollinger Bands
            if len(close) >= 20:
                sma_20 = close.rolling(window=20).mean()
                std_20 = close.rolling(window=20).std()

                bb_upper = sma_20 + (std_20 * 2)
                bb_lower = sma_20 - (std_20 * 2)

                indicators['bb_upper'] = float(bb_upper.iloc[-1])
                indicators['bb_middle'] = float(sma_20.iloc[-1])
                indicators['bb_lower'] = float(bb_lower.iloc[-1])

                # BB position and width
                bb_position = ((close.iloc[-1] - bb_lower.iloc[-1]) /
                             (bb_upper.iloc[-1] - bb_lower.iloc[-1])) * 100
                indicators['bb_position'] = round(bb_position, 1)

                bb_width = ((bb_upper.iloc[-1] - bb_lower.iloc[-1]) / sma_20.iloc[-1]) * 100
                indicators['bb_width'] = round(bb_width, 2)

                # BB squeeze detection
                if bb_width < 10:  # Threshold for squeeze
                    indicators['bb_squeeze'] = True
                else:
                    indicators['bb_squeeze'] = False

            # Historical Volatility
            if len(close) >= 21:
                returns = close.pct_change().dropna()
                hist_vol_20 = returns.rolling(window=20).std() * np.sqrt(252) * 100
                indicators['historical_volatility_20'] = round(hist_vol_20.iloc[-1], 2)

                # Enhanced volatility classification with ATR-based thresholds
                atr_volatility = indicators.get('atr_volatility_pct', 2.5)

                # Dynamic volatility regimes based on ATR percentage
                if atr_volatility < 1.5:
                    indicators['volatility_regime'] = 'low'
                elif 1.5 <= atr_volatility <= 3.0:
                    indicators['volatility_regime'] = 'medium'
                else:
                    indicators['volatility_regime'] = 'high'

                # Additional classification based on historical volatility
                if indicators['historical_volatility_20'] < 15:
                    indicators['hist_vol_regime'] = 'low'
                elif indicators['historical_volatility_20'] > 35:
                    indicators['hist_vol_regime'] = 'high'
                else:
                    indicators['hist_vol_regime'] = 'medium'

            # Daily Range Analysis
            daily_range = ((high - low) / close) * 100
            avg_daily_range = daily_range.rolling(window=20).mean()
            indicators['avg_daily_range_pct'] = round(avg_daily_range.iloc[-1], 2)

        except Exception as e:
            logger.error(f"Error calculating volatility indicators: {str(e)}")

        return indicators

    def _calculate_volume_indicators(self, close: pd.Series, volume: pd.Series) -> Dict:
        """Calculate volume-based indicators"""
        indicators = {}

        try:
            # Volume Moving Averages
            periods = [10, 20, 50]
            for period in periods:
                if len(volume) >= period:
                    vol_ma = volume.rolling(window=period).mean()
                    indicators[f'volume_ma_{period}'] = float(vol_ma.iloc[-1])

                    # Current volume vs average
                    vol_ratio = volume.iloc[-1] / vol_ma.iloc[-1]
                    indicators[f'volume_ratio_{period}'] = round(vol_ratio, 2)

            # On-Balance Volume (OBV)
            if len(close) >= 2:
                price_change = close.diff()
                volume_direction = np.where(price_change > 0, volume,
                                          np.where(price_change < 0, -volume, 0))
                obv = pd.Series(volume_direction).cumsum()
                indicators['obv'] = float(obv.iloc[-1])

                # OBV trend
                if len(obv) >= 10:
                    obv_trend = obv.iloc[-1] - obv.iloc[-10]
                    indicators['obv_trend'] = 'rising' if obv_trend > 0 else 'falling'

            # Volume Rate of Change
            if len(volume) >= 10:
                vol_roc = ((volume.iloc[-1] - volume.iloc[-10]) / volume.iloc[-10]) * 100
                indicators['volume_roc_10'] = round(vol_roc, 2)

            # Price-Volume Trend (PVT)
            if len(close) >= 2:
                price_change_pct = close.pct_change()
                pvt = (price_change_pct * volume).cumsum()
                indicators['pvt'] = float(pvt.iloc[-1])

            # Volume classification
            current_vol = volume.iloc[-1]
            if 'volume_ma_20' in indicators:
                if current_vol > indicators['volume_ma_20'] * 1.5:
                    indicators['volume_classification'] = 'high'
                elif current_vol < indicators['volume_ma_20'] * 0.7:
                    indicators['volume_classification'] = 'low'
                else:
                    indicators['volume_classification'] = 'normal'

        except Exception as e:
            logger.error(f"Error calculating volume indicators: {str(e)}")

        return indicators

    def _calculate_support_resistance(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        """Calculate support and resistance levels"""
        indicators = {}

        try:
            # Pivot Points (Traditional)
            if len(high) >= 1 and len(low) >= 1 and len(close) >= 1:
                pivot = (high.iloc[-1] + low.iloc[-1] + close.iloc[-1]) / 3

                resistance_1 = 2 * pivot - low.iloc[-1]
                support_1 = 2 * pivot - high.iloc[-1]

                resistance_2 = pivot + (high.iloc[-1] - low.iloc[-1])
                support_2 = pivot - (high.iloc[-1] - low.iloc[-1])

                indicators['pivot_point'] = round(pivot, 2)
                indicators['resistance_1'] = round(resistance_1, 2)
                indicators['support_1'] = round(support_1, 2)
                indicators['resistance_2'] = round(resistance_2, 2)
                indicators['support_2'] = round(support_2, 2)

            # Recent highs and lows as S/R levels
            periods = [20, 50]
            for period in periods:
                if len(high) >= period and len(low) >= period:
                    recent_high = high.rolling(window=period).max().iloc[-1]
                    recent_low = low.rolling(window=period).min().iloc[-1]

                    indicators[f'resistance_{period}d'] = round(recent_high, 2)
                    indicators[f'support_{period}d'] = round(recent_low, 2)

            # Current price position relative to S/R
            current_price = close.iloc[-1]
            if 'support_1' in indicators and 'resistance_1' in indicators:
                sr_range = indicators['resistance_1'] - indicators['support_1']
                if sr_range > 0:
                    price_position = ((current_price - indicators['support_1']) / sr_range) * 100
                    indicators['price_position_sr'] = round(price_position, 1)

        except Exception as e:
            logger.error(f"Error calculating support/resistance: {str(e)}")

        return indicators

    def _detect_chart_patterns(self, high: pd.Series, low: pd.Series,
                             close: pd.Series, open_price: pd.Series) -> Dict:
        """Detect basic chart patterns"""
        indicators = {}

        try:
            # Candlestick patterns
            if len(close) >= 2:
                # Doji detection
                body_size = abs(close.iloc[-1] - open_price.iloc[-1])
                total_range = high.iloc[-1] - low.iloc[-1]

                if total_range > 0 and (body_size / total_range) < 0.1:
                    indicators['doji_pattern'] = True
                else:
                    indicators['doji_pattern'] = False

                # Hammer/Hanging Man
                upper_shadow = high.iloc[-1] - max(close.iloc[-1], open_price.iloc[-1])
                lower_shadow = min(close.iloc[-1], open_price.iloc[-1]) - low.iloc[-1]

                if (lower_shadow > 2 * body_size and upper_shadow < body_size and
                    total_range > 0):
                    indicators['hammer_pattern'] = True
                else:
                    indicators['hammer_pattern'] = False

            # Gap analysis
            if len(close) >= 2:
                gap_up = low.iloc[-1] > high.iloc[-2]
                gap_down = high.iloc[-1] < low.iloc[-2]

                indicators['gap_up'] = gap_up
                indicators['gap_down'] = gap_down

                if gap_up or gap_down:
                    gap_size = abs(close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
                    indicators['gap_size_pct'] = round(gap_size, 2)

            # Trend line breaks (simplified)
            if len(close) >= 20:
                # Simple trend line using linear regression
                x = np.arange(len(close.tail(20)))
                y = close.tail(20).values
                slope = np.polyfit(x, y, 1)[0]

                indicators['trend_slope'] = round(slope, 4)
                indicators['trend_direction_simple'] = 'up' if slope > 0 else 'down'

        except Exception as e:
            logger.error(f"Error detecting chart patterns: {str(e)}")

        return indicators

    def _calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict:
        """Calculate Average Directional Index"""
        indicators = {}

        try:
            if len(close) < period + 1:
                return indicators

            # True Range
            high_low = high - low
            high_close = (high - close.shift()).abs()
            low_close = (low - close.shift()).abs()
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

            # Directional Movement
            plus_dm = high.diff()
            minus_dm = -low.diff()

            plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
            minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

            # Smoothed averages
            atr = true_range.rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

            # ADX calculation
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()

            indicators['adx'] = round(adx.iloc[-1], 2)
            indicators['plus_di'] = round(plus_di.iloc[-1], 2)
            indicators['minus_di'] = round(minus_di.iloc[-1], 2)

            # ADX interpretation
            if indicators['adx'] > 25:
                indicators['trend_strength'] = 'strong'
            elif indicators['adx'] > 20:
                indicators['trend_strength'] = 'moderate'
            else:
                indicators['trend_strength'] = 'weak'

        except Exception as e:
            logger.error(f"Error calculating ADX: {str(e)}")

        return indicators

    def _calculate_parabolic_sar(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        """Calculate Parabolic SAR"""
        indicators = {}

        try:
            if len(close) < 10:
                return indicators

            # Simplified Parabolic SAR calculation
            af = 0.02  # Acceleration factor
            max_af = 0.20

            # Use recent data for calculation
            recent_data = close.tail(20)
            if len(recent_data) < 5:
                return indicators

            # Simple implementation - compare with recent high/low
            recent_high = high.tail(10).max()
            recent_low = low.tail(10).min()
            current_price = close.iloc[-1]

            # Determine if price is above or below SAR
            if current_price > recent_low:
                sar_value = recent_low
                sar_trend = 'bullish'
            else:
                sar_value = recent_high
                sar_trend = 'bearish'

            indicators['parabolic_sar'] = round(sar_value, 2)
            indicators['sar_trend'] = sar_trend
            indicators['price_above_sar'] = current_price > sar_value

        except Exception as e:
            logger.error(f"Error calculating Parabolic SAR: {str(e)}")

        return indicators

    def _calculate_ichimoku(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict:
        """Calculate Ichimoku Cloud components"""
        indicators = {}

        try:
            if len(close) < 52:
                return indicators

            # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
            tenkan_high = high.rolling(window=9).max()
            tenkan_low = low.rolling(window=9).min()
            tenkan_sen = (tenkan_high + tenkan_low) / 2

            # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
            kijun_high = high.rolling(window=26).max()
            kijun_low = low.rolling(window=26).min()
            kijun_sen = (kijun_high + kijun_low) / 2

            # Senkou Span A: (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
            senkou_span_a = (tenkan_sen + kijun_sen) / 2

            # Senkou Span B: (52-period high + 52-period low) / 2, plotted 26 periods ahead
            senkou_high = high.rolling(window=52).max()
            senkou_low = low.rolling(window=52).min()
            senkou_span_b = (senkou_high + senkou_low) / 2

            indicators['tenkan_sen'] = round(tenkan_sen.iloc[-1], 2)
            indicators['kijun_sen'] = round(kijun_sen.iloc[-1], 2)
            indicators['senkou_span_a'] = round(senkou_span_a.iloc[-1], 2)
            indicators['senkou_span_b'] = round(senkou_span_b.iloc[-1], 2)

            # Ichimoku signals
            current_price = close.iloc[-1]
            cloud_top = max(indicators['senkou_span_a'], indicators['senkou_span_b'])
            cloud_bottom = min(indicators['senkou_span_a'], indicators['senkou_span_b'])

            if current_price > cloud_top:
                indicators['ichimoku_signal'] = 'above_cloud'
            elif current_price < cloud_bottom:
                indicators['ichimoku_signal'] = 'below_cloud'
            else:
                indicators['ichimoku_signal'] = 'in_cloud'

            # TK Cross
            indicators['tk_cross_bullish'] = (tenkan_sen.iloc[-1] > kijun_sen.iloc[-1] and
                                            tenkan_sen.iloc[-2] <= kijun_sen.iloc[-2])
            indicators['tk_cross_bearish'] = (tenkan_sen.iloc[-1] < kijun_sen.iloc[-1] and
                                            tenkan_sen.iloc[-2] >= kijun_sen.iloc[-2])

        except Exception as e:
            logger.error(f"Error calculating Ichimoku: {str(e)}")

        return indicators

    def _calculate_strength_indicators(self, close: pd.Series, high: pd.Series,
                                     low: pd.Series, volume: pd.Series) -> Dict:
        """Calculate market strength indicators"""
        indicators = {}

        try:
            # Money Flow Index (MFI)
            if len(close) >= 15:
                typical_price = (high + low + close) / 3
                money_flow = typical_price * volume

                positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0)
                negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0)

                pos_mf_sum = positive_flow.rolling(window=14).sum()
                neg_mf_sum = negative_flow.rolling(window=14).sum()

                money_ratio = pos_mf_sum / (neg_mf_sum + 1e-10)
                mfi = 100 - (100 / (1 + money_ratio))

                indicators['mfi'] = round(mfi.iloc[-1], 2)

                # MFI signals
                if indicators['mfi'] < 20:
                    indicators['mfi_signal'] = 'oversold'
                elif indicators['mfi'] > 80:
                    indicators['mfi_signal'] = 'overbought'
                else:
                    indicators['mfi_signal'] = 'neutral'

            # Commodity Channel Index (CCI)
            if len(close) >= 20:
                typical_price = (high + low + close) / 3
                sma_tp = typical_price.rolling(window=20).mean()
                mad = typical_price.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())

                cci = (typical_price - sma_tp) / (0.015 * mad)
                indicators['cci'] = round(cci.iloc[-1], 2)

                # CCI signals
                if indicators['cci'] < -100:
                    indicators['cci_signal'] = 'oversold'
                elif indicators['cci'] > 100:
                    indicators['cci_signal'] = 'overbought'
                else:
                    indicators['cci_signal'] = 'neutral'

            # Force Index
            if len(close) >= 2:
                force_index = (close - close.shift(1)) * volume
                force_index_13 = force_index.rolling(window=13).mean()
                indicators['force_index'] = round(force_index_13.iloc[-1], 0)

        except Exception as e:
            logger.error(f"Error calculating strength indicators: {str(e)}")

        return indicators

    def _calculate_daily_momentum(self, close: pd.Series) -> Dict:
        """Calculate daily momentum indicators"""
        indicators = {}

        try:
            # Daily returns
            daily_returns = close.pct_change()

            # Multi-period momentum
            periods = [1, 3, 5, 10, 20]
            for period in periods:
                if len(close) > period:
                    momentum_pct = ((close.iloc[-1] - close.iloc[-period-1]) /
                                  close.iloc[-period-1]) * 100
                    indicators[f'momentum_{period}d_pct'] = round(momentum_pct, 2)

            # Momentum acceleration
            if len(close) >= 10:
                mom_5d = indicators.get('momentum_5d_pct', 0)
                mom_10d = indicators.get('momentum_10d_pct', 0)

                momentum_acceleration = mom_5d - (mom_10d / 2)  # Simplified acceleration
                indicators['momentum_acceleration'] = round(momentum_acceleration, 2)

            # Consecutive up/down days
            if len(daily_returns) >= 10:
                recent_returns = daily_returns.tail(10)
                consecutive_up = 0
                consecutive_down = 0

                for ret in reversed(recent_returns.values):
                    if ret > 0:
                        consecutive_up += 1
                        break
                    elif ret < 0:
                        consecutive_down += 1
                    else:
                        break

                indicators['consecutive_up_days'] = consecutive_up
                indicators['consecutive_down_days'] = consecutive_down

        except Exception as e:
            logger.error(f"Error calculating daily momentum: {str(e)}")

        return indicators

    def _calculate_risk_metrics(self, close: pd.Series) -> Dict:
        """Calculate risk-based metrics"""
        indicators = {}

        try:
            if len(close) < 21:
                return indicators

            # Daily returns
            returns = close.pct_change().dropna()

            # Value at Risk (VaR) - 95% confidence
            if len(returns) >= 20:
                var_95 = np.percentile(returns.tail(20), 5) * 100
                indicators['var_95_1d'] = round(var_95, 2)

            # Maximum Drawdown
            if len(close) >= 50:
                peak = close.rolling(window=50, min_periods=1).max()
                drawdown = (close - peak) / peak * 100
                max_drawdown = drawdown.min()
                indicators['max_drawdown_50d'] = round(max_drawdown, 2)

            # Sharpe Ratio (simplified, assuming risk-free rate = 0)
            if len(returns) >= 20:
                avg_return = returns.tail(20).mean()
                std_return = returns.tail(20).std()
                if std_return > 0:
                    sharpe = (avg_return / std_return) * np.sqrt(252)  # Annualized
                    indicators['sharpe_ratio_20d'] = round(sharpe, 2)

            # Downside Deviation
            if len(returns) >= 20:
                negative_returns = returns[returns < 0]
                if len(negative_returns) > 0:
                    downside_dev = negative_returns.std() * np.sqrt(252) * 100
                    indicators['downside_deviation'] = round(downside_dev, 2)

        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")

        return indicators

    def _calculate_market_microstructure(self, data: pd.DataFrame) -> Dict:
        """Calculate advanced market microstructure metrics"""
        try:
            # Calculate basic microstructure metrics
            volume_weighted_price = (data['close'] * data['volume']).sum() / data['volume'].sum()
            avg_price = data['close'].mean()

            # Price impact approximation
            price_changes = data['close'].pct_change().abs()
            volume_changes = data['volume'].pct_change().abs()

            # Correlation between price and volume changes
            price_volume_corr = price_changes.corr(volume_changes) if len(price_changes) > 1 else 0

            # Liquidity ratio (volume relative to price volatility)
            price_volatility = data['close'].pct_change().std()
            avg_volume = data['volume'].mean()
            liquidity_ratio = avg_volume / (price_volatility * 1000000) if price_volatility > 0 else 1.0

            return {
                'bid_ask_spread': abs(volume_weighted_price - avg_price) / avg_price if avg_price > 0 else 0.0,
                'market_impact': price_volume_corr if not pd.isna(price_volume_corr) else 0.0,
                'liquidity_ratio': min(liquidity_ratio, 10.0)  # Cap at reasonable value
            }

        except Exception as e:
            logger.warning(f"Market microstructure calculation failed: {str(e)}")
            return {
                'bid_ask_spread': 0.0,
                'market_impact': 0.0,
                'liquidity_ratio': 1.0
            }

    def _calculate_temporal_patterns(self, daily_data: pd.DataFrame) -> Dict:
        """Calculate temporal and seasonal patterns"""
        indicators = {}

        try:
            if len(daily_data) >= 30:
                # Day of week effect
                daily_data['day_of_week'] = daily_data.index.dayofweek
                daily_data['returns'] = daily_data['Close'].pct_change()

                # Average returns by day of week
                day_returns = daily_data.groupby('day_of_week')['returns'].mean()

                # Monday effect (often negative)
                monday_return = day_returns.get(0, 0)  # Monday is 0
                friday_return = day_returns.get(4, 0)  # Friday is 4

                indicators['monday_effect'] = round(monday_return * 100, 3)
                indicators['friday_effect'] = round(friday_return * 100, 3)

                # Month effect (if enough data)
                if len(daily_data) >= 90:
                    daily_data['month'] = daily_data.index.month
                    month_returns = daily_data.groupby('month')['returns'].mean()
                    current_month = datetime.now().month
                    indicators['current_month_avg_return'] = round(month_returns.get(current_month, 0) * 100, 3)

                # Volatility clustering
                returns_vol = daily_data['returns'].rolling(window=5).std()
                vol_persistence = returns_vol.autocorr(lag=1)
                indicators['volatility_clustering'] = round(vol_persistence, 3) if not pd.isna(vol_persistence) else 0

        except Exception as e:
            logger.error(f"Error calculating temporal patterns: {str(e)}")

        return indicators

    def _calculate_market_regime_indicators(self) -> Dict:
        """Calculate market regime indicators for better prediction context"""
        indicators = {}

        try:
            # Simplified market regime detection
            # In production, this would fetch broader market data

            # VIX-like indicator (simplified using recent volatility)
            indicators['market_fear_index'] = 'medium'  # Would be calculated from broader market

            # Market trend regime
            indicators['market_regime'] = 'normal'  # Would be determined from index analysis

            # Sector rotation indicator
            indicators['sector_rotation_phase'] = 'mid_cycle'  # Would analyze sector performance

            # Liquidity conditions
            indicators['liquidity_conditions'] = 'normal'  # Would analyze market depth

        except Exception as e:
            logger.error(f"Error calculating market regime indicators: {str(e)}")

        return indicators


    def generate_daily_technical_summary(self, indicators: Dict) -> str:
        """Generate a comprehensive technical summary"""
        try:
            summary_parts = []

            # Trend summary
            trend_direction = indicators.get('trend_direction', 'sideways')
            summary_parts.append(f"Trend: {trend_direction.replace('_', ' ').title()}")

            # RSI summary
            rsi = indicators.get('rsi_14', 50)
            rsi_signal = indicators.get('rsi_signal', 'neutral')
            summary_parts.append(f"RSI: {rsi:.1f} ({rsi_signal})")

            # Moving average summary
            if indicators.get('above_sma_20', False):
                summary_parts.append("Above 20-day SMA")
            else:
                summary_parts.append("Below 20-day SMA")

            # Volume summary
            vol_class = indicators.get('volume_classification', 'normal')
            summary_parts.append(f"Volume: {vol_class}")

            # Volatility summary
            vol_regime = indicators.get('volatility_regime', 'medium')
            summary_parts.append(f"Volatility: {vol_regime}")

            # Support/Resistance
            if 'price_position_sr' in indicators:
                sr_pos = indicators['price_position_sr']
                if sr_pos > 75:
                    summary_parts.append("Near resistance")
                elif sr_pos < 25:
                    summary_parts.append("Near support")
                else:
                    summary_parts.append("Mid-range")

            return " | ".join(summary_parts)

        except Exception as e:
            logger.error(f"Error generating technical summary: {str(e)}")
            return "Technical analysis summary unavailable"

# Convenience function for integration
def get_daily_technical_analysis(symbol: str) -> Dict:
    """Get daily technical analysis for a symbol"""
    analyzer = DailyTechnicalAnalyzer()
    return analyzer.calculate_daily_technical_indicators(symbol)

def main():
    """Test the daily technical analyzer"""
    analyzer = DailyTechnicalAnalyzer()

    # Test with a sample stock
    test_symbol = "RELIANCE"
    print(f"Testing daily technical analysis for {test_symbol}...")

    indicators = analyzer.calculate_daily_technical_indicators(test_symbol)

    if indicators:
        print(f"\nDaily Technical Analysis Results for {test_symbol}:")
        print(f"Current Price: {indicators.get('current_price', 'N/A')}")
        print(f"Trend Direction: {indicators.get('trend_direction', 'N/A')}")
        print(f"RSI (14): {indicators.get('rsi_14', 'N/A')}")
        print(f"Above 20-day SMA: {indicators.get('above_sma_20', 'N/A')}")
        print(f"Volume Classification: {indicators.get('volume_classification', 'N/A')}")
        print(f"Volatility Regime: {indicators.get('volatility_regime', 'N/A')}")

        summary = analyzer.generate_daily_technical_summary(indicators)
        print(f"\nTechnical Summary: {summary}")
    else:
        print("Failed to get technical analysis data")

if __name__ == "__main__":
    main()