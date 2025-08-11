
import os
from flask import Flask, request, g, jsonify
from src.core.logging import before_request, after_request

def create_app():
    """Create and configure Flask application"""
    try:
        app = Flask(__name__, 
                    template_folder='../../web/templates',
                    static_folder='../../web/static')

        # Set up app configuration
        app.config['SECRET_KEY'] = 'your-secret-key-here'
        app.config['DEBUG'] = True
        app.config['JSON_SORT_KEYS'] = False

        # Register request handlers
        app.before_request(before_request)
        app.after_request(after_request)

        # Health check endpoint
        @app.route("/health")
        def health():
            return {"status": "healthy", "message": "Server is running"}, 200

        # Root endpoint
        @app.route("/")
        def index():
            return {"message": "Stock Analyst API", "status": "active"}, 200

        print("✅ Flask app created successfully")
        return app

    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        raise
