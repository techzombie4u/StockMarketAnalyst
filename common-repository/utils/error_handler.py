
"""
Error Handling Utilities
"""

import logging
import traceback
import functools
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

def safe_execute(func: Callable, default_return: Any = None, 
                log_errors: bool = True) -> Any:
    """Safely execute a function with error handling"""
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__}: {str(e)}")
        return default_return

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                        if delay > 0:
                            import time
                            time.sleep(delay)
                    else:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator

def log_execution_time(func):
    """Decorator to log function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {str(e)}")
            raise
    return wrapper

def validate_input(validation_func: Callable[[Any], bool], 
                  error_message: str = "Invalid input"):
    """Decorator to validate function input"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not validation_func(*args, **kwargs):
                raise ValueError(error_message)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class ErrorContext:
    """Context manager for error handling"""
    
    def __init__(self, operation_name: str, reraise: bool = True):
        self.operation_name = operation_name
        self.reraise = reraise
        self.error = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is not None:
            self.error = exc_value
            logger.error(f"Error in {self.operation_name}: {str(exc_value)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            if not self.reraise:
                return True  # Suppress exception
        
        return False  # Let exception propagate

def format_error_message(error: Exception, context: str = "") -> str:
    """Format error message with context"""
    base_message = f"{type(error).__name__}: {str(error)}"
    if context:
        return f"{context} - {base_message}"
    return base_message
