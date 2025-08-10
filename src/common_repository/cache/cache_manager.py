
"""
Two-Tier Cache Manager
In-memory LRU + on-disk JSON with TTL and request coalescing
"""

import json
import os
import time
import hashlib
import threading
import asyncio
from typing import Any, Dict, Optional, Callable, Awaitable
from collections import OrderedDict
from datetime import datetime, timedelta
import logging

from ..utils.telemetry import telemetry

logger = logging.getLogger(__name__)

class LRUCache:
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
            
    def put(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value
            
            # Evict LRU if over limit
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)
                
    def clear(self, prefix: Optional[str] = None):
        with self.lock:
            if prefix:
                keys_to_remove = [k for k in self.cache.keys() if k.startswith(prefix)]
                for key in keys_to_remove:
                    del self.cache[key]
            else:
                self.cache.clear()

class CacheManager:
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # In-memory cache
        self.memory_cache = LRUCache(max_size=2000)
        
        # TTL settings (in seconds)
        self.ttls = {
            'quotes': 15,
            'ohlc': 900,  # 15 minutes
            'options_chain': 60,
            'model_inference': 300,  # 5 minutes
            'default': 300
        }
        
        # Request coalescing - track in-flight requests
        self.in_flight = {}
        self.coalescing_lock = threading.Lock()
        
    def _get_cache_key(self, provider: str, resource: str, symbol: str, params: Dict) -> str:
        """Generate cache key with params hash"""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{provider}:{resource}:{symbol}:{params_hash}"
        
    def _get_file_path(self, key: str) -> str:
        """Get file path for disk cache"""
        safe_key = key.replace(':', '_').replace('/', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.json")
        
    def _get_ttl(self, resource_type: str) -> int:
        """Get TTL for resource type"""
        return self.ttls.get(resource_type, self.ttls['default'])
        
    def _is_expired(self, cache_entry: Dict, ttl: int) -> bool:
        """Check if cache entry is expired"""
        timestamp = cache_entry.get('timestamp', 0)
        return time.time() - timestamp > ttl
        
    def get(self, provider: str, resource: str, symbol: str, params: Dict = None) -> Optional[Any]:
        """Get from cache with TTL check"""
        params = params or {}
        key = self._get_cache_key(provider, resource, symbol, params)
        ttl = self._get_ttl(resource)
        
        # Try memory cache first
        memory_entry = self.memory_cache.get(key)
        if memory_entry and not self._is_expired(memory_entry, ttl):
            telemetry.increment('cache_hits')
            return memory_entry['data']
            
        # Try disk cache
        try:
            file_path = self._get_file_path(key)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    disk_entry = json.load(f)
                    
                if not self._is_expired(disk_entry, ttl):
                    # Load back to memory cache
                    self.memory_cache.put(key, disk_entry)
                    telemetry.increment('cache_hits')
                    return disk_entry['data']
                else:
                    # Clean up expired file
                    os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error reading disk cache for {key}: {e}")
            
        telemetry.increment('cache_misses')
        return None
        
    def put(self, provider: str, resource: str, symbol: str, data: Any, params: Dict = None):
        """Store in both memory and disk cache"""
        params = params or {}
        key = self._get_cache_key(provider, resource, symbol, params)
        
        cache_entry = {
            'data': data,
            'timestamp': time.time()
        }
        
        # Store in memory
        self.memory_cache.put(key, cache_entry)
        
        # Store on disk
        try:
            file_path = self._get_file_path(key)
            with open(file_path, 'w') as f:
                json.dump(cache_entry, f, default=str)
        except Exception as e:
            logger.warning(f"Error writing disk cache for {key}: {e}")
            
    async def get_or_fetch(self, provider: str, resource: str, symbol: str, 
                          fetch_func: Callable[[], Awaitable[Any]], params: Dict = None) -> Any:
        """Get from cache or fetch with request coalescing"""
        params = params or {}
        key = self._get_cache_key(provider, resource, symbol, params)
        
        # Try cache first
        cached_data = self.get(provider, resource, symbol, params)
        if cached_data is not None:
            return cached_data
            
        # Check if request is already in flight
        with self.coalescing_lock:
            if key in self.in_flight:
                # Wait for existing request
                return await self.in_flight[key]
                
            # Create new request future
            future = asyncio.create_task(self._fetch_and_cache(
                provider, resource, symbol, fetch_func, params, key
            ))
            self.in_flight[key] = future
            
        try:
            return await future
        finally:
            # Clean up in-flight tracking
            with self.coalescing_lock:
                self.in_flight.pop(key, None)
                
    async def _fetch_and_cache(self, provider: str, resource: str, symbol: str,
                              fetch_func: Callable[[], Awaitable[Any]], params: Dict, key: str) -> Any:
        """Fetch data and store in cache"""
        try:
            telemetry.increment('api_calls')
            data = await fetch_func()
            
            if data is not None:
                self.put(provider, resource, symbol, data, params)
                
            return data
            
        except Exception as e:
            telemetry.increment('api_failures')
            logger.error(f"Error fetching data for {key}: {e}")
            raise
            
    def clear_expired(self):
        """Clear expired entries from cache"""
        current_time = time.time()
        
        # Clear memory cache expired entries
        with self.memory_cache.lock:
            expired_keys = []
            for key, entry in self.memory_cache.cache.items():
                resource_type = key.split(':')[1] if ':' in key else 'default'
                ttl = self._get_ttl(resource_type)
                if self._is_expired(entry, ttl):
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self.memory_cache.cache[key]
                
        # Clear disk cache expired files
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            entry = json.load(f)
                            
                        # Extract resource type from filename
                        key_parts = filename.replace('.json', '').split('_')
                        resource_type = key_parts[1] if len(key_parts) > 1 else 'default'
                        ttl = self._get_ttl(resource_type)
                        
                        if self._is_expired(entry, ttl):
                            os.remove(file_path)
                            
                    except Exception as e:
                        logger.warning(f"Error checking expired file {filename}: {e}")
                        
        except Exception as e:
            logger.warning(f"Error clearing expired disk cache: {e}")
            
    def clear_scope(self, scope: str):
        """Clear cache for specific scope (provider:resource pattern)"""
        self.memory_cache.clear(prefix=scope)
        
        # Clear matching disk files
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.startswith(scope.replace(':', '_')):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
        except Exception as e:
            logger.warning(f"Error clearing scope {scope}: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_size = len(self.memory_cache.cache)
        
        disk_files = 0
        disk_size_mb = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    disk_files += 1
                    file_path = os.path.join(self.cache_dir, filename)
                    disk_size_mb += os.path.getsize(file_path) / 1024 / 1024
        except Exception:
            pass
            
        return {
            'memory_entries': memory_size,
            'disk_files': disk_files,
            'disk_size_mb': round(disk_size_mb, 2),
            'in_flight_requests': len(self.in_flight)
        }

# Global cache manager instance
cache_manager = CacheManager()
