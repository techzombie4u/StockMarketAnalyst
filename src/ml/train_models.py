
import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import joblib

# ML imports with fallbacks
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.preprocessing import MinMaxScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from src.utils.file_utils import load_json_safe, save_json_safe
from src.data.fetch_historical_data import HistoricalDataFetcher

logger = logging.getLogger(__name__)

class ModelTrainer:
    """Enhanced model training pipeline with 5-year data support"""
    
    def __init__(self):
        self.data_fetcher = HistoricalDataFetcher()
        self.models_dir = "models_trained"
        self.logs_dir = "logs/retrain"
        self.kpi_file = "data/tracking/model_kpi.json"
        
        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.kpi_file), exist_ok=True)
        
        self.scaler = MinMaxScaler() if SKLEARN_AVAILABLE else None

    def prepare_lstm_data(self, df: pd.DataFrame, lookback_window: int = 60) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare time-series data for LSTM training"""
        try:
            if not TF_AVAILABLE:
                logger.warning("TensorFlow not available, skipping LSTM data preparation")
                return None, None
            
            # Select features
            feature_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 'RSI', 'Volume_Ratio']
            available_cols = [col for col in feature_cols if col in df.columns]
            
            if len(available_cols) < 5:
                logger.warning(f"Insufficient columns for LSTM: {available_cols}")
                return None, None
            
            # Clean data
            df_clean = df[available_cols].fillna(method='ffill').fillna(method='bfill').fillna(0)
            
            if len(df_clean) < lookback_window + 1:
                logger.warning(f"Insufficient data: {len(df_clean)} < {lookback_window + 1}")
                return None, None
            
            # Scale features
            scaled_features = self.scaler.fit_transform(df_clean)
            
            # Create sequences
            X, y = [], []
            for i in range(lookback_window, len(scaled_features)):
                X.append(scaled_features[i-lookback_window:i])
                # Predict next day's close price (normalized)
                close_idx = available_cols.index('Close') if 'Close' in available_cols else 3
                y.append(scaled_features[i, close_idx])
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"Error preparing LSTM data: {str(e)}")
            return None, None

    def prepare_rf_data(self, df: pd.DataFrame) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Prepare feature data for Random Forest classification"""
        try:
            if not SKLEARN_AVAILABLE:
                logger.warning("Scikit-learn not available, skipping RF data preparation")
                return None, None
            
            # Calculate features for each day
            features = []
            targets = []
            
            window_size = 30
            for i in range(window_size, len(df) - 1):
                window_data = df.iloc[i-window_size:i]
                
                # Extract features
                feature_vector = [
                    window_data['ATR'].tail(5).mean() if 'ATR' in window_data.columns else 0,
                    window_data['RSI'].iloc[-1] if 'RSI' in window_data.columns else 50,
                    window_data['Volume_Ratio'].tail(5).mean() if 'Volume_Ratio' in window_data.columns else 1,
                    window_data['Volatility'].tail(5).mean() if 'Volatility' in window_data.columns else 0,
                    window_data['Price_vs_MA20'].iloc[-1] if 'Price_vs_MA20' in window_data.columns else 0,
                    window_data['Momentum_5d'].tail(5).mean() if 'Momentum_5d' in window_data.columns else 0,
                    window_data['Momentum_20d'].tail(5).mean() if 'Momentum_20d' in window_data.columns else 0,
                ]
                
                # Target: next day direction (1 = up, 0 = down)
                current_price = df.iloc[i]['Close']
                next_price = df.iloc[i + 1]['Close']
                direction = 1 if next_price > current_price else 0
                
                features.append(feature_vector)
                targets.append(direction)
            
            return np.array(features), np.array(targets)
            
        except Exception as e:
            logger.error(f"Error preparing RF data: {str(e)}")
            return None, None

    def train_lstm_model(self, X: np.ndarray, y: np.ndarray, symbol: str) -> Dict:
        """Train LSTM model for price prediction"""
        try:
            if not TF_AVAILABLE:
                return {'success': False, 'error': 'TensorFlow not available'}
            
            logger.info(f"Training LSTM model for {symbol}")
            
            # Split data
            split_idx = int(len(X) * 0.8)
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Create model
            model = Sequential([
                LSTM(50, return_sequences=True, input_shape=(X.shape[1], X.shape[2])),
                Dropout(0.2),
                LSTM(50, return_sequences=False),
                Dropout(0.2),
                Dense(25),
                Dense(1)
            ])
            
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
            
            # Train model
            history = model.fit(
                X_train, y_train,
                epochs=20,
                batch_size=32,
                validation_data=(X_val, y_val),
                verbose=0
            )
            
            # Evaluate
            train_loss = history.history['loss'][-1]
            val_loss = history.history['val_loss'][-1]
            
            # Save model
            model_path = os.path.join(self.models_dir, f"{symbol}_lstm.h5")
            model.save(model_path)
            
            return {
                'success': True,
                'model_path': model_path,
                'train_loss': float(train_loss),
                'val_loss': float(val_loss),
                'epochs': 20,
                'samples': len(X_train)
            }
            
        except Exception as e:
            logger.error(f"Error training LSTM for {symbol}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def train_rf_model(self, X: np.ndarray, y: np.ndarray, symbol: str) -> Dict:
        """Train Random Forest model for direction prediction"""
        try:
            if not SKLEARN_AVAILABLE:
                return {'success': False, 'error': 'Scikit-learn not available'}
            
            logger.info(f"Training Random Forest model for {symbol}")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
            model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            model_path = os.path.join(self.models_dir, f"{symbol}_rf.pkl")
            joblib.dump(model, model_path)
            
            return {
                'success': True,
                'model_path': model_path,
                'accuracy': float(accuracy),
                'samples_train': len(X_train),
                'samples_test': len(X_test)
            }
            
        except Exception as e:
            logger.error(f"Error training RF for {symbol}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def train_single_stock(self, symbol: str, data_path: Optional[str] = None) -> Dict:
        """Train models for a single stock"""
        try:
            logger.info(f"🎯 Training models for {symbol}")
            
            # Load data
            if data_path and os.path.exists(data_path):
                df = pd.read_csv(data_path)
            else:
                # Fetch fresh data
                df = self.data_fetcher.get_stock_history(symbol, period="5y")
                
            if df is None or len(df) < 500:
                return {'success': False, 'error': f'Insufficient data for {symbol}'}
            
            results = {
                'symbol': symbol,
                'training_date': datetime.now().isoformat(),
                'data_rows': len(df),
                'lstm': {'success': False},
                'rf': {'success': False}
            }
            
            # Prepare and train LSTM
            X_lstm, y_lstm = self.prepare_lstm_data(df)
            if X_lstm is not None and y_lstm is not None:
                results['lstm'] = self.train_lstm_model(X_lstm, y_lstm, symbol)
            
            # Prepare and train RF
            X_rf, y_rf = self.prepare_rf_data(df)
            if X_rf is not None and y_rf is not None:
                results['rf'] = self.train_rf_model(X_rf, y_rf, symbol)
            
            # Log results
            log_path = os.path.join(self.logs_dir, f"{datetime.now().strftime('%Y-%m-%d')}_{symbol}.json")
            save_json_safe(log_path, results)
            
            logger.info(f"✅ Training completed for {symbol}")
            return results
            
        except Exception as e:
            logger.error(f"Error training {symbol}: {str(e)}")
            return {'success': False, 'error': str(e), 'symbol': symbol}

    def train_all_models(self) -> Dict:
        """Train models for all tracked stocks"""
        logger.info("🚀 Starting comprehensive model training")
        
        results = {
            'training_start': datetime.now().isoformat(),
            'stocks': {},
            'summary': {'total': 0, 'successful': 0, 'failed': 0}
        }
        
        # First, fetch all data
        data_results = self.data_fetcher.fetch_all_tracked_stocks()
        
        # Train models for each successful data fetch
        for symbol in data_results['successful'][:20]:  # Limit to first 20 for efficiency
            try:
                data_path = f"data/historical/downloaded_historical_data/{symbol}.csv"
                stock_results = self.train_single_stock(symbol, data_path)
                results['stocks'][symbol] = stock_results
                
                if stock_results.get('lstm', {}).get('success') or stock_results.get('rf', {}).get('success'):
                    results['summary']['successful'] += 1
                else:
                    results['summary']['failed'] += 1
                    
                results['summary']['total'] += 1
                
            except Exception as e:
                logger.error(f"Error in training pipeline for {symbol}: {str(e)}")
                results['summary']['failed'] += 1
        
        results['training_end'] = datetime.now().isoformat()
        
        # Update model KPI registry
        self.update_model_kpi(results)
        
        logger.info(f"🎉 Training completed: {results['summary']['successful']} successful, {results['summary']['failed']} failed")
        return results

    def update_model_kpi(self, training_results: Dict):
        """Update model KPI registry"""
        try:
            kpi_data = load_json_safe(self.kpi_file, {})
            
            kpi_data['last_training'] = {
                'date': datetime.now().isoformat(),
                'total_stocks': training_results['summary']['total'],
                'successful': training_results['summary']['successful'],
                'failed': training_results['summary']['failed']
            }
            
            # Update individual stock KPIs
            for symbol, stock_result in training_results['stocks'].items():
                if symbol not in kpi_data:
                    kpi_data[symbol] = {}
                
                kpi_data[symbol]['last_trained'] = stock_result.get('training_date')
                kpi_data[symbol]['data_rows'] = stock_result.get('data_rows', 0)
                
                if stock_result.get('lstm', {}).get('success'):
                    kpi_data[symbol]['lstm_val_loss'] = stock_result['lstm'].get('val_loss', 0)
                
                if stock_result.get('rf', {}).get('success'):
                    kpi_data[symbol]['rf_accuracy'] = stock_result['rf'].get('accuracy', 0)
            
            save_json_safe(self.kpi_file, kpi_data)
            logger.info("✅ Model KPI registry updated")
            
        except Exception as e:
            logger.error(f"Error updating model KPI: {str(e)}")

def main():
    """Main training function"""
    logging.basicConfig(level=logging.INFO)
    
    trainer = ModelTrainer()
    
    # Train all models
    results = trainer.train_all_models()
    
    print(f"🎯 Training Summary:")
    print(f"   Total: {results['summary']['total']}")
    print(f"   Successful: {results['summary']['successful']}")
    print(f"   Failed: {results['summary']['failed']}")
    
    return results

if __name__ == "__main__":
    main()
