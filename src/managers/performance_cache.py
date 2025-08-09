
"""
Performance Caching Module for Stock Market Analyst

Implements in-memory caching to speed up repeated calculations
and reduce API calls without external dependencies.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib

logger = logging.getLogger(__name__)

class PerformanceCache:
    def __init__(self):
        # Minimal in-memory cache storage
        self.cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        
        # Reduced cache configuration for stability
        self.config = {
            'max_cache_size': 100,   # Reduced cache size
            'default_ttl': 300,      # 5 minutes default TTL
            'price_data_ttl': 60,    # 1 minute for price data
            'technical_ttl': 300,    # 5 minutes for technical indicators
            'fundamental_ttl': 1800, # 30 minutes for fundamental data
            'cleanup_interval': 300  # 5 minutes cleanup interval
        }
        
        self.last_cleanup = time.time()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache"""
        try:
            self.cache_stats['total_requests'] += 1
            
            # Clean up expired items periodically
            if time.time() - self.last_cleanup > self.config['cleanup_interval']:
                self._cleanup_expired()
            
            if key in self.cache:
                item = self.cache[key]
                
                # Check if item has expired
                if time.time() > item['expires_at']:
                    del self.cache[key]
                    self.cache_stats['misses'] += 1
                    return default
                
                # Update access time for LRU
                item['last_accessed'] = time.time()
                item['access_count'] += 1
                
                self.cache_stats['hits'] += 1
                logger.debug(f"Cache hit for key: {key}")
                return item['data']
            
            self.cache_stats['misses'] += 1
            return default
            
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return default
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Set item in cache"""
        try:
            # Use default TTL if not specified
            if ttl is None:
                ttl = self.config['default_ttl']
            
            # Check cache size and evict if necessary
            if len(self.cache) >= self.config['max_cache_size']:
                self._evict_lru()
            
            # Store item with metadata
            self.cache[key] = {
                'data': data,
                'created_at': time.time(),
                'expires_at': time.time() + ttl,
                'last_accessed': time.time(),
                'access_count': 0,
                'ttl': ttl
            }
            
            logger.debug(f"Cached item with key: {key}, TTL: {ttl}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    def invalidate(self, pattern: str = None) -> int:
        """Invalidate cache items by pattern or all"""
        try:
            if pattern is None:
                # Clear all cache
                count = len(self.cache)
                self.cache.clear()
                logger.info(f"Cleared entire cache ({count} items)")
                return count
            
            # Remove items matching pattern
            keys_to_remove = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self.cache[key]
            
            logger.info(f"Invalidated {len(keys_to_remove)} cache items matching pattern: {pattern}")
            return len(keys_to_remove)
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        hit_rate = 0
        if self.cache_stats['total_requests'] > 0:
            hit_rate = (self.cache_stats['hits'] / self.cache_stats['total_requests']) * 100
        
        return {
            'cache_size': len(self.cache),
            'max_cache_size': self.config['max_cache_size'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': self.cache_stats['total_requests'],
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'memory_usage_estimate': self._estimate_memory_usage()
        }
    
    def _cleanup_expired(self) -> int:
        """Remove expired items from cache"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, item in self.cache.items()
                if current_time > item['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            self.last_cleanup = current_time
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache items")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Error during cache cleanup: {str(e)}")
            return 0
    
    def _evict_lru(self) -> bool:
        """Evict least recently used item"""
        try:
            if not self.cache:
                return False
            
            # Find LRU item
            lru_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k]['last_accessed']
            )
            
            del self.cache[lru_key]
            self.cache_stats['evictions'] += 1
            
            logger.debug(f"Evicted LRU item: {lru_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error during LRU eviction: {str(e)}")
            return False
    
    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of cache"""
        try:
            # Rough estimation
            total_size = 0
            for item in self.cache.values():
                # Estimate size of data (rough approximation)
                data_str = str(item['data'])
                total_size += len(data_str) + 200  # Add overhead for metadata
            
            if total_size < 1024:
                return f"{total_size} bytes"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"
                
        except Exception as e:
            logger.error(f"Error estimating memory usage: {str(e)}")
            return "Unknown"

# Global cache instance
cache = PerformanceCache()

# Caching decorators and utilities
def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments"""
    try:
        # Create a string representation of all arguments
        key_data = f"{args}_{sorted(kwargs.items())}"
        
        # Hash for consistent key length
        return hashlib.md5(key_data.encode()).hexdigest()
        
    except Exception as e:
        logger.error(f"Error generating cache key: {str(e)}")
        return f"fallback_key_{time.time()}"

