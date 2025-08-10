#!/usr/bin/env python3
"""
Stock Market Analyst - Main Application Entry Point
Enhanced with shared-core + product-plugins architecture
Version 1.7.4 - Foundation & Restructure Phase
"""

import os
import sys
import logging
import threading
import time

# Add current directory and src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, current_dir)
sys.path.insert(0, src_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a')
    ]
)

logger = logging.getLogger(__name__)

# Placeholder for delayed_scheduler_init if it were defined elsewhere
def delayed_scheduler_init():
    """Placeholder for scheduler initialization"""
    logger.info("Scheduler initialized (placeholder)")


# This is the entry point for the script when run directly
if __name__ == "__main__":
    try:
        print("🚀 Starting Stock Analyst Application...")

        # Initialize the application
        from src.core.initialize import initialize_application
        initialize_application()

        # Create Flask app
        from src.core.app import create_app
        app = create_app()

        # Run the application
        print("✅ Application initialized successfully")
        print("🌐 Server starting on http://0.0.0.0:5000")
        print("📊 Main Dashboard: http://0.0.0.0:5000/")
        print("🔥 Fusion Dashboard: http://0.0.0.0:5000/fusion-dashboard")
        app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)

    except Exception as e:
        print(f"❌ Failed to start application: {str(e)}")
        import traceback
        traceback.print_exc()
else:
    # For WSGI deployment (e.g., Gunicorn, uWSGI)
    # Import the Flask app from the organized structure
    from src.core.app import app
    application = app
    logger.info("✅ WSGI application initialized successfully")