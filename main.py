
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
    """Optimized main function with minimal imports"""
    try:
        print("🚀 Starting Stock Market Analyst Application")
        
        # Import core app only when needed
        from src.core.app import app, initialize_app
        
        # Initialize with minimal overhead
        initialize_app()
        
        # Configure for stability
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
        app.config['TEMPLATES_AUTO_RELOAD'] = False
        
        print("✅ Application initialized successfully")
        print("🌐 Starting web server on http://0.0.0.0:5000")
        
        # Run with optimized settings for Replit
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False,  # Disable reloader to prevent multiple processes
            processes=1          # Single process to prevent resource conflicts
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Critical error: {e}")
        sys.exit(1)
    finally:
        # Cleanup any remaining resources
        try:
            import gc
            gc.collect()
        except:
            pass

if __name__ == '__main__':
    main()
