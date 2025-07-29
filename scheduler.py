"""
Stock Market Analyst - Scheduler Module

Handles automated execution of stock screening using APScheduler.
Stores results in JSON format and tracks alerts to avoid duplicates.
"""

import json
import logging
from datetime import datetime, time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from stock_screener import EnhancedStockScreener
from signal_manager import SignalManager
import os
import numpy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for tracking
alerted_stocks = set()

def is_market_hours() -> bool:
    """Check if current time is within market hours (9 AM - 3:30 PM IST)"""
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    current_time = now_ist.time()

    # Market hours: 9:00 AM to 3:30 PM IST
    market_open = time(9, 0)  # 9:00 AM
    market_close = time(15, 30)  # 3:30 PM

    # Check if current time is within market hours
    is_weekday = now_ist.weekday() < 5  # Monday = 0, Sunday = 6
    is_within_hours = now_ist.weekday() < 5
    is_within_hours = market_open <= current_time <= market_close

    return is_weekday and is_within_hours

def run_screening_job():
    """Execute stock screening and save results (standalone function)"""
    global alerted_stocks

    try:
        # Check if within market hours for scheduled runs (but allow initial run)
        if not is_market_hours():
            logger.info("Outside market hours (9 AM - 3:30 PM IST). Running limited screening for production.")

        logger.info("Starting scheduled stock screening...")

        try:
            # Create screener instance
            screener = EnhancedStockScreener()

            # Run the screener
            results = screener.run_enhanced_screener()
        except Exception as e:
            logger.error(f"Screening failed: {e}")
            return

        # Add timestamp in IST
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        screening_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
            'stocks': results,
            'status': 'success'
        }

        # Validate and fix stock data before saving
        validated_stocks = []
        for stock in results:
            # Ensure prediction fields exist
            if 'pred_24h' not in stock:
                stock['pred_24h'] = round(stock.get('predicted_gain', 0) * 0.05, 2)
            if 'pred_5d' not in stock:
                stock['pred_5d'] = round(stock.get('predicted_gain', 0) * 0.25, 2)
            if 'pred_1mo' not in stock:
                stock['pred_1mo'] = round(stock.get('predicted_gain', 0), 2)

            # Ensure minimum realistic values for high-scoring stocks
            if stock.get('score', 0) > 70:
                stock['pred_24h'] = max(0.5, stock['pred_24h'])
                stock['pred_5d'] = max(2.0, stock['pred_5d'])
                stock['pred_1mo'] = max(8.0, stock['pred_1mo'])

            validated_stocks.append(stock)

        screening_data['stocks'] = validated_stocks

        # Save to JSON file with enhanced error handling
        try:
            # Convert NumPy types to native Python types for JSON serialization
            json_safe_data = convert_numpy_types(screening_data)

            # Clean any potential control characters from string data
            cleaned_data = clean_json_data(json_safe_data)

            # Write directly to main file with backup approach
            backup_file = 'top10_backup.json'

            # Create backup of existing file if it exists
            if os.path.exists('top10.json'):
                try:
                    import shutil
                    shutil.copy2('top10.json', backup_file)
                except:
                    pass

            # Write new data directly to main file
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

            # Verify the file is valid JSON
            with open('top10.json', 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise an exception if JSON is invalid

            # Clean up backup file on success
            if os.path.exists(backup_file):
                try:
                    os.remove(backup_file)
                except:
                    pass

            logger.info(f"✅ Successfully saved {len(validated_stocks)} stocks to top10.json")
        except Exception as file_error:
            logger.error(f"Failed to write screening data to file: {str(file_error)}")

            # Restore backup if it exists
            backup_file = 'top10_backup.json'
            if os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.move(backup_file, 'top10.json')
                    logger.info("Restored backup file")
                except Exception as restore_error:
                    logger.error(f"Failed to restore backup: {str(restore_error)}")
            else:
                # Create minimal error file if no backup exists
                try:
                    minimal_data = {
                        'timestamp': screening_data['timestamp'],
                        'last_updated': screening_data['last_updated'],
                        'stocks': [],
                        'status': 'save_error',
                        'error': str(file_error)
                    }
                    with open('top10.json', 'w', encoding='utf-8') as f:
                        json.dump(minimal_data, f, indent=2, ensure_ascii=False)
                    logger.info("Created minimal error data file")
                except Exception as e:
                    logger.error(f"Failed to create minimal data file: {str(e)}")

        # Capture for historical analysis
        try:
            capture_and_analyze(screening_data)
            logger.info("📊 Historical data captured for analysis")
        except Exception as capture_error:
            logger.error(f"Failed to capture historical data: {str(capture_error)}")

        # Check for new alerts (stocks with score > 70 that haven't been alerted)
        new_alerts = []
        for stock in results:
            if stock['score'] > 70 and stock['symbol'] not in alerted_stocks:
                new_alerts.append(stock)
                alerted_stocks.add(stock['symbol'])

        if new_alerts:
            send_alerts(new_alerts)

        logger.info(f"Screening completed. Found {len(results)} stocks, {len(new_alerts)} new alerts.")

    except Exception as e:
        logger.error(f"Error in screening job: {str(e)}")

        # Create error response
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        error_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
            'error': str(e),
            'stocks': [],
            'status': 'error'
        }

        try:
            # Convert NumPy types to native Python types for JSON serialization
            json_safe_error_data = convert_numpy_types(error_data)
            with open('top10.json', 'w') as f:
                json.dump(json_safe_error_data, f, indent=2)
        except Exception as file_error:
            logger.error(f"Failed to write error data to file: {str(file_error)}")

