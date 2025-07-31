
#!/usr/bin/env python3
"""
Train ML Models with CSV Historical Data

This script trains the ML models using historical CSV data.
Place your CSV files in the historical_csv_data/ directory.
Expected format: SYMBOL.csv with columns: Date, Open, High, Low, Close, Volume
"""

import os
import logging
from external_data_importer import ExternalDataImporter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("🚀 Training ML Models with CSV Historical Data")
    print("=" * 60)
    
    # Check for CSV files
    csv_dir = "historical_csv_data"
    if not os.path.exists(csv_dir):
        print(f"❌ Directory {csv_dir} not found!")
        print("Please create the directory and place your CSV files there.")
        return False
    
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}")
        print("Please place your CSV files in the directory.")
        return False
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for i, file in enumerate(csv_files, 1):
        symbol = file.replace('.csv', '')
        print(f"   {i}. {symbol}")
    
    print("\n🤖 Starting enhanced model training...")
    
    # Initialize importer
    importer = ExternalDataImporter()
    
    print("\n🔍 Testing CSV file reading...")
    # Test reading one CSV file first
    test_file = os.path.join(csv_dir, csv_files[0])
    test_symbol = csv_files[0].replace('.csv', '')
    
    test_df = importer.import_historical_csv(test_file, test_symbol)
    if test_df is not None:
        print(f"✅ Successfully read {test_symbol}: {len(test_df)} rows")
        print(f"   Columns: {list(test_df.columns)}")
        print(f"   Date range: {test_df['Date'].min()} to {test_df['Date'].max()}")
    else:
        print(f"❌ Failed to read {test_symbol}")
        return False
    
    # Train models with CSV data
    print("\n🤖 Starting model training...")
    success = importer.train_models_with_external_data(
        csv_data_path=csv_dir,
        symbols_file="symbols_list.txt"
    )
    
    if success:
        print("\n✅ Enhanced model training completed successfully!")
        print("🎯 Models are now trained with your historical CSV data")
        print("📊 You can now run the stock screening with improved predictions")
        
        # Check if models were created
        model_files = ['lstm_model.h5', 'rf_model.pkl', 'scalers.pkl']
        created_files = [f for f in model_files if os.path.exists(f)]
        
        if created_files:
            print(f"\n📁 Model files created: {created_files}")
        else:
            print("\n⚠️ Model files not found - check logs for training issues")
        
        return True
    else:
        print("\n❌ Enhanced model training failed!")
        print("Check the logs above for error details")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
