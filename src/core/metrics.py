
"""
Metrics collection and monitoring
"""

import json
import time
import psutil
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict
import threading

class MetricsCollector:
    def __init__(self):
        self.requests_total = defaultdict(int)
        self.errors_total = defaultdict(int)
        self.latency_data = defaultdict(list)
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)
        self.start_time = time.time()
        self._lock = threading.Lock()

    def increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric"""
        with self._lock:
            if metric_name.startswith('requests_total_'):
                endpoint = metric_name.replace('requests_total_', '')
                self.requests_total[endpoint] += value
            elif metric_name.startswith('errors_total_'):
                endpoint = metric_name.replace('errors_total_', '')
                self.errors_total[endpoint] += value
            else:
                self.requests_total[metric_name] += value

    def record_latency(self, path: str, latency_ms: float):
        """Record request latency"""
        with self._lock:
            self.latency_data[path].append(latency_ms)
            # Keep only last 1000 entries per path
            if len(self.latency_data[path]) > 1000:
                self.latency_data[path] = self.latency_data[path][-1000:]

    def get_p95_latency(self, endpoint: str) -> float:
        """Calculate p95 latency for an endpoint"""
        with self._lock:
            if endpoint not in self.latency_data or not self.latency_data[endpoint]:
                return 0.0
                
            latencies = sorted(self.latency_data[endpoint])
            if len(latencies) < 5:
                return 0.0
                
            p95_index = int(len(latencies) * 0.95)
            return latencies[p95_index]

    def get_cache_hit_rate(self, endpoint: str) -> float:
        """Calculate cache hit rate for an endpoint"""
        with self._lock:
            hits = self.cache_hits.get(endpoint, 0)
            misses = self.cache_misses.get(endpoint, 0)
            total = hits + misses
            
            if total == 0:
                return 1.0
                
            return hits / total

    def get_memory_usage_mb(self) -> float:
        """Get current RSS memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self._lock:
            uptime = time.time() - self.start_time

            # Calculate latency percentiles per endpoint
            latency_p95 = {}
            cache_hit_rates = {}
            
            for endpoint in self.latency_data.keys():
                latency_p95[endpoint] = round(self.get_p95_latency(endpoint), 2)
                cache_hit_rates[endpoint] = round(self.get_cache_hit_rate(endpoint), 3)

            return {
                'uptime_seconds': round(uptime, 2),
                'memory_mb': round(self.get_memory_usage_mb(), 2),
                'requests_total': dict(self.requests_total),
                'errors_total': dict(self.errors_total),
                'latency_p95_ms': latency_p95,
                'cache_hit_rate': cache_hit_rates,
                'timestamp': datetime.now().isoformat()
            }

# Global metrics collector
metrics = MetricsCollector()

def update_request_metrics(path: str, method: str, status_code: int, duration_ms: float):
    """Update request metrics"""
    # Count requests by path
    metrics.increment(f"requests_total_{path}")

    # Count errors by path
    if status_code >= 400:
        metrics.increment(f"errors_total_{path}")

    # Record latency
    metrics.record_latency(path, duration_ms)
