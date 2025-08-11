import os
from flask import Flask, request, jsonify
import logging
from datetime import datetime
from src.core.logging import add_request_logging
from src.core.metrics import metrics

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

        # Add request logging middleware
        app = add_request_logging(app)

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

        print("✅ Flask app created successfully")
        return app

    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        raise
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
