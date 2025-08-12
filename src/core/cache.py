import json
import time
import os
from typing import Any, Dict, Optional, Callable
from functools import wraps
import threading
import logging

logger = logging.getLogger(__name__)

class Cache:
    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get(self, key: str):
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 300):
        self._cache[key] = value
        self._timestamps[key] = time.time() + ttl

    def invalidate(self, key: str):
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]

    def is_expired(self, key: str) -> bool:
        if key not in self._timestamps:
            return True
        return time.time() > self._timestamps[key]

# Global cache instance
cache = Cache()

def ttl_cache(ttl: int = 300):
    """TTL cache decorator"""
    def decorator(func: Callable):
        cache_dict = {}
        cache_times = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # Check if cached result exists and is not expired
            if key in cache_dict and key in cache_times:
                if time.time() < cache_times[key]:
                    return cache_dict[key]

            # Call function and cache result
            result = func(*args, **kwargs)
            cache_dict[key] = result
            cache_times[key] = time.time() + ttl

            return result

        return wrapper
    return decorator

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