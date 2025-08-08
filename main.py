#!/usr/bin/env python3
"""
Stock Market Analyst - Main Entry Point
Version 1.7.4 - Consolidated Structure
"""

import os
import sys
import logging
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_logging():
    """Configure logging for the application"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main application entry point"""
    try:
        setup_logging()
        logger = logging.getLogger(__name__)

        logger.info("🚀 Starting Stock Market Analyst - Version 1.7.4 (Consolidated)")
        logger.info("📁 Using consolidated /src/ structure")

        # Import from src structure
        from core.app import app

        # Run the Flask application
        if __name__ == '__main__':
            app.run(
                host='0.0.0.0',
                port=5000,
                debug=False,
                threaded=True
            )

    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("🔧 Please ensure all modules are properly installed")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()