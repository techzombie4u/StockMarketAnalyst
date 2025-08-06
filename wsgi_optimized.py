
#!/usr/bin/env python3
"""
WSGI Optimized Entry Point for Stock Market Analyst
"""

import os
import sys
import logging
import time
import threading

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delayed_scheduler_init():
    """Initialize scheduler after Flask starts"""
    try:
        time.sleep(3)  # Give Flask time to start
        from src.core.scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=60)  # More frequent for production
        logger.info("✅ Production scheduler started successfully")
        
        # Always run initial screening for production (ignore market hours)
        logger.info("🔄 Running initial screening for production deployment")
        try:
            scheduler.run_screening_job_manual()
            logger.info("✅ Initial production screening completed")
        except Exception as screening_error:
            logger.error(f"❌ Initial screening failed: {str(screening_error)}")
            # Create default data if screening fails
            try:
                import json
                from datetime import datetime
                import pytz
                ist = pytz.timezone('Asia/Kolkata')
                now_ist = datetime.now(ist)
                fallback_data = {
                    'timestamp': now_ist.isoformat(),
                    'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
                    'stocks': [],
                    'status': 'fallback',
                    'error': f'Initial screening failed: {str(screening_error)}'
                }
                with open('top10.json', 'w') as f:
                    json.dump(fallback_data, f, indent=2)
                logger.info("📄 Created fallback data file")
            except Exception as fallback_error:
                logger.error(f"❌ Failed to create fallback data: {str(fallback_error)}")
                    
    except Exception as e:
        logger.error(f"❌ Scheduler initialization failed: {str(e)}")

try:
    # Import the Flask app from the organized structure
    from src.core.app import app
    application = app
    
    # Start scheduler in background thread for production
    if os.environ.get('REPL_SLUG') or os.environ.get('REPLIT_DEPLOYMENT'):
        logger.info("🚀 Production environment detected - starting scheduler")
        scheduler_thread = threading.Thread(target=delayed_scheduler_init, daemon=True)
        scheduler_thread.start()
    
    logger.info("✅ WSGI application initialized successfully")
    
except Exception as e:
    logger.error(f"❌ Failed to initialize WSGI application: {str(e)}")
    # Create a minimal Flask app as fallback
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def error_page():
        return f'<h1>Application Error</h1><p>Failed to initialize: {str(e)}</p>'

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000, debug=False)
