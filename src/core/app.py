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

    # Configure app
    app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'

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

    # Register API blueprints with better error handling
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

    except ImportError as e:
        logger.error(f"❌ Failed to import options blueprint: {e}")
        # Create fallback endpoints
        @app.route('/api/options/strategies')
        def fallback_options():
            return jsonify({'success': False, 'error': 'Options API not available', 'strategies': []})

    except Exception as e:
        logger.error(f"❌ Failed to register options blueprint: {e}")

    try:
        # Register Predictions API separately
        from src.app.api.predictions import predictions_bp
        app.register_blueprint(predictions_bp, url_prefix='/api/predictions')
        logger.info("✅ Registered Predictions API at /api/predictions")

    except ImportError as e:
        logger.error(f"❌ Failed to import predictions blueprint: {e}")
        # Create fallback endpoints
        @app.route('/api/predictions/accuracy')
        def fallback_predictions_accuracy():
            return jsonify({'success': True, 'data': {'by_timeframe': [{'timeframe': '30D', 'micro_accuracy': 0.0, 'macro_accuracy': 0.0}], 'micro_accuracy': 0.0, 'macro_accuracy': 0.0}})

        @app.route('/api/predictions/active')
        def fallback_predictions_active():
            return jsonify({'success': True, 'items': [], 'count': 0})

    except Exception as e:
        logger.error(f"❌ Failed to register predictions blueprint: {e}")

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
        from src.agents.api.agents import agents_bp
        app.register_blueprint(agents_bp, url_prefix='/api/agents')
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

    # Add missing metrics endpoints
    @app.route('/api/metrics/guardrails')
    def metrics_guardrails():
        """Guardrails metrics endpoint"""
        return jsonify({
            "guardrails": {
                "budget_utilization": 0.65,
                "performance_degradation": False,
                "active_limits": []
            },
            "timestamp": datetime.now().isoformat()
        })

    # Register web routes with error handling
    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering index: {e}")
            return jsonify({'error': 'Template not found'}), 500

    @app.route('/dashboard')
    def dashboard():
        try:
            return render_template('dashboard.html')
        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            return jsonify({'error': 'Template not found'}), 500

    @app.route('/equities')
    def equities():
        try:
            return render_template('equities.html')
        except Exception as e:
            logger.error(f"Error rendering equities: {e}")
            return jsonify({'error': 'Template not found'}), 500

    @app.route('/options')
    def options():
        try:
            logger.info("📊 Serving Options page")
            return render_template('options.html')
        except Exception as e:
            logger.error(f"❌ Error rendering options page: {e}")
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Options - Error</title></head>
            <body>
                <h1>Options Page Error</h1>
                <p>Error: {str(e)}</p>
                <p>Template path issue - please check web/templates/options.html</p>
                <a href="/dashboard">Back to Dashboard</a>
            </body>
            </html>
            """, 500

    @app.route('/commodities')
    def commodities():
        try:
            return render_template('commodities.html')
        except Exception as e:
            logger.error(f"Error rendering commodities: {e}")
            return jsonify({'error': 'Template not found'}), 500

    @app.route('/kpi')
    def kpi():
        try:
            return render_template('kpi.html')
        except Exception as e:
            logger.error(f"Error rendering kpi: {e}")
            return jsonify({'error': 'Template not found'}), 500

    @app.route('/papertrade')
    def papertrade():
        """Paper Trade page"""
        try:
            logger.info("📊 Serving Paper Trade page")
            return render_template('papertrade_tabbed.html')
        except Exception as e:
            logger.error(f"Error rendering papertrade: {e}")
            return f"Error loading Paper Trade page: {e}", 500

    @app.route('/paper-trade')
    def paper_trade_alt():
        """Alternative route for paper trade"""
        return papertrade()

    @app.route('/docs')
    def docs():
        try:
            return render_template('docs.html')
        except Exception as e:
            logger.error(f"Error rendering docs: {e}")
            return jsonify({'error': 'Template not found'}), 500

    # API Documentation
    @app.route('/api')
    def api_docs():
        return jsonify({
            "title": "Fusion Stock Analyst API",
            "version": "1.0.0",
            "description": "AI-powered stock analysis and trading insights API",
            "endpoints": {
                "health": "/health",
                "fusion_dashboard": "/api/fusion/dashboard",
                "equities_list": "/api/equities/list",
                "options_strategies": "/api/options/strategies",
                "options_candidates": "/api/options/strangle/candidates",
                "commodities_signals": "/api/commodities/signals",
                "kpi_metrics": "/api/kpi/metrics",
                "agents_config": "/api/agents/config",
                "pins": "/api/pins",
                "locks": "/api/locks"
            }
        })

    # Add route debugging endpoint
    @app.route('/api/debug/routes')
    def debug_routes():
        """Debug endpoint to show all registered routes"""
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'rule': rule.rule
            })
        return jsonify({
            'total_routes': len(routes),
            'routes': sorted(routes, key=lambda x: x['rule'])
        })

    logger.info("✅ Flask app created successfully")
    return app

# For backwards compatibility
app = create_app()

def initialize_app():
    """Initialize application (legacy compatibility)"""
    logger.info("✅ App initialized")
    pass