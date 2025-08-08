"""
Stock Market Analyst - Model Training Script

Run this script to train ML models with historical data.
Usage: python train_models.py
"""

import logging
from src.models.data_loader import MLDataLoader
from src.models.models import MLModels
from src.analyzers.stock_screener import EnhancedStockScreener

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Train ML models with historical data"""
    try:
        logger.info("🚀 Starting ML model training process...")

        # Get stock symbols from screener
        screener = EnhancedStockScreener()
        symbols = screener.watchlist[:20]  # Use first 20 stocks for training

        logger.info(f"Training models with {len(symbols)} stocks: {symbols}")

        # Create fundamentals data (simplified for training)
        fundamentals_data = {}
        for symbol in symbols:
            try:
                fundamentals = screener.scrape_screener_data(symbol)
                fundamentals_data[symbol] = fundamentals
                logger.info(f"Collected fundamentals for {symbol}")
            except Exception as e:
                logger.warning(f"Could not get fundamentals for {symbol}: {str(e)}")
                # Use default values
                fundamentals_data[symbol] = {
                    'pe_ratio': 20.0,
                    'revenue_growth': 5.0,
                    'earnings_growth': 3.0,
                    'promoter_buying': False
                }

        # Create data loader and prepare training data
        logger.info("📊 Preparing training data...")
        data_loader = MLDataLoader()
        training_data = data_loader.create_training_dataset(symbols, fundamentals_data)

        # Check if we have sufficient data
        lstm_samples = len(training_data['lstm']['X']) if training_data['lstm']['X'] is not None else 0
        rf_samples = len(training_data['rf']['X']) if training_data['rf']['X'] is not None else 0

        logger.info(f"Training data prepared - LSTM: {lstm_samples} samples, RF: {rf_samples} samples")

        if lstm_samples < 100 or rf_samples < 50:
            logger.warning("⚠️  Limited training data. Models may have reduced accuracy.")

        # Train models with enhanced strategy
        logger.info("🤖 Training ML models with advanced techniques...")
        models = MLModels()
        
        # Use cross-validation for better model selection
        success = models.train_models_with_validation(training_data)
        
        # Train ensemble of models for better predictions
        if success:
            logger.info("🔄 Training ensemble models...")
            ensemble_success = models.train_ensemble_models(training_data)

        if success:
            logger.info("✅ Model training completed successfully!")
            logger.info("Models saved:")
            logger.info("  - lstm_model.h5 (LSTM price prediction)")
            logger.info("  - rf_model.joblib (Random Forest direction classification)")
            logger.info("\n🎯 Models are now ready for predictions!")
        else:
            logger.error("❌ Model training failed!")

    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
    except Exception as e:
        logger.error(f"Error in model training: {str(e)}")

if __name__ == "__main__":
    main()