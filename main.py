"""
Main entry point for the Stock Market Analyst application
Routes to either organized version or backup based on availability
"""

import os
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
            # Test import without importing Callable separately
            from src.core.app import app
            return True, "Organized structure is functional"
        except ImportError as e:
            return False, f"Import error in organized structure: {e}"
        except Exception as e:
            return False, f"Error in organized structure: {e}"

    except Exception as e:
        return False, f"Failed to check organized structure: {e}"

def run_organized_version():
    """Run the organized version of the application"""
    try:
        logger.info("🚀 Starting Stock Market Analyst - Version 1.7.1 (Organized Version)")

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
        logger.info("🚀 Starting Stock Market Analyst - Version 1.7.1 (Backup Version)")

        # Change to backup directory
        backup_dir = '_backup_before_organization'
        if os.path.exists(backup_dir):
            # Add backup directory to Python path
            backup_path = os.path.abspath(backup_dir)
            if backup_path not in sys.path:
                sys.path.insert(0, backup_path)
            
            logger.info(f"🔄 Using backup version from: {backup_path}")

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
        raise

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