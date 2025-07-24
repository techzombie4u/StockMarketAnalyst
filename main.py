
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

if __name__ == "__main__":
    main()
