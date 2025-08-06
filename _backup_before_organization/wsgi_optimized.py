
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
                logger.error(f"❌ Fallback data creation failed: {str(fallback_error)}")
            
    except Exception as e:
        logger.error(f"❌ Scheduler initialization failed: {str(e)}")

# Import Flask app with error handling
try:
    from src.core.app import create_app
    application = create_app()
except ImportError:
    try:
        from src.core.app import app
        application = app
    except Exception as e:
        import logging
        logging.error(f"Failed to import app: {str(e)}")
        # Create minimal Flask app as fallback
        from flask import Flask
        application = Flask(__name__)
        @application.route('/health')
        def health():
            return {'status': 'error', 'message': str(e)}
except Exception as e:
    import logging
    logging.error(f"Critical error importing app: {str(e)}")
    # Create minimal Flask app as fallback
    from flask import Flask
    application = Flask(__name__)
    @application.route('/health')
    def health():
        return {'status': 'critical_error', 'message': str(e)}

# Start scheduler in background thread for production
Thread(target=delayed_scheduler_init, daemon=True).start()

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5000)
