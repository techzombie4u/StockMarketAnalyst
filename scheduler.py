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
from stock_screener import StockScreener
from signal_manager import SignalManager
import os

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
    is_within_hours = market_open <= current_time <= market_close

    return is_weekday and is_within_hours

def run_screening_job():
    """Execute stock screening and save results (standalone function)"""
    global alerted_stocks

    try:
        # Check if within market hours for scheduled runs
        if not is_market_hours():
            logger.info("Outside market hours (9 AM - 3:30 PM IST). Skipping scheduled screening.")
            return

        logger.info("Starting scheduled stock screening...")

        try:
            # Create screener instance
            screener = StockScreener()

            # Run the screener
            results = screener.run_screener()
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

        # Save to JSON file
        try:
            with open('top10.json', 'w') as f:
                json.dump(screening_data, f, indent=2)
        except Exception as file_error:
            logger.error(f"Failed to write screening data to file: {str(file_error)}")

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
            with open('top10.json', 'w') as f:
                json.dump(error_data, f, indent=2)
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
        screener = StockScreener()
        signal_manager = SignalManager()

        # Run the screener
        raw_results = screener.run_screener()
        
        # Filter through signal management for stable predictions
        results = signal_manager.filter_trading_signals(raw_results)
        
        logger.info(f"Signal filtering: {len(raw_results)} raw signals → {len(results)} confirmed signals")

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

        # Save to JSON file
        try:
            with open('top10.json', 'w') as f:
                json.dump(screening_data, f, indent=2)
        except Exception as file_error:
            logger.error(f"Failed to write screening data to file: {str(file_error)}")

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
            with open('top10.json', 'w') as f:
                json.dump(error_data, f, indent=2)
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
                with open('top10.json', 'w') as f:
                    json.dump(initial_data, f, indent=2)
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