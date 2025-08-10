
"""
Runtime Configuration Constants
Defines constants for scheduler, market hours, refresh intervals, and KPI calculations
"""

import os
import pytz
from datetime import time

# Market timezone and hours (IST)
MARKET_TZ = "Asia/Kolkata"
MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"

# Auto-refresh and caching intervals
AUTO_REFRESH_INTERVAL_SEC = int(os.getenv('AUTO_REFRESH_INTERVAL_SEC', 60))
PREDICTION_TTL_SEC = int(os.getenv('PREDICTION_TTL_SEC', 300))  # 5 minutes

# KPI calculation parameters
KPI_ROLLING_WINDOW_DAYS = int(os.getenv('KPI_ROLLING_WINDOW_DAYS', 90))
KPI_MIN_SAMPLES = {
    "3D": int(os.getenv('KPI_MIN_SAMPLES_3D', 10)),
    "5D": int(os.getenv('KPI_MIN_SAMPLES_5D', 10)),
    "10D": int(os.getenv('KPI_MIN_SAMPLES_10D', 5)),
    "15D": int(os.getenv('KPI_MIN_SAMPLES_15D', 5)),
    "30D": int(os.getenv('KPI_MIN_SAMPLES_30D', 3))
}

def get_market_tz():
    """Get market timezone object"""
    return pytz.timezone(MARKET_TZ)

def get_market_open_time():
    """Get market open time"""
    return time.fromisoformat(MARKET_OPEN)

def get_market_close_time():
    """Get market close time"""
    return time.fromisoformat(MARKET_CLOSE)

def is_market_hours_now():
    """Check if current time is within market hours (IST)"""
    try:
        ist = get_market_tz()
        now_ist = ist.localize(ist.normalize().now().replace(tzinfo=None))
        
        market_open = get_market_open_time()
        market_close = get_market_close_time()
        
        current_time = now_ist.time()
        
        return market_open <= current_time <= market_close
    except Exception:
        # Default to False if timezone calculation fails
        return False
