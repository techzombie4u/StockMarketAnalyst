
"""
Performance Profiler and Budget Enforcer
Monitors performance and auto-disables heavy features when budgets exceeded
"""

import time
import logging
from functools import wraps
from typing import Callable, Dict, Any
from .telemetry import telemetry
from ..config.feature_flags import feature_flags

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    def __init__(self):
        self._budget_violations = {}
        self._last_check = time.time()
        
    def profile_execution(self, metric_name: str):
        """Decorator to profile function execution time"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    telemetry.increment('function_calls')
                    return result
                except Exception as e:
                    telemetry.increment('function_errors')
                    raise
                finally:
                    execution_time = time.time() - start_time
                    telemetry.record_histogram(f'{metric_name}_execution_time', execution_time)
                    
                    # Check if execution time exceeds budget
                    if execution_time > 1.0:  # 1 second threshold
                        logger.warning(f"Slow execution: {metric_name} took {execution_time:.2f}s")
                        
            return wrapper
        return decorator
        
    def check_and_enforce_budgets(self):
        """Check budgets and auto-disable features if violated"""
        now = time.time()
        
        # Only check every 30 seconds to avoid overhead
        if now - self._last_check < 30:
            return
            
        self._last_check = now
        budgets = telemetry.check_budgets()
        
        # Check for budget violations
        for budget_name, is_ok in budgets.items():
            if not is_ok:
                violation_key = budget_name
                
                # Track violation duration
                if violation_key not in self._budget_violations:
                    self._budget_violations[violation_key] = now
                    logger.warning(f"Budget violation detected: {budget_name}")
                else:
                    violation_duration = now - self._budget_violations[violation_key]
                    
                    # Auto-disable features after 3 minutes of violation
                    if violation_duration > 180:  # 3 minutes
                        self._auto_disable_features(budget_name)
                        self._budget_violations[violation_key] = now  # Reset timer
            else:
                # Clear violation if budget is now OK
                if violation_key in self._budget_violations:
                    del self._budget_violations[violation_key]
                    
    def _auto_disable_features(self, budget_name: str):
        """Auto-disable heavy features based on budget violation"""
        logger.warning(f"Auto-disabling heavy features due to budget violation: {budget_name}")
        
        if budget_name == 'memory_under_budget':
            feature_flags.set_flag('enable_dynamic_confidence', False)
            feature_flags.set_flag('enable_visual_roi_trends', False)
            feature_flags.set_flag('enable_all_timeframes_concurrent', False)
            logger.warning("Disabled memory-intensive features")
            
        elif budget_name == 'api_calls_under_limit':
            feature_flags.set_flag('enable_realtime_agents', False)
            logger.warning("Disabled real-time agents due to API call limit")
            
        elif budget_name == 'job_queue_ok':
            feature_flags.set_flag('enable_all_timeframes_concurrent', False)
            logger.warning("Disabled concurrent timeframes due to job queue overload")

# Global profiler instance
profiler = PerformanceProfiler()

def performance_monitor(metric_name: str):
    """Decorator for performance monitoring"""
    return profiler.profile_execution(metric_name)
