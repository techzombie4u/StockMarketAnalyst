
"""
Interactive Tracker Manager

Handles progressive tracking data, lock management, and daily updates for the interactive prediction tracker.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import pytz

logger = logging.getLogger(__name__)

# Timezone for India
IST = pytz.timezone('Asia/Kolkata')

class InteractiveTrackerManager:
    def __init__(self):
        self.tracking_file = 'interactive_tracking.json'
        self.daily_updates_file = 'daily_tracker_updates.json'
        
    def initialize_stock_tracking(self, symbol: str, initial_data: Dict) -> bool:
        """Initialize tracking for a new stock"""
        try:
            tracking_data = self.load_tracking_data()
            
            if symbol not in tracking_data:
                base_price = initial_data.get('current_price', 100)
                pred_5d = initial_data.get('pred_5d', 0)
                pred_30d = initial_data.get('pred_1mo', 0)
                
                # Generate predicted price arrays
                predicted_5d = []
                predicted_30d = []
                
                for i in range(5):
                    predicted_5d.append(base_price * (1 + (pred_5d/100) * (i+1)/5))
                
                for i in range(30):
                    predicted_30d.append(base_price * (1 + (pred_30d/100) * (i+1)/30))
                
                tracking_data[symbol] = {
                    'symbol': symbol,
                    'start_date': datetime.now(IST).strftime('%Y-%m-%d'),
                    'current_price': base_price,
                    'confidence': initial_data.get('confidence', 0),
                    'score': initial_data.get('score', 0),
                    
                    # Prediction arrays
                    'predicted_5d': predicted_5d,
                    'predicted_30d': predicted_30d,
                    
                    # Actual progress (null initially, filled as days pass)
                    'actual_progress_5d': [base_price] + [None] * 4,
                    'actual_progress_30d': [base_price] + [None] * 29,
                    
                    # Updated predictions (only if change > 3%)
                    'updated_prediction_5d': [None] * 5,
                    'updated_prediction_30d': [None] * 30,
                    
                    # Change tracking
                    'changed_on_5d': None,
                    'changed_on_30d': None,
                    'change_threshold': 3.0,  # 3% threshold
                    
                    # Lock status
                    'locked_5d': False,
                    'locked_30d': False,
                    'lock_date_5d': None,
                    'lock_date_30d': None,
                    
                    # Metadata
                    'last_updated': datetime.now(IST).isoformat(),
                    'days_tracked': 0
                }
                
                self.save_tracking_data(tracking_data)
                logger.info(f"Initialized tracking for {symbol}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing tracking for {symbol}: {str(e)}")
            return False
    
    def update_daily_actual_prices(self) -> Dict:
        """Update actual prices for all tracked stocks"""
        try:
            tracking_data = self.load_tracking_data()
            update_summary = {
                'updated_stocks': [],
                'failed_stocks': [],
                'total_processed': 0,
                'timestamp': datetime.now(IST).isoformat()
            }
            
            for symbol, data in tracking_data.items():
                try:
                    # Calculate days since start
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
                    days_passed = (datetime.now(IST).date() - start_date.date()).days
                    
                    if days_passed <= 0:
                        continue  # Same day, no update needed
                    
                    # Get current market price
                    current_price = self.fetch_current_price(symbol)
                    
                    if current_price:
                        # Update 5D tracking if within period and not locked
                        if days_passed <= 5 and not data.get('locked_5d', False):
                            if days_passed < len(data['actual_progress_5d']):
                                data['actual_progress_5d'][days_passed] = current_price
                        
                        # Update 30D tracking if within period and not locked
                        if days_passed <= 30 and not data.get('locked_30d', False):
                            if days_passed < len(data['actual_progress_30d']):
                                data['actual_progress_30d'][days_passed] = current_price
                        
                        # Check for prediction changes
                        self.check_prediction_changes(symbol, data, days_passed, current_price)
                        
                        data['current_price'] = current_price
                        data['days_tracked'] = days_passed
                        data['last_updated'] = datetime.now(IST).isoformat()
                        
                        update_summary['updated_stocks'].append(symbol)
                        logger.info(f"Updated daily price for {symbol}: ₹{current_price}")
                    else:
                        update_summary['failed_stocks'].append(symbol)
                        logger.warning(f"Could not fetch price for {symbol}")
                    
                    update_summary['total_processed'] += 1
                    
                except Exception as e:
                    logger.error(f"Error updating {symbol}: {str(e)}")
                    update_summary['failed_stocks'].append(symbol)
            
            # Save updated tracking data
            self.save_tracking_data(tracking_data)
            
            # Save update summary
            self.save_daily_update_summary(update_summary)
            
            logger.info(f"Daily update completed: {len(update_summary['updated_stocks'])} updated, {len(update_summary['failed_stocks'])} failed")
            return update_summary
            
        except Exception as e:
            logger.error(f"Error in daily update: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.now(IST).isoformat()}
    
    def fetch_current_price(self, symbol: str) -> Optional[float]:
        """Fetch current market price for a symbol"""
        try:
            # Add .NS suffix for Indian stocks if not present
            yf_symbol = symbol if symbol.endswith('.NS') else f"{symbol}.NS"
            
            ticker = yf.Ticker(yf_symbol)
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            
            return None
            
        except Exception as e:
            logger.warning(f"Error fetching price for {symbol}: {str(e)}")
            return None
    
    def check_prediction_changes(self, symbol: str, data: Dict, day_index: int, current_price: float):
        """Check if predictions need to be updated due to significant changes"""
        try:
            threshold = data.get('change_threshold', 3.0) / 100  # Convert % to decimal
            
            # Check 5D predictions
            if day_index < 5 and not data.get('locked_5d', False):
                original_pred = data['predicted_5d'][day_index] if day_index < len(data['predicted_5d']) else current_price
                price_change = abs(current_price - original_pred) / original_pred
                
                if price_change > threshold and data.get('changed_on_5d') is None:
                    # Significant change detected, start tracking updated predictions
                    data['changed_on_5d'] = day_index
                    self.generate_updated_predictions(data, '5d', day_index, current_price)
                    logger.info(f"{symbol}: 5D prediction change detected on day {day_index + 1}")
            
            # Check 30D predictions
            if day_index < 30 and not data.get('locked_30d', False):
                original_pred = data['predicted_30d'][day_index] if day_index < len(data['predicted_30d']) else current_price
                price_change = abs(current_price - original_pred) / original_pred
                
                if price_change > threshold and data.get('changed_on_30d') is None:
                    # Significant change detected, start tracking updated predictions
                    data['changed_on_30d'] = day_index
                    self.generate_updated_predictions(data, '30d', day_index, current_price)
                    logger.info(f"{symbol}: 30D prediction change detected on day {day_index + 1}")
            
        except Exception as e:
            logger.error(f"Error checking prediction changes for {symbol}: {str(e)}")
    
    def generate_updated_predictions(self, data: Dict, period: str, start_day: int, current_price: float):
        """Generate updated predictions from the day of change"""
        try:
            period_days = 5 if period == '5d' else 30
            updated_key = f'updated_prediction_{period}'
            original_key = f'predicted_{period}'
            
            # Calculate new trajectory based on current price and remaining days
            remaining_days = period_days - start_day
            if remaining_days <= 0:
                return
            
            # Use original final target but adjust trajectory
            original_final = data[original_key][-1]
            current_to_target_change = (original_final - current_price) / current_price
            
            # Generate updated predictions from current day to end
            for i in range(start_day, period_days):
                days_remaining = period_days - i
                if days_remaining > 0:
                    progress = (period_days - i) / remaining_days
                    updated_price = current_price * (1 + current_to_target_change * (1 - progress))
                    data[updated_key][i] = updated_price
            
            logger.info(f"Generated updated {period} predictions from day {start_day + 1}")
            
        except Exception as e:
            logger.error(f"Error generating updated predictions: {str(e)}")
    
    def update_lock_status(self, symbol: str, period: str, locked: bool, timestamp: str = None) -> bool:
        """Update lock status for a stock prediction"""
        try:
            tracking_data = self.load_tracking_data()
            
            if symbol not in tracking_data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False
            
            lock_key = f'locked_{period}'
            date_key = f'lock_date_{period}'
            
            tracking_data[symbol][lock_key] = locked
            tracking_data[symbol][date_key] = timestamp.split('T')[0] if locked and timestamp else None
            tracking_data[symbol]['last_updated'] = datetime.now(IST).isoformat()
            
            self.save_tracking_data(tracking_data)
            
            logger.info(f"Lock status updated: {symbol} {period} = {locked}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lock status: {str(e)}")
            return False
    
    def get_tracking_summary(self) -> Dict:
        """Get summary of all tracking data"""
        try:
            tracking_data = self.load_tracking_data()
            
            summary = {
                'total_stocks': len(tracking_data),
                'locked_5d': 0,
                'locked_30d': 0,
                'active_tracking': 0,
                'stocks_with_changes': 0,
                'timestamp': datetime.now(IST).isoformat()
            }
            
            for symbol, data in tracking_data.items():
                if data.get('locked_5d'):
                    summary['locked_5d'] += 1
                if data.get('locked_30d'):
                    summary['locked_30d'] += 1
                if data.get('days_tracked', 0) > 0:
                    summary['active_tracking'] += 1
                if data.get('changed_on_5d') is not None or data.get('changed_on_30d') is not None:
                    summary['stocks_with_changes'] += 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting tracking summary: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.now(IST).isoformat()}
    
    def load_tracking_data(self) -> Dict:
        """Load tracking data from file"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"Could not load tracking data: {str(e)}")
            return {}
    
    def save_tracking_data(self, data: Dict):
        """Save tracking data to file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving tracking data: {str(e)}")
    
    def save_daily_update_summary(self, summary: Dict):
        """Save daily update summary"""
        try:
            # Load existing summaries
            summaries = []
            if os.path.exists(self.daily_updates_file):
                with open(self.daily_updates_file, 'r') as f:
                    summaries = json.load(f)
            
            # Add new summary
            summaries.append(summary)
            
            # Keep only last 30 days of summaries
            summaries = summaries[-30:]
            
            # Save updated summaries
            with open(self.daily_updates_file, 'w') as f:
                json.dump(summaries, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving daily update summary: {str(e)}")
