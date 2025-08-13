
#!/usr/bin/env python3
"""
Real-Time ML Model Trainer
Trains models using real-time data feeds and updates predictions continuously
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
import joblib
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class RealTimeMLTrainer:
    """Real-time ML model trainer with live data integration"""
    
    def __init__(self):
        self.models_dir = "models_trained"
        self.scalers_dir = os.path.join(self.models_dir, "scalers")
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.scalers_dir, exist_ok=True)
        
        # Training parameters
        self.lookback_days = 60
        self.prediction_days = 5
        self.lstm_epochs = 50
        self.rf_estimators = 100
        
        # Real-time data cache
        self.data_cache = {}
        self.model_cache = {}
        self.last_training = {}
        
    def fetch_realtime_training_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        """Fetch real-time training data for a symbol"""
        try:
            # Try to get fresh data from Yahoo Finance
            ticker = yf.Ticker(f"{symbol}.NS")
            
            # Get historical data
            hist_data = ticker.history(period=period)
            
            if hist_data.empty:
                logger.warning(f"No historical data for {symbol}")
                return pd.DataFrame()
            
            # Get real-time intraday data
            try:
                intraday = ticker.history(period="1d", interval="1m")
                if not intraday.empty:
                    # Merge with historical data
                    latest_date = hist_data.index[-1].date()
                    today = datetime.now().date()
                    
                    if today > latest_date:
                        # Add today's data
                        today_data = intraday.resample('1D').agg({
                            'Open': 'first',
                            'High': 'max',
                            'Low': 'min',
                            'Close': 'last',
                            'Volume': 'sum'
                        }).dropna()
                        
                        if not today_data.empty:
                            hist_data = pd.concat([hist_data, today_data])
            except Exception as e:
                logger.warning(f"Could not fetch intraday data for {symbol}: {str(e)}")
            
            # Calculate technical indicators
            hist_data = self._add_technical_indicators(hist_data)
            
            # Cache the data
            self.data_cache[symbol] = {
                'data': hist_data,
                'timestamp': datetime.now()
            }
            
            logger.info(f"Fetched {len(hist_data)} days of data for {symbol}")
            return hist_data
            
        except Exception as e:
            logger.error(f"Error fetching training data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to the dataframe"""
        try:
            # Moving averages
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Exponential moving averages
            df['EMA_12'] = df['Close'].ewm(span=12).mean()
            df['EMA_26'] = df['Close'].ewm(span=26).mean()
            
            # MACD
            df['MACD'] = df['EMA_12'] - df['EMA_26']
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['BB_Middle'] = df['Close'].rolling(window=20).mean()
            bb_std = df['Close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
            df['BB_Position'] = (df['Close'] - df['BB_Lower']) / df['BB_Width']
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
            
            # Price change indicators
            df['Price_Change'] = df['Close'].pct_change()
            df['High_Low_Ratio'] = (df['High'] - df['Low']) / df['Close']
            df['Open_Close_Ratio'] = (df['Close'] - df['Open']) / df['Open']
            
            return df.fillna(method='bfill').fillna(method='ffill')
            
        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            return df
    
    def prepare_lstm_data(self, data: pd.DataFrame, symbol: str) -> Tuple[np.ndarray, np.ndarray, MinMaxScaler]:
        """Prepare data for LSTM training"""
        try:
            # Select features for LSTM
            feature_columns = [
                'Close', 'Volume', 'SMA_5', 'SMA_10', 'SMA_20', 
                'RSI', 'MACD', 'BB_Position', 'Volume_Ratio', 'Price_Change'
            ]
            
            # Filter available columns
            available_columns = [col for col in feature_columns if col in data.columns]
            
            if not available_columns:
                logger.error(f"No valid features found for {symbol}")
                return None, None, None
            
            # Prepare data
            dataset = data[available_columns].values
            
            # Scale the data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(dataset)
            
            # Create sequences
            X, y = [], []
            for i in range(self.lookback_days, len(scaled_data) - self.prediction_days + 1):
                X.append(scaled_data[i-self.lookback_days:i])
                y.append(scaled_data[i:i+self.prediction_days, 0])  # Predict Close price
            
            X, y = np.array(X), np.array(y)
            
            # Save scaler
            scaler_path = os.path.join(self.scalers_dir, f"{symbol}_scaler.pkl")
            joblib.dump(scaler, scaler_path)
            
            logger.info(f"Prepared LSTM data: {X.shape}, {y.shape}")
            return X, y, scaler
            
        except Exception as e:
            logger.error(f"Error preparing LSTM data for {symbol}: {str(e)}")
            return None, None, None
    
    def train_lstm_model(self, symbol: str, X: np.ndarray, y: np.ndarray) -> Optional[tf.keras.Model]:
        """Train LSTM model for price prediction"""
        try:
            if X is None or y is None:
                return None
            
            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
                Dropout(0.2),
                LSTM(50, return_sequences=True),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(self.prediction_days)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=self.lstm_epochs,
                batch_size=32,
                validation_split=0.2,
                verbose=0
            )
            
            # Test model
            predictions = model.predict(X_test)
            mse = mean_squared_error(y_test.flatten(), predictions.flatten())
            
            # Save model
            model_path = os.path.join(self.models_dir, f"{symbol}_lstm.keras")
            model.save(model_path)
            
            # Cache model
            self.model_cache[f"{symbol}_lstm"] = model
            
            logger.info(f"LSTM model trained for {symbol}, MSE: {mse:.6f}")
            return model
            
        except Exception as e:
            logger.error(f"Error training LSTM model for {symbol}: {str(e)}")
            return None
    
    def prepare_rf_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for Random Forest training"""
        try:
            # Select features
            feature_columns = [
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'RSI',
                'BB_Position', 'BB_Width', 'Volume_Ratio',
                'High_Low_Ratio', 'Open_Close_Ratio'
            ]
            
            available_columns = [col for col in feature_columns if col in data.columns]
            
            if not available_columns:
                logger.error("No valid features found for Random Forest")
                return None, None
            
            # Prepare features and targets
            X = data[available_columns].fillna(method='bfill').fillna(method='ffill').values[:-self.prediction_days]
            
            # Target: direction of price movement (up/down)
            future_prices = data['Close'].shift(-self.prediction_days)
            current_prices = data['Close']
            y = (future_prices > current_prices).astype(int).values[:-self.prediction_days]
            
            # Remove NaN values
            valid_indices = ~np.isnan(y) & ~np.any(np.isnan(X), axis=1)
            X = X[valid_indices]
            y = y[valid_indices]
            
            logger.info(f"Prepared RF data: {X.shape}, {len(y)}")
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing RF data: {str(e)}")
            return None, None
    
    def train_rf_model(self, symbol: str, X: np.ndarray, y: np.ndarray) -> Optional[RandomForestClassifier]:
        """Train Random Forest model for direction prediction"""
        try:
            if X is None or y is None:
                return None
            
            # Split data
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            # Train Random Forest
            model = RandomForestClassifier(
                n_estimators=self.rf_estimators,
                random_state=42,
                n_jobs=-1
            )
            
            model.fit(X_train, y_train)
            
            # Test model
            predictions = model.predict(X_test)
            accuracy = accuracy_score(y_test, predictions)
            
            # Save model
            model_path = os.path.join(self.models_dir, f"{symbol}_rf.pkl")
            joblib.dump(model, model_path)
            
            # Cache model
            self.model_cache[f"{symbol}_rf"] = model
            
            logger.info(f"RF model trained for {symbol}, Accuracy: {accuracy:.4f}")
            return model
            
        except Exception as e:
            logger.error(f"Error training RF model for {symbol}: {str(e)}")
            return None
    
    def train_symbol(self, symbol: str) -> Dict[str, Any]:
        """Train both LSTM and RF models for a symbol using real-time data"""
        try:
            logger.info(f"Starting real-time training for {symbol}")
            
            # Fetch real-time data
            data = self.fetch_realtime_training_data(symbol)
            
            if data.empty:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'No data available',
                    'timestamp': datetime.now().isoformat()
                }
            
            results = {
                'symbol': symbol,
                'data_points': len(data),
                'date_range': f"{data.index[0].strftime('%Y-%m-%d')} to {data.index[-1].strftime('%Y-%m-%d')}",
                'timestamp': datetime.now().isoformat()
            }
            
            # Train LSTM model
            X_lstm, y_lstm, scaler = self.prepare_lstm_data(data, symbol)
            lstm_model = self.train_lstm_model(symbol, X_lstm, y_lstm)
            
            results['lstm_trained'] = lstm_model is not None
            
            # Train Random Forest model
            X_rf, y_rf = self.prepare_rf_data(data)
            rf_model = self.train_rf_model(symbol, X_rf, y_rf)
            
            results['rf_trained'] = rf_model is not None
            results['success'] = lstm_model is not None and rf_model is not None
            
            # Update last training time
            self.last_training[symbol] = datetime.now()
            
            logger.info(f"Training completed for {symbol}: LSTM={results['lstm_trained']}, RF={results['rf_trained']}")
            return results
            
        except Exception as e:
            logger.error(f"Error training {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def train_multiple_symbols(self, symbols: List[str]) -> Dict[str, Any]:
        """Train models for multiple symbols"""
        results = {
            'training_started': datetime.now().isoformat(),
            'symbols': symbols,
            'results': {}
        }
        
        for symbol in symbols:
            try:
                result = self.train_symbol(symbol)
                results['results'][symbol] = result
                
                # Small delay between trainings
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in batch training for {symbol}: {str(e)}")
                results['results'][symbol] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Summary
        successful = sum(1 for r in results['results'].values() if r.get('success'))
        results['summary'] = {
            'total_symbols': len(symbols),
            'successful_trainings': successful,
            'success_rate': successful / len(symbols) if symbols else 0,
            'training_completed': datetime.now().isoformat()
        }
        
        return results
    
    def get_realtime_predictions(self, symbol: str) -> Dict[str, Any]:
        """Get real-time predictions for a symbol"""
        try:
            # Load models if not cached
            if f"{symbol}_lstm" not in self.model_cache:
                lstm_path = os.path.join(self.models_dir, f"{symbol}_lstm.keras")
                if os.path.exists(lstm_path):
                    self.model_cache[f"{symbol}_lstm"] = tf.keras.models.load_model(lstm_path)
            
            if f"{symbol}_rf" not in self.model_cache:
                rf_path = os.path.join(self.models_dir, f"{symbol}_rf.pkl")
                if os.path.exists(rf_path):
                    self.model_cache[f"{symbol}_rf"] = joblib.load(rf_path)
            
            # Get fresh data
            data = self.fetch_realtime_training_data(symbol, period="1y")
            
            if data.empty:
                return {'error': 'No data available for predictions'}
            
            predictions = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'data_freshness': 'real-time',
                'last_price': float(data['Close'].iloc[-1])
            }
            
            # LSTM predictions
            if f"{symbol}_lstm" in self.model_cache:
                lstm_predictions = self._get_lstm_predictions(symbol, data)
                predictions.update(lstm_predictions)
            
            # RF predictions
            if f"{symbol}_rf" in self.model_cache:
                rf_predictions = self._get_rf_predictions(symbol, data)
                predictions.update(rf_predictions)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting predictions for {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def _get_lstm_predictions(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Get LSTM model predictions"""
        try:
            model = self.model_cache[f"{symbol}_lstm"]
            scaler_path = os.path.join(self.scalers_dir, f"{symbol}_scaler.pkl")
            
            if not os.path.exists(scaler_path):
                return {}
            
            scaler = joblib.load(scaler_path)
            
            # Prepare recent data
            feature_columns = [
                'Close', 'Volume', 'SMA_5', 'SMA_10', 'SMA_20', 
                'RSI', 'MACD', 'BB_Position', 'Volume_Ratio', 'Price_Change'
            ]
            
            available_columns = [col for col in feature_columns if col in data.columns]
            recent_data = data[available_columns].tail(self.lookback_days).values
            
            scaled_data = scaler.transform(recent_data)
            X = scaled_data.reshape(1, self.lookback_days, len(available_columns))
            
            # Make prediction
            lstm_pred = model.predict(X)[0]
            
            # Inverse transform predictions
            dummy_array = np.zeros((len(lstm_pred), len(available_columns)))
            dummy_array[:, 0] = lstm_pred
            inverse_pred = scaler.inverse_transform(dummy_array)[:, 0]
            
            current_price = data['Close'].iloc[-1]
            
            return {
                'lstm_predictions': inverse_pred.tolist(),
                'lstm_direction': 'UP' if inverse_pred[-1] > current_price else 'DOWN',
                'lstm_confidence': min(abs((inverse_pred[-1] - current_price) / current_price) * 100, 100)
            }
            
        except Exception as e:
            logger.error(f"LSTM prediction error for {symbol}: {str(e)}")
            return {}
    
    def _get_rf_predictions(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Get Random Forest predictions"""
        try:
            model = self.model_cache[f"{symbol}_rf"]
            
            # Prepare recent data
            feature_columns = [
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50',
                'EMA_12', 'EMA_26', 'MACD', 'RSI',
                'BB_Position', 'BB_Width', 'Volume_Ratio',
                'High_Low_Ratio', 'Open_Close_Ratio'
            ]
            
            available_columns = [col for col in feature_columns if col in data.columns]
            recent_features = data[available_columns].tail(1).fillna(method='bfill').values
            
            # Make prediction
            rf_pred = model.predict(recent_features)[0]
            rf_proba = model.predict_proba(recent_features)[0]
            
            return {
                'rf_direction': 'UP' if rf_pred == 1 else 'DOWN',
                'rf_confidence': max(rf_proba) * 100,
                'rf_probability_up': rf_proba[1] * 100 if len(rf_proba) > 1 else 50.0
            }
            
        except Exception as e:
            logger.error(f"RF prediction error for {symbol}: {str(e)}")
            return {}

# Global trainer instance
realtime_trainer = RealTimeMLTrainer()

def train_realtime_models(symbols: List[str] = None) -> Dict[str, Any]:
    """Train models with real-time data"""
    if symbols is None:
        # Default symbols
        symbols = [
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK',
            'HINDUNILVR', 'ITC', 'KOTAKBANK', 'LT', 'AXISBANK',
            'BAJFINANCE', 'BHARTIARTL', 'ASIANPAINT', 'MARUTI', 'SBIN'
        ]
    
    return realtime_trainer.train_multiple_symbols(symbols)

def get_realtime_model_predictions(symbol: str) -> Dict[str, Any]:
    """Get predictions using real-time trained models"""
    return realtime_trainer.get_realtime_predictions(symbol)
