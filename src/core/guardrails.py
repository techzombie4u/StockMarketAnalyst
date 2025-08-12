
"""
Performance Guardrails System
Auto-disables heavy features when performance budgets are exceeded
"""

import time
import json
import os
import psutil
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class PerformanceGuardrails:
    def __init__(self):
        self.feature_flags_path = "data/persistent/feature_flags.json"
        self.metrics_lock = threading.Lock()
        
        # Rolling metrics storage
        self.latency_data = defaultdict(lambda: deque(maxlen=100))
        self.cache_hits = defaultdict(int)
        self.cache_misses = defaultdict(int)
        
        # Budget violation tracking
        self.budget_violations = {}
        self.last_check = time.time()
        
        # Performance budgets
        self.budgets = {
            'p95_latency_ms': 600,     # 600ms p95 latency
            'memory_mb': 250,          # 250MB RSS memory
            'cache_hit_rate': 0.70     # 70% cache hit rate minimum
        }
        
        # Feature flag mappings for degradation
        self.degradation_flags = {
            'charts_enabled': False,
            'agents_run_enabled': False,
            'enable_ai_agents': False,
            'enable_advanced_charting': False,
            'enable_realtime_agents': False,
            'enable_all_timeframes_concurrent': False,
            'enable_background_kpi_jobs': False
        }
        
        # Ensure feature flags file exists
        self._ensure_feature_flags_file()
        
        logger.info("Performance guardrails initialized")

    def _ensure_feature_flags_file(self):
        """Ensure feature flags file exists with defaults"""
        os.makedirs(os.path.dirname(self.feature_flags_path), exist_ok=True)
        
        if not os.path.exists(self.feature_flags_path):
            default_flags = {
                'charts_enabled': True,
                'agents_run_enabled': True,
                'enable_ai_agents': True,
                'enable_advanced_charting': True,
                'enable_realtime_agents': True,
                'enable_all_timeframes_concurrent': False,
                'enable_background_kpi_jobs': True,
                'degraded_mode': False,
                'degraded_reason': None,
                'last_updated': datetime.now().isoformat()
            }
            self._save_feature_flags(default_flags)

    def _save_feature_flags(self, flags: Dict[str, Any]):
        """Save feature flags to persistent storage"""
        try:
            with open(self.feature_flags_path, 'w') as f:
                json.dump(flags, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")

    def _load_feature_flags(self) -> Dict[str, Any]:
        """Load feature flags from persistent storage"""
        try:
            if os.path.exists(self.feature_flags_path):
                with open(self.feature_flags_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
            return {}

    def record_request_latency(self, endpoint: str, latency_ms: float):
        """Record request latency for an endpoint"""
        with self.metrics_lock:
            self.latency_data[endpoint].append({
                'latency_ms': latency_ms,
                'timestamp': time.time()
            })

    def record_cache_hit(self, endpoint: str):
        """Record cache hit for an endpoint"""
        with self.metrics_lock:
            self.cache_hits[endpoint] += 1

    def record_cache_miss(self, endpoint: str):
        """Record cache miss for an endpoint"""
        with self.metrics_lock:
            self.cache_misses[endpoint] += 1

    def get_p95_latency(self, endpoint: str) -> float:
        """Calculate p95 latency for an endpoint"""
        with self.metrics_lock:
            if endpoint not in self.latency_data or not self.latency_data[endpoint]:
                return 0.0
                
            latencies = [entry['latency_ms'] for entry in self.latency_data[endpoint]]
            latencies.sort()
            
            if len(latencies) < 5:  # Need at least 5 samples
                return 0.0
                
            p95_index = int(len(latencies) * 0.95)
            return latencies[p95_index]

    def get_cache_hit_rate(self, endpoint: str) -> float:
        """Calculate cache hit rate for an endpoint"""
        with self.metrics_lock:
            hits = self.cache_hits.get(endpoint, 0)
            misses = self.cache_misses.get(endpoint, 0)
            total = hits + misses
            
            if total == 0:
                return 1.0  # No requests = perfect hit rate
                
            return hits / total

    def get_memory_usage_mb(self) -> float:
        """Get current RSS memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0

    def check_budgets(self) -> Dict[str, bool]:
        """Check if performance budgets are being met"""
        now = time.time()
        
        # Only check every 30 seconds to avoid overhead
        if now - self.last_check < 30:
            return {}
            
        self.last_check = now
        budget_status = {}
        
        # Check memory budget
        memory_mb = self.get_memory_usage_mb()
        budget_status['memory_ok'] = memory_mb <= self.budgets['memory_mb']
        
        # Check latency and cache hit rate per endpoint
        with self.metrics_lock:
            endpoints = set(list(self.latency_data.keys()) + list(self.cache_hits.keys()))
            
            overall_latency_ok = True
            overall_cache_ok = True
            
            for endpoint in endpoints:
                # Check p95 latency
                p95_latency = self.get_p95_latency(endpoint)
                if p95_latency > self.budgets['p95_latency_ms']:
                    overall_latency_ok = False
                    logger.warning(f"Endpoint {endpoint} p95 latency: {p95_latency:.1f}ms > {self.budgets['p95_latency_ms']}ms")
                
                # Check cache hit rate
                hit_rate = self.get_cache_hit_rate(endpoint)
                if hit_rate < self.budgets['cache_hit_rate']:
                    overall_cache_ok = False
                    logger.warning(f"Endpoint {endpoint} cache hit rate: {hit_rate:.2%} < {self.budgets['cache_hit_rate']:.2%}")
            
            budget_status['latency_ok'] = overall_latency_ok
            budget_status['cache_ok'] = overall_cache_ok
        
        return budget_status

    def enforce_guardrails(self):
        """Check budgets and enforce guardrails by disabling features"""
        budgets = self.check_budgets()
        now = time.time()
        
        # Track budget violations
        for budget_name, is_ok in budgets.items():
            if not is_ok:
                if budget_name not in self.budget_violations:
                    self.budget_violations[budget_name] = now
                    logger.warning(f"Budget violation started: {budget_name}")
                else:
                    violation_duration = now - self.budget_violations[budget_name]
                    
                    # Auto-disable features after 2 minutes (120 seconds)
                    if violation_duration >= 120:
                        self._enable_degraded_mode(f"Budget exceeded: {budget_name}")
                        logger.error(f"Entering degraded mode due to {budget_name} violation for {violation_duration:.0f}s")
            else:
                # Clear violation if budget is now OK
                if budget_name in self.budget_violations:
                    violation_duration = now - self.budget_violations[budget_name]
                    logger.info(f"Budget violation cleared: {budget_name} after {violation_duration:.0f}s")
                    del self.budget_violations[budget_name]
        
        # Check if we can exit degraded mode
        if not budgets or all(budgets.values()):
            self._disable_degraded_mode()

    def _enable_degraded_mode(self, reason: str):
        """Enable degraded mode by disabling heavy features"""
        flags = self._load_feature_flags()
        
        # Update degradation flags
        flags.update(self.degradation_flags)
        flags['degraded_mode'] = True
        flags['degraded_reason'] = reason
        flags['degraded_at'] = datetime.now().isoformat()
        flags['last_updated'] = datetime.now().isoformat()
        
        self._save_feature_flags(flags)
        logger.warning(f"Degraded mode enabled: {reason}")

    def _disable_degraded_mode(self):
        """Disable degraded mode and restore features"""
        flags = self._load_feature_flags()
        
        # Only exit degraded mode if currently in it
        if not flags.get('degraded_mode', False):
            return
            
        # Restore feature flags
        flags.update({
            'charts_enabled': True,
            'agents_run_enabled': True,
            'enable_ai_agents': True,
            'enable_advanced_charting': True,
            'enable_realtime_agents': True,
            'enable_background_kpi_jobs': True,
            'degraded_mode': False,
            'degraded_reason': None,
            'restored_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        })
        
        self._save_feature_flags(flags)
        logger.info("Degraded mode disabled - features restored")

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        flags = self._load_feature_flags()
        return flags.get(feature_name, True)

    def is_degraded_mode(self) -> Dict[str, Any]:
        """Check if system is in degraded mode"""
        flags = self._load_feature_flags()
        return {
            'degraded': flags.get('degraded_mode', False),
            'reason': flags.get('degraded_reason', None)
        }

    def get_performance_status(self) -> Dict[str, Any]:
        """Get current performance status"""
        budgets = self.check_budgets()
        degraded = self.is_degraded_mode()
        
        return {
            'budgets': budgets,
            'degraded_mode': degraded,
            'memory_mb': self.get_memory_usage_mb(),
            'violations': {
                name: time.time() - start_time 
                for name, start_time in self.budget_violations.items()
            },
            'timestamp': datetime.now().isoformat()
        }

# Global instance
guardrails = PerformanceGuardrails()

def record_request_metrics(endpoint: str, latency_ms: float, cache_hit: bool = False):
    """Convenience function to record request metrics"""
    guardrails.record_request_latency(endpoint, latency_ms)
    if cache_hit:
        guardrails.record_cache_hit(endpoint)
    else:
        guardrails.record_cache_miss(endpoint)

def check_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    return guardrails.is_feature_enabled(feature_name)

def get_degraded_status() -> Dict[str, Any]:
    """Get degraded mode status for API responses"""
    return guardrails.is_degraded_mode()
