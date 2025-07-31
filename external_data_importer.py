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

logger = logging.getLogger(__name__)

class ExternalDataImporter:
    def __init__(self):
        self.data_loader = MLDataLoader()
        self.models = MLModels()

    def import_historical_csv(self, csv_file_path: str, symbol: str) -> Optional[pd.DataFrame]:
        """
        Import historical data from CSV file
        Expected columns: Date, Open, High, Low, Close, Volume
        """
        try:
            # Check if file exists
            if not os.path.exists(csv_file_path):
                logger.warning(f"CSV file not found: {csv_file_path}")
                return None

            logger.info(f"Reading CSV file: {csv_file_path}")

            # First, check if we need to skip header rows
            with open(csv_file_path, 'r') as f:
                first_few_lines = [f.readline().strip() for _ in range(5)]

            skip_rows = 0
            for i, line in enumerate(first_few_lines):
                if line.startswith('Date,') or (line and line.split(',')[0].replace('-', '').replace('/', '').isdigit()):
                    skip_rows = i
                    break

            if skip_rows > 0:
                logger.info(f"Skipping {skip_rows} header rows in {csv_file_path}")
                df = pd.read_csv(csv_file_path, skiprows=skip_rows)
            else:
                df = pd.read_csv(csv_file_path)

            # Log available columns for debugging
            logger.info(f"Available columns in {symbol} CSV: {list(df.columns)}")

            # Standardize column names (handle various formats)
            column_mapping = {
                'date': 'Date', 'Date': 'Date', 'DATE': 'Date',
                'Price': 'Date', 'price': 'Date', 'PRICE': 'Date',  # Handle Price as Date column
                'open': 'Open', 'Open': 'Open', 'OPEN': 'Open',
                'high': 'High', 'High': 'High', 'HIGH': 'High',
                'low': 'Low', 'Low': 'Low', 'LOW': 'Low',
                'close': 'Close', 'Close': 'Close', 'CLOSE': 'Close',
                'volume': 'Volume', 'Volume': 'Volume', 'VOLUME': 'Volume',
                'adj close': 'Adj Close', 'Adj Close': 'Adj Close',
                'Adj Close': 'Adj Close', 'ADJ CLOSE': 'Adj Close',
                # Handle additional common variations
                'Close Price': 'Close', 'close_price': 'Close',
                'Open Price': 'Open', 'open_price': 'Open',
                'High Price': 'High', 'high_price': 'High',
                'Low Price': 'Low', 'low_price': 'Low'
            }

            df = df.rename(columns=column_mapping)

            # Check if we have a valid Date column after mapping
            if 'Date' not in df.columns:
                # Try to find any date-like column
                date_candidates = [col for col in df.columns if any(word in col.lower() for word in ['date', 'time', 'day'])]
                if date_candidates:
                    df = df.rename(columns={date_candidates[0]: 'Date'})
                    logger.info(f"Using {date_candidates[0]} as Date column for {symbol}")
                else:
                    # If no date column found, use index as dates (assuming sequential data)
                    logger.warning(f"No date column found in {symbol} CSV, using row index as dates")
                    df['Date'] = pd.date_range(start='2023-01-01', periods=len(df), freq='D')

            # Ensure required columns exist
            required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                logger.error(f"Missing required columns in {symbol} CSV: {missing_cols}")
                logger.error(f"Available columns: {list(df.columns)}")

                # Try to handle missing Volume column
                if 'Volume' in missing_cols and len(missing_cols) == 1:
                    logger.warning(f"Volume column missing for {symbol}, using default values")
                    df['Volume'] = 100000  # Default volume
                    missing_cols.remove('Volume')

                if missing_cols:
                    return None

            # Convert Date column with multiple format support
            date_formats = [
                '%Y-%m-%d',
                '%d-%m-%Y', 
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y/%m/%d',
                '%d-%b-%Y',
                '%d %b %Y',
                '%Y-%m-%d %H:%M:%S'
            ]

            date_parsed = False
            for fmt in date_formats:
                try:
                    df['Date'] = pd.to_datetime(df['Date'], format=fmt, errors='coerce')
                    if not df['Date'].isna().all():
                        date_parsed = True
                        logger.info(f"Successfully parsed dates using format: {fmt}")
                        break
                except:
                    continue

            if not date_parsed:
                # Try pandas' automatic parsing as last resort
                try:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce', infer_datetime_format=True)
                    if not df['Date'].isna().all():
                        date_parsed = True
                        logger.info("Successfully parsed dates using automatic detection")
                except:
                    logger.error(f"Failed to parse dates in {symbol} CSV file")
                    return None

            # Remove rows with invalid dates
            df = df.dropna(subset=['Date'])
            df = df.sort_values('Date')

            # Ensure numeric columns
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Remove rows with missing OHLC data
            df = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

            # Add symbol for reference
            df['Symbol'] = symbol

            logger.info(f"✅ Imported {len(df)} days of historical data for {symbol}")
            logger.info(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")

            return df

        except Exception as e:
            logger.error(f"Error importing CSV data for {symbol}: {str(e)}")
            return None

    def import_yfinance_extended(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        Import extended historical data using yfinance
        """
        try:
            ticker = f"{symbol}.NS"  # NSE format

            # Try different ticker formats if NSE fails
            ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]

            for ticker_format in ticker_formats:
                try:
                    stock = yf.Ticker(ticker_format)
                    df = stock.history(period=period, interval="1d")

                    if not df.empty and len(df) > 200:  # At least 200 days
                        df.reset_index(inplace=True)
                        df['Symbol'] = symbol
                        logger.info(f"Downloaded {len(df)} days for {symbol} using {ticker_format}")
                        return df

                except Exception as e:
                    logger.debug(f"Failed {ticker_format}: {str(e)}")
                    continue

            logger.warning(f"Could not download data for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Error downloading extended data for {symbol}: {str(e)}")
            return None

    def create_enhanced_training_dataset_from_data(self, downloaded_data):
        """
        Create enhanced training dataset from downloaded Yahoo Finance data
        """
        try:
            logger.info("🎯 Creating enhanced training dataset from downloaded data...")

            lstm_X, lstm_y = [], []
            rf_X, rf_y = [], []
            metadata = {
                'symbols_processed': 0,
                'lstm_samples': 0,
                'rf_samples': 0,
                'data_period': '1 year'
            }

            for symbol, data in downloaded_data.items():
                try:
                    logger.info(f"Processing {symbol} for training...")

                    # Calculate technical indicators
                    enhanced_data = self.data_loader.calculate_technical_indicators(data)

                    # Prepare LSTM data
                    lstm_x, lstm_y_vals = self.data_loader.prepare_lstm_data(enhanced_data)
                    if lstm_x is not None and lstm_y_vals is not None:
                        lstm_X.extend(lstm_x)
                        lstm_y.extend(lstm_y_vals)

                    # Prepare RF data (using default fundamentals for now)
                    fundamentals = self.create_default_fundamentals(symbol)
                    rf_x, rf_y_vals = self.data_loader.prepare_rf_data(enhanced_data, fundamentals)
                    if rf_x is not None and rf_y_vals is not None:
                        rf_X.extend(rf_x)
                        rf_y.extend(rf_y_vals)

                    metadata['symbols_processed'] += 1

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
                    continue

            metadata['lstm_samples'] = len(lstm_X)
            metadata['rf_samples'] = len(rf_X)

            logger.info(f"Enhanced dataset created:")
            logger.info(f"  Symbols: {metadata['symbols_processed']}")
            logger.info(f"  LSTM samples: {metadata['lstm_samples']}")
            logger.info(f"  RF samples: {metadata['rf_samples']}")

            return {
                'lstm': {
                    'X': np.array(lstm_X) if lstm_X else None,
                    'y': np.array(lstm_y) if lstm_y else None
                },
                'rf': {
                    'X': np.array(rf_X) if rf_X else None,
                    'y': np.array(rf_y) if rf_y else None
                },
                'metadata': metadata
            }

        except Exception as e:
            logger.error(f"Error creating enhanced training dataset: {str(e)}")
            return None

    def create_training_dataset_from_csv_folder(self, csv_folder="downloaded_historical_data"):
        """
        Create training dataset from CSV files in the specified folder
        """
        try:
            logger.info(f"🎯 Creating training dataset from CSV folder: {csv_folder}")

            if not os.path.exists(csv_folder):
                logger.error(f"CSV folder not found: {csv_folder}")
                return None

            csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
            if not csv_files:
                logger.error(f"No CSV files found in {csv_folder}")
                return None

            logger.info(f"Found {len(csv_files)} CSV files")

            # Load all CSV data
            loaded_data = {}
            for csv_file in csv_files:
                symbol = csv_file.replace('.csv', '')
                csv_path = os.path.join(csv_folder, csv_file)

                try:
                    df = pd.read_csv(csv_path)
                    # Ensure Date column is properly formatted
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'])
                    loaded_data[symbol] = df
                    logger.info(f"Loaded {symbol}: {len(df)} rows")
                except Exception as e:
                    logger.error(f"Error loading {csv_file}: {str(e)}")
                    continue

            if not loaded_data:
                logger.error("No CSV files were successfully loaded")
                return None

            # Create training dataset using the loaded data
            return self.create_enhanced_training_dataset_from_data(loaded_data)

        except Exception as e:
            logger.error(f"Error creating training dataset from CSV folder: {str(e)}")
            return None

    def _create_lstm_sequences(self, df: pd.DataFrame) -> Optional[Dict]:
        """Create LSTM training sequences from historical data"""
        try:
            # Use data loader's LSTM preparation
            X, y = self.data_loader.prepare_lstm_data(df)

            if X is not None and y is not None:
                return {'X': X, 'y': y}
            return None

        except Exception as e:
            logger.error(f"Error creating LSTM sequences: {str(e)}")
            return None

    def _create_rf_samples(self, df: pd.DataFrame, fundamentals: Dict) -> Optional[Dict]:
        """Create Random Forest training samples from historical data"""
        try:
            # Create multiple samples from different time windows
            samples_X, samples_y = [], []

            # Use last 60 days for sample creation, moving window approach
            window_size = 30

            for i in range(window_size, len(df)):
                window_data = df.iloc[i-window_size:i]

                # Use data loader's RF preparation
                X, y = self.data_loader.prepare_rf_data(window_data, fundamentals)

                if X is not None and y is not None:
                    samples_X.extend(X)
                    samples_y.extend(y)

            if samples_X:
                return {'X': samples_X, 'y': samples_y}
            return None

        except Exception as e:
            logger.error(f"Error creating RF samples: {str(e)}")
            return None

    def _get_fundamentals_for_symbol(self, symbol: str) -> Dict:
        """Get fundamental data for symbol"""
        try:
            from stock_screener import EnhancedStockScreener
            screener = EnhancedStockScreener()
            return screener.scrape_screener_data(symbol)
        except Exception:
            # Return default values if screener fails
            return {
                'pe_ratio': 20.0,
                'revenue_growth': 5.0,
                'earnings_growth': 3.0,
                'promoter_buying': False,
                'debt_to_equity': 1.0,
                'roe': 15.0
            }

    def train_models_with_external_data(self, 
                                      csv_data_path: str = None,
                                      symbols_file: str = None) -> bool:
        """
        Complete pipeline to train models with external historical data
        """
        try:
            logger.info("🚀 Starting enhanced model training with external data...")

            # Get symbols list
            if symbols_file:
                with open(symbols_file, 'r') as f:
                    symbols_list = [line.strip() for line in f.readlines()]
            else:
                # Use default watchlist
                from stock_screener import EnhancedStockScreener
                screener = EnhancedStockScreener()
                symbols_list = screener.watchlist[:50]  # Use more symbols for training

            logger.info(f"Training with {len(symbols_list)} symbols...")

            # Create enhanced training dataset
            training_data = self.create_enhanced_training_dataset(
                symbols_list, 
                csv_data_path=csv_data_path,
                use_extended_period=True
            )

            if not training_data or not training_data.get('lstm') or not training_data.get('rf'):
                logger.error("Failed to create training dataset")
                return False

            # Train models
            logger.info("🤖 Training ML models with enhanced dataset...")
            success = self.models.train_models(training_data)

            if success:
                logger.info("✅ Enhanced model training completed successfully!")
                logger.info(f"Models trained with:")
                logger.info(f"  - LSTM samples: {training_data['metadata']['lstm_samples']}")
                logger.info(f"  - RF samples: {training_data['metadata']['rf_samples']}")
                logger.info(f"  - Symbols: {training_data['metadata']['symbols_processed']}")

                # Save training metadata
                with open('training_metadata.json', 'w') as f:
                    json.dump(training_data['metadata'], f, indent=2)

                return True
            else:
                logger.error("❌ Enhanced model training failed!")
                return False

        except Exception as e:
            logger.error(f"Error in enhanced model training: {str(e)}")
            return False

def main():
    """Example usage of external data importer"""
    importer = ExternalDataImporter()

    # Check if we have CSV files in the local directory
    csv_dir = "downloaded_historical_data"  # Changed to downloaded_historical_data
    csv_files = []

    if os.path.exists(csv_dir):
        csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
        print(f"Found {len(csv_files)} CSV files: {csv_files}")

    if csv_files:
        # Train with local CSV data
        print("🎯 Training with local CSV data...")
        # Use the new method to create the training dataset from the CSV folder
        training_data = importer.create_training_dataset_from_csv_folder(csv_dir)

        if training_data:
            # Train the models
            print("🤖 Training ML models with enhanced dataset...")
            success = importer.models.train_models(training_data)

            if success:
                print("✅ Enhanced training completed!")
            else:
                print("❌ Enhanced training failed!")
        else:
            print("❌ Failed to create training dataset from CSV folder.")
    else:
        # Fall back to extended yfinance data
        print("📈 Training with extended yfinance data...")
        success = importer.train_models_with_external_data()

    if success:
        print("✅ Enhanced training completed!")
    else:
        print("❌ Enhanced training failed!")

if __name__ == "__main__":
    main()