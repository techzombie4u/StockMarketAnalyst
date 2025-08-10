
"""
Date and Time Utilities
"""

import pytz
from datetime import datetime, timedelta
from typing import Optional

# Standard timezone
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now() -> datetime:
    """Get current time in IST"""
    return datetime.now(IST)

def get_ist_date_str() -> str:
    """Get current IST date as string (YYYY-MM-DD)"""
    return get_ist_now().strftime('%Y-%m-%d')

def get_ist_datetime_str() -> str:
    """Get current IST datetime as string"""
    return get_ist_now().strftime('%Y-%m-%d %H:%M:%S')

def get_ist_iso_str() -> str:
    """Get current IST datetime as ISO string"""
    return get_ist_now().isoformat()

def parse_date_string(date_str: str, format_str: str = '%Y-%m-%d') -> Optional[datetime]:
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        return None

def is_market_hours() -> bool:
    """Check if current time is within market hours (9 AM - 4 PM IST)"""
    now = get_ist_now()
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Check if it's a weekday and within market hours
    return (now.weekday() < 5 and  # Monday = 0, Friday = 4
            market_open <= now <= market_close)

def get_trading_days_ago(days: int) -> datetime:
    """Get trading date N days ago (excluding weekends)"""
    current_date = get_ist_now().date()
    trading_days_back = 0
    check_date = current_date
    
    while trading_days_back < days:
        check_date -= timedelta(days=1)
        # Skip weekends (Saturday = 5, Sunday = 6)
        if check_date.weekday() < 5:
            trading_days_back += 1
    
    return datetime.combine(check_date, datetime.min.time())

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
