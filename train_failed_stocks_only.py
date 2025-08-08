
#!/usr/bin/env python3
"""
Retry Training for Failed Stocks Only
Reads from training results JSON and retries only failed stocks
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_failed_stocks_from_log():
    """Extract failed stocks from latest training results"""
    try:
        # Find latest training results file
        log_files = [f for f in os.listdir('.') if f.startswith('new_stock_training_results_')]
        if not log_files:
            logger.error("No training results files found")
            return []
        
        latest_log = sorted(log_files)[-1]
        logger.info(f"Reading failed stocks from {latest_log}")
        
        with open(latest_log, 'r') as f:
            results = json.load(f)
        
        failed_stocks = []
        for symbol, result in results.get('stock_results', {}).items():
            lstm_success = result.get('lstm', {}).get('success', False)
            rf_success = result.get('rf', {}).get('success', False)
            
            if not lstm_success and not rf_success:
                failed_stocks.append(symbol)
                logger.info(f"Found failed stock: {symbol}")
        
        return failed_stocks
        
    except Exception as e:
        logger.error(f"Error reading training results: {str(e)}")
        return []

def main():
    """Retry training for failed stocks only"""
    logger.info("🔄 Starting retry training for failed stocks only")
    
    failed_stocks = get_failed_stocks_from_log()
    
    if not failed_stocks:
        logger.info("✅ No failed stocks found to retry")
        return
    
    logger.info(f"🎯 Found {len(failed_stocks)} failed stocks to retry")
    
    try:
        from src.ml.train_models import ModelTrainer
        trainer = ModelTrainer()
        
        retry_results = {
            'retry_start': datetime.now().isoformat(),
            'total_retried': len(failed_stocks),
            'successful': 0,
            'still_failed': 0,
            'results': {}
        }
        
        for i, symbol in enumerate(failed_stocks, 1):
            logger.info(f"🔄 Retrying {i}/{len(failed_stocks)}: {symbol}")
            
            try:
                result = trainer.train_single_stock(symbol)
                retry_results['results'][symbol] = result
                
                lstm_success = result.get('lstm', {}).get('success', False)
                rf_success = result.get('rf', {}).get('success', False)
                
                if lstm_success or rf_success:
                    retry_results['successful'] += 1
                    logger.info(f"✅ {symbol} succeeded on retry!")
                else:
                    retry_results['still_failed'] += 1
                    logger.warning(f"⚠️ {symbol} still failed after retry")
                    
            except Exception as e:
                logger.error(f"❌ Error retrying {symbol}: {str(e)}")
                retry_results['still_failed'] += 1
                retry_results['results'][symbol] = {
                    'success': False, 
                    'error': str(e), 
                    'symbol': symbol
                }
        
        retry_results['retry_end'] = datetime.now().isoformat()
        
        # Save retry results
        retry_file = f"retry_training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(retry_file, 'w') as f:
            json.dump(retry_results, f, indent=2)
        
        # Print summary
        print(f"\n🔄 RETRY TRAINING SUMMARY")
        print(f"📊 Total Retried: {retry_results['total_retried']}")
        print(f"✅ Now Successful: {retry_results['successful']}")
        print(f"❌ Still Failed: {retry_results['still_failed']}")
        print(f"💾 Results saved to: {retry_file}")
        
        return retry_results
        
    except Exception as e:
        logger.error(f"Critical error in retry training: {str(e)}")
        return None

if __name__ == "__main__":
    main()
