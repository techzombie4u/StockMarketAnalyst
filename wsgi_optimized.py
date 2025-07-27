
"""
Optimized WSGI entry point for production deployment
Removes ML dependencies for faster startup and smaller bundle
"""

import os
import logging
from app import create_app

# Configure minimal logging for production
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Enable ML features for predictions (set to '1' to disable if needed)
# os.environ['DISABLE_ML_FEATURES'] = '1'

# Create Flask app instance
application = create_app()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000)
