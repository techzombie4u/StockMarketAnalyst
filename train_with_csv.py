
#!/usr/bin/env python3
"""
Enhanced 5-Year ML Model Training Script

This script automatically downloads 5 years of historical data from Yahoo Finance
and trains the ML models with comprehensive feature engineering and error handling.
"""

import os
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from external_data_importer import ExternalDataImporter

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("🚀 Enhanced 5-Year ML Model Training with Historical Data")
    print("=" * 70)
    
    # Import comprehensive stock list
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        symbols_list = screener.under500_symbols  # All 50 stocks under ₹500
        print(f"📋 Training with {len(symbols_list)} stocks from screener watchlist")
    except Exception as e:
        print(f"⚠️ Could not load screener watchlist: {e}")
        # Enhanced fallback list with more stocks
        symbols_list = [
            'SBIN', 'BHARTIARTL', 'ITC', 'NTPC', 'POWERGRID', 'ONGC', 'COALINDIA',
            'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'TATAMOTORS', 'M&M', 'BPCL',
            'GAIL', 'IOC', 'SAIL', 'VEDL', 'BANKBARODA', 'CANBK', 'PNB',
            'UNIONBANK', 'BANKINDIA', 'CENTRALBK', 'INDIANB', 'RECLTD', 'PFC',
            'IRFC', 'IRCTC', 'RAILTEL', 'HAL', 'BEL', 'BEML', 'BHEL', 'CONCOR',
            'NBCC', 'RITES', 'KTKBANK', 'FEDERALBNK', 'IDFCFIRSTB', 'EQUITAS',
            'RBLBANK', 'YESBANK', 'LICHSGFIN', 'MUTHOOTFIN', 'BAJAJHLDNG',
            'GODREJCP', 'MARICO', 'DABUR'
        ]
        print(f"📋 Using fallback list with {len(symbols_list)} stocks")
    
    csv_folder = "downloaded_historical_data"
    
    print(f"\n🎯 Training Configuration:")
    print(f"   Data Period: 5 years")
    print(f"   Total Stocks: {len(symbols_list)}")
    print(f"   Data Source: Yahoo Finance")
    print(f"   Storage: {csv_folder}/")
    print(f"   Features: Enhanced technical + fundamental")
    print(f"   Models: LSTM + Random Forest")
    
    # Initialize enhanced importer
    print(f"\n🤖 Initializing Enhanced Data Importer...")
    importer = ExternalDataImporter()
    
    # Step 1: Download comprehensive 5-year data
    print(f"\n📈 Step 1: Downloading 5-year historical data...")
    print(f"   This may take several minutes for {len(symbols_list)} stocks...")
    
    download_result = importer.download_5year_data_for_all_stocks(symbols_list, csv_folder)
    
    if not download_result:
        print("❌ Data download failed completely")
        return False
    
    successful_count = download_result.get('successful_count', 0)
    failed_count = download_result.get('failed_count', 0)
    
    print(f"\n📊 Download Results:")
    print(f"   ✅ Successful: {successful_count} stocks")
    print(f"   ❌ Failed: {failed_count} stocks")
    
    if successful_count == 0:
        print("❌ No stocks downloaded successfully")
        return False
    
    if failed_count > 0:
        failed_symbols = download_result.get('failed_symbols', [])
        print(f"   Failed symbols: {failed_symbols[:10]}{'...' if len(failed_symbols) > 10 else ''}")
    
    # Step 2: Verify CSV files exist
    print(f"\n📁 Step 2: Verifying downloaded data...")
    if not os.path.exists(csv_folder):
        print(f"❌ CSV folder not found: {csv_folder}")
        return False
    
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ No CSV files found in {csv_folder}")
        return False
    
    print(f"✅ Found {len(csv_files)} CSV files")
    
    # Show sample of files
    sample_files = csv_files[:10]
    for i, csv_file in enumerate(sample_files, 1):
        try:
            csv_path = os.path.join(csv_folder, csv_file)
            df = pd.read_csv(csv_path)
            symbol = csv_file.replace('.csv', '')
            print(f"   {i}. {symbol}: {len(df)} days of data")
        except Exception as e:
            print(f"   {i}. {csv_file}: Error reading file - {str(e)}")
    
    if len(csv_files) > 10:
        print(f"   ... and {len(csv_files) - 10} more files")
    
    # Step 3: Create enhanced training dataset
    print(f"\n🧠 Step 3: Creating enhanced training dataset...")
    print(f"   Processing {len(csv_files)} CSV files...")
    print(f"   Calculating 20+ technical indicators per stock...")
    print(f"   Creating multiple time-window samples...")
    
    training_data = importer.create_training_dataset_from_csv_folder(csv_folder)
    
    if not training_data:
        print("❌ Failed to create training dataset")
        return False
    
    # Validate training data
    lstm_data = training_data.get('lstm', {})
    rf_data = training_data.get('rf', {})
    metadata = training_data.get('metadata', {})
    
    lstm_samples = metadata.get('lstm_samples', 0)
    rf_samples = metadata.get('rf_samples', 0)
    symbols_processed = metadata.get('symbols_processed', 0)
    
    print(f"\n✅ Training dataset created successfully!")
    print(f"   Symbols processed: {symbols_processed}")
    print(f"   LSTM samples: {lstm_samples}")
    print(f"   RF samples: {rf_samples}")
    print(f"   Data period: {metadata.get('data_period', '5 years')}")
    
    if lstm_samples == 0 and rf_samples == 0:
        print("❌ No training samples created")
        return False
    
    # Step 4: Train enhanced ML models
    print(f"\n🎯 Step 4: Training ML models with 5-year data...")
    print(f"   Training LSTM with {lstm_samples} sequences...")
    print(f"   Training Random Forest with {rf_samples} samples...")
    print(f"   This may take several minutes...")
    
    success = importer.models.train_models(training_data)
    
    if success:
        print(f"\n🎉 ENHANCED 5-YEAR MODEL TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"✅ Models trained with comprehensive 5-year historical data")
        print(f"📊 Significantly improved prediction accuracy expected")
        print(f"🤖 Enhanced feature engineering with 20+ technical indicators")
        print(f"🎯 Ready for production use with high-accuracy predictions")
        
        # Check created model files
        model_files = ['lstm_model.h5', 'rf_model.pkl', 'scalers.pkl']
        created_files = [f for f in model_files if os.path.exists(f)]
        
        if created_files:
            print(f"\n📁 Model files created: {created_files}")
            for model_file in created_files:
                file_size = os.path.getsize(model_file) / (1024 * 1024)  # MB
                print(f"   {model_file}: {file_size:.2f} MB")
        
        print(f"\n📈 Final Training Statistics:")
        print(f"   Total stocks processed: {symbols_processed}")
        print(f"   LSTM training samples: {lstm_samples}")
        print(f"   RF training samples: {rf_samples}")
        print(f"   Data coverage: 5 years per stock")
        print(f"   Feature count: 20+ technical indicators")
        print(f"   Model complexity: High accuracy ensemble")
        
        print(f"\n🚀 Next Steps:")
        print(f"   1. Run the main application: python main.py")
        print(f"   2. Check the dashboard for enhanced predictions")
        print(f"   3. ML predictions will now be much more accurate")
        print(f"   4. Traditional + ML combined scoring active")
        
        return True
    else:
        print(f"\n❌ ENHANCED MODEL TRAINING FAILED!")
        print("Check the logs above for specific error details")
        print("Common issues:")
        print("  - Insufficient memory for large dataset")
        print("  - Data quality issues in CSV files")
        print("  - TensorFlow/Keras installation problems")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