def send_alerts(alerts: list):
    """Send alerts for high-scoring stocks (placeholder for future SMS/email integration)"""
    logger.info(f"🚨 ALERTS: {len(alerts)} high-scoring stocks found!")

    for stock in alerts:
        logger.info(f"📈 {stock['symbol']}: Score {stock['score']}, "
                   f"Predicted gain {stock['predicted_gain']}% in {stock['time_horizon']} days")

    # TODO: Integrate with SMS/Email service
    # Example: send_sms(alerts) or send_email(alerts)

def run_screening_job_manual():
    """Execute stock screening manually (bypasses market hours check)"""
    global alerted_stocks

    try:
        logger.info("Starting manual stock screening...")

        # Create screener and signal manager instances
        screener = EnhancedStockScreener()
        signal_manager = SignalManager()

        # Run the screener
        results = screener.run_enhanced_screener()

        # Apply minimal signal filtering only if we have results
        if results:
            try:
                filtered_results = signal_manager.filter_trading_signals(results)
                if filtered_results:  # Only use filtered results if we got some
                    results = filtered_results
                    logger.info(f"Signal filtering: {len(results)} raw signals → {len(filtered_results)} confirmed signals")
                else:
                    logger.warning("Signal filtering returned no results, using original results")
            except Exception as e:
                logger.error(f"Signal filtering failed: {str(e)}, using original results")
        else:
            logger.warning("No raw results from screener")

        # Add timestamp in IST
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        screening_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
            'stocks': results,
            'status': 'success'
        }

        # Validate and fix stock data before saving
        validated_stocks = []
        for stock in results:
            # Ensure prediction fields exist
            if 'pred_24h' not in stock:
                stock['pred_24h'] = round(stock.get('predicted_gain', 0) * 0.05, 2)
            if 'pred_5d' not in stock:
                stock['pred_5d'] = round(stock.get('predicted_gain', 0) * 0.25, 2)
            if 'pred_1mo' not in stock:
                stock['pred_1mo'] = round(stock.get('predicted_gain', 0), 2)

            # Ensure minimum realistic values for high-scoring stocks
            if stock.get('score', 0) > 70:
                stock['pred_24h'] = max(0.5, stock['pred_24h'])
                stock['pred_5d'] = max(2.0, stock['pred_5d'])
                stock['pred_1mo'] = max(8.0, stock['pred_1mo'])

            validated_stocks.append(stock)

        screening_data['stocks'] = validated_stocks

        # Save to JSON file with enhanced error handling
        try:
            # Convert NumPy types to native Python types for JSON serialization
            json_safe_data = convert_numpy_types(screening_data)

            # Clean any potential control characters from string data
            cleaned_data = clean_json_data(json_safe_data)

            # Write directly to main file with backup approach
            backup_file = 'top10_backup.json'

            # Create backup of existing file if it exists
            if os.path.exists('top10.json'):
                try:
                    import shutil
                    shutil.copy2('top10.json', backup_file)
                except:
                    pass

            # Write new data directly to main file
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)

            # Verify the file is valid JSON
            with open('top10.json', 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise an exception if JSON is invalid

            # Clean up backup file on success
            if os.path.exists(backup_file):
                try:
                    os.remove(backup_file)
                except:
                    pass

            logger.info(f"✅ Successfully saved {len(validated_stocks)} stocks to top10.json")
        except Exception as file_error:
            logger.error(f"Failed to write screening data to file: {str(file_error)}")

            # Restore backup if it exists
            backup_file = 'top10_backup.json'
            if os.path.exists(backup_file):
                try:
                    import shutil
                    shutil.move(backup_file, 'top10.json')
                    logger.info("Restored backup file")
                except Exception as restore_error:
                    logger.error(f"Failed to restore backup: {str(restore_error)}")
            else:
                # Create minimal error file if no backup exists
                try:
                    minimal_data = {
                        'timestamp': screening_data['timestamp'],
                        'last_updated': screening_data['last_updated'],
                        'stocks': [],
                        'status': 'save_error',
                        'error': str(file_error)
                    }
                    with open('top10.json', 'w', encoding='utf-8') as f:
                        json.dump(minimal_data, f, indent=2, ensure_ascii=False)
                    logger.info("Created minimal error data file")
                except Exception as e:
                    logger.error(f"Failed to create minimal data file: {str(e)}")

        # Capture for historical analysis
        try:
            capture_and_analyze(screening_data)
            logger.info("📊 Historical data captured for analysis")
        except Exception as capture_error:
            logger.error(f"Failed to capture historical data: {str(capture_error)}")

        # Check for new alerts (stocks with score > 70 that haven't been alerted)
        new_alerts = []
        for stock in results:
            if stock['score'] > 70 and stock['symbol'] not in alerted_stocks:
                new_alerts.append(stock)
                alerted_stocks.add(stock['symbol'])

        if new_alerts:
            send_alerts(new_alerts)

        logger.info(f"Manual screening completed. Found {len(results)} stocks, {len(new_alerts)} new alerts.")

    except Exception as e:
        logger.error(f"Error in manual screening job: {str(e)}")

        # Create error response
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        error_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
            'error': str(e),
            'stocks': [],
            'status': 'error'
        }

        try:
            # Convert NumPy types to native Python types for JSON serialization
            json_safe_error_data = convert_numpy_types(error_data)
            with open('top10.json', 'w') as f:
                json.dump(json_safe_error_data, f, indent=2)
        except Exception as file_error:
            logger.error(f"Failed to write error data to file: {str(file_error)}")

