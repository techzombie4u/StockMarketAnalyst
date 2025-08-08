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

        # Import from src structure with error handling
        try:
            from src.core.app import app
            logger.info("✅ Successfully imported app from src.core.app")
        except ImportError:
            logger.warning("⚠️ Fallback: trying alternate import path")
            from core.app import app

        # Print startup information
        print("\n" + "="*60)
        print("📈 STOCK MARKET ANALYST - DASHBOARD")
        print("="*60)
        print(f"🌐 Web Dashboard: http://0.0.0.0:5000")
        print(f"📊 API Endpoint: http://0.0.0.0:5000/api/stocks")
        print(f"🔄 Auto-refresh: Every 60 minutes")
        print("="*60)
        print("\n✅ Application started successfully!")
        print("📱 Open your browser and navigate to the preview URL")
        print("\n🛑 Press Ctrl+C to stop the application\n")

        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )

    except ImportError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("🔧 Please ensure all modules are properly installed")
        
        # Try to create a minimal Flask app as fallback
        try:
            from flask import Flask, jsonify
            app = Flask(__name__)
            
            @app.route('/')
            def home():
                return jsonify({
                    'status': 'error',
                    'message': f'Application modules failed to load: {str(e)}',
                    'solution': 'Please check the application structure and try again'
                })
            
            print(f"🔧 Starting minimal fallback server on port 5000")
            app.run(host='0.0.0.0', port=5000, debug=False)
        except Exception as fallback_error:
            logger.error(f"❌ Even fallback failed: {fallback_error}")
            sys.exit(1)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()