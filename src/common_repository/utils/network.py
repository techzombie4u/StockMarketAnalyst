
"""
Network utilities with rate limiting, backoff, and circuit breaker
"""

import time
import random
import threading
import logging
from typing import Dict, Callable, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from .telemetry import telemetry

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
    def acquire(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.time()
            # Refill tokens based on time passed
            time_passed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + time_passed * self.refill_rate
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

class CircuitBreaker:
    def __init__(self, failure_threshold: float = 0.5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = threading.Lock()
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        with self.lock:
            # Check if circuit should transition states
            self._check_state_transition()
            
            if self.state == CircuitState.OPEN:
                raise Exception("Circuit breaker is OPEN")
                
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise
            
    def _check_state_transition(self):
        now = time.time()
        
        if self.state == CircuitState.OPEN:
            if (self.last_failure_time and 
                now - self.last_failure_time > self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker transitioning to HALF_OPEN")
                
        elif self.state == CircuitState.HALF_OPEN:
            if self.success_count > 0:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker transitioning to CLOSED")
                
    def _record_success(self):
        with self.lock:
            self.success_count += 1
            if self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = max(0, self.failure_count - 1)
                
    def _record_failure(self):
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            total_calls = self.failure_count + self.success_count
            if total_calls >= 10:  # Minimum calls before evaluating
                failure_rate = self.failure_count / total_calls
                if failure_rate >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker OPEN due to failure rate: {failure_rate:.2%}")

class RateLimiter:
    def __init__(self):
        # Global token bucket: 30 requests/min, burst 10
        self.global_bucket = TokenBucket(capacity=10, refill_rate=30/60)
        
        # Per-symbol rate limiting: min 30s between calls
        self.symbol_last_call = defaultdict(float)
        self.symbol_lock = threading.Lock()
        
        # Circuit breakers per provider
        self.circuit_breakers = defaultdict(lambda: CircuitBreaker())
        
    def can_make_request(self, symbol: str) -> bool:
        """Check if request is allowed for symbol"""
        # Check global rate limit
        if not self.global_bucket.acquire():
            logger.debug(f"Global rate limit exceeded for {symbol}")
            return False
            
        # Check per-symbol rate limit
        with self.symbol_lock:
            now = time.time()
            last_call = self.symbol_last_call[symbol]
            
            if now - last_call < 30:  # 30 second minimum interval
                logger.debug(f"Symbol rate limit active for {symbol}")
                return False
                
            self.symbol_last_call[symbol] = now
            return True
            
    def make_request_with_retry(self, provider: str, func: Callable, 
                               max_retries: int = 3, *args, **kwargs) -> Any:
        """Make request with exponential backoff retry"""
        circuit_breaker = self.circuit_breakers[provider]
        
        for attempt in range(max_retries + 1):
            try:
                return circuit_breaker.call(func, *args, **kwargs)
                
            except Exception as e:
                if attempt == max_retries:
                    raise
                    
                # Exponential backoff with jitter
                base_delay = 0.5 * (2 ** attempt)  # 0.5s, 1s, 2s
                jitter = random.uniform(-0.2, 0.2) * base_delay
                delay = base_delay + jitter
                
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}), "
                             f"retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
                
    def get_circuit_state(self, provider: str) -> str:
        """Get circuit breaker state for provider"""
        return self.circuit_breakers[provider].state.value
        
    def reset_circuit(self, provider: str):
        """Reset circuit breaker for provider"""
        circuit_breaker = self.circuit_breakers[provider]
        with circuit_breaker.lock:
            circuit_breaker.state = CircuitState.CLOSED
            circuit_breaker.failure_count = 0
            circuit_breaker.success_count = 0
            
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            'global_tokens': self.global_bucket.tokens,
            'tracked_symbols': len(self.symbol_last_call),
            'circuit_states': {
                provider: cb.state.value 
                for provider, cb in self.circuit_breakers.items()
            }
        }

# Global rate limiter instance
rate_limiter = RateLimiter()
