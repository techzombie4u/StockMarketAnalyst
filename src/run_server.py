
#!/usr/bin/env python3

import sys
import os
import gc
import time
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

def create_minimal_app():
    """Create a minimal Flask app that works"""
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    # Basic configuration
    app.config.update({
        'SECRET_KEY': 'fusion-stock-analyst-key',
        'DEBUG': False,
        'JSON_SORT_KEYS': False,
        'PROPAGATE_EXCEPTIONS': True
    })
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "message": "Server is running"})
    
    @app.route('/')
    def index():
        return jsonify({"message": "Fusion Stock Analyst API", "status": "active"})
    
    @app.route('/api/test')
    def api_test():
        return jsonify({"success": True, "message": "API is working"})
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found", "message": str(error)}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Server error", "message": str(error)}), 500
    
    return app

def register_blueprints_safely(app):
    """Register blueprints with comprehensive error handling"""
    blueprints_registered = 0
    
    # Blueprint configurations
    blueprint_configs = [
        ('src.core.pins_locks', 'pins_locks_bp'),
        ('src.equities.api', 'equities_bp'),
        ('src.options.api', 'options_bp'),
        ('src.commodities.api', 'commodities_bp'),
        ('src.kpi.api', 'kpi_bp'),
        ('src.agents.api', 'agents_bp'),
    ]
    
    for module_path, blueprint_name in blueprint_configs:
        try:
            # Import the module
            module = __import__(module_path, fromlist=[blueprint_name])
            blueprint = getattr(module, blueprint_name)
            
            # Register the blueprint
            app.register_blueprint(blueprint)
            blueprints_registered += 1
            print(f"✅ Registered {blueprint_name}")
            
        except ImportError as e:
            print(f"⚠️  Module not found for {blueprint_name}: {e}")
        except AttributeError as e:
            print(f"⚠️  Blueprint not found in module {module_path}: {e}")
        except Exception as e:
            print(f"⚠️  Failed to register {blueprint_name}: {e}")
    
    print(f"📊 Successfully registered {blueprints_registered} blueprints")
    return blueprints_registered

def main():
    """Main server startup with robust error handling"""
    print("🚀 Starting Fusion Stock Analyst Server...")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        # Clean up memory first
        cleanup_memory()
        
        # Create minimal app
        print("🔄 Creating Flask application...")
        app = create_minimal_app()
        print("✅ Basic Flask app created")
        
        # Register blueprints
        print("🔄 Registering blueprints...")
        blueprints_count = register_blueprints_safely(app)
        
        # Show registered routes
        print("\n🔍 Registered routes:")
        route_count = 0
        api_routes = []
        
        for rule in app.url_map.iter_rules():
            route_count += 1
            methods = ', '.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f"  {methods} {rule.rule} -> {rule.endpoint}")
            
            if rule.rule.startswith('/api/'):
                api_routes.append(rule.rule)
        
        print(f"\n📊 Total routes: {route_count}")
        print(f"📊 API routes: {len(api_routes)}")
        print(f"📊 Blueprints: {blueprints_count}")
        
        if api_routes:
            print("\n🔗 Available API endpoints:")
            for route in sorted(api_routes):
                print(f"  http://0.0.0.0:5000{route}")
        
        # Start server
        print(f"\n🚀 Server starting on http://0.0.0.0:5000")
        print("🔗 Health check: http://0.0.0.0:5000/health")
        print("🔗 API test: http://0.0.0.0:5000/api/test")
        
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
