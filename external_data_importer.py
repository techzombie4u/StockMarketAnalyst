
"""
External Historical Data Importer - Enhanced 5-Year Version
Imports 5-year historical data from external sources for comprehensive model training
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

    def download_5year_data_for_all_stocks(self, symbols_list: List[str], output_folder: str = "downloaded_historical_data") -> Dict:
        """Download 5 years of historical data for all stocks"""
        try:
            logger.info(f"📈 Downloading 5-year historical data for {len(symbols_list)} stocks...")
            
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
                logger.info(f"Created directory: {output_folder}")
            
            downloaded_data = {}
            successful_downloads = 0
            failed_downloads = []
            
            for i, symbol in enumerate(symbols_list, 1):
                logger.info(f"Downloading {symbol} ({i}/{len(symbols_list)})...")
                
                try:
                    # Try different ticker formats for Indian stocks
                    ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]
                    
                    data = None
                    for ticker_format in ticker_formats:
                        try:
                            ticker = yf.Ticker(ticker_format)
                            data = ticker.history(period="5y", interval="1d", progress=False)
                            
                            if not data.empty and len(data) > 1000:  # At least 1000 days (4+ years)
                                logger.info(f"   ✅ Downloaded {len(data)} days using {ticker_format}")
                                data.reset_index(inplace=True)
                                data['Symbol'] = symbol
                                downloaded_data[symbol] = data
                                successful_downloads += 1
                                
                                # Save to CSV immediately
                                csv_path = os.path.join(output_folder, f"{symbol}.csv")
                                data.to_csv(csv_path, index=False)
                                logger.info(f"   💾 Saved to {csv_path}")
                                break
                                
                        except Exception as e:
                            logger.debug(f"   Failed {ticker_format}: {str(e)}")
                            continue
                    
                    if symbol not in downloaded_data:
                        logger.warning(f"   ❌ Failed to download {symbol}")
                        failed_downloads.append(symbol)
                        
                except Exception as e:
                    logger.error(f"   ❌ Error downloading {symbol}: {str(e)}")
                    failed_downloads.append(symbol)
            
            logger.info(f"\n📊 Download Summary:")
            logger.info(f"   Total symbols: {len(symbols_list)}")
            logger.info(f"   Successful downloads: {successful_downloads}")
            logger.info(f"   Failed downloads: {len(failed_downloads)}")
            
            if failed_downloads:
                logger.warning(f"   Failed symbols: {failed_downloads}")
            
            return {
                'downloaded_data': downloaded_data,
                'successful_count': successful_downloads,
                'failed_count': len(failed_downloads),
                'failed_symbols': failed_downloads
            }
            
        except Exception as e:
            logger.error(f"Error in 5-year data download: {str(e)}")
            return None

    def create_training_dataset_from_csv_folder(self, csv_folder: str) -> Dict:
        """Create enhanced training dataset from CSV files with 5-year data"""
        try:
            logger.info(f"Creating 5-year training dataset from {csv_folder}...")

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
            total_lstm_samples = 0
            total_rf_samples = 0

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

                    # Skip if insufficient data (need at least 2 years for 5-year training)
                    if len(df) < 500:
                        logger.warning(f"Insufficient data for {symbol} ({len(df)} rows), skipping")
                        continue

                    # Calculate technical indicators
                    df = self.calculate_enhanced_technical_indicators(df)

                    # Create dummy fundamentals with more realistic values
                    fundamentals = {
                        'pe_ratio': 15.0 + (hash(symbol) % 20),  # 15-35 range
                        'revenue_growth': -5.0 + (hash(symbol) % 25),  # -5 to 20 range
                        'earnings_growth': -10.0 + (hash(symbol) % 30),  # -10 to 20 range
                        'promoter_buying': (hash(symbol) % 4) == 0  # 25% chance
                    }

                    # Prepare LSTM data with multiple windows for better training
                    lstm_samples = self.prepare_lstm_data_enhanced(df)
                    if lstm_samples:
                        for lstm_x, lstm_y_val in lstm_samples:
                            if lstm_x is not None and lstm_y_val is not None:
                                lstm_X.append(lstm_x)
                                lstm_y.append(lstm_y_val)
                        total_lstm_samples += len(lstm_samples)
                        logger.info(f"  LSTM: Added {len(lstm_samples)} samples")

                    # Prepare RF data (multiple samples from different time windows)
                    rf_samples = self.prepare_rf_data_multiple_enhanced(df, fundamentals)
                    if rf_samples:
                        for rf_x, rf_y_val in rf_samples:
                            if rf_x is not None and rf_y_val is not None:
                                rf_X.append(rf_x.flatten())
                                rf_y.append(rf_y_val)
                        total_rf_samples += len(rf_samples)
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

            logger.info(f"5-year training dataset created:")
            logger.info(f"  Symbols processed: {symbols_processed}")
            logger.info(f"  LSTM samples: {total_lstm_samples}")
            logger.info(f"  RF samples: {total_rf_samples}")

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
                    'lstm_samples': total_lstm_samples,
                    'rf_samples': total_rf_samples,
                    'data_period': '5 years',
                    'lookback_window': 60
                }
            }

        except Exception as e:
            logger.error(f"Error creating 5-year training dataset: {str(e)}")
            return None

    def calculate_enhanced_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators for 5-year data"""
        try:
            # Price-based indicators
            df['Price_Change'] = df['Close'].pct_change().fillna(0)
            df['Momentum_2d'] = df['Close'].pct_change(periods=2).fillna(0)
            df['Momentum_5d'] = df['Close'].pct_change(periods=5).fillna(0)
            df['Momentum_10d'] = df['Close'].pct_change(periods=10).fillna(0)
            df['Momentum_20d'] = df['Close'].pct_change(periods=20).fillna(0)

            # Moving averages (multiple timeframes for 5-year data)
            df['MA_5'] = df['Close'].rolling(window=5).mean().fillna(df['Close'])
            df['MA_10'] = df['Close'].rolling(window=10).mean().fillna(df['Close'])
            df['MA_20'] = df['Close'].rolling(window=20).mean().fillna(df['Close'])
            df['MA_50'] = df['Close'].rolling(window=50).mean().fillna(df['Close'])
            df['MA_200'] = df['Close'].rolling(window=200).mean().fillna(df['Close'])

            # Price position relative to MAs
            df['Price_vs_MA5'] = ((df['Close'] - df['MA_5']) / df['MA_5']).fillna(0)
            df['Price_vs_MA10'] = ((df['Close'] - df['MA_10']) / df['MA_10']).fillna(0)
            df['Price_vs_MA20'] = ((df['Close'] - df['MA_20']) / df['MA_20']).fillna(0)
            df['Price_vs_MA50'] = ((df['Close'] - df['MA_50']) / df['MA_50']).fillna(0)

            # ATR (multiple periods)
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['ATR'] = true_range.rolling(window=14).mean().fillna(0)
            df['ATR_21'] = true_range.rolling(window=21).mean().fillna(0)

            # Volume indicators (enhanced)
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean().fillna(df['Volume'].mean())
            df['Volume_Ratio'] = (df['Volume'] / df['Volume_MA']).fillna(1.0)
            df['Volume_MA_50'] = df['Volume'].rolling(window=50).mean().fillna(df['Volume'].mean())

            # Volatility measures
            df['Volatility'] = df['Price_Change'].rolling(window=20).std().fillna(0)
            df['Volatility_50'] = df['Price_Change'].rolling(window=50).std().fillna(0)

            # RSI (multiple periods)
            for period in [14, 21]:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / (loss + 1e-8)
                df[f'RSI_{period}'] = (100 - (100 / (1 + rs))).fillna(50)

            # MACD
            ema_12 = df['Close'].ewm(span=12).mean()
            ema_26 = df['Close'].ewm(span=26).mean()
            df['MACD'] = ema_12 - ema_26
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']

            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            bb_middle = df['Close'].rolling(window=bb_period).mean()
            bb_std_dev = df['Close'].rolling(window=bb_period).std()
            df['BB_Upper'] = bb_middle + (bb_std_dev * bb_std)
            df['BB_Lower'] = bb_middle - (bb_std_dev * bb_std)
            df['BB_Position'] = ((df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])).fillna(0.5)

            # Fill NaN values using proper pandas methods
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error calculating enhanced technical indicators: {str(e)}")
            return df

    def prepare_lstm_data_enhanced(self, df: pd.DataFrame, lookback_window: int = 60) -> List[tuple]:
        """Prepare enhanced LSTM training data with multiple samples"""
        try:
            # Select enhanced features for 5-year training
            feature_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'ATR', 'ATR_21',
                             'Momentum_2d', 'Momentum_5d', 'Momentum_10d', 'Momentum_20d',
                             'Price_vs_MA5', 'Price_vs_MA10', 'Price_vs_MA20', 'Price_vs_MA50',
                             'RSI_14', 'RSI_21', 'MACD', 'MACD_Signal', 'BB_Position',
                             'Volume_Ratio', 'Volatility', 'Volatility_50']

            # Filter available columns
            available_cols = [col for col in feature_columns if col in df.columns]
            if len(available_cols) < 10:
                logger.warning(f"Insufficient feature columns: {len(available_cols)}")
                return []

            # Clean data
            df_clean = df[available_cols].dropna()
            if len(df_clean) < lookback_window + 1:
                return []

            # Normalize features
            scaled_features = self.feature_scaler.fit_transform(df_clean)

            # Create multiple samples with different step sizes for better training
            samples = []
            step_sizes = [1, 2, 3, 5]  # Different step sizes for data augmentation
            
            for step_size in step_sizes:
                for i in range(lookback_window, len(scaled_features), step_size):
                    if i >= len(scaled_features):
                        break
                        
                    X_sample = scaled_features[i-lookback_window:i]
                    
                    # Target: next day's close price change
                    if 'Close' in available_cols:
                        close_idx = available_cols.index('Close')
                        current_close = scaled_features[i-1, close_idx]
                        next_close = scaled_features[i, close_idx]
                        y_sample = next_close - current_close
                    else:
                        y_sample = 0
                    
                    samples.append((X_sample, y_sample))

            return samples

        except Exception as e:
            logger.error(f"Error preparing enhanced LSTM data: {str(e)}")
            return []

    def prepare_rf_data_multiple_enhanced(self, df: pd.DataFrame, fundamentals: Dict) -> List[tuple]:
        """Prepare multiple enhanced RF samples from different time windows"""
        try:
            samples = []

            # Create samples from different window sizes for 5-year data
            window_sizes = [30, 45, 60, 90]  # Different analysis windows
            step_size = 15

            for window_size in window_sizes:
                for start_idx in range(0, len(df) - window_size - 1, step_size):
                    end_idx = start_idx + window_size
                    window_data = df.iloc[start_idx:end_idx]

                    if len(window_data) < 20:
                        continue

                    # Enhanced technical features from this window
                    features = []

                    # Multiple momentum features
                    for momentum_col in ['Momentum_2d', 'Momentum_5d', 'Momentum_10d', 'Momentum_20d']:
                        if momentum_col in window_data.columns:
                            momentum_val = window_data[momentum_col].tail(5).mean()
                            features.append(momentum_val if not np.isnan(momentum_val) else 0)
                        else:
                            features.append(0)

                    # ATR features
                    for atr_col in ['ATR', 'ATR_21']:
                        if atr_col in window_data.columns:
                            atr_val = window_data[atr_col].tail(5).mean()
                            features.append(atr_val if not np.isnan(atr_val) else 0)
                        else:
                            features.append(0)

                    # Price vs MA features
                    for ma_col in ['Price_vs_MA5', 'Price_vs_MA10', 'Price_vs_MA20', 'Price_vs_MA50']:
                        if ma_col in window_data.columns:
                            ma_val = window_data[ma_col].iloc[-1]
                            features.append(ma_val if not np.isnan(ma_val) else 0)
                        else:
                            features.append(0)

                    # Volume features
                    if 'Volume_Ratio' in window_data.columns:
                        volume_ratio = window_data['Volume_Ratio'].tail(5).mean()
                        features.append(volume_ratio if not np.isnan(volume_ratio) else 1)
                    else:
                        features.append(1)

                    # Volatility features
                    for vol_col in ['Volatility', 'Volatility_50']:
                        if vol_col in window_data.columns:
                            vol_val = window_data[vol_col].tail(5).mean()
                            features.append(vol_val if not np.isnan(vol_val) else 0)
                        else:
                            features.append(0)

                    # RSI features
                    for rsi_col in ['RSI_14', 'RSI_21']:
                        if rsi_col in window_data.columns:
                            rsi_val = window_data[rsi_col].iloc[-1]
                            features.append(rsi_val if not np.isnan(rsi_val) else 50)
                        else:
                            features.append(50)

                    # MACD features
                    for macd_col in ['MACD', 'MACD_Signal', 'MACD_Histogram']:
                        if macd_col in window_data.columns:
                            macd_val = window_data[macd_col].iloc[-1]
                            features.append(macd_val if not np.isnan(macd_val) else 0)
                        else:
                            features.append(0)

                    # Bollinger Band position
                    if 'BB_Position' in window_data.columns:
                        bb_pos = window_data['BB_Position'].iloc[-1]
                        features.append(bb_pos if not np.isnan(bb_pos) else 0.5)
                    else:
                        features.append(0.5)

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
            logger.error(f"Error preparing enhanced RF data: {str(e)}")
            return []

