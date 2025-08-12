import json
import time
import os
from typing import Any, Dict, Optional, Callable
from functools import wraps
import threading
import logging

logger = logging.getLogger(__name__)

class TTLCache:
    def __init__(self, default_ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = default_ttl
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None

            if time.time() - self.timestamps[key] > self.default_ttl:
                del self.cache[key]
                del self.timestamps[key]
                return None

            return self.cache[key]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self.lock:
            self.cache[key] = value
            self.timestamps[key] = time.time()

    def clear(self):
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()

# Global cache instance
_cache = TTLCache()

def ttl_cache(ttl: int = 300):
    """
    TTL cache decorator
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"

            # Try to get from cache
            cached_result = _cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            _cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    with _cache.lock:
        return {
            "cache_size": len(_cache.cache),
            "cache_keys": list(_cache.cache.keys())
        }

def clear_cache():
    """Clear all cached data"""
    _cache.clear()
    logger.info("Cache cleared")

# File-based cache for persistent data
class FileCache:
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get_file_path(self, key: str) -> str:
        return os.path.join(self.cache_dir, f"{key}.json")

    def get(self, key: str) -> Optional[Any]:
        file_path = self.get_file_path(key)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'expires_at' in data and time.time() > data['expires_at']:
                        os.remove(file_path)
                        return None
                    return data.get('value')
        except Exception as e:
            logger.error(f"Error reading cache file {file_path}: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        file_path = self.get_file_path(key)
        try:
            data = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time()
            }
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing cache file {file_path}: {e}")

# Global file cache instance
file_cache = FileCache()