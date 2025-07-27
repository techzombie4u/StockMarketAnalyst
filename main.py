#!/usr/bin/env python3
"""
Stock Market Analyst - Main Application Entry Point

This application provides:
1. Automated stock screening of Indian markets
2. Real-time dashboard with Flask web interface
3. Scheduled data collection and analysis
4. Technical and fundamental analysis scoring

Run this file to start the complete application.
"""

import os
import sys
import logging
from initialize import initialize_system
from app import app, initialize_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    logger.info("🚀 Starting Stock Market Analyst Application")

    try:
        # Initialize system files and settings
        if not initialize_system():
            logger.error("❌ System initialization failed")
            sys.exit(1)

        # Run system health check
        health_check_result = run_system_health_check()
        if not health_check_result:
            logger.warning("⚠️ Some system components may not be working optimally")

        # Initialize the application (starts scheduler)
        initialize_app()

        # Print startup information
        print("\n" + "="*60)
        print("📈 STOCK MARKET ANALYST - AI-ENHANCED DASHBOARD")
        print("="*60)
        print(f"🌐 Web Dashboard: http://localhost:5000")
        print(f"📊 API Endpoint: http://localhost:5000/api/stocks")
        print(f"⚡ Auto-refresh: Every 1 hour")
        print(f"🔄 Screening: Every 1 hour (Market Hours: 9 AM - 4 PM IST)")
        print(f"📈 Stocks: Top 38 Indian stocks under ₹1000")
        print(f"🤖 AI Features: LSTM Price Prediction + Random Forest Direction")
        print("="*60)
        print("💡 Tips:")
        print("  - Click 'Refresh Now' for manual updates")
        print("  - Run 'python train_models.py' to train ML models")
        print("  - ML predictions enhance traditional scoring")
        print("  - Check browser console for any errors")
        print("="*60)
        print("\n✅ Application started successfully!")
        print("📱 Open your browser and navigate to http://localhost:5000")
        print("\n🛑 Press Ctrl+C to stop the application\n")

        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False  # Disable reloader to prevent duplicate scheduler
        )

    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        sys.exit(1)

def run_system_health_check():
    """Run comprehensive system health check"""
    try:
        print("🔧 Running system health check...")

        # Check if required files exist
        required_files = ['stock_screener.py', 'scheduler.py', 'app.py', 'templates/index.html']
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ Missing required file: {file}")
                return False

        # Test stock screener functionality
        from stock_screener import StockScreener
        screener = StockScreener()
        print("✅ Stock screener module loaded successfully")

        # Test scheduler functionality
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        print("✅ Scheduler module loaded successfully")

        # Create directories if they don't exist
        os.makedirs('historical_data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        print("✅ Required directories created/verified")

        print("✅ System health check completed successfully")
        return True

    except Exception as e:
        print(f"❌ System health check failed: {str(e)}")
        return False

if __name__ == "__main__":
    main()