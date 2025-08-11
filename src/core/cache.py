
import time
from datetime import datetime, timezone

class TTLCache:
    """Simple TTL (Time To Live) cache implementation"""
    
    def __init__(self, ttl_sec=300, namespace="default"):
        self.ttl_sec = ttl_sec
        self.namespace = namespace
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key):
        """Get item from cache if not expired"""
        full_key = f"{self.namespace}:{key}"
        
        if full_key not in self._cache:
            return None
            
        # Check if expired
        if time.time() - self._timestamps[full_key] > self.ttl_sec:
            del self._cache[full_key]
            del self._timestamps[full_key]
            return None
            
        return self._cache[full_key]
    
    def set(self, key, value):
        """Set item in cache with current timestamp"""
        full_key = f"{self.namespace}:{key}"
        self._cache[full_key] = value
        self._timestamps[full_key] = time.time()
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._timestamps.clear()

def ttl_cache(ttl_sec=300, namespace="default"):
    """Create a TTL cache instance"""
    return TTLCache(ttl_sec=ttl_sec, namespace=namespace)

def now_iso():
    """Return current UTC time in ISO format"""
    return datetime.now(timezone.utc).isoformat()
