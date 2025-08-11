"""
Metrics collection and monitoring
"""

import json
import time
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict
import threading

class MetricsCollector:
    def __init__(self):
        self.requests_total = defaultdict(int)
        self.latency_data = defaultdict(list)
        self.start_time = time.time()
        self._lock = threading.Lock()

    def increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric"""
        with self._lock:
            self.requests_total[metric_name] += value

    def record_latency(self, path: str, latency_ms: float):
        """Record request latency"""
        with self._lock:
            self.latency_data[path].append(latency_ms)
            # Keep only last 1000 entries per path
            if len(self.latency_data[path]) > 1000:
                self.latency_data[path] = self.latency_data[path][-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self._lock:
            uptime = time.time() - self.start_time

            # Calculate latency percentiles
            latency_p95 = {}
            for path, latencies in self.latency_data.items():
                if latencies:
                    sorted_latencies = sorted(latencies)
                    p95_index = int(len(sorted_latencies) * 0.95)
                    latency_p95[path] = round(sorted_latencies[p95_index], 2)

            return {
                'uptime_seconds': round(uptime, 2),
                'requests_total': {
                    'by_path': dict(self.requests_total)
                },
                'latency_p95_ms': latency_p95,
                'timestamp': datetime.now().isoformat()
            }

# Global metrics collector
metrics = MetricsCollector()

def update_request_metrics(path: str, method: str, status_code: int, duration_ms: float):
    """Update request metrics"""
    # Count requests by path
    metrics.increment(path)

    # Count requests by status code
    metrics.increment(f"status_{status_code}")

    # Record latency
    metrics.record_latency(path, duration_ms)