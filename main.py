
"""
Stock Market Analyst - Optimized Main Entry Point

Memory-optimized startup to prevent disconnections and hangs.
"""

import sys
import os
import logging
import warnings

# Suppress unnecessary warnings that cause console spam
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Configure minimal logging
logging.basicConfig(
    level=logging.WARNING,  # Reduced logging to prevent I/O overhead
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Prevent memory leaks from TensorFlow
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

def main():
    """Optimized main function with resource limits"""
    try:
        print("🚀 Starting Stock Market Analyst Application")
        
        # Set resource limits to prevent memory leaks
        try:
            import resource
            # Set memory limit to 512MB
            resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))
            print("✅ Memory limits set")
        except:
            print("⚠️ Could not set memory limits")
        
        # Import core app only when needed
        from src.core.app import app, initialize_app, cleanup_resources
        
        # Initialize with minimal overhead
        initialize_app()
        
        # Configure for maximum stability
        app.config.update({
            'SEND_FILE_MAX_AGE_DEFAULT': 0,
            'TEMPLATES_AUTO_RELOAD': False,
            'JSON_SORT_KEYS': False,
            'JSONIFY_PRETTYPRINT_REGULAR': False,
            'TESTING': False,
            'PROPAGATE_EXCEPTIONS': False
        })
        
        print("✅ Application initialized successfully")
        print("🌐 Starting web server on http://0.0.0.0:5000")
        
        # Periodic cleanup function
        def periodic_cleanup():
            import threading
            import time
            while True:
                time.sleep(300)  # Every 5 minutes
                cleanup_resources()
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        print("✅ Periodic cleanup started")
        
        # Run with maximum stability settings
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False,
            processes=1,
            request_handler=None  # Use default
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        cleanup_resources()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        cleanup_resources()
        sys.exit(1)
    finally:
        # Final cleanup
        try:
            cleanup_resources()
            import gc
            gc.collect()
            print("✅ Final cleanup completed")
        except:
            pass

if __name__ == '__main__':
    main()
