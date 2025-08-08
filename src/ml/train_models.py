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
        self.models_dir = "models_trained"
        self.data_dir = "data/historical/downloaded_historical_data"
        self.logs_dir = "logs"
        self.kpi_file = "data/tracking/model_kpi.json"

        # Initialize data fetcher
        self.data_fetcher = HistoricalDataFetcher()

        # Ensure directories exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.kpi_file), exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        # Comprehensive symbol normalization mapping for options universe
        self.symbol_mapping = {
            "M&M": "M_M",
            "TATA STEEL": "TATASTEEL",
            "CANARA": "CANBK",
            "CENTRALBANK": "CENTRALBK", 
            "FEDERALBANK": "FEDERALBNK",
            "INDIANBANK": "INDIANB",
            "BANK OF BARODA": "BANKBARODA",
            "PUNJAB NATIONAL BANK": "PNB",
            "UNION BANK": "UNIONBANK",
            "BANK OF INDIA": "BANKINDIA",
            "CENTRAL BANK": "CENTRALBK",
            "FEDERAL BANK": "FEDERALBNK",
            "INDIAN BANK": "INDIANB",
            "KOTAK MAHINDRA BANK": "KOTAKBANK",
            "AXIS BANK": "AXISBANK",
            "HDFC BANK": "HDFCBANK",
            "ICICI BANK": "ICICIBANK",
            "INDUSIND BANK": "INDUSINDBK",
            "YES BANK": "YESBANK",
            "IDFC FIRST BANK": "IDFCFIRSTB",
            "BAJAJ FINANCE": "BAJFINANCE",
            "BAJAJ FINSERV": "BAJAJFINSV",
            "BAJAJ HOLDINGS": "BAJAJHLDNG",
            "LIC HOUSING FINANCE": "LICHSGFIN",
            "MUTHOOT FINANCE": "MUTHOOTFIN",
            "TATA CONSULTANCY": "TCS",
            "INFOSYS": "INFY",
            "WIPRO": "WIPRO",
            "HCL TECHNOLOGIES": "HCLTECH",
            "TECH MAHINDRA": "TECHM",
            "L&T INFOTECH": "LTIM",
            "LARSEN & TOUBRO": "LT",
            "RELIANCE INDUSTRIES": "RELIANCE",
            "ADANI PORTS": "ADANIPORTS",
            "TATA MOTORS": "TATAMOTORS",
            "MARUTI SUZUKI": "MARUTI",
            "HERO MOTOCORP": "HEROMOTOCO",
            "EICHER MOTORS": "EICHERMOT",
            "MAHINDRA AND MAHINDRA": "M_M",
            "HINDUSTAN UNILEVER": "HINDUNILVR",
            "ITC LIMITED": "ITC",
            "ASIAN PAINTS": "ASIANPAINT",
            "BRITANNIA": "BRITANNIA",
            "DABUR": "DABUR",
            "GODREJ CONSUMER": "GODREJCP",
            "MARICO": "MARICO",
            "NESTLE INDIA": "NESTLEIND",
            "TATA CONSUMER": "TATACONSUM",
            "HINDUSTAN ZINC": "HINDZINC",
            "VEDANTA": "VEDL",
            "JSW STEEL": "JSWSTEEL",
            "TATA STEEL": "TATASTEEL",
            "HINDALCO": "HINDALCO",
            "STEEL AUTHORITY": "SAIL",
            "NMDC": "NMDC",
            "COAL INDIA": "COALINDIA",
            "NTPC": "NTPC",
            "POWER GRID": "POWERGRID",
            "ONGC": "ONGC",
            "IOC": "IOC",
            "BPCL": "BPCL",
            "GAIL": "GAIL",
            "STATE BANK": "SBIN",
            "BHARTI AIRTEL": "BHARTIARTL",
            "VODAFONE IDEA": "IDEA",
            "INDIAN RAILWAY": "IRCTC",
            "RAILTEL": "RAILTEL",
            "CONTAINER CORP": "CONCOR",
            "IRFC": "IRFC",
            "PFC": "PFC",
            "REC": "RECLTD",
            "BHARAT ELECTRONICS": "BEL",
            "HINDUSTAN AERONAUTICS": "HAL",
            "BHEL": "BHEL",
            "BEML": "BEML",
            "NBCC": "NBCC",
            "RITES": "RITES",
            "DR REDDY": "DRREDDY",
            "SUN PHARMA": "SUNPHARMA",
            "CIPLA": "CIPLA",
            "LUPIN": "LUPIN",
            "BIOCON": "BIOCON",
            "DIVI'S LAB": "DIVISLAB",
            "APOLLO HOSPITALS": "APOLLOHOSP",
            "FORTIS": "FORTIS",
            "MAX HEALTHCARE": "MAXHEALTH",
            "TITAN": "TITAN",
            "ULTRATECH CEMENT": "ULTRACEMCO",
            "UPL": "UPL",
            "GRASIM": "GRASIM"
        }

        self.scaler = MinMaxScaler() if SKLEARN_AVAILABLE else None

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for the DataFrame"""
        try:
            df = df.copy()
            
            # Calculate ATR (Average True Range)
            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            df['ATR'] = df['TR'].rolling(window=14).mean()
            
            # Calculate RSI
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Calculate Volume Ratio
            df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
            
            # Calculate Volatility
            df['Volatility'] = df['Close'].rolling(window=20).std()
            
            # Calculate Moving Averages
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['Price_vs_MA20'] = df['Close'] / df['MA20'] - 1
            
            # Calculate Momentum
            df['Momentum_5d'] = df['Close'] / df['Close'].shift(5) - 1
            df['Momentum_20d'] = df['Close'] / df['Close'].shift(20) - 1
            
            # Clean up temporary columns
            df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
            
            # Fill NaN values
            df.ffill(inplace=True)
            df.fillna(0, inplace=True)
            
            logger.info(f"✅ Technical indicators calculated for {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return df

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
            df_clean = df[available_cols].ffill().bfill().fillna(0)

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
            model_path = os.path.join(self.models_dir, f"{symbol}_lstm.keras")
            model.save(model_path, save_format="keras")

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

            # Normalize symbol if needed
            normalized_symbol = self.symbol_mapping.get(symbol, symbol)
            effective_data_path = data_path if data_path else os.path.join(self.data_dir, f"{normalized_symbol}.csv")

            # Load data
            if os.path.exists(effective_data_path):
                df = pd.read_csv(effective_data_path)
                # Convert Date column to datetime if needed
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
            else:
                # Fetch fresh data
                df = self.data_fetcher.fetch_historical_data(symbol)

            if df is None:
                logger.error(f"No data available for {symbol}")
                return {'success': False, 'error': f'No data available for {symbol}', 'symbol': symbol}
            
            if len(df) < 500:
                logger.warning(f"Insufficient data for {symbol}. Found {len(df)} rows.")
                return {'success': False, 'error': f'Insufficient data for {symbol} - only {len(df)} rows', 'symbol': symbol}

            # Calculate technical indicators
            df = self.calculate_technical_indicators(df)

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
                lstm_results = self.train_lstm_model(X_lstm, y_lstm, normalized_symbol)
                results['lstm'] = lstm_results
                if not lstm_results.get('success'):
                    logger.error(f"LSTM training failed for {symbol}: {lstm_results.get('error')}")

            # Prepare and train RF
            X_rf, y_rf = self.prepare_rf_data(df)
            if X_rf is not None and y_rf is not None:
                rf_results = self.train_rf_model(X_rf, y_rf, normalized_symbol)
                results['rf'] = rf_results
                if not rf_results.get('success'):
                    logger.error(f"RF training failed for {symbol}: {rf_results.get('error')}")

            # Log results
            os.makedirs(self.logs_dir, exist_ok=True)
            log_path = os.path.join(self.logs_dir, f"{datetime.now().strftime('%Y-%m-%d')}_{normalized_symbol}.json")
            try:
                save_json_safe(log_path, results)
            except Exception as e:
                logger.warning(f"Could not save training log: {str(e)}")
                # Save to backup location
                backup_log_path = f"training_log_{normalized_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_log_path, 'w') as f:
                    json.dump(results, f, indent=2)

            logger.info(f"✅ Training completed for {symbol}")
            return results

        except FileNotFoundError:
            logger.error(f"Data file not found for {symbol} at {effective_data_path}")
            return {'success': False, 'error': 'Data file not found', 'symbol': symbol}
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

        # First, get list of stocks to train (from existing CSV files or predefined list)
        try:
            # Get symbols from existing CSV files
            if os.path.exists(self.data_dir):
                csv_files = [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
                symbols_to_train = [f.replace('.csv', '') for f in csv_files][:20]  # Limit to first 20
            else:
                # Default stock list if no CSV files exist
                symbols_to_train = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'HINDUNILVR', 'KOTAKBANK']
            
            logger.info(f"Training models for {len(symbols_to_train)} stocks.")
        except Exception as e:
            logger.error(f"Failed to get stock symbols: {str(e)}")
            results['summary']['failed'] = 20  # Assume default count failed
            return results
        results['summary']['total'] = len(symbols_to_train)

        for symbol in symbols_to_train:
            try:
                # Construct the expected data path using the normalized symbol
                normalized_symbol = self.symbol_mapping.get(symbol, symbol)
                data_path = os.path.join(self.data_dir, f"{normalized_symbol}.csv")

                stock_results = self.train_single_stock(symbol, data_path)
                results['stocks'][symbol] = stock_results

                # Update summary based on actual training success
                if stock_results.get('lstm', {}).get('success') or stock_results.get('rf', {}).get('success'):
                    results['summary']['successful'] += 1
                else:
                    results['summary']['failed'] += 1

            except Exception as e:
                logger.error(f"Critical error in training pipeline for {symbol}: {str(e)}")
                results['summary']['failed'] += 1
                results['stocks'][symbol] = {'success': False, 'error': str(e), 'symbol': symbol}


        results['training_end'] = datetime.now().isoformat()

        # Update model KPI registry
        self.update_model_kpi(results)

        logger.info(f"🎉 Training completed: {results['summary']['successful']} successful, {results['summary']['failed']} failed out of {results['summary']['total']} processed.")
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
                normalized_symbol = self.symbol_mapping.get(symbol, symbol)
                if normalized_symbol not in kpi_data:
                    kpi_data[normalized_symbol] = {}

                kpi_data[normalized_symbol]['last_trained'] = stock_result.get('training_date')
                kpi_data[normalized_symbol]['data_rows'] = stock_result.get('data_rows', 0)

                if stock_result.get('lstm', {}).get('success'):
                    kpi_data[normalized_symbol]['lstm_val_loss'] = stock_result['lstm'].get('val_loss', 0)
                else:
                    kpi_data[normalized_symbol]['lstm_val_loss'] = None # Explicitly set to None if not successful

                if stock_result.get('rf', {}).get('success'):
                    kpi_data[normalized_symbol]['rf_accuracy'] = stock_result['rf'].get('accuracy', 0)
                else:
                    kpi_data[normalized_symbol]['rf_accuracy'] = None # Explicitly set to None if not successful

            save_json_safe(self.kpi_file, kpi_data)
            logger.info("✅ Model KPI registry updated")

        except Exception as e:
            logger.error(f"Error updating model KPI: {str(e)}")

def main():
    """Main training function"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    trainer = ModelTrainer()

    # Train all models
    results = trainer.train_all_models()

    print(f"\n🎯 Training Summary:")
    print(f"   Total Stocks Processed: {results['summary']['total']}")
    print(f"   Successfully Trained: {results['summary']['successful']}")
    print(f"   Failed Training: {results['summary']['failed']}")
    print(f"   Training Start: {results['training_start']}")
    print(f"   Training End: {results['training_end']}")

    return results

if __name__ == "__main__":
    main()