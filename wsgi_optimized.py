
import os
import logging
from threading import Thread
import time

# Configure logging for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delayed_scheduler_init():
    """Initialize scheduler after Flask starts"""
    try:
        time.sleep(3)  # Give Flask time to start
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=30)
        logger.info("✅ Production scheduler started successfully")
        
        # Run initial screening if no data exists
        if not os.path.exists('top10.json'):
            logger.info("🔄 Running initial screening for production")
            scheduler.run_screening_job_manual()
            
    except Exception as e:
        logger.error(f"❌ Scheduler initialization failed: {str(e)}")

# Import Flask app
from app import app

# Start scheduler in background thread for production
Thread(target=delayed_scheduler_init, daemon=True).start()

# WSGI application entry point
application = app

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
