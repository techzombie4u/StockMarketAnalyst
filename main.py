"""
Main entry point for the Stock Market Analyst application
Routes to either organized version or backup based on availability
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Callable
import warnings
import importlib
import time
from datetime import datetime
import traceback

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_flask_cache():
    """Clear Flask-related modules from cache"""
    modules_to_clear = []
    for module_name in sys.modules.keys():
        if 'app' in module_name.lower() and 'flask' in str(sys.modules[module_name]):
            modules_to_clear.append(module_name)

    for module_name in modules_to_clear:
        if module_name in sys.modules:
            logger.info(f"Cleared module: {module_name}")
            del sys.modules[module_name]

def check_organized_structure():
    """Check if organized structure is available and functional"""
    try:
        # Check if src directory exists and has required modules
        if not os.path.exists('src'):
            return False, "src directory not found"

        if not os.path.exists('src/core'):
            return False, "src/core directory not found"

        if not os.path.exists('src/core/app.py'):
            return False, "src/core/app.py not found"

        # Try to import the main modules to check for import errors
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        try:
            # Test import of the main app - this should now work with fixed imports
            from src.core.app import app
            return True, "Organized structure is functional"
        except ImportError as e:
            logger.error(f"Import error in organized structure: {e}")
            return False, f"Import error in organized structure: {e}"
        except Exception as e:
            logger.error(f"Error in organized structure: {e}")
            return False, f"Error in organized structure: {e}"

    except Exception as e:
        logger.error(f"Failed to check organized structure: {e}")
        return False, f"Failed to check organized structure: {e}"

def try_organized_structure():
    """Try to run the organized structure version"""
    try:
        # Clear any existing Flask app modules
        clear_flask_cache()

        # Try to import the organized structure
        logger.info("🔄 Attempting to load organized structure...")

        # Add src to path if not already there
        src_path = os.path.join(os.getcwd(), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Ensure typing imports are available globally
        import typing
        from typing import Callable, Dict, List, Optional, Any, Union

        # Make Callable available in the global namespace for imports
        globals()['Callable'] = Callable

        # Import and run the organized app
        from src.core.app import app, initialize_app

        logger.info("✅ Organized structure loaded successfully")

        # Initialize the application
        initialize_app()

        return app

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in organized structure: {error_msg}")

        # Check for specific import errors that we can handle
        if "name 'Callable' is not defined" in error_msg:
            logger.warning("⚠️ Callable import error detected, attempting comprehensive fix...")
            try:
                # Force clean import with proper typing setup
                import typing
                from typing import Callable, Dict, List, Optional, Any, Union

                # Clear all related modules from cache
                modules_to_clear = [k for k in sys.modules.keys() if k.startswith('src.')]
                for module in modules_to_clear:
                    if module in sys.modules:
                        del sys.modules[module]

                # Set up proper namespace
                typing.Callable = Callable
                globals()['Callable'] = Callable

                # Retry import with comprehensive typing setup
                from src.core.app import app, initialize_app
                logger.info("✅ Fixed Callable import with comprehensive approach")
                initialize_app()
                return app

            except Exception as fix_error:
                logger.error(f"Failed to fix Callable import: {fix_error}")

        logger.warning(f"⚠️ Error in organized structure: {error_msg}")
        return None

def run_organized_version():
    """Run the organized version of the application"""
    try:
        logger.info("🚀 Starting Stock Market Analyst - Version 1.7.2 (Organized Version)")

        # Import the app directly without separate Callable import
        from src.core.app import app

        # Run the Flask application
        logger.info("✅ Running organized Flask application")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True
        )

    except Exception as e:
        logger.error(f"❌ Error starting organized version: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def run_backup_version():
    """Run the backup version of the application"""
    try:
        logger.info("🚀 Starting Stock Market Analyst - Version 1.7.2 (Backup Version)")

        # Change to backup directory
        backup_dir = '_backup_before_organization'
        if os.path.exists(backup_dir):
            # Add backup directory to Python path
            backup_path = os.path.abspath(backup_dir)
            if backup_path not in sys.path:
                sys.path.insert(0, backup_path)

            logger.info(f"🔄 Using backup version from: {backup_path}")

            # Clear any existing Flask app instances to prevent route conflicts
            modules_to_remove = [key for key in sys.modules.keys() if 'src.core.app' in key or key.endswith('.app')]
            for module in modules_to_remove:
                try:
                    del sys.modules[module]
                    logger.info(f"Cleared module: {module}")
                except KeyError:
                    pass

            # Import and run backup app
            from app import app
            logger.info("✅ Running backup Flask application")
            app.run(
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        else:
            logger.error("❌ Backup directory not found")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error starting backup version: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Try to run a minimal version instead of completely failing
        try:
            logger.info("🔄 Attempting minimal emergency version...")
            run_emergency_version()
        except Exception as emergency_error:
            logger.error(f"❌ Emergency version also failed: {emergency_error}")
            raise

def run_emergency_version():
    """Run a minimal emergency version"""
    from flask import Flask, jsonify, render_template_string

    emergency_app = Flask(__name__)

    @emergency_app.route('/')
    def home():
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Stock Market Analyst - Emergency Mode</title></head>
        <body>
            <h1>🔧 Stock Market Analyst - Emergency Mode</h1>
            <p>The application is running in emergency mode due to startup issues.</p>
            <p>Please check the console logs for more details.</p>
            <a href="/api/health">Health Check</a>
        </body>
        </html>
        ''')

    @emergency_app.route('/api/health')
    def health():
        return jsonify({'status': 'emergency_mode', 'message': 'Application running in emergency mode'})

    logger.info("🚨 Running in emergency mode")
    emergency_app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    try:
        # Check organized structure availability
        is_organized_available, message = check_organized_structure()

        if is_organized_available:
            logger.info(f"✅ {message}")
            run_organized_version()
        else:
            logger.warning(f"⚠️ {message}")
            logger.info("🔄 Falling back to backup version...")
            run_backup_version()

    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)