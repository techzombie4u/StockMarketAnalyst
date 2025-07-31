
"""
Stock Market Analyst - ML Data Loader Module

Handles data preparation for machine learning models:
1. Historical OHLC data fetching (5 years for training)
2. Technical indicators calculation
3. Time-series windowing for LSTM
4. Target variable preparation for both models
"""

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MLDataLoader:
    def __init__(self, lookback_window: int = 60):
        self.lookback_window = lookback_window
        self.price_scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()
        
    def fetch_historical_data(self, symbol: str, period: str = "5y") -> Optional[pd.DataFrame]:
        """Fetch 5 years of historical OHLC data from Yahoo Finance"""
        try:
            ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]
            
            for ticker_format in ticker_formats:
                try:
                    ticker = yf.Ticker(ticker_format)
                    data = ticker.history(period=period, progress=False)
                    
                    if data is not None and not data.empty and len(data) > 100:
                        logger.info(f"✅ Fetched {len(data)} days of data for {symbol} using {ticker_format}")
                        # Reset index to have Date as column
                        data.reset_index(inplace=True)
                        return data
                except Exception as e:
                    logger.debug(f"Failed {ticker_format} for {symbol}: {str(e)}")
                    continue
            
            logger.warning(f"No historical data found for {symbol}")
            return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for ML features with proper error handling"""
        try:
            df = data.copy()
            
            # Ensure we have the required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing required column: {col}")
                    return data
            
            # Calculate ATR (14-day)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['ATR'] = true_range.rolling(window=14).mean().fillna(0)
            
            # Calculate momentum ratios
            df['Price_Change'] = df['Close'].pct_change().fillna(0)
            df['Momentum_2d'] = df['Close'].pct_change(periods=2).fillna(0)
            df['Momentum_5d'] = df['Close'].pct_change(periods=5).fillna(0)
            df['Momentum_10d'] = df['Close'].pct_change(periods=10).fillna(0)
            
            # Volume indicators - Fix the DataFrame assignment error
            volume_ma = df['Volume'].rolling(window=20).mean().fillna(df['Volume'].mean())
            df['Volume_MA'] = volume_ma
            
            # Fix: Ensure volume_ratio is calculated properly
            volume_ratio = df['Volume'] / volume_ma
            volume_ratio = volume_ratio.fillna(1.0)
            df['Volume_Ratio'] = volume_ratio
            
            # Moving averages
            df['MA_5'] = df['Close'].rolling(window=5).mean().fillna(df['Close'])
            df['MA_10'] = df['Close'].rolling(window=10).mean().fillna(df['Close'])
            df['MA_20'] = df['Close'].rolling(window=20).mean().fillna(df['Close'])
            
            # Price position relative to moving averages
            df['Price_vs_MA5'] = ((df['Close'] - df['MA_5']) / df['MA_5']).fillna(0)
            df['Price_vs_MA10'] = ((df['Close'] - df['MA_10']) / df['MA_10']).fillna(0)
            df['Price_vs_MA20'] = ((df['Close'] - df['MA_20']) / df['MA_20']).fillna(0)
            
            # Volatility
            df['Volatility'] = df['Price_Change'].rolling(window=20).std().fillna(0)
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            # Avoid division by zero
            rs = gain / (loss + 1e-8)
            df['RSI'] = (100 - (100 / (1 + rs))).fillna(50)
            
            # Fill any remaining NaN values using proper pandas methods
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return data
    
    def prepare_lstm_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare windowed time-series data for LSTM with fixed fillna method"""
        try:
            # Select features for LSTM
            feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 
                             'Momentum_2d', 'Momentum_5d', 'Price_vs_MA5', 'Price_vs_MA10', 'RSI']
            
            # Check which columns actually exist
            available_columns = [col for col in feature_columns if col in data.columns]
            
            if len(available_columns) < 5:  # Need at least basic OHLCV
                logger.warning(f"Insufficient columns for LSTM. Available: {available_columns}")
                return None, None
            
            # Use available columns
            df_clean = data[available_columns].copy()
            
            # Fix: Use proper pandas fillna methods
            df_clean = df_clean.fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            if len(df_clean) < self.lookback_window + 1:
                logger.warning(f"Insufficient data for LSTM preparation: {len(df_clean)} < {self.lookback_window + 1}")
                return None, None
            
            # Normalize features
            try:
                scaled_features = self.feature_scaler.fit_transform(df_clean)
            except Exception as e:
                logger.error(f"Error in feature scaling: {str(e)}")
                return None, None
            
            # Create sequences
            X, y = [], []
            close_idx = available_columns.index('Close') if 'Close' in available_columns else 3
            
            for i in range(self.lookback_window, len(scaled_features)):
                X.append(scaled_features[i-self.lookback_window:i])
                y.append(scaled_features[i, close_idx])  # Next day's close price
            
            if len(X) == 0:
                logger.warning("No sequences created for LSTM")
                return None, None
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing LSTM data: {str(e)}")
            return None, None
    
    def prepare_rf_data(self, data: pd.DataFrame, fundamentals: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare feature data for Random Forest classification with fixed Series ambiguity"""
        try:
            # Calculate recent features (last 30 days)
            recent_data = data.tail(30)
            
            if len(recent_data) < 10:
                logger.warning("Insufficient recent data for RF preparation")
                return None, None
            
            # Technical features
            features = []
            
            # Recent ATR (average of last 5 days)
            if 'ATR' in recent_data.columns and not recent_data['ATR'].isna().all():
                recent_atr = recent_data['ATR'].tail(5).mean()
                recent_atr = recent_atr if not np.isnan(recent_atr) else 0
            else:
                recent_atr = 0
            features.append(recent_atr)
            
            # Recent momentum ratios
            if 'Momentum_2d' in recent_data.columns and not recent_data['Momentum_2d'].isna().all():
                recent_momentum_2d = recent_data['Momentum_2d'].tail(5).mean()
                recent_momentum_2d = recent_momentum_2d if not np.isnan(recent_momentum_2d) else 0
            else:
                recent_momentum_2d = 0
                
            if 'Momentum_5d' in recent_data.columns and not recent_data['Momentum_5d'].isna().all():
                recent_momentum_5d = recent_data['Momentum_5d'].tail(5).mean()
                recent_momentum_5d = recent_momentum_5d if not np.isnan(recent_momentum_5d) else 0
            else:
                recent_momentum_5d = 0
                
            features.extend([recent_momentum_2d, recent_momentum_5d])
            
            # Price vs moving averages
            if 'Price_vs_MA5' in recent_data.columns and len(recent_data['Price_vs_MA5']) > 0:
                price_vs_ma5 = recent_data['Price_vs_MA5'].iloc[-1]
                price_vs_ma5 = price_vs_ma5 if not np.isnan(price_vs_ma5) else 0
            else:
                price_vs_ma5 = 0
                
            if 'Price_vs_MA10' in recent_data.columns and len(recent_data['Price_vs_MA10']) > 0:
                price_vs_ma10 = recent_data['Price_vs_MA10'].iloc[-1]
                price_vs_ma10 = price_vs_ma10 if not np.isnan(price_vs_ma10) else 0
            else:
                price_vs_ma10 = 0
                
            features.extend([price_vs_ma5, price_vs_ma10])
            
            # Volume trend
            if 'Volume_Ratio' in recent_data.columns and not recent_data['Volume_Ratio'].isna().all():
                volume_ratio = recent_data['Volume_Ratio'].tail(5).mean()
                volume_ratio = volume_ratio if not np.isnan(volume_ratio) else 1
            else:
                volume_ratio = 1
            features.append(volume_ratio)
            
            # Volatility
            if 'Volatility' in recent_data.columns and not recent_data['Volatility'].isna().all():
                recent_volatility = recent_data['Volatility'].tail(5).mean()
                recent_volatility = recent_volatility if not np.isnan(recent_volatility) else 0
            else:
                recent_volatility = 0
            features.append(recent_volatility)
            
            # RSI
            if 'RSI' in recent_data.columns and len(recent_data['RSI']) > 0:
                recent_rsi = recent_data['RSI'].iloc[-1]
                recent_rsi = recent_rsi if not np.isnan(recent_rsi) else 50
            else:
                recent_rsi = 50
            features.append(recent_rsi)
            
            # Fundamental features
            pe_ratio = fundamentals.get('pe_ratio', 20) or 20
            revenue_growth = fundamentals.get('revenue_growth', 0) or 0
            earnings_growth = fundamentals.get('earnings_growth', 0) or 0
            promoter_buying = 1 if fundamentals.get('promoter_buying', False) else 0
            
            features.extend([pe_ratio, revenue_growth, earnings_growth, promoter_buying])
            
            # Create target variable (next day direction) - Fix Series ambiguity
            price_changes = data['Close'].pct_change().dropna()
            if len(price_changes) > 0:
                last_change = price_changes.iloc[-1]
                # Fix: Use explicit boolean conversion instead of ambiguous Series evaluation
                next_day_direction = 1 if (not np.isnan(last_change) and float(last_change) > 0) else 0
            else:
                next_day_direction = 0
            
            # Ensure all features are valid numbers
            features = [float(f) if not np.isnan(float(f)) else 0.0 for f in features]
            
            return np.array(features).reshape(1, -1), np.array([next_day_direction])
            
        except Exception as e:
            logger.error(f"Error preparing RF data: {str(e)}")
            return None, None
    
    def create_training_dataset(self, symbols: List[str], fundamentals_data: Dict) -> Dict:
        """Create training dataset for both models using 5 years of data"""
        lstm_X, lstm_y = [], []
        rf_X, rf_y = [], []
        
        logger.info(f"Creating 5-year training dataset for {len(symbols)} symbols...")
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing {symbol} for training data ({i+1}/{len(symbols)})...")
                
                # Fetch 5 years of historical data
                hist_data = self.fetch_historical_data(symbol, period="5y")
                if hist_data is None:
                    continue
                
                # Calculate technical indicators
                hist_data = self.calculate_technical_indicators(hist_data)
                
                # Prepare LSTM data
                lstm_x, lstm_y_vals = self.prepare_lstm_data(hist_data)
                if lstm_x is not None and lstm_y_vals is not None:
                    lstm_X.extend(lstm_x)
                    lstm_y.extend(lstm_y_vals)
                    logger.info(f"  ✅ LSTM: Added {len(lstm_x)} samples for {symbol}")
                
                # Prepare RF data
                fundamentals = fundamentals_data.get(symbol, {})
                rf_x, rf_y_vals = self.prepare_rf_data(hist_data, fundamentals)
                if rf_x is not None and rf_y_vals is not None:
                    rf_X.extend(rf_x)
                    rf_y.extend(rf_y_vals)
                    logger.info(f"  ✅ RF: Added {len(rf_x)} samples for {symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol} for training: {str(e)}")
                continue
        
        logger.info(f"Training dataset completed:")
        logger.info(f"  Total LSTM samples: {len(lstm_X)}")
        logger.info(f"  Total RF samples: {len(rf_X)}")
        
        return {
            'lstm': {
                'X': np.array(lstm_X) if lstm_X else None,
                'y': np.array(lstm_y) if lstm_y else None
            },
            'rf': {
                'X': np.array(rf_X) if rf_X else None,
                'y': np.array(rf_y) if rf_y else None
            }
        }
    
    def prepare_prediction_data(self, symbol: str, fundamentals: Dict) -> Dict:
        """Prepare data for real-time prediction"""
        try:
            # Fetch recent historical data (3 months for prediction)
            hist_data = self.fetch_historical_data(symbol, period="3mo")
            if hist_data is None:
                return None
            
            # Calculate technical indicators
            hist_data = self.calculate_technical_indicators(hist_data)
            
            # Prepare LSTM input
            lstm_x, _ = self.prepare_lstm_data(hist_data)
            lstm_input = lstm_x[-1:] if lstm_x is not None else None
            
            # Prepare RF input
            rf_x, _ = self.prepare_rf_data(hist_data, fundamentals)
            
            return {
                'lstm_input': lstm_input,
                'rf_input': rf_x,
                'current_price': hist_data['Close'].iloc[-1] if not hist_data.empty else 0
            }
            
        except Exception as e:
            logger.error(f"Error preparing prediction data for {symbol}: {str(e)}")
            return None
