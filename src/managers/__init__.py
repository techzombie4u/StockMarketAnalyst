"""
Managers package - Contains various management modules for the application
"""

# Import error tracking for safe module loading
error_tracker = None

def safe_execute(func, *args, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return {'error': str(e), 'success': False}