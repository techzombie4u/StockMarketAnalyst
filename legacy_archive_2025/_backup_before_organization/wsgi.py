
#!/usr/bin/env python3
"""
WSGI Entry Point for Stock Market Analyst

This file serves as the WSGI entry point for production deployment
with Gunicorn or other WSGI servers.
"""

import sys
import os
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    # Import the Flask application
    from src.core.app import app, initialize_app
    
    # Initialize the application (starts scheduler)
    initialize_app()
    
    # This is what Gunicorn will look for
    application = app
    
    if __name__ == "__main__":
        # For testing the WSGI file directly
        app.run(host='0.0.0.0', port=5000)
        
except Exception as e:
    logging.error(f"Failed to initialize application: {str(e)}")
    raise
