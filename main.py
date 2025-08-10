#!/usr/bin/env python3
"""
Stock Market Analyst - Main Application Entry Point
Enhanced with shared-core + product-plugins architecture
Version 1.7.4 - Foundation & Restructure Phase
"""

import os
import sys
import logging

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

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

def main():
    """Main application entry point with new architecture"""
    try:
        logger.info("🚀 Starting Stock Market Analyst Application - New Architecture")

        # Load and display feature flags
        from common_repository.config.feature_flags import feature_flags
        logger.info(f"Feature flags loaded: {feature_flags.get_all_flags()}")

        # Import and run the Flask application
        from src.core.app import create_app

        app = create_app()

        # Set app start time for uptime calculation
        import time
        app.start_time = time.time()

        # Print startup information
        print("\n" + "="*60)
        print("STOCK MARKET ANALYST - VERSION 1.7.4")
        print("SHARED-CORE + PRODUCT-PLUGINS ARCHITECTURE")
        print("="*60)
        print(f"🌐 Web Dashboard: http://localhost:5000")
        print(f"📊 API Endpoints: http://localhost:5000/api/*")
        print(f"🔧 Equity API: http://localhost:5000/api/equity/*")
        print(f"📈 Options API: http://localhost:5000/api/options/*")
        print(f"🔄 Auto-refresh: Every 60 minutes")
        print("="*60)
        print("\n✨ Architecture Features:")
        print("  📦 Shared Core Components")
        print("  🎯 Product-Specific Services")
        print("  🔧 Feature Flags System")
        print("  💾 Enhanced Storage Layer")
        print("  🛡️ Comprehensive Error Handling")
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

    except ImportError as e:
        logger.error(f"Import error: {str(e)}")
        print(f"❌ Import error: {str(e)}")
        print("Please ensure all dependencies are installed.")
        print("If you're seeing import errors for new modules, this is expected during restructure.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Application startup failed: {str(e)}")
        print(f"❌ Application startup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()