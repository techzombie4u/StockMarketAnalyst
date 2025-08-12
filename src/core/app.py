import os
import time
import uuid
from flask import Flask, request, jsonify, g
import logging
from datetime import datetime
from src.core.logging import add_request_logging
from src.core.metrics import metrics
from src.core.guardrails import guardrails

def create_app():
    """Create and configure Flask application"""
    try:
        app = Flask(__name__,
                    template_folder='../../web/templates',
                    static_folder='../../web/static')

        # Basic Flask configuration
        app.config.update({
            'SECRET_KEY': 'fusion-stock-analyst-key',
            'DEBUG': False,
            'JSON_SORT_KEYS': False,
            'PROPAGATE_EXCEPTIONS': True
        })

        # Configure logging
        logging.basicConfig(level=logging.INFO)

        # Add request tracking middleware
        @app.before_request
        def before_request():
            g.start_time = time.time()
            g.request_id = str(uuid.uuid4())

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
                print(f"REQUEST_LOG: {log_entry}")

                # Update metrics
                endpoint = request.path
                metrics.increment(f"requests_total_{endpoint}")
                if response.status_code >= 400:
                    metrics.increment(f"errors_total_{endpoint}")

                metrics.record_latency(endpoint, duration_ms)

                # Record guardrails metrics
                cache_hit = response.headers.get('X-Cache-Hit', 'false').lower() == 'true'
                guardrails.record_request_latency(endpoint, duration_ms)
                if cache_hit:
                    guardrails.record_cache_hit(endpoint)
                else:
                    guardrails.record_cache_miss(endpoint)

                # Enforce guardrails
                guardrails.enforce_guardrails()

            except Exception as e:
                print(f"Error in after_request middleware: {e}")

            return response

        # Add request logging middleware (already handled by after_request, but keeping for completeness if add_request_logging does more)
        # app = add_request_logging(app) # This line might be redundant or need careful integration if add_request_logging is purely for logging and not middleware insertion. Assuming after_request handles the core logging.

        # Health check endpoint
        @app.route("/health")
        def health():
            return jsonify({"status": "healthy", "message": "Server is running"})

        # Root endpoint
        @app.route("/")
        def index():
            return jsonify({"message": "Stock Analyst API", "status": "active"})

        # JSON Error handlers
        @app.errorhandler(404)
        def not_found(error):
            return jsonify({"success": False, "error": "not_found"}), 404

        @app.errorhandler(500)
        def server_error(error):
            return jsonify({"success": False, "error": "server_error"}), 500

        # Metrics endpoint
        @app.route('/metrics')
        def get_metrics():
            """Get application metrics"""
            return jsonify(metrics.get_metrics())

        # Performance status endpoint
        @app.route('/api/performance/status')
        def get_performance_status():
            """Get performance guardrails status"""
            from src.core.guardrails import guardrails
            return jsonify(guardrails.get_performance_status())

        # Register blueprints with proper URL prefixes
        try:
            from src.api.fusion_api import fusion_bp
            app.register_blueprint(fusion_bp, url_prefix="/api/fusion")
            print("✅ Registered fusion_bp")
        except Exception as e:
            print(f"⚠️  Failed to register fusion_bp: {e}")

        try:
            from src.agents.api.agents import agents_bp as agents_api_bp
            app.register_blueprint(agents_api_bp, url_prefix="/api/agents")
            print("✅ Registered agents_bp")
        except Exception as e:
            print(f"⚠️  Failed to register agents_bp: {e}")

        # Import and register other blueprints with prefixes
        blueprints_to_register = []
        
        try:
            from src.core.pins_locks import pins_locks_bp
            blueprints_to_register.append((pins_locks_bp, "/api", "pins_locks_bp"))
        except Exception as e:
            print(f"⚠️  Failed to import pins_locks_bp: {e}")
            
        try:
            from src.equities.api import equities_bp
            blueprints_to_register.append((equities_bp, "/api/equities", "equities_bp"))
        except Exception as e:
            print(f"⚠️  Failed to import equities_bp: {e}")
            
        try:
            from src.options.api import options_bp
            blueprints_to_register.append((options_bp, "/api/options", "options_bp"))
        except Exception as e:
            print(f"⚠️  Failed to import options_bp: {e}")
            
        try:
            from src.commodities.api import commodities_bp
            blueprints_to_register.append((commodities_bp, "/api/commodities", "commodities_bp"))
        except Exception as e:
            print(f"⚠️  Failed to import commodities_bp: {e}")
            
        try:
            from src.kpi.api import kpi_bp
            blueprints_to_register.append((kpi_bp, "/api/kpi", "kpi_bp"))
        except Exception as e:
            print(f"⚠️  Failed to import kpi_bp: {e}")

        for bp, prefix, name in blueprints_to_register:
            try:
                app.register_blueprint(bp, url_prefix=prefix)
                print(f"✅ Registered {name}")
            except Exception as e:
                print(f"⚠️  Failed to register {name}: {e}")

        # OpenAPI specification endpoint
        @app.route('/api', methods=['GET'])
        def serve_openapi_spec():
            """Serve the OpenAPI specification"""
            try:
                import yaml
                import os

                # Get the path to openapi.yaml in repo root
                repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                openapi_path = os.path.join(repo_root, 'openapi.yaml')

                if os.path.exists(openapi_path):
                    with open(openapi_path, 'r') as f:
                        spec = yaml.safe_load(f)
                    return jsonify(spec)
                else:
                    return jsonify({
                        "error": "OpenAPI specification not found",
                        "message": "The openapi.yaml file is missing from the repository root"
                    }), 404

            except Exception as e:
                return jsonify({
                    "error": "Failed to load OpenAPI specification",
                    "details": str(e)
                }), 500

        # Swagger UI integration
        try:
            from flask_swagger_ui import get_swaggerui_blueprint
            
            # Swagger UI Blueprint
            SWAGGER_URL = '/docs'
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
            print("✅ Registered Swagger UI at /docs")
            
        except ImportError:
            print("⚠️  flask-swagger-ui not available. Install with: pip install flask-swagger-ui")

        print("✅ Flask app created successfully")
        return app

    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        raise

app = create_app()