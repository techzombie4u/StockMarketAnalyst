
#!/usr/bin/env python3
"""
Train New Stocks - Simple Script

This script will:
1. Extract fresh data from Yahoo Finance, NSE, BSE
2. Train ML models with comprehensive 5-year historical data
3. Handle any missing or corrupted data files
4. Work with your existing stock list

Usage: python train_new_stocks.py
"""

import logging
import sys
import os

# Add src to path
sys.path.append('src')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main training function"""
    print("🚀 Stock Market Analyst - New Stock Training")
    print("=" * 60)
    
    try:
        # Import the enhanced trainer
        from src.utils.enhanced_data_trainer import EnhancedDataTrainer
        
        print("📊 Initializing Enhanced Data Trainer...")
        trainer = EnhancedDataTrainer()
        
        print(f"🎯 Training Configuration:")
        print(f"   Total Stocks: {len(trainer.all_stocks)}")
        print(f"   Data Sources: Yahoo Finance, NSE, BSE")
        print(f"   Period: 5 years historical data")
        print(f"   Features: 20+ technical indicators")
        print(f"   Models: LSTM + Random Forest")
        
        print(f"\n🔄 Starting comprehensive training process...")
        print("   This may take 10-15 minutes for all stocks...")
        
        # Run the complete training pipeline
        success = trainer.train_models_for_new_stocks()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 TRAINING COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("✅ Fresh data extracted from multiple sources")
            print("✅ Technical indicators calculated")
            print("✅ ML models trained with comprehensive dataset")
            print("✅ System ready for high-accuracy predictions")
            print("\n📈 Next Steps:")
            print("   1. Run: python main.py")
            print("   2. Check the dashboard for enhanced predictions")
            print("   3. ML predictions will now be much more accurate")
            
            # Show model files created
            model_files = ['models_trained/lstm_model.h5', 'models_trained/rf_model.pkl']
            created_files = [f for f in model_files if os.path.exists(f)]
            if created_files:
                print(f"\n📁 Model Files Created:")
                for model_file in created_files:
                    if os.path.exists(model_file):
                        size_mb = os.path.getsize(model_file) / (1024 * 1024)
                        print(f"   {model_file}: {size_mb:.2f} MB")
            
            return True
            
        else:
            print("\n" + "=" * 60)
            print("❌ TRAINING FAILED!")
            print("=" * 60)
            print("Please check the logs above for specific errors.")
            print("Common issues:")
            print("  - Internet connectivity problems")
            print("  - Rate limiting from data sources")
            print("  - Insufficient memory for large datasets")
            print("\nTry running the script again after a few minutes.")
            return False
            
    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
        print("Please ensure all dependencies are installed:")
        print("  pip install yfinance pandas numpy scikit-learn tensorflow")
        return False
        
    except Exception as e:
        logger.error(f"Training failed with error: {str(e)}")
        print(f"❌ Unexpected Error: {str(e)}")
        print("Check training.log for detailed error information.")
        return False

if __name__ == "__main__":
    print("Starting new stock training process...")
    success = main()
    
    if success:
        print("\n🎯 Training completed successfully!")
        exit(0)
    else:
        print("\n💥 Training failed - check logs for details")
        exit(1)
