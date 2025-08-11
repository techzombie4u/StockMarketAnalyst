import os
from flask import Flask, request, jsonify

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

        print("✅ Flask app created successfully")
        return app

    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        raise