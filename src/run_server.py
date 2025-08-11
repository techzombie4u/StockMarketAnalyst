
# src/run_server.py
import os, sys

# Absolute paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))           # /.../src
ROOT_DIR = os.path.dirname(SRC_DIR)                            # /.../

# Make both 'src' and its parent importable
for p in (SRC_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.app import create_app

def safe_import_blueprint(module_path, blueprint_name):
    """Safely import a blueprint with error handling"""
    try:
        module = __import__(module_path, fromlist=[blueprint_name])
        blueprint = getattr(module, blueprint_name)
        print(f"✅ Successfully imported {blueprint_name} from {module_path}")
        return blueprint
    except Exception as e:
        print(f"⚠️  Failed to import {blueprint_name} from {module_path}: {e}")
        return None

if __name__ == "__main__":
    try:
        app = create_app()

        # Try to register blueprints safely
        blueprints_to_register = [
            ('src.app.api.fusion', 'fusion_bp'),
            ('src.app.api.meta', 'meta_bp'),
            ('src.app.api.predictions', 'predictions_bp'),
            ('src.equities.api', 'equities_bp'),
            ('src.options.api', 'options_bp'),
            ('src.commodities.api', 'commodities_bp'),
            ('src.core.pins_locks', 'pins_locks_bp'),
        ]

        registered_blueprints = []
        for module_path, blueprint_name in blueprints_to_register:
            blueprint = safe_import_blueprint(module_path, blueprint_name)
            if blueprint:
                try:
                    app.register_blueprint(blueprint)
                    registered_blueprints.append(blueprint_name)
                    print(f"✅ Registered blueprint: {blueprint_name}")
                except Exception as e:
                    print(f"❌ Failed to register {blueprint_name}: {e}")

        # Add error handlers
        @app.errorhandler(404)
        def not_found(error):
            return {"error": "Not found", "message": "The requested endpoint does not exist"}, 404

        @app.errorhandler(500)
        def internal_error(error):
            return {"error": "Internal server error", "message": str(error)}, 500

        # Debug: Print all registered routes
        print(f"\n🔍 Registered {len(registered_blueprints)} blueprints: {registered_blueprints}")
        print("\nRegistered routes:")
        route_count = 0
        api_routes = []
        for rule in app.url_map.iter_rules():
            route_count += 1
            print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
            if '/api/' in rule.rule:
                api_routes.append(rule.rule)

        print(f"\n📊 Total routes: {route_count}")
        print(f"📊 API routes: {len(api_routes)}")

        if api_routes:
            print("\n🔗 API Endpoints:")
            for route in sorted(api_routes):
                print(f"  http://0.0.0.0:5000{route}")

        print(f"\n🚀 Starting server on http://0.0.0.0:5000")
        app.run(host="0.0.0.0", port=5000, debug=True)

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
