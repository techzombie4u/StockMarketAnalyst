
#!/usr/bin/env python3

import sys
import os
import gc
import time
import threading
from pathlib import Path

# Add src to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

def cleanup_memory():
    """Clean up memory to improve performance"""
    gc.collect()
    print(f"🧹 Memory cleanup completed")

def create_app_with_fallback():
    """Create Flask app with fallback error handling"""
    try:
        print("🔄 Creating Flask application...")
        
        # Clear memory before starting
        cleanup_memory()
        
        from src.core.app import create_app
        app = create_app()
        
        if app is None:
            raise Exception("App creation returned None")
            
        print("✅ Flask app created successfully")
        return app
        
    except Exception as e:
        print(f"❌ Error creating app: {e}")
        print("🔄 Attempting fallback app creation...")
        
        # Fallback: Create minimal Flask app
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/health')
        def health():
            return jsonify({"status": "ok", "mode": "fallback"})
            
        @app.route('/')
        def index():
            return jsonify({
                "message": "Fusion Stock Analyst - Fallback Mode", 
                "status": "running",
                "endpoints": ["/health"]
            })
            
        print("✅ Fallback app created")
        return app

def register_blueprints_safely(app):
    """Register blueprints with error handling"""
    blueprints_registered = 0
    
    # List of blueprints to try
    blueprint_configs = [
        ('src.core.pins_locks', 'pins_locks_bp', '/api'),
        ('src.products.equities.api', 'equities_bp', '/api/equities'),
        ('src.products.options.api', 'options_bp', '/api/options'),
        ('src.commodities.api', 'commodities_bp', '/api/commodities'),
    ]
    
    for module_path, blueprint_name, url_prefix in blueprint_configs:
        try:
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            app.register_blueprint(blueprint, url_prefix=url_prefix)
            blueprints_registered += 1
            print(f"✅ Registered {blueprint_name}")
        except Exception as e:
            print(f"⚠️  Failed to register {blueprint_name}: {e}")
            
    print(f"📊 Registered {blueprints_registered} blueprints")
    return blueprints_registered

def main():
    """Main server startup"""
    print("🚀 Starting Fusion Stock Analyst Server...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path[:3]}")
    
    try:
        # Create app
        app = create_app_with_fallback()
        
        # Register blueprints
        blueprints_count = register_blueprints_safely(app)
        
        # Add error handlers
        @app.errorhandler(404)
        def not_found(error):
            return {"error": "Not found", "message": str(error)}, 404

        @app.errorhandler(500)
        def server_error(error):
            return {"error": "Server error", "message": str(error)}, 500
        
        # Debug routes
        print("\n🔍 Registered routes:")
        route_count = 0
        for rule in app.url_map.iter_rules():
            route_count += 1
            print(f"  {rule.methods} {rule.rule} -> {rule.endpoint}")
            
        print(f"\n📊 Total routes: {route_count}")
        print(f"📊 Blueprints: {blueprints_count}")
        
        # Start server
        print(f"\n🚀 Server starting on http://0.0.0.0:5000")
        print("🔗 Health check: http://0.0.0.0:5000/health")
        
        # Start memory cleanup timer
        def periodic_cleanup():
            while True:
                time.sleep(300)  # 5 minutes
                cleanup_memory()
                
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        
        app.run(
            host="0.0.0.0", 
            port=5000, 
            debug=False,  # Disable debug for better performance
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server startup failed: {e}")
        print("🔧 Check the error above and try restarting")
        sys.exit(1)

if __name__ == "__main__":
    main()
