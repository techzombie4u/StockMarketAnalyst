#!/usr/bin/env python3
"""
Main server entry point for the Fusion Stock Analyst API
"""

import os
import sys
import logging
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main server startup function"""
    try:
        logger.info("🚀 Starting Fusion Stock Analyst Server")
        logger.info(f"⏰ Server started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Import and create the Flask app
        from src.core.app import create_app

        app = create_app()

        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))

        logger.info(f"🌐 Server will start on: http://0.0.0.0:{port}")
        logger.info("📊 Available endpoints:")
        logger.info("  - http://0.0.0.0:5000/health")
        logger.info("  - http://0.0.0.0:5000/api/fusion/dashboard")
        logger.info("  - http://0.0.0.0:5000/dashboard")
        logger.info("  - http://0.0.0.0:5000/docs")

        # Start the server
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )

    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()