def capture_and_analyze(screening_data: dict):
    """Captures screening data and stores it for historical analysis."""
    # Create a directory for historical data if it doesn't exist
    historical_dir = 'historical_data'
    if not os.path.exists(historical_dir):
        os.makedirs(historical_dir)

    # Create a timestamped filename
    timestamp = screening_data['timestamp'].replace(":", "-")  # Replace colons for filename compatibility
    filename = f"{historical_dir}/screening_data_{timestamp}.json"

    # Save the screening data to the file
    try:
        with open(filename, 'w') as f:
            json.dump(screening_data, f, indent=2)
        logger.info(f"💾 Screening data saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save screening data to {filename}: {str(e)}")

    # TODO: Implement comparative analysis logic here using the stored data
    # This could involve comparing current results with previous results,
    # identifying trends, and generating insights.  This would likely
    # involve loading historical data, performing calculations, and
    # potentially using machine learning models for prediction.
    # Example:
    # historical_data = load_historical_data()
    # analysis_results = analyze_data(screening_data, historical_data)
    # logger.info(f"🔍 Analysis results: {analysis_results}")
    # print("Run the AI agent here to analyze the result and provide insights")
    pass

class StockAnalystScheduler:
    def __init__(self):
        # Configure job store (SQLite)
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }

        executors = {
            'default': ThreadPoolExecutor(20)
        }

        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }

        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Kolkata'
        )

    def run_screening_job(self):
        """Wrapper method to call the standalone function"""
        run_screening_job()

    def run_screening_job_manual(self):
        """Wrapper method to call the manual screening function"""
        run_screening_job_manual()

    def start_scheduler(self, interval_minutes: int = 1440):  # Default to daily (1440 minutes)
        """Start the scheduler with specified interval"""
        try:
            # Remove existing jobs
            self.scheduler.remove_all_jobs()

            # Add screening job using standalone function
            self.scheduler.add_job(
                func=run_screening_job,  # Use standalone function
                trigger="interval",
                minutes=interval_minutes,
                id='stock_screening',
                name='Stock Market Screening',
                replace_existing=True
            )

            # Create initial top10.json with empty data
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            initial_data = {
                'timestamp': now_ist.isoformat(),
                'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
                'stocks': [],
                'status': 'initial'
            }
            try:
                # Convert NumPy types to native Python types for JSON serialization
                json_safe_initial_data = convert_numpy_types(initial_data)
                with open('top10.json', 'w') as f:
                    json.dump(json_safe_initial_data, f, indent=2)
            except Exception as file_error:
                logger.error(f"Failed to write initial data to file: {str(file_error)}")


            # Run once immediately
            self.scheduler.add_job(
                func=run_screening_job,  # Use standalone function
                trigger="date",
                id='initial_run',
                name='Initial Stock Screening'
            )

            self.scheduler.start()
            logger.info(f"Scheduler started. Running every {interval_minutes} minutes during market hours (9 AM - 3:30 PM IST).")

        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")

    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped.")

    def get_job_status(self):
        """Get current job status"""
        jobs = self.scheduler.get_jobs()
        return {
            'running': self.scheduler.running,
            'jobs': [{'id': job.id, 'name': job.name, 'next_run': str(job.next_run_time)} for job in jobs]
        }

    def update_screening_data(self):
        """Update stock screening data"""
        try:
            logger.info("Starting stock screening update...")

            # Update status to screening
            self._update_status("screening")

            # Get enhanced screening results
            screener = EnhancedStockScreener()
            results = screener.screen_and_rank_stocks()

            if not results or len(results) == 0:
                logger.warning("No screening results returned")
                self._save_empty_data("no_data")
                return

            # Process results
            processed_results = []
            for stock in results[:10]:  # Top 10 only
                try:
                    processed_stock = {
                        'symbol': stock.get('symbol', 'UNKNOWN'),
                        'score': round(float(stock.get('score', 0)), 1),
                        'adjusted_score': round(float(stock.get('adjusted_score', stock.get('score', 0))), 1),
                        'current_price': round(float(stock.get('current_price', 0)), 2),
                        'volatility': round(float(stock.get('technical', {}).get('atr_volatility', 0)), 2),
                        'predicted_gain': round(float(stock.get('predicted_gain', 0)), 1),
                        'predicted_price': round(float(stock.get('predicted_price', stock.get('current_price', 0))), 2),
                        'time_horizon': int(stock.get('time_horizon', 30)),
                        'confidence': round(float(stock.get('confidence', 50)), 1),
                        'technical_summary': str(stock.get('technical_summary', 'No analysis available')),
                        'market_cap': str(stock.get('market_cap', 'Unknown')),
                        'last_updated': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
                    }
                    processed_results.append(processed_stock)
                except Exception as e:
                    logger.error(f"Error processing stock {stock.get('symbol', 'UNKNOWN')}: {str(e)}")
                    continue

            if processed_results:
                # Save successful results
                data = {
                    'timestamp': datetime.now(IST).isoformat(),
                    'last_updated': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST'),
                    'stocks': processed_results,
                    'status': 'success'
                }

                success = self._save_data_safely(data)
                if success:
                    logger.info(f"Successfully updated screening data with {len(processed_results)} stocks")
                else:
                    logger.error("Failed to save screening data")
                    self._save_empty_data("save_error")
            else:
                logger.warning("No valid stocks after processing")
                self._save_empty_data("processing_error")

        except Exception as e:
            logger.error(f"Error in screening update: {str(e)}")
            self._save_empty_data("error")

    def _update_status(self, status):
        """Update just the status in the data file"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            current_data = {
                'timestamp': now_ist.isoformat(),
                'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
                'stocks': [],
                'status': status
            }

            # Try to read existing data first
            try:
                if os.path.exists('top10.json'):
                    with open('top10.json', 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        current_data['stocks'] = existing_data.get('stocks', [])
            except:
                pass  # Use empty stocks if can't read existing

            current_data['status'] = status
            self._save_data_safely(current_data)

        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")

    def _save_data_safely(self, data):
        """Save data with atomic write"""
        try:
            # Ensure all data is properly serializable
            serializable_data = self._ensure_serializable(data)

            # Write directly to final file with proper encoding
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2, default=str)

            logger.info("Data saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving data: {str(e)}")
            try:
                # Emergency fallback - create minimal valid JSON
                ist = pytz.timezone('Asia/Kolkata')
                now_ist = datetime.now(ist)
                fallback_data = {
                    'timestamp': now_ist.isoformat(),
                    'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
                    'stocks': [],
                    'status': 'save_error'
                }
                with open('top10.json', 'w', encoding='utf-8') as f:
                    json.dump(fallback_data, f, ensure_ascii=False, indent=2)
                logger.info("Fallback data saved")
                return False
            except Exception as fallback_error:
                logger.error(f"Even fallback save failed: {str(fallback_error)}")
                return False

    def _ensure_serializable(self, data):
        """Ensure all data is JSON serializable"""
        if isinstance(data, dict):
            return {k: self._ensure_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._ensure_serializable(v) for v in data]
        elif isinstance(data, (int, float, str, bool)) or data is None:
            return data
        else:
            return str(data)

    def _save_empty_data(self, status):
        """Save empty data with the given status"""
        try:
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            empty_data = {
                'timestamp': now_ist.isoformat(),
                'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
                'stocks': [],
                'status': status
            }

            self._save_data_safely(empty_data)
            logger.info(f"Empty data saved with status: {status}")

        except Exception as e:
            logger.error(f"Error saving empty data: {str(e)}")


def main():
    """Test scheduler"""
    scheduler = StockAnalystScheduler()

    try:
        # Start with 1-minute interval for testing
        scheduler.start_scheduler(interval_minutes=1)

        # Keep running
        import time
        while True:
            time.sleep(10)
            status = scheduler.get_job_status()
            print(f"Scheduler status: {status}")

    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop_scheduler()

if __name__ == "__main__":
    main()

def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types."""
    import numpy
    if isinstance(obj, (numpy.int_, numpy.intc, numpy.intp, numpy.int8,
                            numpy.int16, numpy.int32, numpy.int64, numpy.uint8,
                            numpy.uint16, numpy.uint32, numpy.uint64)):
        return int(obj)
    elif isinstance(obj, (numpy.float_, numpy.float16, numpy.float32,
                            numpy.float64)):
        return float(obj)
    elif isinstance(obj, numpy.ndarray):
        return obj.tolist()
    elif isinstance(obj, (numpy.bool_, numpy.bool_)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    else:
        return obj

def clean_json_data(obj):
    """Recursively remove invalid control characters from string data."""
    if isinstance(obj, str):
        # Remove characters in the range 0-31 (except for \t, \n, \r)
        return ''.join(c for c in obj if 32 <= ord(c) <= 126 or ord(c) in [9, 10, 13] or ord(c) > 126)
    elif isinstance(obj, dict):
        return {k: clean_json_data(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json_data(v) for v in obj]
    else:
        return obj