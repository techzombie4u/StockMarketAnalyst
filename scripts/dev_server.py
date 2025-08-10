
#!/usr/bin/env python3
"""
Development server with proper error handling and debugging
"""

import os
import sys
import traceback

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))

def main():
    try:
        print("🔧 Starting Flask server with debugging...")
        print(f"Python path: {sys.path[:3]}")
        
        # Import and create app
        from src.core.app import create_app
        app = create_app()
        
        print("✅ App created successfully")
        print("🌐 Starting server on 127.0.0.1:5000...")
        
        # Run with minimal configuration for stability
        app.run(
            host="127.0.0.1", 
            port=5000, 
            debug=False, 
            use_reloader=False,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("📍 Traceback:")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server Error: {e}")
        print("📍 Traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
