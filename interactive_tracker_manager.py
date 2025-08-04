#!/usr/bin/env python3
"""
Interactive Tracker Manager - Enhanced Prediction Tracking

Manages the enhanced prediction tracking system with:
- 5D and 30D view support
- Progressive actual price tracking
- Lock functionality
- Updated prediction tracking
"""

import json
import os
import logging
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')

class InteractiveTrackerManager:
    def __init__(self):
        self.tracking_file = 'interactive_tracking.json'
        self.data = self.load_tracking_data()

    def load_tracking_data(self):
        """Load tracking data from file"""
        try:
            if os.path.exists(self.tracking_file):
                with open(self.tracking_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded tracking data for {len(data)} stocks")
                    return data
            else:
                logger.info("No tracking data file found, creating new structure")
                return {}
        except Exception as e:
            logger.error(f"Error loading tracking data: {str(e)}")
            return {}

    def save_tracking_data(self):
        """Save tracking data to file"""
        try:
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved tracking data for {len(self.data)} stocks")
            return True
        except Exception as e:
            logger.error(f"Error saving tracking data: {str(e)}")
            return False

    def initialize_stock_tracking(self, symbol, current_price, pred_5d, pred_30d, confidence=0, score=0):
        """Initialize tracking for a new stock"""
        try:
            # Generate predicted price arrays
            predicted_5d = []
            predicted_30d = []

            for i in range(5):
                daily_gain = (pred_5d / 100) * (i + 1) / 5
                predicted_5d.append(round(current_price * (1 + daily_gain), 2))

            for i in range(30):
                daily_gain = (pred_30d / 100) * (i + 1) / 30
                predicted_30d.append(round(current_price * (1 + daily_gain), 2))

            self.data[symbol] = {
                'symbol': symbol,
                'start_date': datetime.now(IST).strftime('%Y-%m-%d'),
                'current_price': current_price,
                'confidence': confidence,
                'score': score,
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

            self.save_tracking_data()
            logger.info(f"Initialized tracking for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error initializing tracking for {symbol}: {str(e)}")
            return False

    def update_actual_price(self, symbol, day_index, actual_price, period='5d'):
        """Update actual price for a specific day"""
        try:
            if symbol not in self.data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False

            progress_key = f'actual_progress_{period}'

            if progress_key not in self.data[symbol]:
                logger.error(f"Progress key {progress_key} not found for {symbol}")
                return False

            if day_index < len(self.data[symbol][progress_key]):
                self.data[symbol][progress_key][day_index] = actual_price
                self.data[symbol]['last_updated'] = datetime.now(IST).isoformat()
                self.data[symbol]['days_tracked'] = max(self.data[symbol].get('days_tracked', 0), day_index + 1)

                self.save_tracking_data()
                logger.info(f"Updated actual price for {symbol} day {day_index}: {actual_price}")
                return True
            else:
                logger.error(f"Day index {day_index} out of range for {symbol} {period}")
                return False

        except Exception as e:
            logger.error(f"Error updating actual price for {symbol}: {str(e)}")
            return False

    def update_prediction(self, symbol, new_prediction, period='5d', change_threshold=3.0):
        """Update prediction if change is significant"""
        try:
            if symbol not in self.data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False

            # Check if stock is locked for this period
            lock_key = f'locked_{period}'
            if self.data[symbol].get(lock_key, False):
                logger.info(f"Stock {symbol} is locked for {period}, ignoring prediction update")
                return False

            original_pred_key = f'predicted_{period}'
            updated_pred_key = f'updated_prediction_{period}'
            changed_key = f'changed_on_{period}'

            original_prediction = self.data[symbol].get(original_pred_key, [])
            if not original_prediction:
                logger.error(f"No original prediction found for {symbol} {period}")
                return False

            # Calculate percentage change from original prediction
            final_original = original_prediction[-1]
            final_new = new_prediction[-1] if isinstance(new_prediction, list) else new_prediction

            percent_change = abs((final_new - final_original) / final_original * 100)

            if percent_change >= change_threshold:
                # Store updated prediction
                self.data[symbol][updated_pred_key] = new_prediction
                self.data[symbol][changed_key] = datetime.now(IST).strftime('%Y-%m-%d')
                self.data[symbol]['last_updated'] = datetime.now(IST).isoformat()

                self.save_tracking_data()
                logger.info(f"Updated prediction for {symbol} {period}: {percent_change:.1f}% change")
                return True
            else:
                logger.info(f"Prediction change for {symbol} {period} below threshold: {percent_change:.1f}%")
                return False

        except Exception as e:
            logger.error(f"Error updating prediction for {symbol}: {str(e)}")
            return False

    def update_lock_status(self, symbol, period, locked, timestamp=None):
        """Update lock status for a stock prediction"""
        try:
            if symbol not in self.data:
                logger.warning(f"Stock {symbol} not found in tracking data")
                return False

            lock_key = f'locked_{period}'
            lock_date_key = f'lock_date_{period}'

            self.data[symbol][lock_key] = locked
            self.data[symbol][lock_date_key] = timestamp or datetime.now(IST).isoformat()
            self.data[symbol]['last_updated'] = datetime.now(IST).isoformat()

            self.save_tracking_data()

            status = "locked" if locked else "unlocked"
            logger.info(f"Stock {symbol} {period} prediction {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating lock status for {symbol}: {str(e)}")
            return False

    def get_stock_data(self, symbol):
        """Get tracking data for a specific stock"""
        return self.data.get(symbol, {})

    def get_all_stocks(self):
        """Get all tracked stocks"""
        return list(self.data.keys())

    def get_chart_data(self, symbol, period='5d'):
        """Get formatted data for chart display"""
        try:
            if symbol not in self.data:
                return {}

            stock_data = self.data[symbol]

            # Generate labels (days)
            days = 5 if period == '5d' else 30
            labels = [f"Day {i+1}" for i in range(days)]

            # Get data arrays
            predicted_key = f'predicted_{period}'
            actual_key = f'actual_progress_{period}'
            updated_key = f'updated_prediction_{period}'

            predicted = stock_data.get(predicted_key, [])
            actual = stock_data.get(actual_key, [])
            updated = stock_data.get(updated_key, [])

            return {
                'labels': labels,
                'predicted': predicted,
                'actual': actual,
                'updated': updated,
                'locked': stock_data.get(f'locked_{period}', False),
                'changed_on': stock_data.get(f'changed_on_{period}'),
                'days_tracked': stock_data.get('days_tracked', 0)
            }

        except Exception as e:
            logger.error(f"Error getting chart data for {symbol}: {str(e)}")
            return {}

    def daily_update_job(self):
        """Daily job to update actual prices from market data"""
        try:
            logger.info("Running daily update job for interactive tracker")

            # This would be called by the scheduler
            # For now, just log that it's being called
            updated_count = 0

            for symbol in self.data.keys():
                try:
                    # Here you would fetch actual market data
                    # For now, we'll just log the intention
                    logger.info(f"Would update actual price for {symbol}")
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Error updating {symbol}: {str(e)}")

            logger.info(f"Daily update completed for {updated_count} stocks")
            return True

        except Exception as e:
            logger.error(f"Error in daily update job: {str(e)}")
            return False