"""Integrate backtesting into screening job"""
"""Fixing the date format for JavaScript compatibility by changing the date format string in the screening_data dictionary."""
"""Removing signal timeout handling to avoid threading issues in the stock screening process."""
"""
Stock Market Analyst - Scheduler Module

Handles automated screening with APScheduler and data persistence.
"""

import json
import os
import time
import logging
import pytz
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import numpy as np
import threading

logger = logging.getLogger(__name__)

# Global set to track alerted stocks (avoid duplicate alerts)
alerted_stocks = set()

# Global variables for session tracking
total_sessions_run = 0
successful_sessions = 0

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def clean_json_data(data):
    """Clean data for JSON serialization"""
    try:
        # Convert to JSON string and back to remove any problematic characters
        json_str = json.dumps(data, ensure_ascii=False)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error cleaning JSON data: {str(e)}")
        return data

def is_market_hours():
    """Check if current time is within Indian market hours (9 AM - 3:30 PM IST)"""
    try:
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)

        start_time = now_ist.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)

        return start_time <= now_ist <= end_time
    except Exception:
        return True  # Default to True if timezone calculation fails

def send_alerts(stocks):
    """Send alerts for high-scoring stocks (placeholder for future implementation)"""
    for stock in stocks:
        logger.info(f"🚨 HIGH SCORE ALERT: {stock['symbol']} - Score: {stock['score']}")

def record_successful_session(num_stocks, status):
    """Records a successful screening session."""
    global total_sessions_run, successful_sessions
    total_sessions_run += 1
    if status == 'success' and num_stocks > 0:
        successful_sessions += 1
    logger.info(f"Session recorded: Total runs={total_sessions_run}, Successful runs={successful_sessions}")

