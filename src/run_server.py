#!/usr/bin/env python3

import sys
import os
import gc
import time
from pathlib import Path
import uuid
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

# Add src to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(current_dir))

# Initialize metrics (assuming a simple dictionary for demonstration)
metrics = {
    "requests_total": {},
    "latency_p95_ms": {}
}

# Placeholder for a simple logging/metrics module
# In a real scenario, this would be a separate file (e.g., src/core/logging.py and src/core/metrics.py)
# For this example, we'll define the necessary functions here.

# --- src/core/logging.py ---
def before_request():
    """Set up request-specific context."""
    request_id = str(uuid.uuid4())
    request.request_id = request_id
    request.start_time = time.time()
    print(f"[{request.request_id}] Incoming request: {request.method} {request.path}")

def after_request(response):
    """Log request details and update metrics."""
    request_id = getattr(request, 'request_id', 'no-id')
    start_time = getattr(request, 'start_time', time.time())
    duration_ms = (time.time() - start_time) * 1000
    method = request.method
    path = request.path
    status_code = response.status_code

    print(f"[{request_id}] Request completed: {method} {path} - Status: {status_code} - Duration: {duration_ms:.2f}ms")

    # Update metrics
    # Update requests_total
    path_metrics = metrics["requests_total"]
    path_metrics[path] = path_metrics.get(path, 0) + 1

    # Update latency_p95_ms (simplified: just storing duration for now, real P95 would need more data)
    # In a real application, you'd use a proper metrics library (e.g., Prometheus client)
    # For this example, we'll just store the current duration as a placeholder for latency.
    # A proper implementation would aggregate latencies and calculate percentiles.
    latency_metrics = metrics["latency_p95_ms"]
    latency_metrics[path] = duration_ms # This is a simplification

    return response

# --- src/core/metrics.py ---
# (Metrics dictionary is defined globally above for this single-file example)
def get_metrics():
    """Returns the current metrics data."""
    return metrics

# --- End of src/core/logging.py and src/core/metrics.py ---


def cleanup_memory():
    """Clean up memory to improve performance"""
    gc.collect()
    print(f"🧹 Memory cleanup completed")

def create_minimal_app():
    """Create a minimal Flask app that works"""
    from flask import Flask, jsonify, request
    from werkzeug.exceptions import HTTPException
    import uuid
    import time

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

    # JSON Error handlers
    @app.errorhandler(404)
    def nf(_):
        return jsonify({"success":False,"error":"not_found"}), 404

    @app.errorhandler(500)
    def se(e):
        # Log the exception details on the server side
        print(f"Server Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success":False,"error":"server_error"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
        response = e.get_response()
        # Replace the default HTML error response with a JSON response
        return jsonify({"success":False,"error": e.name.lower().replace(" ", "_"), "message": e.description}), e.code

    # Metrics endpoint
    @app.route('/metrics')
    def metrics_endpoint():
        return jsonify(get_metrics())

    return app

def register_blueprints_safely(app):
    """Register blueprints with error handling"""
    blueprints_count = 0

    # Register logging hooks
    try:
        # In a real scenario, these would be imported from src.core.logging
        # For this example, they are defined in this file.
        app.before_request(before_request)
        app.after_request(after_request)
        print("✅ Registered logging hooks")
    except Exception as e:
        print(f"⚠️  Failed to register logging hooks: {e}")

    try:
        # Import and register pins/locks blueprint
        from src.core.pins_locks import pins_locks_bp
        app.register_blueprint(pins_locks_bp)
        print("✅ Registered pins_locks_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register pins_locks_bp: {e}")

    try:
        # Import and register equities blueprint
        from src.equities.api import equities_bp
        app.register_blueprint(equities_bp)
        print("✅ Registered equities_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register equities_bp: {e}")

    try:
        # Import and register options blueprint
        from src.options.api import options_bp
        app.register_blueprint(options_bp)
        print("✅ Registered options_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register options_bp: {e}")

    try:
        # Import and register commodities blueprint
        from src.commodities.api import commodities_bp
        app.register_blueprint(commodities_bp)
        print("✅ Registered commodities_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register commodities_bp: {e}")

    try:
        # Import and register kpi blueprint
        from src.kpi.api import kpi_bp
        app.register_blueprint(kpi_bp)
        print("✅ Registered kpi_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register kpi_bp: {e}")

    try:
        # Import and register agents blueprint
        from src.agents.api import agents_bp
        app.register_blueprint(agents_bp)
        print("✅ Registered agents_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register agents_bp: {e}")

    # Register Fusion API blueprint
    try:
        from src.fusion.api.fusion import fusion_api_bp
        app.register_blueprint(fusion_api_bp)
        print("✅ Registered fusion_api_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register fusion_api_bp: {e}")


    print(f"📊 Successfully registered {blueprints_count} blueprints")
    return blueprints_count

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
        print("🔄 Registering blueprints and hooks...")
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
        print("🔗 Metrics: http://0.0.0.0:5000/metrics")


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