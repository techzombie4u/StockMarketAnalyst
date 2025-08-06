
"""
Enhanced Error Handling Module for Stock Market Analyst

Implements comprehensive error handling, logging, and recovery mechanisms
to improve system reliability without external dependencies.
"""

import logging
import traceback
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
import sys
import os

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stock_analyst.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ErrorTracker:
    """Track and analyze system errors"""
    
    def __init__(self):
        self.error_log_file = 'logs/error_tracking.json'
        self.error_stats = {
            'total_errors': 0,
            'error_types': {},
            'error_frequency': {},
            'recovery_success_rate': 0,
            'last_error_time': None
        }
        self._ensure_log_directory()
        self._load_error_history()
    
    def _ensure_log_directory(self):
        """Ensure logs directory exists"""
        os.makedirs('logs', exist_ok=True)
    
    def _load_error_history(self):
        """Load error history from file"""
        try:
            if os.path.exists(self.error_log_file):
                with open(self.error_log_file, 'r') as f:
                    self.error_stats = json.load(f)
        except Exception as e:
            logging.error(f"Error loading error history: {str(e)}")
    
    def _save_error_history(self):
        """Save error history to file"""
        try:
            with open(self.error_log_file, 'w') as f:
                json.dump(self.error_stats, f, indent=2, default=str)
        except Exception as e:
            logging.error(f"Error saving error history: {str(e)}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict = None, recovered: bool = False):
        """Log an error with context"""
        try:
            self.error_stats['total_errors'] += 1
            self.error_stats['last_error_time'] = datetime.now().isoformat()
            
            # Track error types
            if error_type not in self.error_stats['error_types']:
                self.error_stats['error_types'][error_type] = 0
            self.error_stats['error_types'][error_type] += 1
            
            # Track error frequency by hour
            hour_key = datetime.now().strftime('%Y-%m-%d-%H')
            if hour_key not in self.error_stats['error_frequency']:
                self.error_stats['error_frequency'][hour_key] = 0
            self.error_stats['error_frequency'][hour_key] += 1
            
            # Track recovery success
            if recovered:
                self.error_stats.setdefault('recovered_errors', 0)
                self.error_stats['recovered_errors'] += 1
                
            # Update recovery rate
            if self.error_stats['total_errors'] > 0:
                recovered_count = self.error_stats.get('recovered_errors', 0)
                self.error_stats['recovery_success_rate'] = (recovered_count / self.error_stats['total_errors']) * 100
            
            # Create detailed error record
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'message': error_message,
                'context': context or {},
                'recovered': recovered,
                'stack_trace': traceback.format_exc() if sys.exc_info()[0] else None
            }
            
            # Log to file and console
            logging.error(f"Error tracked: {error_type} - {error_message}")
            if context:
                logging.error(f"Context: {context}")
            
            self._save_error_history()
            
        except Exception as e:
            # Fallback logging if error tracking fails
            logging.critical(f"Error in error tracking system: {str(e)}")
    
    def get_error_summary(self) -> Dict:
        """Get summary of error statistics"""
        try:
            recent_errors = 0
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            for hour_key, count in self.error_stats.get('error_frequency', {}).items():
                try:
                    error_time = datetime.strptime(hour_key, '%Y-%m-%d-%H')
                    if error_time > cutoff_time:
                        recent_errors += count
                except ValueError:
                    continue
            
            return {
                'total_errors': self.error_stats.get('total_errors', 0),
                'recent_errors_24h': recent_errors,
                'recovery_rate': round(self.error_stats.get('recovery_success_rate', 0), 2),
                'most_common_errors': sorted(
                    self.error_stats.get('error_types', {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                'last_error': self.error_stats.get('last_error_time'),
                'system_stability': self._calculate_stability_score()
            }
            
        except Exception as e:
            logging.error(f"Error generating error summary: {str(e)}")
            return {'error': 'Unable to generate error summary'}
    
    def _calculate_stability_score(self) -> str:
        """Calculate system stability score"""
        try:
            total_errors = self.error_stats.get('total_errors', 0)
            recovery_rate = self.error_stats.get('recovery_success_rate', 0)
            
            if total_errors == 0:
                return "Excellent (No errors recorded)"
            elif total_errors < 10 and recovery_rate > 80:
                return "Good (Low error rate, high recovery)"
            elif total_errors < 50 and recovery_rate > 60:
                return "Fair (Moderate errors, decent recovery)"
            else:
                return "Poor (High error rate or low recovery)"
                
        except Exception:
            return "Unknown"

# Global error tracker
error_tracker = ErrorTracker()

class RetryStrategy:
    """Implement retry strategies for failed operations"""
    
    @staticmethod
    def exponential_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """Exponential backoff retry decorator"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        result = func(*args, **kwargs)
                        
                        # Log successful retry if not first attempt
                        if attempt > 0:
                            logging.info(f"Function {func.__name__} succeeded on attempt {attempt + 1}")
                            error_tracker.log_error(
                                'RetrySuccess',
                                f"Function {func.__name__} recovered after {attempt} retries",
                                {'function': func.__name__, 'attempts': attempt + 1},
                                recovered=True
                            )
                        
                        return result
                        
                    except Exception as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            logging.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s")
                            time.sleep(delay)
                        else:
                            # Log final failure
                            error_tracker.log_error(
                                'RetryFailure',
                                f"Function {func.__name__} failed after {max_retries + 1} attempts: {str(e)}",
                                {'function': func.__name__, 'max_retries': max_retries}
                            )
                
                # Re-raise the last exception if all retries failed
                raise last_exception
            
            return wrapper
        return decorator
    
    @staticmethod
    def circuit_breaker(failure_threshold: int = 5, timeout: int = 60):
        """Circuit breaker pattern decorator"""
        failure_count = {}
        last_failure_time = {}
        
        def decorator(func: Callable) -> Callable:
            func_name = func.__name__
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # Check if circuit is open
                if func_name in failure_count:
                    if failure_count[func_name] >= failure_threshold:
                        if current_time - last_failure_time.get(func_name, 0) < timeout:
                            error_msg = f"Circuit breaker open for {func_name}"
                            logging.warning(error_msg)
                            raise Exception(error_msg)
                        else:
                            # Reset circuit breaker after timeout
                            failure_count[func_name] = 0
                            logging.info(f"Circuit breaker reset for {func_name}")
                
                try:
                    result = func(*args, **kwargs)
                    # Reset failure count on success
                    failure_count[func_name] = 0
                    return result
                    
                except Exception as e:
                    # Increment failure count
                    failure_count[func_name] = failure_count.get(func_name, 0) + 1
                    last_failure_time[func_name] = current_time
                    
                    logging.error(f"Circuit breaker failure {failure_count[func_name]}/{failure_threshold} for {func_name}: {str(e)}")
                    
                    if failure_count[func_name] >= failure_threshold:
                        error_tracker.log_error(
                            'CircuitBreakerOpen',
                            f"Circuit breaker opened for {func_name} after {failure_threshold} failures",
                            {'function': func_name, 'threshold': failure_threshold}
                        )
                    
                    raise e
            
            return wrapper
        return decorator

class GracefulDegradation:
    """Implement graceful degradation strategies"""
    
    @staticmethod
    def fallback_data(fallback_value: Any = None, log_fallback: bool = True):
        """Provide fallback data when operations fail"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if log_fallback:
                        logging.warning(f"Using fallback data for {func.__name__}: {str(e)}")
                        error_tracker.log_error(
                            'FallbackUsed',
                            f"Fallback data used for {func.__name__}: {str(e)}",
                            {'function': func.__name__, 'fallback_value': str(fallback_value)},
                            recovered=True
                        )
                    return fallback_value
            return wrapper
        return decorator
    
    @staticmethod
    def partial_success(required_success_rate: float = 0.5):
        """Allow partial success for batch operations"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(items: List[Any], *args, **kwargs):
                successful_items = []
                failed_items = []
                
                for item in items:
                    try:
                        result = func(item, *args, **kwargs)
                        successful_items.append(result)
                    except Exception as e:
                        failed_items.append({'item': item, 'error': str(e)})
                        logging.error(f"Item failed in {func.__name__}: {str(e)}")
                
                success_rate = len(successful_items) / len(items) if items else 0
                
                if success_rate >= required_success_rate:
                    logging.info(f"Partial success in {func.__name__}: {len(successful_items)}/{len(items)} items succeeded")
                    return {
                        'successful': successful_items,
                        'failed': failed_items,
                        'success_rate': success_rate,
                        'status': 'partial_success'
                    }
                else:
                    error_msg = f"Success rate {success_rate} below threshold {required_success_rate}"
                    error_tracker.log_error(
                        'PartialSuccessFailure',
                        error_msg,
                        {'function': func.__name__, 'success_rate': success_rate, 'threshold': required_success_rate}
                    )
                    raise Exception(error_msg)
            
            return wrapper
        return decorator

class DataValidation:
    """Enhanced data validation with error handling"""
    
    @staticmethod
    def validate_stock_data(data: Dict) -> Dict:
        """Validate and clean stock data"""
        try:
            validated_data = {}
            errors = []
            
            # Required fields
            required_fields = ['symbol', 'current_price']
            for field in required_fields:
                if field not in data or data[field] is None:
                    errors.append(f"Missing required field: {field}")
                else:
                    validated_data[field] = data[field]
            
            # Validate price data
            if 'current_price' in data:
                try:
                    price = float(data['current_price'])
                    if price <= 0:
                        errors.append("Price must be positive")
                    else:
                        validated_data['current_price'] = price
                except (ValueError, TypeError):
                    errors.append("Invalid price format")
            
            # Validate technical indicators
            if 'technical' in data and isinstance(data['technical'], dict):
                validated_technical = {}
                for key, value in data['technical'].items():
                    try:
                        if isinstance(value, (int, float)) and not math.isnan(float(value)):
                            validated_technical[key] = float(value)
                        elif isinstance(value, str):
                            validated_technical[key] = value
                    except (ValueError, TypeError):
                        errors.append(f"Invalid technical indicator: {key}")
                
                validated_data['technical'] = validated_technical
            
            # Validate fundamentals
            if 'fundamentals' in data and isinstance(data['fundamentals'], dict):
                validated_fundamentals = {}
                for key, value in data['fundamentals'].items():
                    try:
                        if value is not None:
                            if isinstance(value, bool):
                                validated_fundamentals[key] = value
                            elif isinstance(value, (int, float)):
                                validated_fundamentals[key] = float(value)
                            else:
                                validated_fundamentals[key] = str(value)
                    except (ValueError, TypeError):
                        errors.append(f"Invalid fundamental data: {key}")
                
                validated_data['fundamentals'] = validated_fundamentals
            
            # Add validation results
            validated_data['validation_errors'] = errors
            validated_data['is_valid'] = len(errors) == 0
            
            if errors:
                error_tracker.log_error(
                    'DataValidationError',
                    f"Data validation errors for {data.get('symbol', 'unknown')}: {errors}",
                    {'symbol': data.get('symbol'), 'errors': errors}
                )
            
            return validated_data
            
        except Exception as e:
            error_tracker.log_error(
                'ValidationSystemError',
                f"Error in data validation system: {str(e)}",
                {'data_keys': list(data.keys()) if isinstance(data, dict) else 'not_dict'}
            )
            return {'is_valid': False, 'validation_errors': [f"Validation system error: {str(e)}"]}

# Error handling utilities for the main application
def safe_execute(func: Callable, *args, **kwargs) -> Dict:
    """Safely execute a function with comprehensive error handling"""
    try:
        result = func(*args, **kwargs)
        return {'success': True, 'data': result, 'error': None}
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Safe execution failed for {func.__name__}: {error_msg}")
        error_tracker.log_error(
            'SafeExecutionError',
            f"Safe execution failed for {func.__name__}: {error_msg}",
            {'function': func.__name__, 'args_count': len(args), 'kwargs_keys': list(kwargs.keys())}
        )
        return {'success': False, 'data': None, 'error': error_msg}

def get_system_health_report() -> str:
    """Generate a comprehensive system health report"""
    try:
        error_summary = error_tracker.get_error_summary()
        
        report = []
        report.append("=== SYSTEM HEALTH REPORT ===")
        report.append(f"Total Errors: {error_summary.get('total_errors', 0)}")
        report.append(f"Recent Errors (24h): {error_summary.get('recent_errors_24h', 0)}")
        report.append(f"Recovery Rate: {error_summary.get('recovery_rate', 0)}%")
        report.append(f"System Stability: {error_summary.get('system_stability', 'Unknown')}")
        report.append("")
        
        # Most common errors
        report.append("Most Common Errors:")
        for error_type, count in error_summary.get('most_common_errors', []):
            report.append(f"  • {error_type}: {count} occurrences")
        
        report.append("")
        
        # Health recommendations
        if error_summary.get('total_errors', 0) == 0:
            report.append("✅ System is running smoothly with no errors")
        elif error_summary.get('recovery_rate', 0) > 80:
            report.append("✅ Good error recovery rate - system is resilient")
        elif error_summary.get('recent_errors_24h', 0) > 10:
            report.append("⚠️  High recent error rate - investigate system issues")
        
        return "\n".join(report)
        
    except Exception as e:
        logging.error(f"Error generating health report: {str(e)}")
        return "Error generating system health report"

# Import required modules for math operations
import math

class EnhancedErrorHandler:
    """Enhanced error handler class for the application"""
    
    def __init__(self):
        self.error_tracker = error_tracker
    
    def handle_error(self, error_type: str, error_message: str, context: dict = None):
        """Handle an error with enhanced logging"""
        return self.error_tracker.log_error(error_type, error_message, context)
    
    def get_error_summary(self):
        """Get error summary"""
        return self.error_tracker.get_error_summary()
    
    def safe_execute(self, func, *args, **kwargs):
        """Safely execute a function"""
        return safe_execute(func, *args, **kwargs)
