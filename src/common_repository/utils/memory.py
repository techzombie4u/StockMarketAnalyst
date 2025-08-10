
"""
Memory Management and Leak Prevention
"""

import gc
import weakref
import threading
import time
import logging
from typing import Dict, List, Any, Optional
from collections import deque, defaultdict
import sys

from .telemetry import telemetry

logger = logging.getLogger(__name__)

class RingBuffer:
    """Fixed-size ring buffer to prevent unbounded growth"""
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()
        
    def append(self, item: Any):
        with self.lock:
            self.buffer.append(item)
            
    def extend(self, items: List[Any]):
        with self.lock:
            self.buffer.extend(items)
            
    def get_all(self) -> List[Any]:
        with self.lock:
            return list(self.buffer)
            
    def clear(self):
        with self.lock:
            self.buffer.clear()
            
    def __len__(self):
        return len(self.buffer)

class DataFrameConverter:
    """Convert pandas DataFrames to memory-efficient formats"""
    
    @staticmethod
    def dataframe_to_dict(df) -> Dict[str, Any]:
        """Convert DataFrame to dict, handling various data types"""
        if df is None:
            return {}
            
        try:
            # Convert to dict with lists
            result = {}
            for column in df.columns:
                series = df[column]
                
                # Handle different data types efficiently
                if series.dtype == 'object':
                    result[column] = series.fillna('').astype(str).tolist()
                elif 'datetime' in str(series.dtype):
                    result[column] = series.dt.strftime('%Y-%m-%d %H:%M:%S').fillna('').tolist()
                else:
                    result[column] = series.fillna(0).tolist()
                    
            # Add metadata
            result['_metadata'] = {
                'rows': len(df),
                'columns': len(df.columns),
                'converted_at': time.time()
            }
            
            return result
            
        except Exception as e:
            logger.warning(f"Error converting DataFrame to dict: {e}")
            return {}
            
    @staticmethod
    def truncate_series(data: List[Any], max_length: int = 500) -> List[Any]:
        """Truncate series to prevent memory bloat"""
        if len(data) <= max_length:
            return data
            
        # Keep most recent data
        return data[-max_length:]

class MemoryTracker:
    """Track memory usage and detect leaks"""
    
    def __init__(self):
        self.snapshots = RingBuffer(max_size=100)
        self.object_counts = defaultdict(int)
        self.callback_registry = weakref.WeakKeyDictionary()
        
    def take_snapshot(self) -> Dict[str, Any]:
        """Take memory snapshot"""
        snapshot = {
            'timestamp': time.time(),
            'rss_mb': 0,
            'gc_objects': len(gc.get_objects()),
            'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else []
        }
        
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            snapshot['rss_mb'] = memory_info.rss / 1024 / 1024
            snapshot['vms_mb'] = memory_info.vms / 1024 / 1024
        except ImportError:
            pass
            
        self.snapshots.append(snapshot)
        telemetry.set_gauge('memory_rss_mb', snapshot['rss_mb'])
        
        return snapshot
        
    def detect_leaks(self) -> List[str]:
        """Detect potential memory leaks"""
        warnings = []
        snapshots = self.snapshots.get_all()
        
        if len(snapshots) < 5:
            return warnings
            
        # Check for consistent memory growth
        recent = snapshots[-5:]
        memory_trend = [s['rss_mb'] for s in recent]
        
        # Simple trend detection
        if all(memory_trend[i] < memory_trend[i+1] for i in range(len(memory_trend)-1)):
            growth = memory_trend[-1] - memory_trend[0]
            if growth > 50:  # 50MB growth
                warnings.append(f"Consistent memory growth detected: {growth:.1f}MB")
                
        # Check for excessive object count
        if recent[-1]['gc_objects'] > 100000:
            warnings.append(f"High object count: {recent[-1]['gc_objects']}")
            
        return warnings
        
    def register_callback(self, obj: Any, callback: callable):
        """Register cleanup callback for object"""
        self.callback_registry[obj] = callback

