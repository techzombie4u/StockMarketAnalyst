
#!/usr/bin/env python3
"""
Enhanced New Stock Training Pipeline
Uses the exact same proven approach as src/ml/train_models.py
"""

import os
import logging
import json
from datetime import datetime
from typing import List, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to train new stocks using proven ModelTrainer approach"""
    logger.info("🚀 Starting New Stock Training Pipeline")
    
    try:
        # Import the proven ModelTrainer from existing codebase
        from src.ml.train_models import ModelTrainer
        
        # Initialize trainer with existing proven configuration
        trainer = ModelTrainer()
        logger.info("✅ ModelTrainer initialized successfully")
        
        # Define new stocks to train (focus on options universe and missing stocks)
        new_stocks_to_train = [
            # Nifty 50 stocks that might be missing
            'RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 
            'BHARTIARTL', 'ITC', 'HINDUNILVR', 'KOTAKBANK', 
            'LT', 'AXISBANK', 'MARUTI', 'SUNPHARMA', 'TITAN',
            'ULTRACEMCO', 'ASIANPAINT', 'BAJFINANCE', 'NESTLEIND',
            'HCLTECH', 'TECHM', 'WIPRO', 'DRREDDY', 'JSWSTEEL',
            'HINDALCO', 'ADANIPORTS', 'GRASIM', 'BAJAJFINSV',
            'HEROMOTOCO', 'EICHERMOT', 'INDUSINDBK', 'TATACONSUM',
            'UPL', 'LTIM', 'POWERGRID', 'NTPC', 'ONGC',
            'COALINDIA', 'TATAMOTORS', 'SBIN', 'TATASTEEL',
            
            # Bank Nifty components
            'HDFCBANK', 'ICICIBANK', 'KOTAKBANK', 'AXISBANK', 
            'SBIN', 'INDUSINDBK', 'BANKBARODA', 'PNB', 'IDFCFIRSTB',
            'FEDERALBNK', 'AUBANK', 'BANDHANBNK',
            
            # Additional high-volume options stocks
            'M&M', 'GODREJCP', 'DABUR', 'MARICO', 'BRITANNIA',
            'DIVISLAB', 'CIPLA', 'LUPIN', 'BIOCON', 'DRREDDYS',
            'APOLLOHOSP', 'FORTIS', 'MAXHEALTH',
            
            # PSU and Metal stocks
            'SAIL', 'NMDC', 'VEDL', 'HINDZINC', 'NALCO',
            'BEL', 'HAL', 'BHEL', 'GAIL', 'IOC', 'BPCL',
            'IRCTC', 'RAILTEL', 'CONCOR', 'IRFC', 'PFC', 'RECLTD',
            
            # Financial services
            'BAJAJHLDNG', 'LICHSGFIN', 'MUTHOOTFIN', 'MANAPPURAM',
            'CHOLAFIN', 'M&MFIN',
            
            # IT and Tech
            'MINDTREE', 'MPHASIS', 'COFORGE', 'PERSISTENT',
            'LTTS', 'CYIENT', 'RAMPGREEN'
        ]
        
        # Remove duplicates while preserving order
        new_stocks_to_train = list(dict.fromkeys(new_stocks_to_train))
        
        logger.info(f"📊 Planning to train {len(new_stocks_to_train)} stocks")
        
        # Training results tracking
        training_summary = {
            'training_start': datetime.now().isoformat(),
            'total_planned': len(new_stocks_to_train),
            'successful': 0,
            'failed': 0,
            'stock_results': {},
            'errors': []
        }
        
        # Train each stock using the proven approach
        for i, symbol in enumerate(new_stocks_to_train, 1):
            logger.info(f"🎯 Training {i}/{len(new_stocks_to_train)}: {symbol}")
            
            try:
                # Use the exact same training method that worked for existing stocks
                result = trainer.train_single_stock(symbol)
                
                training_summary['stock_results'][symbol] = result
                
                # Check if training was successful
                lstm_success = result.get('lstm', {}).get('success', False)
                rf_success = result.get('rf', {}).get('success', False)
                
                if lstm_success or rf_success:
                    training_summary['successful'] += 1
                    logger.info(f"✅ {symbol} trained successfully - LSTM: {lstm_success}, RF: {rf_success}")
                else:
                    training_summary['failed'] += 1
                    logger.warning(f"⚠️ {symbol} training failed - LSTM: {lstm_success}, RF: {rf_success}")
                    training_summary['errors'].append(f"{symbol}: {result.get('error', 'Unknown error')}")
                
            except Exception as e:
                error_msg = f"Critical error training {symbol}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                training_summary['failed'] += 1
                training_summary['errors'].append(error_msg)
                training_summary['stock_results'][symbol] = {
                    'success': False, 
                    'error': str(e), 
                    'symbol': symbol
                }
        
        # Final summary
        training_summary['training_end'] = datetime.now().isoformat()
        
        # Save training results
        results_file = f"new_stock_training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(training_summary, f, indent=2)
        
        # Print comprehensive summary
        print("\n" + "="*80)
        print("🎯 NEW STOCK TRAINING RESULTS")
        print("="*80)
        print(f"📊 Total Stocks Planned: {training_summary['total_planned']}")
        print(f"✅ Successfully Trained: {training_summary['successful']}")
        print(f"❌ Failed Training: {training_summary['failed']}")
        print(f"📈 Success Rate: {(training_summary['successful']/training_summary['total_planned']*100):.1f}%")
        
        if training_summary['successful'] > 0:
            print(f"\n✅ Successfully Trained Stocks:")
            successful_stocks = [s for s, r in training_summary['stock_results'].items() 
                               if r.get('lstm', {}).get('success') or r.get('rf', {}).get('success')]
            for stock in successful_stocks[:10]:  # Show first 10
                print(f"   • {stock}")
            if len(successful_stocks) > 10:
                print(f"   ... and {len(successful_stocks) - 10} more")
        
        if training_summary['errors']:
            print(f"\n❌ Training Errors:")
            for error in training_summary['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(training_summary['errors']) > 5:
                print(f"   ... and {len(training_summary['errors']) - 5} more errors")
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        print("="*80)
        
        # Validate model files were created
        models_dir = "models_trained"
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) if f.endswith(('.h5', '.pkl'))]
            print(f"📁 Total model files in {models_dir}: {len(model_files)}")
        
        # Check KPI updates
        kpi_file = "data/tracking/model_kpi.json"
        if os.path.exists(kpi_file):
            with open(kpi_file, 'r') as f:
                kpi_data = json.load(f)
            print(f"📊 KPI registry now tracks {len([k for k in kpi_data.keys() if k not in ['last_training']])} stocks")
        
        logger.info("🎉 New stock training pipeline completed!")
        return training_summary
        
    except ImportError as e:
        error_msg = f"Failed to import ModelTrainer: {str(e)}"
        logger.error(f"❌ {error_msg}")
        print(f"\n❌ CRITICAL ERROR: {error_msg}")
        print("🔧 Please ensure src/ml/train_models.py exists and is working correctly")
        return None
        
    except Exception as e:
        error_msg = f"Critical error in training pipeline: {str(e)}"
        logger.error(f"❌ {error_msg}")
        print(f"\n❌ CRITICAL ERROR: {error_msg}")
        return None

if __name__ == "__main__":
    results = main()
    if results:
        print(f"\n🎯 Training completed with {results['successful']} successes out of {results['total_planned']} attempts")
    else:
        print("\n❌ Training pipeline failed to execute")
