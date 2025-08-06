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

# Global dictionary to hold prediction data, keyed by symbol
# This is used by generate_sample_tracking_data to potentially merge with existing data
predictionData = {}

class InteractiveTrackerManager:
    def __init__(self):
        self.data_file = 'interactive_tracking.json'
        self.tracking_data = {}
        self.load_tracking_data()

    def load_tracking_data(self):
        """Load existing tracking data and merge with current stocks"""
        try:
            # Load existing tracking data
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            parsed_data = json.loads(content)
                            # Validate that it's a dictionary
                            if isinstance(parsed_data, dict):
                                self.tracking_data = parsed_data
                                logger.info(f"Loaded existing tracking data for {len(self.tracking_data)} stocks")
                                # Populate global predictionData from loaded tracking_data
                                global predictionData
                                predictionData = self.tracking_data.copy()
                            else:
                                logger.warning("Invalid tracking data format, initializing empty")
                                self.tracking_data = {}
                                predictionData = {}
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error in tracking data: {str(e)}")
                            # Try to recover from backup or initialize empty
                            backup_file = f"{self.data_file}.backup"
                            if os.path.exists(backup_file):
                                logger.info("Attempting to restore from backup")
                                try:
                                    with open(backup_file, 'r', encoding='utf-8') as bf:
                                        backup_content = bf.read().strip()
                                        if backup_content:
                                            restored_data = json.loads(backup_content)
                                            if isinstance(restored_data, dict):
                                                self.tracking_data = restored_data
                                                predictionData = self.tracking_data.copy()
                                                logger.info("Successfully restored from backup")
                                            else:
                                                logger.warning("Backup data invalid, initializing empty")
                                                self.tracking_data = {}
                                                predictionData = {}
                                        else:
                                            self.tracking_data = {}
                                            predictionData = {}
                                except Exception as backup_restore_error:
                                    logger.warning(f"Backup restoration failed: {str(backup_restore_error)}, initializing empty")
                                    self.tracking_data = {}
                                    predictionData = {}
                            else:
                                self.tracking_data = {}
                                predictionData = {}
                    else:
                        self.tracking_data = {}
                        predictionData = {}
            else:
                self.tracking_data = {}
                predictionData = {}

            # Always ensure current top stocks are tracked
            self._ensure_current_stocks_tracked()

            return self.tracking_data

        except Exception as e:
            logger.error(f"Error loading tracking data: {str(e)}")
            self.tracking_data = {}
            predictionData = {}
            return {}

    def _ensure_current_stocks_tracked(self):
        """Ensure current top-performing stocks are being tracked"""
        try:
            # Load current stock data
            if os.path.exists('top10.json'):
                with open('top10.json', 'r') as f:
                    current_data = json.load(f)
                    current_stocks = current_data.get('stocks', [])

                    # Add tracking for top stocks that aren't already tracked
                    for stock in current_stocks[:10]:  # Track top 10 stocks
                        symbol = stock.get('symbol')
                        if symbol and symbol not in self.tracking_data:
                            logger.info(f"🔄 Auto-initializing tracking for {symbol}")
                            predictions = {
                                'pred_5d': stock.get('pred_5d', 0),
                                'pred_1mo': stock.get('pred_1mo', 0),
                                'confidence': stock.get('confidence', 0),
                                'score': stock.get('score', 0)
                            }
                            self.initialize_stock_tracking(symbol, stock.get('current_price', 100), predictions)

        except Exception as e:
            logger.warning(f"Could not ensure current stocks tracked: {str(e)}")

    def save_tracking_data(self):
        """Save tracking data to file with improved atomic write and backup strategy"""
        try:
            import tempfile
            import shutil

            # Create backup before saving
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                try:
                    shutil.copy2(self.data_file, backup_file)
                except Exception as backup_error:
                    logger.warning(f"Could not create backup: {backup_error}")

            # Use a unique temporary file to avoid conflicts
            import time
            temp_file = f"{self.data_file}.tmp_{int(time.time())}"

            try:
                # Write to temporary file with validation
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tracking_data, f, indent=2, ensure_ascii=False)

                # Validate the written file
                with open(temp_file, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                    if not isinstance(test_data, dict):
                        raise ValueError("Invalid data structure in temp file")

                # Atomic move to replace original file
                if os.path.exists(self.data_file):
                    # On Windows, remove target file first
                    try:
                        os.remove(self.data_file)
                    except OSError:
                        pass

                shutil.move(temp_file, self.data_file)
                logger.info(f"Tracking data saved successfully with {len(self.tracking_data)} stocks")
                return True

            except Exception as write_error:
                logger.error(f"Error during file write: {write_error}")
                # Clean up temp file
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
                raise write_error

        except Exception as e:
            logger.error(f"Error saving tracking data: {str(e)}")
            return False

    def initialize_stock_tracking(self, symbol, current_price, predictions):
        """Initialize tracking for a new stock"""
        try:
            # Generate predicted price arrays based on predictions
            pred_5d = predictions.get('pred_5d', 2.0)  # Default to 2% if missing
            pred_30d = predictions.get('pred_1mo', 5.0)  # Default to 5% if missing

            logger.info(f"Generating tracking data for {symbol}: base_price={current_price}, pred_5d={pred_5d}%, pred_30d={pred_30d}%")

            predicted_5d_arr = []
            predicted_30d_arr = []

            # Generate 5-day predictions (straight line from start to end)
            final_price_5d = current_price * (1 + pred_5d / 100)
            for i in range(5):
                if i == 0:
                    # First day is current price
                    predicted_5d_arr.append(current_price)
                else:
                    # Linear progression from day 1 to day 4
                    progress = i / 4  # Linear progression from day 0 to day 4
                    predicted_price = current_price + (final_price_5d - current_price) * progress
                    predicted_5d_arr.append(predicted_price)

            # Generate 30-day predictions (straight line from start to end)
            final_price_30d = current_price * (1 + pred_30d / 100)
            for i in range(30):
                if i == 0:
                    # First day is current price
                    predicted_30d_arr.append(current_price)
                else:
                    # Linear progression from day 1 to day 29
                    progress = i / 29  # Linear progression from day 0 to day 29
                    predicted_price = current_price + (final_price_30d - current_price) * progress
                    predicted_30d_arr.append(predicted_price)

            logger.info(f"Generated prediction arrays: 5d={len(predicted_5d_arr)} points ({predicted_5d_arr[0]:.2f} -> {predicted_5d_arr[-1]:.2f}), 30d={len(predicted_30d_arr)} points ({predicted_30d_arr[0]:.2f} -> {predicted_30d_arr[-1]:.2f})")

            stock_data = {
                'symbol': symbol,
                'start_date': datetime.now(IST).strftime('%Y-%m-%d'),
                'current_price': current_price,
                'confidence': predictions.get('confidence', 75),
                'score': predictions.get('score', 65),
                'pred_5d': pred_5d,  # Store original prediction percentages
                'pred_1mo': pred_30d,
                'predicted_5d': predicted_5d_arr,
                'predicted_30d': predicted_30d_arr,
                'actual_progress_5d': [current_price] + [None] * 4,
                'actual_progress_30d': [current_price] + [None] * 29,
                'updated_prediction_5d': [None] * 5,
                'updated_prediction_30d': [None] * 30,
                'changed_on_5d': None,
                'changed_on_30d': None,
                'locked_5d': False,
                'locked_30d': False,
                'persistent_lock_5d': False,
                'persistent_lock_30d': False,
                'lock_date_5d': None,
                'lock_date_30d': None,
                'lock_start_date_5d': None,
                'lock_start_date_30d': None,
                'last_updated': datetime.now(IST).isoformat(),
                'days_tracked': 0,
                'timestamp': datetime.now(IST).isoformat()
            }

            logger.info(f"Initialized tracking for {symbol}")
            self.tracking_data[symbol] = stock_data
            # Also update the global predictionData
            global predictionData
            predictionData[symbol] = stock_data
            self.save_tracking_data()

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
            if 0 <= day_index < 5:
                stock_data['actual_progress_5d'][day_index] = float(actual_price)

            # Update 30D data if within range
            if 0 <= day_index < 30:
                stock_data['actual_progress_30d'][day_index] = float(actual_price)

            stock_data['last_updated'] = datetime.now(IST).isoformat()
            stock_data['days_tracked'] = max(stock_data.get('days_tracked', 0), day_index + 1)

            self.save_tracking_data()
            logger.info(f"Updated actual price for {symbol} day {day_index}: {actual_price}")
            return True

        except Exception as e:
            logger.error(f"Error updating actual price for {symbol}: {str(e)}")
            return False

    def update_prediction(self, symbol, period, new_predictions_list, change_day):
        """Update prediction if change is significant (>3%)"""
        try:
            if symbol not in self.tracking_data:
                return False

            stock_data = self.tracking_data[symbol]
            period_key = f'predicted_{period}'
            updated_key = f'updated_prediction_{period}'
            changed_key = f'changed_on_{period}'

            if period_key not in stock_data or not isinstance(stock_data[period_key], list):
                logger.warning(f"Stock {symbol} or {period_key} not found or not a list.")
                return False

            original_predictions = stock_data[period_key]

            # Ensure new_predictions_list is of the correct length and contains numbers
            if len(new_predictions_list) != len(original_predictions):
                logger.warning(f"New predictions list length mismatch for {symbol} {period}. Expected {len(original_predictions)}, got {len(new_predictions_list)}.")
                return False
            
            valid_new_predictions = []
            for pred_val in new_predictions_list:
                try:
                    valid_new_predictions.append(float(pred_val))
                except (ValueError, TypeError):
                    valid_new_predictions.append(None) # Or some other indicator for invalid data

            # Check if change is significant (>3%)
            significant_change = False
            for i in range(min(len(original_predictions), len(valid_new_predictions))):
                orig = original_predictions[i]
                new = valid_new_predictions[i]
                if orig is not None and new is not None:
                    if abs((new - orig) / orig) > 0.03:  # 3% threshold
                        significant_change = True
                        break

            if significant_change and not stock_data.get(f'locked_{period}', False):
                # Update predictions from the change day onwards
                current_updated_predictions = stock_data.get(updated_key, [None] * len(original_predictions))
                
                for i in range(change_day, len(valid_new_predictions)):
                    if i < len(current_updated_predictions): # Ensure index is within bounds
                        current_updated_predictions[i] = valid_new_predictions[i]

                stock_data[updated_key] = current_updated_predictions
                stock_data[changed_key] = change_day
                stock_data['last_updated'] = datetime.now(IST).isoformat()

                self.save_tracking_data()
                logger.info(f"Updated prediction for {symbol} {period} from day {change_day}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating prediction for {symbol}: {str(e)}")
            return False

    def update_lock_status(self, symbol, period, locked, timestamp=None, persistent=True):
        """Update lock status for a stock prediction with indefinite persistence and robust error handling"""
        try:
            # Ensure stock is tracked before updating lock status
            if symbol not in self.tracking_data:
                logger.warning(f"Stock {symbol} not found - auto-initializing...")
                success = self._auto_initialize_stock(symbol)
                if not success:
                    logger.error(f"Failed to initialize tracking for {symbol}")
                    return False

            if symbol not in self.tracking_data:
                logger.error(f"Still no tracking data for {symbol} after initialization")
                return False

            stock_data = self.tracking_data[symbol]
            lock_key = f'locked_{period}'
            lock_date_key = f'lock_date_{period}'
            lock_start_date_key = f'lock_start_date_{period}'
            persistent_key = f'persistent_lock_{period}'

            # Store previous state for rollback
            previous_state = {
                lock_key: stock_data.get(lock_key, False),
                lock_date_key: stock_data.get(lock_date_key),
                lock_start_date_key: stock_data.get(lock_start_date_key),
                persistent_key: stock_data.get(persistent_key, False)
            }

            try:
                # Update lock status
                stock_data[lock_key] = locked
                stock_data[persistent_key] = persistent

                if locked:
                    current_time = datetime.now(IST)
                    stock_data[lock_date_key] = timestamp or current_time.isoformat()

                    # Store the exact date when locking occurred for fixed date ranges
                    stock_data[lock_start_date_key] = current_time.strftime('%Y-%m-%d')

                    logger.info(f"🔒 {'PERSISTENT' if persistent else 'TEMPORARY'} LOCK: {symbol} {period} with start date: {stock_data[lock_start_date_key]}")
                else:
                    stock_data[lock_date_key] = None
                    stock_data[lock_start_date_key] = None
                    stock_data[persistent_key] = False

                    logger.info(f"🔓 Unlocked {symbol} {period} - dates will revert to dynamic")

                stock_data['last_updated'] = datetime.now(IST).isoformat()

                # Save with retry mechanism
                save_attempts = 0
                max_attempts = 3

                while save_attempts < max_attempts:
                    save_success = self.save_tracking_data()
                    if save_success:
                        break

                    save_attempts += 1
                    logger.warning(f"Save attempt {save_attempts} failed for {symbol} {period}")

                    if save_attempts < max_attempts:
                        import time
                        time.sleep(0.5)  # Wait before retry

                if save_attempts >= max_attempts:
                    # Rollback changes
                    for key, value in previous_state.items():
                        stock_data[key] = value
                    logger.error(f"Failed to save lock status for {symbol} {period} after {max_attempts} attempts")
                    return False

                logger.info(f"✅ Successfully updated lock status for {symbol} {period}: {locked} (persistent: {persistent})")
                return True

            except Exception as update_error:
                # Rollback changes
                for key, value in previous_state.items():
                    stock_data[key] = value
                logger.error(f"Error during lock status update for {symbol} {period}: {update_error}")
                return False

        except Exception as e:
            logger.error(f"Critical error updating lock status for {symbol} {period}: {str(e)}")
            return False

    def _auto_initialize_stock(self, symbol):
        """Auto-initialize tracking for a stock from current data"""
        try:
            # Load current stock data to get details for this symbol
            if os.path.exists('top10.json'):
                with open('top10.json', 'r') as f:
                    current_data = json.load(f)
                    current_stocks = current_data.get('stocks', [])

                    for stock in current_stocks:
                        if stock.get('symbol') == symbol:
                            predictions = {
                                'pred_5d': stock.get('pred_5d', 0),
                                'pred_1mo': stock.get('pred_1mo', 0),
                                'confidence': stock.get('confidence', 0),
                                'score': stock.get('score', 0)
                            }
                            return self.initialize_stock_tracking(symbol, stock.get('current_price', 100), predictions)

            # Fallback initialization if stock not found in current data
            logger.warning(f"Stock {symbol} not found in current data - using fallback initialization")
            fallback_predictions = {
                'pred_5d': 2.0,
                'pred_1mo': 8.0,
                'confidence': 75,
                'score': 65
            }
            return self.initialize_stock_tracking(symbol, 100.0, fallback_predictions)

        except Exception as e:
            logger.error(f"Error auto-initializing {symbol}: {str(e)}")
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
                    start_date_str = stock_data.get('start_date')
                    if not start_date_str:
                        logger.warning(f"Skipping {symbol}: missing 'start_date'")
                        continue
                    
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
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
                start_date_str = stock_data.get('start_date')
                if not start_date_str:
                    logger.warning(f"Skipping cleanup for {symbol}: missing 'start_date'")
                    continue
                
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                    days_old = (current_date - start_date).days

                    if days_old > days_threshold:
                        symbols_to_remove.append(symbol)
                except ValueError:
                    logger.warning(f"Skipping cleanup for {symbol}: invalid 'start_date' format")
                    continue

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

            # Check if lock has expired
            if not self._is_lock_still_valid(symbol, period):
                return []

            # Only generate locked dates if prediction is actually locked
            if not stock_data.get(locked_key, False) or not stock_data.get(lock_start_date_key):
                return []

            # Parse the lock start date
            lock_start_date_str = stock_data.get(lock_start_date_key)
            if not lock_start_date_str:
                return []
            
            try:
                lock_start_date = datetime.strptime(lock_start_date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid lock start date format for {symbol} {period}: {lock_start_date_str}")
                return []


            # Determine number of trading days based on period
            trading_days = 5 if period == '5d' else 30

            # Generate absolute date labels from lock start date
            labels = []
            current_date = lock_start_date
            added_trading_days = 0

            while added_trading_days < trading_days:
                # Only add trading days (Monday to Friday)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    labels.append(current_date.strftime('%b %d'))  # e.g., "Aug 4"
                    added_trading_days += 1
                current_date += timedelta(days=1)

            logger.info(f"📅 Generated locked date labels for {symbol} {period}: {added_trading_days} trading days")
            return labels

        except Exception as e:
            logger.error(f"Error generating locked date labels for {symbol}: {str(e)}")
            return []

    def _is_lock_still_valid(self, symbol, period):
        """Check if a lock is still valid - persistent locks never auto-expire"""
        try:
            if symbol not in self.tracking_data:
                return False

            stock_data = self.tracking_data[symbol]
            locked_key = f'locked_{period}'
            lock_start_date_key = f'lock_start_date_{period}'
            persistent_key = f'persistent_lock_{period}'

            if not stock_data.get(locked_key, False) or not stock_data.get(lock_start_date_key):
                return False

            # Check if this is a persistent lock
            is_persistent = stock_data.get(persistent_key, True)  # Default to persistent for backward compatibility

            if is_persistent:
                # Persistent locks never auto-expire - only manual unlock
                logger.debug(f"🔒 Persistent lock active for {symbol} {period} - will not auto-expire")
                return True

            # For non-persistent locks, use the old behavior
            lock_start_date_str = stock_data.get(lock_start_date_key)
            if not lock_start_date_str:
                return False
            
            try:
                lock_start_date = datetime.strptime(lock_start_date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Invalid lock start date format for {symbol} {period} during validity check: {lock_start_date_str}")
                return False

            lock_start_date_ist = IST.localize(lock_start_date)
            current_ist = datetime.now(IST)

            trading_days_elapsed = self.calculate_trading_days(lock_start_date_ist, current_ist)
            trading_days_limit = 5 if period == '5d' else 30

            # Auto-expire non-persistent lock if trading days limit exceeded
            if trading_days_elapsed >= trading_days_limit:
                logger.info(f"🔓 Auto-expiring temporary lock for {symbol} {period} - {trading_days_elapsed} trading days elapsed")
                stock_data[locked_key] = False
                stock_data[lock_start_date_key] = None
                stock_data[f'lock_date_{period}'] = None
                stock_data[persistent_key] = False
                self.save_tracking_data()
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking lock validity for {symbol}: {str(e)}")
            return False

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

    def generate_sample_tracking_data(self, symbol, pred, existing_data=None):
        """Generate comprehensive sample tracking data with proper numeric arrays"""
        try:
            base_price = float(pred.get('current_price', 100))
            pred_5d = float(pred.get('pred_5d', 2.0))
            pred_30d = float(pred.get('pred_1mo', 8.0))

            logger.info(f"🔧 Generating sample data for {symbol}: base={base_price}, 5d={pred_5d}%, 30d={pred_30d}%")

            # Calculate predicted final prices
            predicted_5d_final_price = base_price * (1 + pred_5d/100)
            predicted_30d_final_price = base_price * (1 + pred_30d/100)

            # Generate 5D predicted data - STRAIGHT line
            predicted_5d = []
            for i in range(5):
                if i == 0:
                    predicted_5d.append(base_price)
                else:
                    progress = i / 4.0  # Linear progression 0 to 1
                    price = base_price + (predicted_5d_final_price - base_price) * progress
                    predicted_5d.append(float(price))

            # Generate 30D predicted data - STRAIGHT line
            predicted_30d = []
            for i in range(30):
                if i == 0:
                    predicted_30d.append(base_price)
                else:
                    progress = i / 29.0  # Linear progression 0 to 1
                    price = base_price + (predicted_30d_final_price - base_price) * progress
                    predicted_30d.append(float(price))

            # Generate actual progress data (progressive real market data)
            actual_5d = [base_price, None, None, None, None]
            actual_30d = [base_price] + [None] * 29

            # Simulate some actual market data for demonstration
            current_date = datetime.now(IST)
            market_closed = current_date.hour >= 15 and current_date.minute >= 30

            if market_closed and current_date.weekday() < 5:  # Market closed on trading day
                # Add one day of actual data
                actual_5d[1] = base_price * (0.98 + 0.04 * (hash(symbol) % 100) / 100)
                actual_30d[1] = actual_5d[1]

            # Generate updated predictions (red line) - incremental from change day
            updated_5d = [None] * 5
            updated_30d = [None] * 30

            # Some stocks get prediction updates
            stock_hash = hash(symbol) % 4
            if stock_hash == 0:  # 25% of stocks get prediction updates
                change_day_5d = 1
                new_final_5d = predicted_5d_final_price * 1.08  # 8% higher prediction

                for i in range(change_day_5d, 5):
                    if actual_5d[change_day_5d] is not None:
                        remaining_days = 4 - change_day_5d
                        if remaining_days > 0:
                            day_progress = (i - change_day_5d) / remaining_days
                            updated_5d[i] = actual_5d[change_day_5d] + (new_final_5d - actual_5d[change_day_5d]) * day_progress

                change_day_30d = 3
                new_final_30d = predicted_30d_final_price * 0.92  # 8% lower prediction

                for i in range(change_day_30d, 30):
                    if actual_30d[change_day_30d] is not None:
                        remaining_days = 29 - change_day_30d
                        if remaining_days > 0:
                            day_progress = (i - change_day_30d) / remaining_days
                            updated_30d[i] = actual_30d[change_day_30d] + (new_final_30d - actual_30d[change_day_30d]) * day_progress

            logger.info(f"✅ Generated arrays: 5d_pred={len(predicted_5d)}, 30d_pred={len(predicted_30d)}, valid_5d={sum(1 for x in predicted_5d if x is not None)}, valid_30d={sum(1 for x in predicted_30d if x is not None)}")

            # Merge with existing data if provided, preserving lock states
            base_data = existing_data or predictionData.get(symbol, {})

            # Create comprehensive stock data structure
            stock_data = {
                'symbol': symbol,
                'current_price': base_price,
                'confidence': pred.get('confidence', 75),
                'score': pred.get('score', 65),
                'pred_5d': pred_5d,
                'pred_1mo': pred_30d,
                'predicted_5d': predicted_5d,
                'predicted_30d': predicted_30d,
                'actual_progress_5d': actual_5d,
                'actual_progress_30d': actual_30d,
                'updated_prediction_5d': updated_5d,
                'updated_prediction_30d': updated_30d,
                'changed_on_5d': 1 if any(x is not None for x in updated_5d) else None,
                'changed_on_30d': 3 if any(x is not None for x in updated_30d) else None,
                # Preserve existing lock states
                'locked_5d': base_data.get('locked_5d', False),
                'locked_30d': base_data.get('locked_30d', False),
                'persistent_lock_5d': base_data.get('persistent_lock_5d', False),
                'persistent_lock_30d': base_data.get('persistent_lock_30d', False),
                'lock_date_5d': base_data.get('lock_date_5d'),
                'lock_date_30d': base_data.get('lock_date_30d'),
                'lock_start_date_5d': base_data.get('lock_start_date_5d'),
                'lock_start_date_30d': base_data.get('lock_start_date_30d'),
                'start_date': datetime.now(IST).strftime('%Y-%m-%d'),
                'last_updated': datetime.now(IST).isoformat(),
                'days_tracked': 0,
                'timestamp': datetime.now(IST).isoformat()
            }

            # Update global prediction data
            predictionData[symbol] = stock_data

            logger.info(f"✅ Generated complete sample data for {symbol} with {len(predicted_5d)} 5D and {len(predicted_30d)} 30D points")
            return stock_data

        except Exception as e:
            logger.error(f"Error generating sample data for {symbol}: {str(e)}")
            return None


if __name__ == "__main__":
    # Test the tracker manager
    manager = InteractiveTrackerManager()

    # Test initialization with sample data generation
    sample_pred_reliance = {
        'current_price': 1400.0,
        'pred_5d': 5.0,
        'pred_1mo': 15.0,
        'confidence': 85,
        'score': 75
    }
    manager.initialize_stock_tracking('RELIANCE', sample_pred_reliance['current_price'], sample_pred_reliance)
    
    # Also generate and store sample data using the new method
    generated_sample_data = manager.generate_sample_tracking_data('RELIANCE', sample_pred_reliance)
    if generated_sample_data:
        manager.tracking_data['RELIANCE'] = generated_sample_data
        print(f"Sample data generated and stored for RELIANCE.")

    # Test data retrieval
    data = manager.get_stock_data('RELIANCE')
    print(f"Test tracking data for RELIANCE: {json.dumps(data, indent=2)}")

    # Test summary
    summary = manager.get_summary_stats()
    print(f"Summary: {summary}")

    # Example of updating actual price
    # Assuming 'RELIANCE' was tracked for 5 days and today is the 2nd day of tracking
    # manager.update_actual_price('RELIANCE', 1, 1415.50) # Update day 1 with price 1415.50

    # Example of updating prediction
    # new_5d_predictions = [1400.0, 1410.0, 1420.0, 1430.0, 1440.0] # Example updated 5-day predictions
    # manager.update_prediction('RELIANCE', '5d', new_5d_predictions, 1) # Update 5-day prediction from day 1

    # Example of updating lock status
    # manager.update_lock_status('RELIANCE', '5d', True, persistent=True) # Lock 5-day prediction
    # manager.update_lock_status('RELIANCE', '5d', False) # Unlock 5-day prediction