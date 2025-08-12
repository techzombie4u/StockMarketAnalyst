from time import time
from typing import Any, Dict, Optional, Union
import threading
import gc
from functools import wraps

class TTLCache:
    """Thread-safe TTL (Time To Live) cache implementation"""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _now_iso(self) -> str:
        """Get current time in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time() > entry['expires_at']

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                return None

            # Update access time
            entry['last_accessed'] = self._now_iso()
            return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL"""
        if ttl is None:
            ttl = self.default_ttl

        with self._lock:
            self._cache[key] = {
                'value': value,
                'created_at': self._now_iso(),
                'last_accessed': self._now_iso(),
                'expires_at': time() + ttl,
                'ttl': ttl
            }

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            gc.collect()

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                gc.collect()

            return len(expired_keys)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(1 for entry in self._cache.values() if self._is_expired(entry))

            return {
                'total_entries': total_entries,
                'active_entries': total_entries - expired_count,
                'expired_entries': expired_count,
                'memory_usage_mb': len(str(self._cache)) / (1024 * 1024)
            }

# Global cache instances
_app_cache = TTLCache(default_ttl=300)  # 5 minutes
_kpi_cache = TTLCache(default_ttl=180)  # 3 minutes
_data_cache = TTLCache(default_ttl=600)  # 10 minutes

def get_app_cache() -> TTLCache:
    """Get application-level cache"""
    return _app_cache

def get_kpi_cache() -> TTLCache:
    """Get KPI-specific cache"""
    return _kpi_cache

def get_data_cache() -> TTLCache:
    """Get data-specific cache"""
    return _data_cache

def cached(ttl: int = 300, cache_name: str = 'app'):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Select cache
            if cache_name == 'kpi':
                cache = _kpi_cache
            elif cache_name == 'data':
                cache = _data_cache
            else:
                cache = _app_cache

            # Create cache key
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator

def clear_all_caches():
    """Clear all cache instances"""
    _app_cache.clear()
    _kpi_cache.clear()
    _data_cache.clear()
    print("🧹 All caches cleared")

def cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'app_cache': _app_cache.stats(),
        'kpi_cache': _kpi_cache.stats(),
        'data_cache': _data_cache.stats()
    }