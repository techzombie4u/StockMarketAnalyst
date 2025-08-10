
#!/usr/bin/env python3
"""
Flask Server Entrypoint for Fusion Dashboard
Starts the Flask application with proper configuration
"""

import os
import sys
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.app import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main server entrypoint"""
    try:
        # Replit sometimes injects PORT; default to 5000
        port = int(os.environ.get("PORT", "5000"))
        
        logger.info(f"🚀 Starting Fusion Dashboard server on port {port}")
        logger.info("📊 Fusion Dashboard available at: /fusion-dashboard")
        logger.info("🔌 Fusion API available at: /api/fusion/dashboard")
        
        # Bind to all interfaces so the validator can hit localhost:5000
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=False, 
            use_reloader=False,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
