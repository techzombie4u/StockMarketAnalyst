# src/run_server.py
import os, sys

# Absolute paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))           # /.../src
ROOT_DIR = os.path.dirname(SRC_DIR)                            # /.../

# Make both 'src' and its parent importable:
# - so 'core', 'fusion', 'agents' (from SRC_DIR) import works
# - and 'src.core', 'src.fusion' (from ROOT_DIR) import works
for p in (SRC_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from core.app import create_app
from src.app.api.fusion import fusion_bp
from src.app.api.meta import meta_bp
from src.app.api.predictions import predictions_bp
from src.equities.api import equities_bp
from src.options.api import options_bp
from src.commodities.api import commodities_bp
from src.core.pins_locks import pins_locks_bp

if __name__ == "__main__":
    app = create_app()

    # Register blueprints
    app.register_blueprint(fusion_bp)
    app.register_blueprint(meta_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(equities_bp)
    app.register_blueprint(options_bp)
    app.register_blueprint(commodities_bp)
    app.register_blueprint(pins_locks_bp)

    # Debug: Print all registered routes
    print("\n🔍 Registered routes:")
    route_count = 0
    api_routes = []
    for rule in app.url_map.iter_rules():
        route_count += 1
        route_info = f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]"
        print(route_info)
        if '/api/' in rule.rule:
            api_routes.append(rule.rule)

    print(f"\n📊 Total routes: {route_count}")
    print(f"📊 API routes: {len(api_routes)}")

    if api_routes:
        print("\n🔗 API Endpoints:")
        for route in sorted(api_routes):
            print(f"  http://0.0.0.0:5000{route}")
    else:
        print("\n⚠️  No API routes found! Check blueprint registration.")

    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found", "message": "The requested endpoint does not exist"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Internal server error", "message": str(error)}, 500

    print(f"\n🚀 Starting server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)