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
        """Update lock status for a stock prediction with date-locking functionality"""
        try:
            if symbol not in self.tracking_data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False

            stock_data = self.tracking_data[symbol]
            lock_key = f'locked_{period}'
            lock_date_key = f'lock_date_{period}'
            lock_start_date_key = f'lock_start_date_{period}'

            stock_data[lock_key] = locked

            if locked:
                current_time = datetime.now(IST)
                stock_data[lock_date_key] = timestamp or current_time.isoformat()
                
                # Store the exact date when locking occurred for fixed date ranges
                stock_data[lock_start_date_key] = current_time.strftime('%Y-%m-%d')
                
                logger.info(f"🔒 Locked {symbol} {period} with start date: {stock_data[lock_start_date_key]}")
            else:
                stock_data[lock_date_key] = None
                stock_data[lock_start_date_key] = None
                
                logger.info(f"🔓 Unlocked {symbol} {period} - dates will revert to dynamic")

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

    def update_daily_actual_prices(self):
        """Fetch real market closing prices and update tracking data"""
        try:
            logger.info("🔄 Starting daily actual price update from market data...")
            
            current_ist = datetime.now(IST)
            updated_stocks = []
            failed_stocks = []
            
            for symbol, stock_data in self.tracking_data.items():
                try:
                    # Calculate which trading day we're on
                    start_date = datetime.strptime(stock_data['start_date'], '%Y-%m-%d')
                    start_date_ist = IST.localize(start_date)
                    
                    # Calculate trading days elapsed (excluding weekends)
                    trading_days_elapsed = self.calculate_trading_days(start_date_ist, current_ist)
                    
                    if trading_days_elapsed > 0 and trading_days_elapsed <= 30:
                        # Check if market has closed today (after 3:30 PM IST)
                        market_close_time = current_ist.replace(hour=15, minute=30, second=0, microsecond=0)
                        
                        if current_ist >= market_close_time or current_ist.weekday() >= 5:
                            # Fetch real closing price from Yahoo Finance
                            real_price = self.fetch_real_closing_price(symbol)
                            
                            if real_price:
                                # Update actual price for this trading day
                                success = self.update_actual_price(symbol, trading_days_elapsed - 1, real_price)
                                
                                if success:
                                    updated_stocks.append({
                                        'symbol': symbol,
                                        'day': trading_days_elapsed - 1,
                                        'price': real_price,
                                        'timestamp': current_ist.isoformat()
                                    })
                                    logger.info(f"✅ {symbol}: Updated Day {trading_days_elapsed-1} with real price ₹{real_price:.2f}")
                                else:
                                    failed_stocks.append(symbol)
                            else:
                                failed_stocks.append(symbol)
                                logger.warning(f"⚠️ {symbol}: Could not fetch real price")
                        else:
                            logger.info(f"⏳ {symbol}: Market hasn't closed yet (current: {current_ist.strftime('%H:%M')})")
                    
                except Exception as e:
                    logger.warning(f"❌ Error updating {symbol}: {str(e)}")
                    failed_stocks.append(symbol)
                    continue

            logger.info(f"📊 Daily update completed: {len(updated_stocks)} updated, {len(failed_stocks)} failed")
            
            return {
                'updated_stocks': updated_stocks,
                'failed_stocks': failed_stocks,
                'update_time': current_ist.isoformat(),
                'total_updated': len(updated_stocks)
            }

        except Exception as e:
            logger.error(f"❌ Error in daily actual price update: {str(e)}")
            return {'error': str(e)}

    def fetch_real_closing_price(self, symbol):
        """Fetch real closing price from Yahoo Finance"""
        try:
            # Try different ticker formats for Indian stocks
            ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]
            
            for ticker_format in ticker_formats:
                try:
                    ticker = yf.Ticker(ticker_format)
                    # Get last 2 days to ensure we get the latest closing price
                    hist = ticker.history(period="2d", interval="1d")
                    
                    if not hist.empty and len(hist) > 0:
                        # Get the most recent closing price
                        latest_close = float(hist['Close'].iloc[-1])
                        logger.info(f"  📈 {symbol}: Fetched real price ₹{latest_close:.2f} using {ticker_format}")
                        return latest_close
                        
                except Exception as e:
                    logger.debug(f"  Failed {ticker_format}: {str(e)}")
                    continue
            
            logger.warning(f"  ❌ All ticker formats failed for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching real price for {symbol}: {str(e)}")
            return None

    def calculate_trading_days(self, start_date, end_date):
        """Calculate number of trading days between two dates (excluding weekends)"""
        try:
            trading_days = 0
            current = start_date
            
            while current.date() < end_date.date():
                # Monday = 0, Sunday = 6. Trading days are Mon-Fri (0-4)
                if current.weekday() < 5:  # Monday to Friday
                    trading_days += 1
                current += timedelta(days=1)
            
            return trading_days
            
        except Exception as e:
            logger.error(f"Error calculating trading days: {str(e)}")
            return 0

    def is_market_open_today(self):
        """Check if market is open today (weekdays only)"""
        current_ist = datetime.now(IST)
        return current_ist.weekday() < 5  # Monday = 0, Friday = 4

    def get_next_market_close_time(self):
        """Get next market close time (3:30 PM IST on next trading day)"""
        current_ist = datetime.now(IST)
        
        # If today is a trading day and market hasn't closed
        if self.is_market_open_today():
            market_close_today = current_ist.replace(hour=15, minute=30, second=0, microsecond=0)
            if current_ist < market_close_today:
                return market_close_today
        
        # Find next trading day
        next_day = current_ist + timedelta(days=1)
        while next_day.weekday() >= 5:  # Skip weekends
            next_day += timedelta(days=1)
            
        return next_day.replace(hour=15, minute=30, second=0, microsecond=0)

    def daily_update(self):
        """Legacy method - redirects to new real market data update"""
        return self.update_daily_actual_prices()

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

    def generate_locked_date_labels(self, symbol, period):
        """Generate fixed date labels for locked predictions"""
        try:
            if symbol not in self.tracking_data:
                return []

            stock_data = self.tracking_data[symbol]
            lock_start_date_key = f'lock_start_date_{period}'
            locked_key = f'locked_{period}'

            # Only generate locked dates if prediction is actually locked
            if not stock_data.get(locked_key, False) or not stock_data.get(lock_start_date_key):
                return []

            # Parse the lock start date
            lock_start_date = datetime.strptime(stock_data[lock_start_date_key], '%Y-%m-%d')
            
            # Determine number of days based on period
            days = 5 if period == '5d' else 30
            
            # Generate absolute date labels from lock start date
            labels = []
            current_date = lock_start_date
            added_days = 0
            
            while added_days < days:
                # Only add trading days (Monday to Friday)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    labels.append(current_date.strftime('%b %d'))  # e.g., "Aug 4"
                    added_days += 1
                current_date += timedelta(days=1)
            
            logger.info(f"📅 Generated locked date labels for {symbol} {period}: {lock_start_date_key} -> {len(labels)} dates")
            return labels

        except Exception as e:
            logger.error(f"Error generating locked date labels for {symbol}: {str(e)}")
            return []

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