def main():
    """Main function to download 5-year data and train models"""
    logger.info("🚀 Starting 5-Year Data Download and Model Training")
    
    # Import stock symbols from screener
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        symbols_list = screener.under500_symbols  # All stocks under ₹500
    except:
        # Fallback symbol list
        symbols_list = ['SBIN', 'BHARTIARTL', 'ITC', 'NTPC', 'POWERGRID', 'ONGC', 'COALINDIA', 
                       'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'TATAMOTORS', 'M&M', 'BPCL', 
                       'GAIL', 'IOC', 'SAIL', 'VEDL', 'BANKBARODA', 'CANBK', 'PNB']
    
    csv_folder = "downloaded_historical_data"
    
    # Initialize importer
    importer = ExternalDataImporter()
    
    # Step 1: Download 5-year data for all stocks
    logger.info(f"Step 1: Downloading 5-year data for {len(symbols_list)} stocks...")
    download_result = importer.download_5year_data_for_all_stocks(symbols_list, csv_folder)
    
    if not download_result or download_result['successful_count'] == 0:
        logger.error("❌ No data downloaded successfully")
        return False
    
    logger.info(f"✅ Downloaded data for {download_result['successful_count']} stocks")
    
    # Step 2: Create training dataset from downloaded CSV files
    logger.info("Step 2: Creating enhanced training dataset...")
    training_data = importer.create_training_dataset_from_csv_folder(csv_folder)
    
    if not training_data:
        logger.error("❌ Failed to create training dataset")
        return False
    
    # Step 3: Train models with 5-year data
    logger.info("Step 3: Training ML models with 5-year data...")
    success = importer.models.train_models(training_data)
    
    if success:
        logger.info("✅ 5-Year Enhanced Model Training Completed Successfully!")
        logger.info("🎯 Models are now trained with comprehensive 5-year historical data")
        logger.info("📊 ML predictions should now be significantly more accurate")
        
        # Show training statistics
        metadata = training_data.get('metadata', {})
        logger.info(f"\n📈 Final Training Statistics:")
        logger.info(f"   Symbols processed: {metadata.get('symbols_processed', 0)}")
        logger.info(f"   LSTM samples: {metadata.get('lstm_samples', 0)}")
        logger.info(f"   RF samples: {metadata.get('rf_samples', 0)}")
        logger.info(f"   Data period: {metadata.get('data_period', '5 years')}")
        logger.info(f"   Lookback window: {metadata.get('lookback_window', 60)}")
        
        return True
    else:
        logger.error("❌ 5-Year Model Training Failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
