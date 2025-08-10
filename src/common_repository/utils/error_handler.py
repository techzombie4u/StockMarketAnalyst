
"""
Error handling utilities
"""

import logging
import traceback
from typing import Any, Callable, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ErrorContext:
    """Context manager for error handling"""
    
    def __init__(self, operation: str, suppress_errors: bool = False):
        self.operation = operation
        self.suppress_errors = suppress_errors
        self.error = None
        self.success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            self.success = False
            logger.error(f"Error in {self.operation}: {exc_val}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            if self.suppress_errors:
                return True  # Suppress the exception
        else:
            self.success = True
        
        return False  # Don't suppress the exception

def safe_execute(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """Execute function safely with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        return default

@contextmanager
def suppress_errors(operation: str = "operation"):
    """Context manager to suppress and log errors"""
    try:
        yield
    except Exception as e:
        logger.error(f"Suppressed error in {operation}: {e}")
        logger.debug(f"Traceback: {traceback.format_exc()}")

def log_error(operation: str, error: Exception, extra_data: Optional[dict] = None):
    """Log error with context"""
    error_msg = f"Error in {operation}: {error}"
    
    if extra_data:
        error_msg += f" | Extra data: {extra_data}"
    
    logger.error(error_msg)
    logger.debug(f"Traceback: {traceback.format_exc()}")
