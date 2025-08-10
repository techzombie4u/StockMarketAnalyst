
"""
Date and time utilities
"""

import pytz
from datetime import datetime
from typing import Optional

# India Standard Time
IST = pytz.timezone('Asia/Kolkata')

def get_ist_now() -> datetime:
    """Get current time in IST"""
    return datetime.now(IST)

def format_ist_time(dt: Optional[datetime] = None) -> str:
    """Format datetime in IST"""
    if dt is None:
        dt = get_ist_now()
    
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    else:
        dt = dt.astimezone(IST)
    
    return dt.strftime('%Y-%m-%d %H:%M:%S IST')

def parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime"""
    try:
        # Try common formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None
