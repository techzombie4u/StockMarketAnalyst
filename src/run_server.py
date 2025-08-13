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

        # Initialize system components
        try:
            from src.core.initialize import initialize_application
            initialize_application()
            logger.info("✅ System components initialized")
        except Exception as e:
            logger.warning(f"⚠️ System initialization warning: {str(e)}")

        # Import and create the Flask app
        from src.core.app import create_app

        app = create_app()

        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        
        # Test if port is available
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('0.0.0.0', port))
            sock.close()
        except OSError:
            logger.warning(f"Port {port} might be in use, attempting to start anyway...")

        logger.info(f"🌐 Server will start on: http://0.0.0.0:{port}")
        logger.info("📊 Available endpoints:")
        logger.info("  - http://0.0.0.0:5000/health")
        logger.info("  - http://0.0.0.0:5000/api/fusion/dashboard")
        logger.info("  - http://0.0.0.0:5000/dashboard")
        logger.info("  - http://0.0.0.0:5000/papertrade")
        logger.info("  - http://0.0.0.0:5000/docs")

        # Start the server with better error handling
        try:
            app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                threaded=True,
                use_reloader=False
            )
        except OSError as e:
            if "Address already in use" in str(e):
                logger.error("❌ Port 5000 is already in use. Please stop other processes using this port.")
                logger.error("   You can try: pkill -f 'python.*run_server.py' or lsof -ti:5000 | xargs kill -9")
            else:
                logger.error(f"❌ Server startup failed: {str(e)}")
            sys.exit(1)

    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("   Please ensure all dependencies are installed and src/ directory is in PYTHONPATH")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start server: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()