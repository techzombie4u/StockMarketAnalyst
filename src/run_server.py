#!/usr/bin/env python3
"""
Main server runner for Fusion Stock Analyst
Starts the Flask application with proper configuration
"""

import os
import sys
from pathlib import Path
import gc
import time
import uuid
from flask import Flask, jsonify, request, render_template
from werkzeug.exceptions import HTTPException

# Add src to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Import core components
try:
    # Import create_app here to ensure path is set before importing other core modules
    from core.app import create_app
    app = create_app()
    from core.metrics import metrics
    from core.guardrails import guardrails
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)

# --- Metrics and Guardrails ---

def get_metrics():
    """Get system metrics including guardrails status."""
    base_metrics = metrics.get_metrics()
    guardrails_status = guardrails.get_performance_status()

    return {
        **base_metrics,
        'guardrails': guardrails_status
    }

# --- Route Definitions ---

# Health check endpoint
@app.route('/health')
def health_check():
    """Provides the health status of the service."""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "service": "fusion-stock-analyst"
    })

# UI Routes
@app.route('/')
@app.route('/dashboard')
def dashboard():
    """Renders the main dashboard page."""
    return render_template('dashboard.html', title="Fusion Stock Analyst Dashboard")

@app.route('/equities')
def equities():
    """Renders the equities page."""
    return render_template('equities.html', title="Equities")

@app.route('/options')
def options():
    """Renders the options page."""
    return render_template('options.html', title="Options")

@app.route('/commodities')
def commodities():
    """Renders the commodities page."""
    return render_template('commodities.html', title="Commodities")

# Fusion Dashboard API (simplified for this example)
@app.route('/api/fusion/dashboard')
def fusion_dashboard():
    """Main dashboard data endpoint."""
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
            "All": {"predictionAccuracy": 0.72, "sharpe": 1.35, "sortino": 1.48, "maxDrawdown": -0.08, "expectancy": 1.42, "coverage": 0.89},
            "30D": {"predictionAccuracy": 0.74, "sharpe": 1.28, "sortino": 1.41, "maxDrawdown": -0.06, "expectancy": 1.38, "coverage": 0.85},
            "10D": {"predictionAccuracy": 0.69, "sharpe": 1.15, "sortino": 1.32, "maxDrawdown": -0.04, "expectancy": 1.25, "coverage": 0.82}
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
            {"symbol": "TCS", "product": "Equity", "signal_score": 8.7, "current_price": 4275.30, "target_price": 4500.00, "potential_roi": 0.0526, "ai_verdict": "STRONG_BUY", "confidence": 0.87},
            {"symbol": "RELIANCE", "product": "Equity", "signal_score": 8.2, "current_price": 2904.10, "target_price": 3100.00, "potential_roi": 0.0675, "ai_verdict": "BUY", "confidence": 0.82},
            {"symbol": "INFY", "product": "Equity", "signal_score": 7.8, "current_price": 1588.20, "target_price": 1680.00, "potential_roi": 0.0578, "ai_verdict": "BUY", "confidence": 0.78}
        ],
        "pinned_rollup": {"total": 8, "met": 5, "not_met": 2, "in_progress": 1},
        "alerts": ["Market volatility above normal levels", "3 positions approaching stop loss"],
        "insights": "Strong buy signals in IT sector. Consider increasing allocation.",
        "agent_insights": [
            {"message": "AI sentiment analysis shows bullish trend"},
            {"message": "Options flow indicates institutional buying"}
        ]
    })

# KPI API
@app.route('/api/kpi/metrics')
def kpi_metrics():
    """Returns KPI metrics for a given timeframe."""
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

# Guardrails metrics endpoint
@app.route('/api/metrics/guardrails')
def guardrails_metrics():
    """Provides guardrails performance status and degraded mode information."""
    status = guardrails.get_performance_status()
    degraded = guardrails.is_degraded_mode()

    return jsonify({
        "degraded": degraded['degraded'],
        "reason": degraded['reason'],
        "memory_mb": status['memory_mb'],
        "budgets": status['budgets'],
        "violations": status['violations'],
        "timestamp": status['timestamp']
    })

# Metrics endpoint
@app.route('/metrics')
def metrics_endpoint():
    """Exposes all collected metrics."""
    return jsonify(get_metrics())

# JSON Error handlers
@app.errorhandler(404)
def nf(_):
    """Handles 404 Not Found errors."""
    return jsonify({"success":False,"error":"not_found"}), 404

@app.errorhandler(500)
def se(e):
    """Handles 500 Internal Server Errors."""
    print(f"Server Error: {e}")
    import traceback
    traceback.print_exc()
    return jsonify({"success":False,"error":"server_error"}), 500

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Handles generic HTTP exceptions, returning JSON."""
    return jsonify({"success":False,"error": e.name.lower().replace(" ", "_"), "message": e.description}), e.code

def main():
    """Main server entry point"""
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"🚀 Starting Fusion Stock Analyst on {host}:{port}")
    print(f"📊 Debug mode: {debug}")

    # Import all route modules to register them
    try:
        # These imports register blueprints and routes automatically
        import fusion.api.fusion
        import equities.api
        import options.api
        import commodities.api
        import kpi.api
        import core.pins_locks
        import agents.api.agents
        print("✅ All API modules and blueprints loaded successfully")
    except ImportError as e:
        print(f"⚠️ Error loading API modules or blueprints: {e}")
        # Decide if this is a fatal error or if the app can continue with partial functionality
        # For now, we'll print the error and continue, assuming some core functionality might still be available.

    # Print registered routes for debugging
    print("\n📝 Registered routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"  {rule.rule} [{methods}]")

    # Attempt to start the server
    try:
        # Run the Flask app. Debug=True is useful for development.
        # For production, consider Gunicorn or uWSGI and set debug=False.
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable reloader for stability
        )
    except OSError as e:
        print(f"❌ Failed to start server on port {port}: {e}")
        print("Please check if the port is already in use or try a different port.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ An unexpected error occurred during server startup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()