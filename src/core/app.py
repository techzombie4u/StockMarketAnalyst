import os
import time
import uuid
from flask import Flask, request, jsonify, g, render_template
import logging
from datetime import datetime
# from src.core.logging import add_request_logging # This seems to be replaced by custom logging in after_request
from src.core.metrics import metrics
from src.core.guardrails import guardrails

# Import necessary modules for blueprints and swagger
from flask_swagger_ui import get_swaggerui_blueprint
import yaml
from pathlib import Path

# --- Blueprint Imports with Error Handling ---
try:
    from src.api.fusion_api import fusion_bp
    print("✅ Successfully imported fusion_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import fusion API: {e}")
    fusion_bp = None

try:
    from src.equities.api import equities_bp
    print("✅ Successfully imported equities_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import equities API: {e}")
    equities_bp = None

try:
    from src.options.api import options_bp
    print("✅ Successfully imported options_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import options API: {e}")
    options_bp = None

try:
    from src.commodities.api import commodities_bp
    print("✅ Successfully imported commodities_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import commodities API: {e}")
    commodities_bp = None

try:
    from src.agents.api.agents import agents_bp as agents_api_bp
    print("✅ Successfully imported agents_api_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import agents API: {e}")
    agents_api_bp = None

try:
    from src.kpi.api import kpi_bp
    print("✅ Successfully imported kpi_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import KPI API: {e}")
    kpi_bp = None

try:
    from src.core.pins_locks import pins_locks_bp
    print("✅ Successfully imported pins_locks_bp")
except ImportError as e:
    print(f"⚠️ Warning: Could not import pins_locks API: {e}")
    pins_locks_bp = None
# --- End Blueprint Imports ---