class MemoryManager:
    """Central memory management"""
    
    def __init__(self):
        self.tracker = MemoryTracker()
        self.data_stores = {}
        self.cleanup_interval = 600  # 10 minutes
        self.last_cleanup = time.time()
        self.lock = threading.Lock()
        
    def create_ring_buffer(self, key: str, max_size: int) -> RingBuffer:
        """Create managed ring buffer"""
        with self.lock:
            if key in self.data_stores:
                return self.data_stores[key]
                
            buffer = RingBuffer(max_size)
            self.data_stores[key] = buffer
            return buffer
            
    def get_ring_buffer(self, key: str) -> Optional[RingBuffer]:
        """Get existing ring buffer"""
        return self.data_stores.get(key)
        
    def cleanup_expired_data(self):
        """Cleanup expired data and run garbage collection"""
        now = time.time()
        
        if now - self.last_cleanup < self.cleanup_interval:
            return
            
        self.last_cleanup = now
        
        logger.info("Running memory cleanup")
        
        # Clear empty ring buffers
        with self.lock:
            empty_keys = [k for k, v in self.data_stores.items() if len(v) == 0]
            for key in empty_keys:
                del self.data_stores[key]
                
        # Force garbage collection
        collected = gc.collect()
        telemetry.set_gauge('gc_collections', collected)
        
        # Take memory snapshot
        snapshot = self.tracker.take_snapshot()
        
        # Check for leaks
        leak_warnings = self.tracker.detect_leaks()
        for warning in leak_warnings:
            logger.warning(f"Memory leak detected: {warning}")
            
        logger.info(f"Memory cleanup completed: {collected} objects collected, "
                   f"RSS: {snapshot['rss_mb']:.1f}MB")
                   
    def convert_dataframe_safely(self, df, max_rows: int = 500) -> Dict[str, Any]:
        """Convert DataFrame with memory safety"""
        if df is None or len(df) == 0:
            return {}
            
        # Truncate if too large
        if len(df) > max_rows:
            df = df.tail(max_rows)
            logger.debug(f"Truncated DataFrame to {max_rows} rows")
            
        # Convert and clear reference
        result = DataFrameConverter.dataframe_to_dict(df)
        del df
        
        return result
        
    def limit_payload_size(self, data: Any, max_size_kb: int = 5000) -> Any:
        """Limit payload size to prevent memory issues"""
        try:
            import json
            size_bytes = len(json.dumps(data, default=str).encode())
            size_kb = size_bytes / 1024
            
            if size_kb > max_size_kb:
                logger.warning(f"Large payload detected: {size_kb:.1f}KB, truncating")
                
                if isinstance(data, dict):
                    # Truncate lists in dict
                    truncated = {}
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 100:
                            truncated[key] = value[-100:]  # Keep last 100 items
                        else:
                            truncated[key] = value
                    return truncated
                elif isinstance(data, list):
                    return data[-100:]  # Keep last 100 items
                    
        except Exception as e:
            logger.warning(f"Error checking payload size: {e}")
            
        return data
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        return {
            'ring_buffers': len(self.data_stores),
            'total_buffer_items': sum(len(buf) for buf in self.data_stores.values()),
            'snapshots_taken': len(self.tracker.snapshots),
            'last_cleanup': self.last_cleanup,
            'current_snapshot': self.tracker.take_snapshot()
        }

# Global memory manager
memory_manager = MemoryManager()

def safe_dataframe_convert(df, max_rows: int = 500) -> Dict[str, Any]:
    """Convenience function for safe DataFrame conversion"""
    return memory_manager.convert_dataframe_safely(df, max_rows)

def get_quotes_buffer(symbol: str) -> RingBuffer:
    """Get or create quotes ring buffer for symbol"""
    return memory_manager.create_ring_buffer(f"quotes_{symbol}", 200)

def get_ohlc_buffer(symbol: str) -> RingBuffer:
    """Get or create OHLC ring buffer for symbol"""
    return memory_manager.create_ring_buffer(f"ohlc_{symbol}", 500)
