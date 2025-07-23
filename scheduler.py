
"""
Stock Market Analyst - Scheduler Module

Handles automated execution of stock screening using APScheduler.
Stores results in JSON format and tracks alerts to avoid duplicates.
"""

import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from stock_screener import StockScreener

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        self.screener = StockScreener()
        self.alerted_stocks = set()
        
    def run_screening_job(self):
        """Execute stock screening and save results"""
        try:
            logger.info("Starting scheduled stock screening...")
            
            # Run the screener
            results = self.screener.run_screener()
            
            # Add timestamp
            screening_data = {
                'timestamp': datetime.now().isoformat(),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'stocks': results
            }
            
            # Save to JSON file
            with open('top10.json', 'w') as f:
                json.dump(screening_data, f, indent=2)
            
            # Check for new alerts (stocks with score > 70 that haven't been alerted)
            new_alerts = []
            for stock in results:
                if stock['score'] > 70 and stock['symbol'] not in self.alerted_stocks:
                    new_alerts.append(stock)
                    self.alerted_stocks.add(stock['symbol'])
            
            if new_alerts:
                self.send_alerts(new_alerts)
            
            logger.info(f"Screening completed. Found {len(results)} stocks, {len(new_alerts)} new alerts.")
            
        except Exception as e:
            logger.error(f"Error in screening job: {str(e)}")
            
            # Create error response
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': str(e),
                'stocks': []
            }
            
            with open('top10.json', 'w') as f:
                json.dump(error_data, f, indent=2)
    
    def send_alerts(self, alerts: list):
        """Send alerts for high-scoring stocks (placeholder for future SMS/email integration)"""
        logger.info(f"🚨 ALERTS: {len(alerts)} high-scoring stocks found!")
        
        for stock in alerts:
            logger.info(f"📈 {stock['symbol']}: Score {stock['score']}, "
                       f"Predicted gain {stock['predicted_gain']}% in {stock['time_horizon']} days")
        
        # TODO: Integrate with SMS/Email service
        # Example: send_sms(alerts) or send_email(alerts)
    
    def start_scheduler(self, interval_minutes: int = 30):
        """Start the scheduler with specified interval"""
        try:
            # Remove existing jobs
            self.scheduler.remove_all_jobs()
            
            # Add screening job
            self.scheduler.add_job(
                func=self.run_screening_job,
                trigger="interval",
                minutes=interval_minutes,
                id='stock_screening',
                name='Stock Market Screening',
                replace_existing=True
            )
            
            # Run once immediately
            self.scheduler.add_job(
                func=self.run_screening_job,
                trigger="date",
                id='initial_run',
                name='Initial Stock Screening'
            )
            
            self.scheduler.start()
            logger.info(f"Scheduler started. Running every {interval_minutes} minutes.")
            
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
