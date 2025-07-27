
"""
Stock Market Analyst - ML Data Loader Module

Handles data preparation for machine learning models:
1. Historical OHLC data fetching
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
        
    def fetch_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """Fetch historical OHLC data from Yahoo Finance"""
        try:
            ticker = f"{symbol}.NS"
            data = yf.download(ticker, period=period, progress=False)
            
            if data is None or data.empty:
                logger.warning(f"No historical data found for {symbol}")
                return None
                
            # Reset index to have Date as column
            data.reset_index(inplace=True)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for ML features"""
        try:
            df = data.copy()
            
            # Calculate ATR (14-day)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['ATR'] = true_range.rolling(window=14).mean()
            
            # Calculate momentum ratios
            df['Price_Change'] = df['Close'].pct_change()
            df['Momentum_2d'] = df['Close'].pct_change(periods=2)
            df['Momentum_5d'] = df['Close'].pct_change(periods=5)
            df['Momentum_10d'] = df['Close'].pct_change(periods=10)
            
            # Volume indicators
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
            
            # Moving averages
            df['MA_5'] = df['Close'].rolling(window=5).mean()
            df['MA_10'] = df['Close'].rolling(window=10).mean()
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            
            # Price position relative to moving averages
            df['Price_vs_MA5'] = (df['Close'] - df['MA_5']) / df['MA_5']
            df['Price_vs_MA10'] = (df['Close'] - df['MA_10']) / df['MA_10']
            df['Price_vs_MA20'] = (df['Close'] - df['MA_20']) / df['MA_20']
            
            # Volatility
            df['Volatility'] = df['Price_Change'].rolling(window=20).std()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return data
    
    def prepare_lstm_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare windowed time-series data for LSTM"""
        try:
            # Select features for LSTM
            feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 
                             'Momentum_2d', 'Momentum_5d', 'Price_vs_MA5', 'Price_vs_MA10', 'RSI']
            
            # Filter and clean data
            df_clean = data[feature_columns].dropna()
            
            if len(df_clean) < self.lookback_window + 1:
                logger.warning("Insufficient data for LSTM preparation")
                return None, None
            
            # Normalize features
            scaled_features = self.feature_scaler.fit_transform(df_clean)
            
            # Create sequences
            X, y = [], []
            for i in range(self.lookback_window, len(scaled_features)):
                X.append(scaled_features[i-self.lookback_window:i])
                y.append(scaled_features[i, 3])  # Next day's close price (index 3)
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing LSTM data: {str(e)}")
            return None, None
    
    def prepare_rf_data(self, data: pd.DataFrame, fundamentals: Dict) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare feature data for Random Forest classification"""
        try:
            # Calculate recent features (last 30 days)
            recent_data = data.tail(30)
            
            if len(recent_data) < 10:
                logger.warning("Insufficient recent data for RF preparation")
                return None, None
            
            # Technical features
            features = []
            
            # Recent ATR (average of last 5 days)
            recent_atr = recent_data['ATR'].tail(5).mean() if 'ATR' in recent_data.columns else 0
            features.append(recent_atr)
            
            # Recent momentum ratios
            recent_momentum_2d = recent_data['Momentum_2d'].tail(5).mean() if 'Momentum_2d' in recent_data.columns else 0
            recent_momentum_5d = recent_data['Momentum_5d'].tail(5).mean() if 'Momentum_5d' in recent_data.columns else 0
            features.extend([recent_momentum_2d, recent_momentum_5d])
            
            # Price vs moving averages
            price_vs_ma5 = recent_data['Price_vs_MA5'].iloc[-1] if 'Price_vs_MA5' in recent_data.columns else 0
            price_vs_ma10 = recent_data['Price_vs_MA10'].iloc[-1] if 'Price_vs_MA10' in recent_data.columns else 0
            features.extend([price_vs_ma5, price_vs_ma10])
            
            # Volume trend
            volume_ratio = recent_data['Volume_Ratio'].tail(5).mean() if 'Volume_Ratio' in recent_data.columns else 1
            features.append(volume_ratio)
            
            # Volatility
            recent_volatility = recent_data['Volatility'].tail(5).mean() if 'Volatility' in recent_data.columns else 0
            features.append(recent_volatility)
            
            # RSI
            recent_rsi = recent_data['RSI'].iloc[-1] if 'RSI' in recent_data.columns else 50
            features.append(recent_rsi)
            
            # Fundamental features
            pe_ratio = fundamentals.get('pe_ratio', 20) or 20
            revenue_growth = fundamentals.get('revenue_growth', 0)
            earnings_growth = fundamentals.get('earnings_growth', 0)
            promoter_buying = 1 if fundamentals.get('promoter_buying', False) else 0
            
            features.extend([pe_ratio, revenue_growth, earnings_growth, promoter_buying])
            
            # Create target variable (next day direction)
            price_changes = data['Close'].pct_change().dropna()
            if len(price_changes) > 0:
                next_day_direction = 1 if price_changes.iloc[-1] > 0 else 0
            else:
                next_day_direction = 0
            
            return np.array(features).reshape(1, -1), np.array([next_day_direction])
            
        except Exception as e:
            logger.error(f"Error preparing RF data: {str(e)}")
            return None, None
    
    def create_training_dataset(self, symbols: List[str], fundamentals_data: Dict) -> Dict:
        """Create training dataset for both models"""
        lstm_X, lstm_y = [], []
        rf_X, rf_y = [], []
        
        logger.info(f"Creating training dataset for {len(symbols)} symbols...")
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing {symbol} for training data ({i+1}/{len(symbols)})")
                
                # Fetch historical data
                hist_data = self.fetch_historical_data(symbol)
                if hist_data is None:
                    continue
                
                # Calculate technical indicators
                hist_data = self.calculate_technical_indicators(hist_data)
                
                # Prepare LSTM data
                lstm_x, lstm_y_vals = self.prepare_lstm_data(hist_data)
                if lstm_x is not None and lstm_y_vals is not None:
                    lstm_X.extend(lstm_x)
                    lstm_y.extend(lstm_y_vals)
                
                # Prepare RF data
                fundamentals = fundamentals_data.get(symbol, {})
                rf_x, rf_y_vals = self.prepare_rf_data(hist_data, fundamentals)
                if rf_x is not None and rf_y_vals is not None:
                    rf_X.extend(rf_x)
                    rf_y.extend(rf_y_vals)
                
            except Exception as e:
                logger.error(f"Error processing {symbol} for training: {str(e)}")
                continue
        
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
            # Fetch recent historical data
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
