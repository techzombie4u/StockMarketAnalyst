
#!/usr/bin/env python3
"""
Stock Market Analyst - Main Entry Point
Version 1.7.1 - Reverted to backup version

This is the main entry point for the Stock Market Analyst application.
"""

import sys
import os

# Add the backup directory to Python path to use the original files
backup_dir = os.path.join(os.path.dirname(__file__), '_backup_before_organization')
if os.path.exists(backup_dir):
    sys.path.insert(0, backup_dir)
    print(f"🔄 Using backup version from: {backup_dir}")
else:
    print("❌ Backup directory not found, using current organized structure")

try:
    # Try to import and run from backup first
    if backup_dir in sys.path:
        print("🚀 Starting Stock Market Analyst - Version 1.7.1 (Backup Version)")
        import main as backup_main
        # Execute the backup version
        if hasattr(backup_main, 'main'):
            backup_main.main()
        else:
            # If no main function, just import and let it run
            pass
    else:
        # Fallback to organized structure
        from src.core.main import main
        main()

except Exception as e:
    print(f"❌ Error starting backup version: {e}")
    print("🔄 Falling back to organized structure...")
    try:
        from src.core.main import main
        main()
    except Exception as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        print("🆘 Please check the application structure")
        sys.exit(1)
