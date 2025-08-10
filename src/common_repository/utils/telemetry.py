
"""
Lightweight Telemetry System
Tracks performance metrics in-process without external dependencies
"""

import time
import threading
import gc
import psutil
import os
from typing import Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta

class TelemetryCollector:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(lambda: deque(maxlen=1000))
        self._start_time = time.time()
        self._process = psutil.Process(os.getpid()) if psutil else None
        
    def increment(self, metric: str, value: int = 1):
        """Increment a counter metric"""
        with self._lock:
            self._counters[metric] += value
            
    def set_gauge(self, metric: str, value: float):
        """Set a gauge metric"""
        with self._lock:
            self._gauges[metric] = value
            
    def record_histogram(self, metric: str, value: float):
        """Record a value in histogram"""
        with self._lock:
            self._histograms[metric].append(value)
            
    def get_memory_stats(self) -> Dict[str, float]:
        """Get current memory statistics"""
        stats = {}
        try:
            if self._process:
                memory_info = self._process.memory_info()
                stats['memory_rss_mb'] = memory_info.rss / 1024 / 1024
                stats['memory_vms_mb'] = memory_info.vms / 1024 / 1024
                stats['memory_percent'] = self._process.memory_percent()
            
            # GC stats
            stats['gc_collections'] = sum(gc.get_stats()) if hasattr(gc, 'get_stats') else 0
            
        except Exception:
            pass
            
        return stats
        
    def get_io_stats(self) -> Dict[str, float]:
        """Get I/O statistics"""
        with self._lock:
            total_api_calls = self._counters.get('api_calls', 0)
            total_failures = self._counters.get('api_failures', 0)
            cache_hits = self._counters.get('cache_hits', 0)
            cache_misses = self._counters.get('cache_misses', 0)
            
            uptime_minutes = (time.time() - self._start_time) / 60
            
            return {
                'api_calls_per_min': total_api_calls / max(uptime_minutes, 1),
                'failures_per_min': total_failures / max(uptime_minutes, 1),
                'cache_hit_rate': cache_hits / max(cache_hits + cache_misses, 1) * 100,
                'cache_hits': cache_hits,
                'cache_misses': cache_misses
            }
            
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job queue statistics"""
        with self._lock:
            return {
                'queue_depth': self._gauges.get('jobs.queue_depth', 0),
                'last_run_sec': self._gauges.get('jobs.last_run_sec', 0),
                'lag_sec': self._gauges.get('jobs.lag_sec', 0)
            }
            
    def check_budgets(self) -> Dict[str, bool]:
        """Check if metrics are within acceptable budgets"""
        memory_stats = self.get_memory_stats()
        io_stats = self.get_io_stats()
        job_stats = self.get_job_stats()
        
        budgets = {
            'memory_under_budget': memory_stats.get('memory_rss_mb', 0) < 250,
            'cache_hit_rate_ok': io_stats.get('cache_hit_rate', 0) >= 80,
            'api_calls_under_limit': io_stats.get('api_calls_per_min', 0) <= 30,
            'job_queue_ok': job_stats.get('queue_depth', 0) <= 10,
            'job_lag_ok': job_stats.get('lag_sec', 0) < 10
        }
        
        return budgets
        
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return {
            'memory': self.get_memory_stats(),
            'io': self.get_io_stats(),
            'jobs': self.get_job_stats(),
            'budgets': self.check_budgets(),
            'uptime_seconds': time.time() - self._start_time
        }

# Global telemetry instance
telemetry = TelemetryCollector()
