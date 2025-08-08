
#!/usr/bin/env python3
"""
Initialization script to ensure the system starts properly
"""

import json
import os
import logging
from datetime import datetime
import pytz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_system():
    """Initialize the system with default files and settings"""
    try:
        # Create initial top10.json if it doesn't exist
        if not os.path.exists('top10.json'):
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            
            initial_data = {
                'timestamp': now_ist.isoformat(),
                'last_updated': now_ist.strftime('%Y-%m-%d %H:%M:%S IST'),
                'stocks': [],
                'status': 'initializing',
                'message': 'System starting up... Please wait for first screening to complete.'
            }
            
            with open('top10.json', 'w') as f:
                json.dump(initial_data, f, indent=2)
            
            logger.info("✅ Created initial top10.json file")
        
        # Ensure log directory exists
        os.makedirs('logs', exist_ok=True)
        
        logger.info("✅ System initialization completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ System initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_system()
