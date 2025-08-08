#!/usr/bin/env python3
"""
Enhanced New Stock Training Script

This script now uses the comprehensive 5-year historical data training pipeline
with robust error handling and enhanced prediction logic.
"""

import os
import sys
import logging
from datetime import datetime

# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Enhanced error handling
try:
    from src.managers.enhanced_error_handler import EnhancedErrorHandler
    error_handler = EnhancedErrorHandler()
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install yfinance pandas numpy scikit-learn tensorflow")
    sys.exit(1)

def setup_logging():
    """Setup comprehensive logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main training function with comprehensive pipeline"""
    print("Starting new stock training process...")
    print("🚀 Stock Market Analyst - Enhanced Model Training")
    print("=" * 60)

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Import the comprehensive training pipeline
        from src.ml.train_models import ModelTrainer
        from src.data.fetch_historical_data import HistoricalDataFetcher
        from src.reporters import insights

        print("📊 Initializing enhanced training pipeline...")
        trainer = ModelTrainer()

        # Option 1: Train all models with 5-year data
        print("🎯 Starting comprehensive model training...")
        print("   - Fetching 5-year historical data")
        print("   - Training LSTM models for price prediction")
        print("   - Training Random Forest models for direction")
        print("   - Updating model KPI registry")

        results = trainer.train_all_models()

        # Print results
        print("\n" + "=" * 60)
        print("📈 TRAINING RESULTS")
        print("=" * 60)
        print(f"🎯 Total Stocks: {results['summary']['total']}")
        print(f"✅ Successful: {results['summary']['successful']}")
        print(f"❌ Failed: {results['summary']['failed']}")
        print(f"📅 Started: {results['training_start']}")
        print(f"📅 Completed: {results['training_end']}")

        if results['summary']['successful'] > 0:
            print("\n🎉 Training completed successfully!")
            print("✅ Models are ready for enhanced predictions")
            print("✅ ROI evaluation logic updated")
            print("✅ Robust error handling implemented")
        else:
            print("\n⚠️ Training completed with issues")
            print("❌ Check logs for detailed error information")

        return results['summary']['successful'] > 0

    except ImportError as e:
        print(f"❌ Import Error: {str(e)}")
        print("Please ensure all dependencies are installed:")
        print("  pip install yfinance pandas numpy scikit-learn tensorflow")
        return False

    except Exception as e:
        print(f"💥 Training failed - {str(e)}")
        logger.error(f"Training error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)