def cached_function(ttl: int = None, key_prefix: str = ""):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # Generate cache key
                func_key = f"{key_prefix}_{func.__name__}_{cache_key(*args, **kwargs)}"
                
                # Try to get from cache
                cached_result = cache.get(func_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.set(func_key, result, ttl)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {str(e)}")
                # Fall back to executing function without caching
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

# Specific caching functions for stock market data
class StockDataCache:
    """Specialized caching for stock market data"""
    
    @staticmethod
    def cache_price_data(symbol: str, price_data: Dict) -> bool:
        """Cache price data with appropriate TTL"""
        key = f"price_data_{symbol}"
        return cache.set(key, price_data, cache.config['price_data_ttl'])
    
    @staticmethod
    def get_cached_price_data(symbol: str) -> Optional[Dict]:
        """Get cached price data"""
        key = f"price_data_{symbol}"
        return cache.get(key)
    
    @staticmethod
    def cache_technical_indicators(symbol: str, technical_data: Dict) -> bool:
        """Cache technical indicators"""
        key = f"technical_{symbol}"
        return cache.set(key, technical_data, cache.config['technical_ttl'])
    
    @staticmethod
    def get_cached_technical_indicators(symbol: str) -> Optional[Dict]:
        """Get cached technical indicators"""
        key = f"technical_{symbol}"
        return cache.get(key)
    
    @staticmethod
    def cache_fundamental_data(symbol: str, fundamental_data: Dict) -> bool:
        """Cache fundamental data"""
        key = f"fundamental_{symbol}"
        return cache.set(key, fundamental_data, cache.config['fundamental_ttl'])
    
    @staticmethod
    def get_cached_fundamental_data(symbol: str) -> Optional[Dict]:
        """Get cached fundamental data"""
        key = f"fundamental_{symbol}"
        return cache.get(key)
    
    @staticmethod
    def invalidate_symbol_cache(symbol: str) -> int:
        """Invalidate all cached data for a symbol"""
        return cache.invalidate(symbol)

# Batch caching utilities
def cache_multiple_stocks(stocks_data: List[Dict]) -> Dict:
    """Cache data for multiple stocks efficiently"""
    cache_results = {
        'cached': 0,
        'skipped': 0,
        'errors': 0
    }
    
    try:
        for stock in stocks_data:
            symbol = stock.get('symbol')
            if not symbol:
                cache_results['skipped'] += 1
                continue
            
            try:
                # Cache different data types
                if 'current_price' in stock:
                    price_data = {
                        'current_price': stock['current_price'],
                        'timestamp': datetime.now().isoformat()
                    }
                    StockDataCache.cache_price_data(symbol, price_data)
                
                if 'technical' in stock:
                    StockDataCache.cache_technical_indicators(symbol, stock['technical'])
                
                if 'fundamentals' in stock:
                    StockDataCache.cache_fundamental_data(symbol, stock['fundamentals'])
                
                cache_results['cached'] += 1
                
            except Exception as e:
                logger.error(f"Error caching data for {symbol}: {str(e)}")
                cache_results['errors'] += 1
        
        logger.info(f"Batch caching completed: {cache_results}")
        return cache_results
        
    except Exception as e:
        logger.error(f"Error in batch caching: {str(e)}")
        return cache_results

def get_cache_performance_report() -> str:
    """Generate a formatted cache performance report"""
    try:
        stats = cache.get_stats()
        
        report = []
        report.append("=== CACHE PERFORMANCE REPORT ===")
        report.append(f"Cache Size: {stats['cache_size']}/{stats['max_cache_size']}")
        report.append(f"Hit Rate: {stats['hit_rate']}%")
        report.append(f"Total Requests: {stats['total_requests']}")
        report.append(f"Cache Hits: {stats['hits']}")
        report.append(f"Cache Misses: {stats['misses']}")
        report.append(f"Evictions: {stats['evictions']}")
        report.append(f"Memory Usage: {stats['memory_usage_estimate']}")
        report.append("")
        
        # Performance recommendations
        if stats['hit_rate'] < 50:
            report.append("⚠️  Low hit rate - consider increasing TTL values")
        elif stats['hit_rate'] > 80:
            report.append("✅ Excellent hit rate - cache is performing well")
        
        if stats['evictions'] > stats['hits'] * 0.1:
            report.append("⚠️  High eviction rate - consider increasing cache size")
        
        return "\n".join(report)
        
    except Exception as e:
        logger.error(f"Error generating cache report: {str(e)}")
        return "Error generating cache performance report"

# Cache warming functions
def warm_cache_for_symbols(symbols: List[str]) -> Dict:
    """Pre-warm cache for frequently accessed symbols"""
    try:
        from src.analyzers.stock_screener import StockScreener
        
        screener = StockScreener()
        warmed = 0
        errors = 0
        
        for symbol in symbols:
            try:
                # Check if already cached
                if StockDataCache.get_cached_technical_indicators(symbol):
                    continue
                
                # Fetch and cache data
                technical_data = screener.get_technical_analysis(symbol)
                if technical_data:
                    StockDataCache.cache_technical_indicators(symbol, technical_data)
                    warmed += 1
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error warming cache for {symbol}: {str(e)}")
                errors += 1
        
        result = {
            'warmed': warmed,
            'errors': errors,
            'total_symbols': len(symbols)
        }
        
        logger.info(f"Cache warming completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in cache warming: {str(e)}")
        return {'error': str(e)}
