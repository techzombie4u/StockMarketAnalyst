import os
from flask import Flask, request, g, jsonify
from src.core.logging import before_request, after_request

def create_app():
    """Create and configure Flask application"""
    try:
        app = Flask(__name__, 
                    template_folder='../../web/templates',
                    static_folder='../../web/static')

        # Optimize Flask configuration for performance
        app.config.update({
            'SECRET_KEY': 'fusion-stock-analyst-key',
            'DEBUG': False,  # Disable debug for performance
            'JSON_SORT_KEYS': False,
            'JSON_COMPACT': True,
            'SEND_FILE_MAX_AGE_DEFAULT': 31536000,  # 1 year cache
            'PROPAGATE_EXCEPTIONS': True,
            'PRESERVE_CONTEXT_ON_EXCEPTION': False
        })

        # Add memory-optimized before/after request handlers
        @app.before_request
        def optimize_request():
            pass  # Lightweight request prep

        @app.after_request
        def optimize_response(response):
            # Add cache headers for static content
            if request.endpoint == 'static':
                response.cache_control.max_age = 31536000
            return response

        # Health check endpoint
        @app.route("/health")
        def health():
            return {"status": "healthy", "message": "Server is running"}, 200

        # Root endpoint
        @app.route("/")
        def index():
            return {"message": "Stock Analyst API", "status": "active"}, 200

        print("✅ Optimized Flask app created")
        return app

    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        raise