def create_app():
    """Create and configure Flask application"""
    try:
        app = Flask(__name__,
                    template_folder='../../web/templates',
                    static_folder='../../web/static')

        # Basic Flask configuration
        app.config.update({
            'SECRET_KEY': 'fusion-stock-analyst-key',
            'DEBUG': False, # Set to False for production environments
            'JSON_SORT_KEYS': False,
            'PROPAGATE_EXCEPTIONS': True # Propagate exceptions to be handled by error handlers
        })

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

        # Add request tracking middleware
        @app.before_request
        def before_request():
            g.start_time = time.time()
            g.request_id = str(uuid.uuid4())
            app.logger.info(f"Request ID: {g.request_id} - Method: {request.method} - Path: {request.path}")

        @app.after_request
        def after_request(response):
            try:
                duration = time.time() - g.start_time
                duration_ms = duration * 1000

                # Add request ID header
                response.headers['X-Request-ID'] = g.request_id

                # Log as JSON
                log_entry = {
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": datetime.now().isoformat()
                }
                app.logger.info(f"REQUEST_LOG: {log_entry}")

                # Update metrics
                endpoint = request.path
                metrics.increment(f"requests_total_{endpoint}")
                if response.status_code >= 400:
                    metrics.increment(f"errors_total_{endpoint}")
                    app.logger.warning(f"Request failed for {endpoint} with status {response.status_code}")

                metrics.record_latency(endpoint, duration_ms)

                # Record guardrails metrics
                cache_hit = response.headers.get('X-Cache-Hit', 'false').lower() == 'true'
                guardrails.record_request_latency(endpoint, duration_ms)
                if cache_hit:
                    guardrails.record_cache_hit(endpoint)
                else:
                    guardrails.record_cache_miss(endpoint)

                # Enforce guardrails - this might need to be called strategically, e.g., before returning
                # guardrails.enforce_guardrails() # Enforcing here might block responses prematurely if not carefully implemented

            except Exception as e:
                app.logger.error(f"Error in after_request middleware: {e}", exc_info=True)

            return response

        # --- Core API Endpoints ---

        # Health check endpoint
        @app.route("/health")
        def health():
            """Health check endpoint"""
            return jsonify({
                "status": "healthy",
                "timestamp": time.time(),
                "version": "1.0.0" # Consider a more dynamic versioning approach
            })

        # Metrics endpoint
        @app.route('/metrics')
        def get_metrics():
            """System metrics endpoint"""
            # In a real-world scenario, these metrics would be dynamically collected
            # For demonstration, using placeholder values
            return jsonify({
                "system": {
                    "uptime": time.time(), # This should be the actual start time + duration
                    "memory_usage": "125MB",
                    "cpu_usage": "15%"
                },
                "application": {
                    "requests_total": metrics.get("requests_total"), # Assuming metrics are stored in a dictionary-like object
                    "requests_per_minute": 45, # Placeholder
                    "response_time_avg_ms": 125, # Placeholder
                    "error_rate": 0.02 # Placeholder
                },
                "business": {
                    "active_users": 8, # Placeholder
                    "api_calls_today": 1250, # Placeholder
                    "cache_hit_rate": 0.85 # Placeholder
                }
            })

        # OpenAPI specification endpoint
        @app.route('/api', methods=['GET'])
        def serve_openapi_spec():
            """Serve the OpenAPI specification"""
            try:
                # Get the path to openapi.yaml in repo root
                # This assumes the file structure: project_root/src/server/server.py
                repo_root = Path(__file__).parent.parent.parent.parent # Adjust path as needed
                openapi_path = repo_root / 'openapi.yaml'

                if openapi_path.exists():
                    with open(openapi_path, 'r') as f:
                        spec = yaml.safe_load(f)
                    return jsonify(spec)
                else:
                    app.logger.error(f"OpenAPI specification not found at {openapi_path}")
                    return jsonify({
                        "error": "OpenAPI specification not found",
                        "message": f"The openapi.yaml file is missing from the repository root at {openapi_path}"
                    }), 404

            except Exception as e:
                app.logger.error(f"Failed to load OpenAPI specification: {e}", exc_info=True)
                return jsonify({
                    "error": "Failed to load OpenAPI specification",
                    "details": str(e)
                }), 500

        # --- UI Routes ---
        @app.route('/')
        def index():
            """Root endpoint redirects to dashboard"""
            return render_template('index.html')

        @app.route('/dashboard')
        def dashboard():
            """Dashboard page"""
            return render_template('dashboard.html')

        @app.route('/equities')
        def equities():
            """Equities page"""
            return render_template('equities.html')

        @app.route('/options')
        def options():
            """Options page"""
            return render_template('options.html')

        @app.route('/commodities')
        def commodities():
            """Commodities page"""
            return render_template('commodities.html')

        # --- Blueprint Registration with Error Handling ---
        blueprints_to_register = [
            (fusion_bp, '/api/fusion', 'Fusion API'),
            (equities_bp, '/api/equities', 'Equities API'),
            (options_bp, '/api/options', 'Options API'),
            (commodities_bp, '/api/commodities', 'Commodities API'),
            (agents_api_bp, '/api/agents', 'Agents API'),
            (kpi_bp, '/api/kpi', 'KPI API'),
            (pins_locks_bp, '/api', 'Pins & Locks API')
        ]

        for blueprint, url_prefix, name in blueprints_to_register:
            if blueprint is not None:
                try:
                    app.register_blueprint(blueprint, url_prefix=url_prefix)
                    app.logger.info(f"✅ Registered {name} at {url_prefix}")
                except Exception as e:
                    app.logger.error(f"❌ Failed to register {name} at {url_prefix}: {e}", exc_info=True)
            else:
                app.logger.warning(f"⚠️ Skipping {name} (blueprint not available)")
        # --- End Blueprint Registration ---

        # --- Swagger UI Integration ---
        try:
            SWAGGER_URL = '/docs'
            # API_URL is the endpoint that serves the OpenAPI spec, which is '/api' in our case
            API_URL = '/api'

            swaggerui_blueprint = get_swaggerui_blueprint(
                SWAGGER_URL,
                API_URL,
                config={
                    'app_name': "Fusion Stock Analyst API",
                    'dom_id': '#swagger-ui',
                    'layout': "StandaloneLayout"
                }
            )
            app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
            app.logger.info(f"✅ Registered Swagger UI at {SWAGGER_URL}")

        except ImportError:
            app.logger.warning("⚠️ flask-swagger-ui not available. Install with: pip install flask-swagger-ui")
        except Exception as e:
            app.logger.error(f"❌ Error setting up Swagger UI: {e}", exc_info=True)
        # --- End Swagger UI Integration ---


        # --- JSON Error Handlers ---
        @app.errorhandler(404)
        def not_found(error):
            app.logger.warning(f"Not Found Error: {request.method} {request.path} - {error}")
            return jsonify({"success": False, "error": "resource_not_found", "message": str(error)}), 404

        @app.errorhandler(500)
        def server_error(error):
            app.logger.error(f"Internal Server Error: {request.method} {request.path} - {error}", exc_info=True)
            return jsonify({"success": False, "error": "internal_server_error", "message": "An unexpected error occurred."}), 500
        # --- End JSON Error Handlers ---


        app.logger.info("✅ Flask app created successfully")
        return app

    except Exception as e:
        # Log the critical error during app creation and re-raise
        logging.critical(f"❌ CRITICAL ERROR creating Flask app: {e}", exc_info=True)
        raise

# Create the app instance
app = create_app()

if __name__ == '__main__':
    # This block is for running the app directly, useful for development
    # In a production environment, use a WSGI server like Gunicorn
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])