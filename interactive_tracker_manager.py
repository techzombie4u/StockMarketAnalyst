
#!/usr/bin/env python3
"""
Interactive Tracker Manager - Enhanced Prediction Tracking

Manages the enhanced prediction tracking functionality for 5D and 30D views
with lock features and progressive data updates.
"""

import json
import os
import logging
from datetime import datetime, timedelta
import yfinance as yf
import pytz

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')

class InteractiveTrackerManager:
    def __init__(self):
        self.data_file = 'interactive_tracking.json'
        self.tracking_data = {}
        self.load_tracking_data()
    
    def load_tracking_data(self):
        """Load existing tracking data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.tracking_data = json.loads(content)
                        logger.info(f"Loaded tracking data for {len(self.tracking_data)} stocks")
                    else:
                        self.tracking_data = {}
            else:
                self.tracking_data = {}
                
            return self.tracking_data
            
        except Exception as e:
            logger.error(f"Error loading tracking data: {str(e)}")
            self.tracking_data = {}
            return {}
    
    def save_tracking_data(self):
        """Save tracking data to file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.tracking_data, f, indent=2, ensure_ascii=False)
            logger.info("Tracking data saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving tracking data: {str(e)}")
            return False
    
    def initialize_stock_tracking(self, symbol, current_price, predictions):
        """Initialize tracking for a new stock"""
        try:
            # Generate predicted price arrays based on predictions
            pred_5d = predictions.get('pred_5d', 0)
            pred_30d = predictions.get('pred_1mo', 0)
            
            predicted_5d = []
            predicted_30d = []
            
            # Generate 5-day predictions
            for i in range(5):
                daily_change = (pred_5d / 100) * (i + 1) / 5
                predicted_5d.append(current_price * (1 + daily_change))
            
            # Generate 30-day predictions
            for i in range(30):
                daily_change = (pred_30d / 100) * (i + 1) / 30
                predicted_30d.append(current_price * (1 + daily_change))
            
            stock_data = {
                'symbol': symbol,
                'start_date': datetime.now(IST).strftime('%Y-%m-%d'),
                'current_price': current_price,
                'confidence': predictions.get('confidence', 0),
                'score': predictions.get('score', 0),
                'predicted_5d': predicted_5d,
                'predicted_30d': predicted_30d,
                'actual_progress_5d': [current_price] + [None] * 4,
                'actual_progress_30d': [current_price] + [None] * 29,
                'updated_prediction_5d': [None] * 5,
                'updated_prediction_30d': [None] * 30,
                'changed_on_5d': None,
                'changed_on_30d': None,
                'locked_5d': False,
                'locked_30d': False,
                'lock_date_5d': None,
                'lock_date_30d': None,
                'last_updated': datetime.now(IST).isoformat(),
                'days_tracked': 0
            }
            
            self.tracking_data[symbol] = stock_data
            self.save_tracking_data()
            
            logger.info(f"Initialized tracking for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing tracking for {symbol}: {str(e)}")
            return False
    
    def update_actual_price(self, symbol, day_index, actual_price):
        """Update actual price for a specific day"""
        try:
            if symbol not in self.tracking_data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False
            
            stock_data = self.tracking_data[symbol]
            
            # Update 5D data if within range
            if day_index < 5:
                stock_data['actual_progress_5d'][day_index] = actual_price
            
            # Update 30D data if within range  
            if day_index < 30:
                stock_data['actual_progress_30d'][day_index] = actual_price
            
            stock_data['last_updated'] = datetime.now(IST).isoformat()
            stock_data['days_tracked'] = max(stock_data.get('days_tracked', 0), day_index + 1)
            
            self.save_tracking_data()
            logger.info(f"Updated actual price for {symbol} day {day_index}: {actual_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating actual price for {symbol}: {str(e)}")
            return False
    
    def update_prediction(self, symbol, period, new_predictions, change_day):
        """Update prediction if change is significant (>3%)"""
        try:
            if symbol not in self.tracking_data:
                return False
            
            stock_data = self.tracking_data[symbol]
            period_key = f'predicted_{period}'
            updated_key = f'updated_prediction_{period}'
            changed_key = f'changed_on_{period}'
            
            if period_key not in stock_data:
                return False
            
            original_predictions = stock_data[period_key]
            
            # Check if change is significant (>3%)
            significant_change = False
            for i, (orig, new) in enumerate(zip(original_predictions, new_predictions)):
                if abs((new - orig) / orig) > 0.03:  # 3% threshold
                    significant_change = True
                    break
            
            if significant_change and not stock_data.get(f'locked_{period}', False):
                # Update predictions from the change day onwards
                updated_predictions = [None] * len(original_predictions)
                for i in range(change_day, len(new_predictions)):
                    updated_predictions[i] = new_predictions[i]
                
                stock_data[updated_key] = updated_predictions
                stock_data[changed_key] = change_day
                stock_data['last_updated'] = datetime.now(IST).isoformat()
                
                self.save_tracking_data()
                logger.info(f"Updated prediction for {symbol} {period} from day {change_day}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating prediction for {symbol}: {str(e)}")
            return False
    
    def update_lock_status(self, symbol, period, locked, timestamp=None):
        """Update lock status for a stock prediction"""
        try:
            if symbol not in self.tracking_data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False
            
            stock_data = self.tracking_data[symbol]
            lock_key = f'locked_{period}'
            lock_date_key = f'lock_date_{period}'
            
            stock_data[lock_key] = locked
            
            if locked:
                stock_data[lock_date_key] = timestamp or datetime.now(IST).isoformat()
            else:
                stock_data[lock_date_key] = None
            
            stock_data['last_updated'] = datetime.now(IST).isoformat()
            
            self.save_tracking_data()
            logger.info(f"Updated lock status for {symbol} {period}: {locked}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lock status for {symbol}: {str(e)}")
            return False
    
    def get_stock_data(self, symbol):
        """Get tracking data for a specific stock"""
        return self.tracking_data.get(symbol, {})
    
    def get_all_tracking_data(self):
        """Get all tracking data"""
        return self.tracking_data
    
    def daily_update(self):
        """Daily update to fetch actual prices and update tracking"""
        try:
            updated_count = 0
            
            for symbol, stock_data in self.tracking_data.items():
                try:
                    # Calculate which day we're on
                    start_date = datetime.strptime(stock_data['start_date'], '%Y-%m-%d')
                    days_elapsed = (datetime.now() - start_date).days
                    
                    if days_elapsed > 0 and days_elapsed <= 30:
                        # Fetch current price
                        ticker = yf.Ticker(f"{symbol}.NS")
                        hist = ticker.history(period="1d")
                        
                        if not hist.empty:
                            current_price = float(hist['Close'].iloc[-1])
                            
                            # Update actual price
                            if self.update_actual_price(symbol, days_elapsed, current_price):
                                updated_count += 1
                
                except Exception as e:
                    logger.warning(f"Error updating {symbol}: {str(e)}")
                    continue
            
            logger.info(f"Daily update completed: {updated_count} stocks updated")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Error in daily update: {str(e)}")
            return False
    
    def cleanup_old_tracking(self, days_threshold=35):
        """Remove tracking data older than threshold"""
        try:
            current_date = datetime.now()
            removed_count = 0
            
            symbols_to_remove = []
            
            for symbol, stock_data in self.tracking_data.items():
                start_date = datetime.strptime(stock_data['start_date'], '%Y-%m-%d')
                days_old = (current_date - start_date).days
                
                if days_old > days_threshold:
                    symbols_to_remove.append(symbol)
            
            for symbol in symbols_to_remove:
                del self.tracking_data[symbol]
                removed_count += 1
            
            if removed_count > 0:
                self.save_tracking_data()
                logger.info(f"Cleaned up {removed_count} old tracking entries")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")
            return 0

    def get_summary_stats(self):
        """Get summary statistics for tracking"""
        try:
            total_stocks = len(self.tracking_data)
            locked_5d = sum(1 for data in self.tracking_data.values() if data.get('locked_5d', False))
            locked_30d = sum(1 for data in self.tracking_data.values() if data.get('locked_30d', False))
            
            active_tracking = sum(1 for data in self.tracking_data.values() 
                                if data.get('days_tracked', 0) > 0)
            
            return {
                'total_stocks': total_stocks,
                'locked_5d': locked_5d,
                'locked_30d': locked_30d,
                'active_tracking': active_tracking,
                'last_updated': datetime.now(IST).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting summary stats: {str(e)}")
            return {}

if __name__ == "__main__":
    # Test the tracker manager
    manager = InteractiveTrackerManager()
    
    # Test initialization
    test_predictions = {
        'pred_5d': 5.0,
        'pred_1mo': 15.0,
        'confidence': 85,
        'score': 75
    }
    
    manager.initialize_stock_tracking('RELIANCE', 1400.0, test_predictions)
    
    # Test data retrieval
    data = manager.get_stock_data('RELIANCE')
    print(f"Test tracking data: {json.dumps(data, indent=2)}")
    
    # Test summary
    summary = manager.get_summary_stats()
    print(f"Summary: {summary}")
