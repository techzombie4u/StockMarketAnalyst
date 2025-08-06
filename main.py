
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
    # Try to run from organized structure first
    print("🚀 Starting Stock Market Analyst - Version 1.7.1 (Organized Version)")
    from src.core.app import app
    
    # Print startup information
    print("\n" + "="*60)
    print("📈 STOCK MARKET ANALYST - DASHBOARD")
    print("="*60)
    print(f"🌐 Web Dashboard: http://localhost:5000")
    print(f"📊 API Endpoint: http://localhost:5000/api/stocks")
    print(f"🔄 Auto-refresh: Every 60 minutes")
    print("="*60)
    print("\n✅ Application started successfully!")
    print("📱 Open your browser and navigate to http://localhost:5000")
    print("\n🛑 Press Ctrl+C to stop the application\n")

    # Run Flask app directly
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )

except Exception as e:
    print(f"❌ Error starting organized version: {e}")
    print("🔄 Falling back to backup version...")
    try:
        # Try to import and run from backup
        if backup_dir in sys.path:
            print("🚀 Starting Stock Market Analyst - Version 1.7.1 (Backup Version)")
            # Import backup main directly
            sys.path.insert(0, backup_dir)
            import app as backup_app
            
            # Run the backup Flask app
            if hasattr(backup_app, 'app'):
                print("✅ Running backup Flask application")
                backup_app.app.run(
                    host='0.0.0.0',
                    port=5000,
                    debug=False,
                    threaded=True
                )
            else:
                raise Exception("Backup app not found")
        else:
            raise Exception("Backup directory not in path")
    except Exception as fallback_error:
        print(f"❌ Fallback also failed: {fallback_error}")
        print("🆘 Please check the application structure")
        sys.exit(1)
