
#!/usr/bin/env python3

import sys
import os
import gc
import time
from pathlib import Path
import uuid
from flask import Flask, jsonify, request, render_template
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
    path_metrics = metrics["requests_total"]
    path_metrics[path] = path_metrics.get(path, 0) + 1

    latency_metrics = metrics["latency_p95_ms"]
    latency_metrics[path] = duration_ms

    return response

def get_metrics():
    """Returns the current metrics data."""
    return metrics

def cleanup_memory():
    """Clean up memory to improve performance"""
    gc.collect()
    print(f"🧹 Memory cleanup completed")

def create_minimal_app():
    """Create a minimal Flask app that works"""
    app = Flask(__name__,
                template_folder='../web/templates',
                static_folder='../web/static')

    # Basic configuration
    app.config.update({
        'SECRET_KEY': 'fusion-stock-analyst-key',
        'DEBUG': False,
        'JSON_SORT_KEYS': False,
        'PROPAGATE_EXCEPTIONS': True
    })

    # Web Routes - Serve HTML pages
    @app.route('/')
    def index():
        return render_template('dashboard.html', title="Fusion Stock Analyst Dashboard")

    @app.route('/dashboard')
    def dashboard():
        return render_template('dashboard.html', title="Dashboard")

    @app.route('/equities')
    def equities():
        return render_template('equities.html', title="Equities")

    @app.route('/options')
    def options():
        return render_template('options.html', title="Options")

    @app.route('/commodities')
    def commodities():
        return render_template('commodities.html', title="Commodities")

    # API Routes
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "message": "Server is running"})

    @app.route('/api/test')
    def api_test():
        return jsonify({"success": True, "message": "API is working"})

    # Fusion Dashboard API
    @app.route('/api/fusion/dashboard')
    def fusion_dashboard():
        """Main dashboard data endpoint"""
        return jsonify({
            "kpis": {
                "total_portfolio_value": 2850000,
                "total_pnl": 125000,
                "total_positions": 45,
                "win_rate": 0.72,
                "sharpe_ratio": 1.35,
                "max_drawdown": -0.08
            },
            "timeframes": {
                "All": {
                    "predictionAccuracy": 0.72,
                    "sharpe": 1.35,
                    "sortino": 1.48,
                    "maxDrawdown": -0.08,
                    "expectancy": 1.42,
                    "coverage": 0.89
                },
                "30D": {
                    "predictionAccuracy": 0.74,
                    "sharpe": 1.28,
                    "sortino": 1.41,
                    "maxDrawdown": -0.06,
                    "expectancy": 1.38,
                    "coverage": 0.85
                },
                "10D": {
                    "predictionAccuracy": 0.69,
                    "sharpe": 1.15,
                    "sortino": 1.32,
                    "maxDrawdown": -0.04,
                    "expectancy": 1.25,
                    "coverage": 0.82
                }
            },
            "summary": {
                "pinned_items": 8,
                "locked_items": 3,
                "alerts": [
                    {"message": "High volatility detected in TCS"},
                    {"message": "RELIANCE approaching target price"}
                ]
            },
            "top_signals": [
                {
                    "symbol": "TCS",
                    "product": "Equity",
                    "signal_score": 8.7,
                    "current_price": 4275.30,
                    "target_price": 4500.00,
                    "potential_roi": 0.0526,
                    "ai_verdict": "STRONG_BUY",
                    "confidence": 0.87
                },
                {
                    "symbol": "RELIANCE",
                    "product": "Equity", 
                    "signal_score": 8.2,
                    "current_price": 2904.10,
                    "target_price": 3100.00,
                    "potential_roi": 0.0675,
                    "ai_verdict": "BUY",
                    "confidence": 0.82
                },
                {
                    "symbol": "INFY",
                    "product": "Equity",
                    "signal_score": 7.8,
                    "current_price": 1588.20,
                    "target_price": 1680.00,
                    "potential_roi": 0.0578,
                    "ai_verdict": "BUY",
                    "confidence": 0.78
                }
            ],
            "pinned_rollup": {
                "total": 8,
                "met": 5,
                "not_met": 2,
                "in_progress": 1
            },
            "alerts": [
                "Market volatility above normal levels",
                "3 positions approaching stop loss"
            ],
            "insights": "Strong buy signals in IT sector. Consider increasing allocation.",
            "agent_insights": [
                {"message": "AI sentiment analysis shows bullish trend"},
                {"message": "Options flow indicates institutional buying"}
            ]
        })

    # KPI API
    @app.route('/api/kpi/metrics')
    def kpi_metrics():
        timeframe = request.args.get('timeframe', 'all')
        return jsonify({
            "timeframe": timeframe,
            "prediction_accuracy": 0.72,
            "sharpe_ratio": 1.35,
            "sortino_ratio": 1.48,
            "max_drawdown": -0.08,
            "expectancy": 1.42,
            "coverage": 0.89,
            "last_updated": "2024-08-11T16:45:00Z"
        })

    # JSON Error handlers
    @app.errorhandler(404)
    def nf(_):
        return jsonify({"success":False,"error":"not_found"}), 404

    @app.errorhandler(500)
    def se(e):
        print(f"Server Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success":False,"error":"server_error"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Return JSON instead of HTML for HTTP errors."""
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
        app.before_request(before_request)
        app.after_request(after_request)
        print("✅ Registered logging hooks")
    except Exception as e:
        print(f"⚠️  Failed to register logging hooks: {e}")

    try:
        # Import and register pins/locks blueprint
        from src.core.pins_locks import pins_locks_bp
        app.register_blueprint(pins_locks_bp, url_prefix="/api")
        print("✅ Registered pins_locks_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register pins_locks_bp: {e}")

    try:
        # Import and register equities blueprint
        from src.equities.api import equities_bp
        app.register_blueprint(equities_bp, url_prefix="/api/equities")
        print("✅ Registered equities_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register equities_bp: {e}")

    try:
        # Import and register options blueprint
        from src.options.api import options_bp
        app.register_blueprint(options_bp, url_prefix="/api/options")
        print("✅ Registered options_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register options_bp: {e}")

    try:
        # Import and register commodities blueprint
        from src.commodities.api import commodities_bp
        app.register_blueprint(commodities_bp, url_prefix="/api/commodities")
        print("✅ Registered commodities_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register commodities_bp: {e}")

    try:
        # Import and register KPI blueprint
        from src.kpi.api import kpi_bp
        app.register_blueprint(kpi_bp, url_prefix="/api/kpi")
        print("✅ Registered kpi_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register kpi_bp: {e}")

    try:
        # Import and register agents blueprint
        from src.agents.api.agents import agents_bp
        app.register_blueprint(agents_bp, url_prefix="/api/agents")
        print("✅ Registered agents_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register agents_bp: {e}")

    try:
        # Import and register fusion API blueprint
        from src.api.fusion_api import fusion_bp
        app.register_blueprint(fusion_bp, url_prefix="/api/fusion")
        print("✅ Registered fusion_bp")
        blueprints_count += 1
    except Exception as e:
        print(f"⚠️  Failed to register fusion_bp: {e}")

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
        print("🔗 Dashboard: http://0.0.0.0:5000/")
        print("🔗 Health check: http://0.0.0.0:5000/health")
        print("🔗 API test: http://0.0.0.0:5000/api/test")
        print("🔗 Metrics: http://0.0.0.0:5000/metrics")

        # Try different ports if 5000 is in use
        port = 5000
        for attempt in range(5):
            try:
                app.run(
                    host="0.0.0.0",
                    port=port,
                    debug=False,
                    threaded=True,
                    use_reloader=False
                )
                break
            except OSError as e:
                if "Address already in use" in str(e) and attempt < 4:
                    port += 1
                    print(f"🔄 Port {port-1} in use, trying port {port}...")
                    continue
                else:
                    raise

    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
