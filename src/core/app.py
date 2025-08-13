import os
import sys
import json
import time
from datetime import datetime
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, 
                template_folder='../../web/templates',
                static_folder='../../web/static')

    # Configure CORS
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/health": {"origins": "*"},
        r"/metrics": {"origins": "*"}
    })

    # Basic health endpoint
    @app.route('/health')
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })

    # Metrics endpoint for performance monitoring
    @app.route('/metrics')
    def metrics():
        return jsonify({
            "server_status": "running",
            "uptime_seconds": time.time(),
            "memory_usage_mb": 128,
            "active_connections": 1,
            "timestamp": datetime.now().isoformat()
        })

    # Register API blueprints
    try:
        # Fusion API
        from src.fusion.api.fusion import fusion_bp
        app.register_blueprint(fusion_bp, url_prefix='/api/fusion')
        logger.info("✅ Registered Fusion API at /api/fusion")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Fusion API: {e}")

    try:
        # Equities API
        from src.equities.api import equities_bp
        app.register_blueprint(equities_bp, url_prefix='/api/equities')
        logger.info("✅ Registered Equities API at /api/equities")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Equities API: {e}")

    try:
        # Options API
        from src.options.api import options_bp
        app.register_blueprint(options_bp, url_prefix='/api/options')
        logger.info("✅ Registered Options API at /api/options")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Options API: {e}")

    try:
        # Commodities API
        from src.commodities.api import commodities_bp
        app.register_blueprint(commodities_bp, url_prefix='/api/commodities')
        logger.info("✅ Registered Commodities API at /api/commodities")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Commodities API: {e}")

    try:
        # KPI API
        from src.kpi.api import kpi_bp
        app.register_blueprint(kpi_bp, url_prefix='/api/kpi')
        logger.info("✅ Registered KPI API at /api/kpi")
    except Exception as e:
        logger.warning(f"⚠️ Could not register KPI API: {e}")

    try:
        # Agents API
        from src.agents.api.agents import agents_api_bp
        app.register_blueprint(agents_api_bp, url_prefix='/api/agents')
        logger.info("✅ Registered Agents API at /api/agents")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Agents API: {e}")

    try:
        # Pins & Locks API
        from src.core.pins_locks import pins_locks_bp
        app.register_blueprint(pins_locks_bp, url_prefix='/api')
        logger.info("✅ Registered Pins & Locks API at /api")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Pins & Locks API: {e}")

    # Register Paper Trade API
    try:
        from src.api.papertrade import papertrade_bp
        app.register_blueprint(papertrade_bp, url_prefix='/api/papertrade')
        logger.info("✅ Registered Paper Trade API at /api/papertrade")
    except Exception as e:
        logger.warning(f"⚠️ Could not register Paper Trade API: {e}")

    # UI Routes
    @app.route('/')
    def main_dashboard():
        return render_template('index.html')

    @app.route('/dashboard')
    def kpi_dashboard():
        return render_template('dashboard.html')

    @app.route('/equities')
    def equities():
        return render_template('equities.html')

    @app.route('/options')
    def options():
        return render_template('options.html')

    @app.route('/commodities')
    def commodities():
        return render_template('commodities.html')

    @app.route('/papertrade')
    def papertrade():
        return render_template('papertrade.html')

    # API Documentation
    @app.route('/api')
    @app.route('/docs')
    def api_docs():
        return jsonify({
            "title": "Fusion Stock Analyst API",
            "version": "1.0.0",
            "description": "AI-powered stock analysis and trading insights API",
            "endpoints": {
                "health": "/health",
                "fusion_dashboard": "/api/fusion/dashboard",
                "equities_list": "/api/equities/list",
                "options_candidates": "/api/options/strangle/candidates",
                "commodities_signals": "/api/commodities/signals",
                "kpi_metrics": "/api/kpi/metrics",
                "agents_config": "/api/agents/config",
                "pins": "/api/pins",
                "locks": "/api/locks"
            }
        })

    logger.info("✅ Flask app created successfully")
    return app

# For backwards compatibility
app = create_app()

def initialize_app():
    """Initialize application (legacy compatibility)"""
    logger.info("✅ App initialized")
    pass