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

# Add the root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.initialize import initialize_system
from src.core.app import app, initialize_app

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
        print(f"📈 Stocks: Top 50 Indian stocks under ₹500")
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
        import socket
        port = 5000
        
        # Check if port is available, find alternative if needed
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            if result == 0:
                logger.warning(f"Port {port} is in use, attempting cleanup...")
                # Try to find available port
                for test_port in range(5000, 5010):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.bind(('0.0.0.0', test_port))
                        sock.close()
                        port = test_port
                        logger.info(f"Using port {port}")
                        break
                    except:
                        continue
        except:
            pass
        
        app.run(
            host='0.0.0.0',
            port=port,
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

        # Check if required files exist in organized structure
        required_files = [
            'src/analyzers/stock_screener.py', 
            'src/core/scheduler.py', 
            'src/core/app.py', 
            'web/templates/templates/index.html'
        ]
        
        all_exist = True
        for file in required_files:
            if not os.path.exists(file):
                print(f"❌ Missing required file: {file}")
                all_exist = False
            else:
                print(f"✅ Found: {file}")
        
        if not all_exist:
            return False

        # Test stock screener functionality
        from src.analyzers.stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        screener.calculate_enhanced_technical_indicators('RELIANCE')
        print("✅ Stock screener working")
        return True
    except Exception as e:
        print(f"❌ System health check failed: {str(e)}")
        return False

if __name__ == "__main__":
    main()