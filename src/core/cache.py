from datetime import datetime, timezone
import time
from typing import Any, Optional, Dict
import json
from datetime import datetime, timedelta

def now_iso() -> str:
    """Return current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

class TTLCache:
    def __init__(self, ttl_sec: int = 30):
        self.ttl = ttl_sec
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() - entry['timestamp'] > self.ttl:
            del self._cache[key]
            return None

        return entry['payload']

    def set(self, key: str, payload: Any) -> None:
        """Set cached value with current timestamp"""
        self._cache[key] = {
            'payload': payload,
            'timestamp': time.time()
        }

    def clear(self, key: Optional[str] = None) -> None:
        """Clear specific key or entire cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

# Global cache instances with different TTLs
cache_short = TTLCache(ttl_sec=15)    # For quotes, real-time data
cache_medium = TTLCache(ttl_sec=300)  # For KPIs, analysis
cache_long = TTLCache(ttl_sec=900)    # For historical data