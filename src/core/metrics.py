
from collections import defaultdict
import statistics

_METRICS = defaultdict(int)
_LATENCIES = defaultdict(list)

def inc(key, by=1): 
    """Increment a counter metric"""
    _METRICS[key] += by

def record_latency(path, latency_ms):
    """Record latency for percentile calculations"""
    _LATENCIES[path].append(latency_ms)
    # Keep only last 1000 measurements to prevent memory growth
    if len(_LATENCIES[path]) > 1000:
        _LATENCIES[path] = _LATENCIES[path][-1000:]

def snapshot(): 
    """Get current metrics snapshot"""
    return dict(_METRICS)

def get_latency_stats():
    """Get latency statistics"""
    stats = {}
    for path, latencies in _LATENCIES.items():
        if latencies:
            stats[path] = {
                "p50": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
                "avg": sum(latencies) / len(latencies),
                "count": len(latencies)
            }
    return stats
