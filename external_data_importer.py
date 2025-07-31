"""
External Historical Data Importer
Imports 1-year historical data from external sources for model training
"""
import pandas as pd
import numpy as np
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_loader import MLDataLoader
from models import MLModels
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

class ExternalDataImporter:
    def __init__(self):
        self.data_loader = MLDataLoader()
        self.models = MLModels()
        self.price_scaler = MinMaxScaler()
        self.feature_scaler = MinMaxScaler()

    def create_training_dataset_from_csv_folder(self, csv_folder: str) -> Dict:
        """Create enhanced training dataset from CSV files"""
        try:
            logger.info(f"Creating training dataset from {csv_folder}...")

            if not os.path.exists(csv_folder):
                logger.error(f"CSV folder not found: {csv_folder}")
                return None

            csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
            if not csv_files:
                logger.error(f"No CSV files found in {csv_folder}")
                return None

            logger.info(f"Processing {len(csv_files)} CSV files...")

            # Collect all data
            lstm_X, lstm_y = [], []
            rf_X, rf_y = [], []
            symbols_processed = 0

            for csv_file in csv_files:
                try:
                    symbol = csv_file.replace('.csv', '')
                    csv_path = os.path.join(csv_folder, csv_file)

                    logger.info(f"Processing {symbol}...")

                    # Load CSV data
                    df = pd.read_csv(csv_path)

                    # Standardize column names
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'])
                        df = df.sort_values('Date')

                    # Ensure we have required columns
                    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    if not all(col in df.columns for col in required_cols):
                        logger.warning(f"Missing required columns in {symbol}, skipping")
                        continue

                    # Skip if insufficient data
                    if len(df) < 100:
                        logger.warning(f"Insufficient data for {symbol} ({len(df)} rows), skipping")
                        continue

                    # Calculate technical indicators
                    df = self.calculate_enhanced_technical_indicators(df)

                    # Create dummy fundamentals
                    fundamentals = {
                        'pe_ratio': 20.0,
                        'revenue_growth': 5.0,
                        'earnings_growth': 3.0,
                        'promoter_buying': False
                    }

                    # Prepare LSTM data
                    lstm_x, lstm_y_vals = self.prepare_lstm_data(df)
                    if lstm_x is not None and lstm_y_vals is not None and len(lstm_x) > 0:
                        lstm_X.extend(lstm_x)
                        lstm_y.extend(lstm_y_vals)
                        logger.info(f"  LSTM: Added {len(lstm_x)} samples")

                    # Prepare RF data (multiple samples from different time windows)
                    rf_samples = self.prepare_rf_data_multiple(df, fundamentals)
                    if rf_samples:
                        for rf_x, rf_y_val in rf_samples:
                            if rf_x is not None and rf_y_val is not None:
                                rf_X.append(rf_x.flatten())
                                rf_y.append(rf_y_val)
                        logger.info(f"  RF: Added {len(rf_samples)} samples")

                    symbols_processed += 1

                except Exception as e:
                    logger.error(f"Error processing {csv_file}: {str(e)}")
                    continue

            # Convert to numpy arrays
            lstm_X_array = np.array(lstm_X) if lstm_X else None
            lstm_y_array = np.array(lstm_y) if lstm_y else None
            rf_X_array = np.array(rf_X) if rf_X else None
            rf_y_array = np.array(rf_y) if rf_y else None

            logger.info(f"Training dataset created:")
            logger.info(f"  Symbols processed: {symbols_processed}")
            logger.info(f"  LSTM samples: {len(lstm_X) if lstm_X else 0}")
            logger.info(f"  RF samples: {len(rf_X) if rf_X else 0}")

            return {
                'lstm': {
                    'X': lstm_X_array,
                    'y': lstm_y_array
                },
                'rf': {
                    'X': rf_X_array,
                    'y': rf_y_array
                },
                'metadata': {
                    'symbols_processed': symbols_processed,
                    'lstm_samples': len(lstm_X) if lstm_X else 0,
                    'rf_samples': len(rf_X) if rf_X else 0,
                    'data_period': '1 year'
                }
            }

        except Exception as e:
            logger.error(f"Error creating training dataset: {str(e)}")
            return None

    def calculate_enhanced_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators"""
        try:
            # Price-based indicators
            df['Price_Change'] = df['Close'].pct_change()
            df['Momentum_2d'] = df['Close'].pct_change(periods=2)
            df['Momentum_5d'] = df['Close'].pct_change(periods=5)
            df['Momentum_10d'] = df['Close'].pct_change(periods=10)

            # Moving averages
            df['MA_5'] = df['Close'].rolling(window=5).mean()
            df['MA_10'] = df['Close'].rolling(window=10).mean()
            df['MA_20'] = df['Close'].rolling(window=20).mean()

            # Price position relative to MAs
            df['Price_vs_MA5'] = (df['Close'] - df['MA_5']) / df['MA_5']
            df['Price_vs_MA10'] = (df['Close'] - df['MA_10']) / df['MA_10']
            df['Price_vs_MA20'] = (df['Close'] - df['MA_20']) / df['MA_20']

            # ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['ATR'] = true_range.rolling(window=14).mean()

            # Volume indicators
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

            # Volatility
            df['Volatility'] = df['Price_Change'].rolling(window=20).std()

            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Fill NaN values
            df = df.fillna(method='bfill').fillna(method='ffill')

            return df

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {str(e)}")
            return df

    def prepare_lstm_data(self, df: pd.DataFrame, lookback_window: int = 30) -> tuple:
        """Prepare LSTM training data"""
        try:
            # Select features
            feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 
                             'Momentum_2d', 'Momentum_5d', 'Price_vs_MA5', 'Price_vs_MA10', 'RSI']

            # Filter available columns
            available_cols = [col for col in feature_columns if col in df.columns]
            if len(available_cols) < 5:
                return None, None

            # Clean data
            df_clean = df[available_cols].dropna()
            if len(df_clean) < lookback_window + 1:
                return None, None

            # Normalize features
            scaled_features = self.feature_scaler.fit_transform(df_clean)

            # Create sequences
            X, y = [], []
            for i in range(lookback_window, len(scaled_features)):
                X.append(scaled_features[i-lookback_window:i])
                # Target: next day's close price change
                current_close = scaled_features[i-1, available_cols.index('Close')]
                next_close = scaled_features[i, available_cols.index('Close')]
                y.append(next_close - current_close)

            return np.array(X), np.array(y)

        except Exception as e:
            logger.error(f"Error preparing LSTM data: {str(e)}")
            return None, None

    def prepare_rf_data_multiple(self, df: pd.DataFrame, fundamentals: Dict) -> List[tuple]:
        """Prepare multiple RF samples from different time windows"""
        try:
            samples = []

            # Create samples from different 30-day windows
            window_size = 30
            step_size = 10

            for start_idx in range(0, len(df) - window_size - 1, step_size):
                end_idx = start_idx + window_size
                window_data = df.iloc[start_idx:end_idx]

                if len(window_data) < 20:
                    continue

                # Technical features from this window
                features = []

                # Recent price momentum
                recent_momentum = window_data['Price_Change'].tail(5).mean() if 'Price_Change' in window_data.columns else 0
                features.append(recent_momentum)

                # ATR
                recent_atr = window_data['ATR'].tail(5).mean() if 'ATR' in window_data.columns else 0
                features.append(recent_atr)

                # Price vs MA
                price_vs_ma5 = window_data['Price_vs_MA5'].iloc[-1] if 'Price_vs_MA5' in window_data.columns else 0
                price_vs_ma10 = window_data['Price_vs_MA10'].iloc[-1] if 'Price_vs_MA10' in window_data.columns else 0
                features.extend([price_vs_ma5, price_vs_ma10])

                # Volume trend
                volume_ratio = window_data['Volume_Ratio'].tail(5).mean() if 'Volume_Ratio' in window_data.columns else 1
                features.append(volume_ratio)

                # Volatility
                volatility = window_data['Volatility'].tail(5).mean() if 'Volatility' in window_data.columns else 0
                features.append(volatility)

                # RSI
                rsi = window_data['RSI'].iloc[-1] if 'RSI' in window_data.columns else 50
                features.append(rsi)

                # Fundamental features
                features.extend([
                    fundamentals.get('pe_ratio', 20),
                    fundamentals.get('revenue_growth', 0),
                    fundamentals.get('earnings_growth', 0),
                    1 if fundamentals.get('promoter_buying', False) else 0
                ])

                # Target: next day direction (after the window)
                if end_idx < len(df) - 1:
                    current_price = df.iloc[end_idx]['Close']
                    next_price = df.iloc[end_idx + 1]['Close']
                    direction = 1 if next_price > current_price else 0

                    samples.append((np.array(features).reshape(1, -1), direction))

            return samples

        except Exception as e:
            logger.error(f"Error preparing RF data: {str(e)}")
            return []

def main():
    """Test the enhanced importer"""
    csv_folder = "downloaded_historical_data"

    importer = ExternalDataImporter()
    training_data = importer.create_training_dataset_from_csv_folder(csv_folder)

    if training_data:
        print("✅ Training dataset created successfully!")
        print(f"LSTM samples: {training_data['metadata']['lstm_samples']}")
        print(f"RF samples: {training_data['metadata']['rf_samples']}")

        # Train models
        success = importer.models.train_models(training_data)
        if success:
            print("✅ Models trained successfully!")
        else:
            print("❌ Model training failed!")
    else:
        print("❌ Failed to create training dataset!")

if __name__ == "__main__":
    main()