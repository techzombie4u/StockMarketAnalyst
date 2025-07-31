
#!/usr/bin/env python3
"""
Train ML Models with Yahoo Finance Data

This script automatically downloads 1-year historical data from Yahoo Finance
and trains the ML models. No need for manual CSV files.
"""

import os
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from external_data_importer import ExternalDataImporter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def download_yahoo_finance_data(symbols_list, period="1y"):
    """
    Download historical data from Yahoo Finance for all symbols
    """
    print(f"📈 Downloading {period} historical data from Yahoo Finance...")
    
    downloaded_data = {}
    successful_downloads = 0
    
    for i, symbol in enumerate(symbols_list, 1):
        print(f"Downloading {symbol} ({i}/{len(symbols_list)})...")
        
        try:
            # Try different ticker formats for Indian stocks
            ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]
            
            data = None
            for ticker_format in ticker_formats:
                try:
                    ticker = yf.Ticker(ticker_format)
                    data = ticker.history(period=period, interval="1d")
                    
                    if not data.empty and len(data) > 200:  # At least 200 days
                        print(f"   ✅ Downloaded {len(data)} days using {ticker_format}")
                        data.reset_index(inplace=True)
                        data['Symbol'] = symbol
                        downloaded_data[symbol] = data
                        successful_downloads += 1
                        break
                        
                except Exception as e:
                    continue
            
            if symbol not in downloaded_data:
                print(f"   ❌ Failed to download {symbol}")
                
        except Exception as e:
            print(f"   ❌ Error downloading {symbol}: {str(e)}")
    
    print(f"\n📊 Download Summary:")
    print(f"   Total symbols: {len(symbols_list)}")
    print(f"   Successful downloads: {successful_downloads}")
    print(f"   Failed downloads: {len(symbols_list) - successful_downloads}")
    
    return downloaded_data

def save_data_as_csv(downloaded_data, csv_dir="downloaded_historical_data"):
    """
    Save downloaded data as CSV files for backup
    """
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    
    print(f"\n💾 Saving data to {csv_dir}/...")
    
    for symbol, data in downloaded_data.items():
        csv_path = os.path.join(csv_dir, f"{symbol}.csv")
        data.to_csv(csv_path, index=False)
        print(f"   Saved {symbol}.csv ({len(data)} rows)")

def main():
    print("🚀 Training ML Models with Yahoo Finance Data")
    print("=" * 60)
    
    # Define the symbols to download (same as your existing watchlist)
    symbols_list = [
        'SBIN', 'BHARTIARTL', 'ITC', 'NTPC', 'POWERGRID',
        'ONGC', 'COALINDIA', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO',
        'TATAMOTORS', 'M&M', 'BPCL', 'GAIL', 'IOC',
        'SAIL', 'VEDL', 'BANKBARODA', 'CANBK', 'PNB',
        'UNIONBANK', 'BANKINDIA', 'CENTRALBK', 'INDIANB',
        'RECLTD', 'PFC', 'IRFC', 'IRCTC', 'RAILTEL',
        'HAL', 'BEL', 'BEML', 'BHEL', 'CONCOR',
        'NBCC', 'RITES', 'KTKBANK', 'FEDERALBNK', 'IDFCFIRSTB',
        'EQUITAS', 'RBLBANK', 'YESBANK', 'LICHSGFIN',
        'MUTHOOTFIN', 'BAJAJHLDNG', 'GODREJCP', 'MARICO', 'DABUR'
    ]
    
    print(f"📋 Symbols to process: {len(symbols_list)}")
    for i, symbol in enumerate(symbols_list, 1):
        if i <= 10:
            print(f"   {i}. {symbol}")
        elif i == 11:
            print(f"   ... and {len(symbols_list) - 10} more")
            break
    
    # Download data from Yahoo Finance
    downloaded_data = download_yahoo_finance_data(symbols_list, period="1y")
    
    if not downloaded_data:
        print("\n❌ No data was downloaded successfully!")
        return False
    
    # Save as CSV backup
    save_data_as_csv(downloaded_data)
    
    # Create enhanced training dataset
    print("\n🤖 Creating enhanced training dataset...")
    importer = ExternalDataImporter()
    
    # Create training dataset using downloaded data
    training_data = importer.create_enhanced_training_dataset_from_data(downloaded_data)
    
    if not training_data or not training_data.get('lstm') or not training_data.get('rf'):
        print("❌ Failed to create training dataset")
        return False
    
    # Train models
    print("\n🎯 Training ML models...")
    success = importer.models.train_models(training_data)
    
    if success:
        print("\n✅ Enhanced model training completed successfully!")
        print("🎯 Models are now trained with 1-year Yahoo Finance data")
        print("📊 You can now run the stock screening with improved predictions")
        
        # Check if models were created
        model_files = ['lstm_model.h5', 'rf_model.pkl', 'scalers.pkl']
        created_files = [f for f in model_files if os.path.exists(f)]
        
        if created_files:
            print(f"\n📁 Model files created: {created_files}")
        else:
            print("\n⚠️ Model files not found - check logs for training issues")
        
        # Show training statistics
        metadata = training_data.get('metadata', {})
        print(f"\n📈 Training Statistics:")
        print(f"   Symbols processed: {metadata.get('symbols_processed', 0)}")
        print(f"   LSTM samples: {metadata.get('lstm_samples', 0)}")
        print(f"   RF samples: {metadata.get('rf_samples', 0)}")
        print(f"   Data period: {metadata.get('data_period', '1 year')}")
        
        return True
    else:
        print("\n❌ Enhanced model training failed!")
        print("Check the logs above for error details")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