def run_screening_job():
    """Execute stock screening and save results (standalone function)"""
    global alerted_stocks, total_sessions_run, successful_sessions

    try:
        logger.info("Starting scheduled stock screening...")

        # Import here to avoid circular imports
        from src.analyzers.stock_screener import EnhancedStockScreener

        # Create screener instance
        screener = EnhancedStockScreener()

        # Run screening with better error handling
        start_time = time.time()
        results = []
        session_status = 'error' # Default status
        try:
            # Check if screener is properly initialized
            if not hasattr(screener, 'under500_symbols'):
                logger.error("Screener not properly initialized")
                results = screener._generate_fallback_data()
                session_status = 'fallback_error'
            else:
                results = screener.run_enhanced_screener()
                session_status = 'success' # Assuming success if no exception

        except SyntaxError as se:
            logger.error(f"Syntax error in screener: {se}")
            results = screener._generate_fallback_data() if screener else []
            session_status = 'syntax_error'
        except Exception as e:
            logger.error(f"Screening failed: {e}")
            # Try fallback data generation
            try:
                results = screener._generate_fallback_data() if screener else []
                session_status = 'fallback_generated'
            except:
                results = []
                session_status = 'failed'

        # Add timestamp in IST
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)

        if results and len(results) > 0:
            # Validate and process results
            valid_results = []
            for stock in results:
                if isinstance(stock, dict) and 'symbol' in stock:
                    # Ensure all required fields
                    if 'score' not in stock:
                        stock['score'] = 50.0
                    if 'current_price' not in stock:
                        stock['current_price'] = 0.0
                    if 'predicted_gain' not in stock:
                        stock['predicted_gain'] = stock.get('score', 50) * 0.2

                    # Ensure prediction fields
                    stock['pred_24h'] = round(stock.get('predicted_gain', 0) * 0.05, 2)
                    stock['pred_5d'] = round(stock.get('predicted_gain', 0) * 0.25, 2)
                    stock['pred_1mo'] = round(stock.get('predicted_gain', 0), 2)

                    valid_results.append(stock)

            if valid_results:
                # Save results with timestamp
                results_data = {
                    'status': session_status, # Use the determined session status
                    'stocks': valid_results,
                    'last_updated': now_ist.strftime('%d/%m/%Y, %H:%M:%S'),
                    'timestamp': now_ist.isoformat(),
                    'total_stocks': len(valid_results),
                    'screening_time': f"{time.time() - start_time:.2f} seconds"
                }

                # Record successful session based on status and number of stocks
                record_successful_session(len(valid_results), results_data.get('status'))

                # Record predictions for backtesting
                try:
                    from src.managers.backtesting_manager import BacktestingManager
                    backtester = BacktestingManager()
                    for stock in valid_results:
                        backtester.record_prediction(stock)
                    logger.info("Predictions recorded for backtesting")
                except Exception as bt_error:
                    logger.warning(f"Failed to record predictions for backtesting: {str(bt_error)}")

                try:
                    json_safe_data = convert_numpy_types(results_data)
                    with open('top10.json', 'w', encoding='utf-8') as f:
                        json.dump(json_safe_data, f, indent=2, ensure_ascii=False)

                    logger.info(f"✅ Screening completed successfully with {len(valid_results)} stocks")

                    # Check for alerts
                    new_alerts = [s for s in valid_results if s['score'] > 70 and s['symbol'] not in alerted_stocks]
                    if new_alerts:
                        for alert in new_alerts:
                            alerted_stocks.add(alert['symbol'])
                        send_alerts(new_alerts)

                    return True

                except Exception as save_error:
                    logger.error(f"Failed to save results: {save_error}")

            else:
                logger.warning("No valid results after processing")
                session_status = 'no_valid_results' # Update status if no valid results

        else:
            logger.warning("No results from screening")
            session_status = 'no_results' # Update status if no results

        # Record session outcome even if there were no results or valid results
        record_successful_session(len(results) if 'results' in locals() and results is not None else 0, session_status)

        # Save empty/error state
        error_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%d/%m/%Y, %H:%M:%S'),
            'stocks': [],
            'status': session_status if 'session_status' in locals() else 'unknown_error'
        }

        try:
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save error state: {e}")

        return False

    except Exception as e:
        logger.error(f"Critical error in screening job: {str(e)}")

        # Emergency fallback - create minimal data
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            emergency_data = {
                'timestamp': now_ist.isoformat(),
                'last_updated': now_ist.strftime('%d/%m/%Y, %H:%M:%S'),
                'stocks': [],
                'status': 'critical_error',
                'error': str(e)[:200]
            }

            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(emergency_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        return False

def run_screening_job_manual():
    """Execute stock screening manually (bypasses market hours check)"""
    logger.info("Manual screening requested")
    return run_screening_job()

class StockAnalystScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone=pytz.timezone('Asia/Kolkata'))

    def configure_scheduler(self):
        """Configure the scheduler timezone"""
        self.scheduler.configure(timezone=pytz.timezone('Asia/Kolkata'))

    def run_initial_screening(self):
        """Run an initial screening job when the scheduler starts"""
        def delayed_initial_run():
            time.sleep(10)  # Wait 10 seconds for app to fully initialize
            try:
                logger.info("Running initial screening...")
                success = run_screening_job()
                if success:
                    logger.info("✅ Initial screening completed successfully")
                else:
                    logger.warning("⚠️ Initial screening had issues")
            except Exception as e:
                logger.error(f"Initial screening failed: {e}")
        threading.Thread(target=delayed_initial_run, daemon=True).start()

    def schedule_market_close_update(self):
        """Schedule the daily job to fetch market close prices"""
        try:
            self.scheduler.add_job(
                func=self.run_daily_tracker_update,
                trigger='cron',
                hour=16,  # 4:00 PM IST
                minute=0,
                id='daily_market_close_update',
                name='Daily Market Close Data Update',
                replace_existing=True,
                misfire_grace_time=600 # 10 minutes grace period
            )
            logger.info("Scheduled daily market close update for 4:00 PM IST.")
        except Exception as e:
            logger.error(f"❌ Error scheduling market close update: {str(e)}")

    def start_scheduler(self, interval_minutes=60):
        """Start the APScheduler with specified interval"""
        try:
            # Configure scheduler
            self.configure_scheduler()

            # Add the main screening job
            self.scheduler.add_job(
                func=run_screening_job,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='stock_screening',
                name='Stock Screening Job',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=300  # 5 minutes grace period
            )

            # Schedule daily market close data update
            self.schedule_market_close_update()

            # Start scheduler
            self.scheduler.start()
            logger.info(f"✅ Scheduler started with {interval_minutes} minute intervals")
            logger.info("✅ Market close data update scheduled for 4:00 PM IST daily")

            # Run initial screening
            self.run_initial_screening()

            return True

        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {str(e)}")
            return False

    def stop_scheduler(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Scheduler stopped.")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")

    def get_job_status(self):
        """Get current job status"""
        try:
            jobs = self.scheduler.get_jobs()
            return {
                'running': self.scheduler.running,
                'jobs': [{'id': job.id, 'name': job.name, 'next_run': str(job.next_run_time)} for job in jobs]
            }
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {'running': False, 'jobs': []}

    def run_screening_job_manual(self):
        """Run screening manually"""
        try:
            return run_screening_job_manual()
        except Exception as e:
            logger.error(f"Manual screening failed: {e}")
            return False

    def run_backtesting_job(self):
        """Run backtesting analysis job"""
        try:
            logger.info("Starting backtesting analysis...")

            from src.managers.backtesting_manager import BacktestingManager
            backtester = BacktestingManager()

            # Run backtest analysis
            results = backtester.run_backtest_analysis()

            if results and results.get('status') == 'success':
                logger.info(f"✅ Backtesting completed: {results.get('summary', {}).get('total_predictions', 0)} predictions analyzed")
            else:
                logger.warning("⚠️ Backtesting completed with limited results")

        except Exception as e:
            logger.error(f"❌ Backtesting job failed: {str(e)}")
            return False

    def run_daily_tracker_update(self):
        """Run daily tracker update job"""
        try:
            logger.info("Starting daily tracker update...")

            from src.managers.interactive_tracker_manager import InteractiveTrackerManager
            tracker_manager = InteractiveTrackerManager()

            # Update daily actual prices for all tracked stocks
            update_summary = tracker_manager.update_daily_actual_prices()

            if update_summary and 'error' not in update_summary:
                updated_count = len(update_summary.get('updated_stocks', []))
                failed_count = len(update_summary.get('failed_stocks', []))
                logger.info(f"✅ Daily tracker update completed: {updated_count} updated, {failed_count} failed")

                # Initialize tracking for any new stocks from latest screening
                self.initialize_new_stock_tracking(tracker_manager)

            else:
                logger.warning("⚠️ Daily tracker update completed with issues")

        except Exception as e:
            logger.error(f"❌ Daily tracker update job failed: {str(e)}")
            return False

    def initialize_new_stock_tracking(self, tracker_manager):
        """Initialize tracking for new stocks from latest screening"""
        try:
            # Load current stock data
            if os.path.exists('top10.json'):
                with open('top10.json', 'r') as f:
                    data = json.load(f)
                    stocks = data.get('stocks', [])

                    for stock in stocks:
                        symbol = stock.get('symbol')
                        if symbol:
                            # Initialize if not already tracking
                            tracker_manager.initialize_stock_tracking(symbol, stock)

                logger.info(f"Checked tracking initialization for {len(stocks)} stocks")

        except Exception as e:
            logger.warning(f"Error initializing new stock tracking: {str(e)}")

def main():
    """Test scheduler"""
    scheduler = StockAnalystScheduler()

    try:
        # Start with 1-minute interval for testing
        scheduler.start_scheduler(interval_minutes=1)

        # Keep running
        while True:
            time.sleep(10)
            status = scheduler.get_job_status()
            print(f"Scheduler status: {status}")

    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop_scheduler()

if __name__ == "__main__":
    main()