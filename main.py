#!/usr/bin/env python3
"""
Stock Market Analyst - Main Entry Point
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application"""
    try:
        logger.info("🚀 Starting Stock Market Analyst Application")

        # Import and run the Flask app
        from src.core.app import app, initialize_app

        # Initialize the application
        initialize_app()

        # Print startup information
        print("\n" + "="*60)
        print("📈 STOCK MARKET ANALYST - DASHBOARD")
        print("="*60)
        print(f"🌐 Web Dashboard: http://localhost:5000")
        print(f"📊 API Endpoint: http://localhost:5000/api/stocks")
        print(f"🔄 Auto-refresh: Every 60 minutes")
        print("="*60)
        print("\n✅ Application started successfully!")
        print("📱 Open your browser and navigate to http://localhost:5000")
        print("\n🛑 Press Ctrl+C to stop the application\n")

        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )

    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("Please check the logs for more details.")
        sys.exit(1)

if __name__ == '__main__':
    main()