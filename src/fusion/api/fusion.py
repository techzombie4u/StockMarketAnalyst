from flask import Blueprint, jsonify, render_template, request
import time
from datetime import datetime, timezone
import os
import json

fusion_bp = Blueprint("fusion", __name__)

# Simple in-memory cache
_cache = {"payload": None, "ts": 0}
_TTL = 30  # seconds

def _now_iso():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

def _payload():
    # Build a fresh payload with a new timestamp each time this is called
    return {
        "last_updated_utc": _now_iso(),
        "market_session": "CLOSED",
        "timeframes": [
            {"timeframe": tf, "prediction_kpis": {}, "financial_kpis": {}, "risk_kpis": {}}
            for tf in ["All","3D","5D","10D","15D","30D"]
        ],
        "ai_verdict_summary": {},
        "product_breakdown": {},
        "pinned_summary": {"total": 5, "met": 2, "not_met": 2, "in_progress": 1},
        "top_signals": [
            {"symbol":"RELIANCE","ai_verdict_normalized":"BUY","confidence":68.0},
            {"symbol":"TCS","ai_verdict_normalized":"STRONG_BUY","confidence":74.0},
            {"symbol":"INFY","ai_verdict_normalized":"HOLD","confidence":61.0},
        ],
        "alerts": [{"msg":"Sample alert"}],
        "generation_time_ms": 0.1
    }

@fusion_bp.route("/dashboard")
def fusion_api():
    force = (request.args.get("forceRefresh", "") or "").lower() in ("1", "true", "yes")
    now = time.time()

    # Serve cached unless force-refresh is requested AND cache is valid
    if not force and _cache["payload"] and (now - _cache["ts"] < _TTL):
        return jsonify(_cache["payload"])

    # Build a fresh payload (this will have a new last_updated_utc)
    data = _payload()
    _cache["payload"] = data
    _cache["ts"] = now
    return jsonify(data)

@fusion_bp.route("/fusion-dashboard")
def fusion_page():
    return render_template("fusion_dashboard.html")

@fusion_bp.route('/health')
def health():
    return {"status": "ok", "service": "fusion"}

def load_pins():
    """Helper function to load pins data from fixtures"""
    pins_data = {"equities": [], "options": [], "commodities": []}
    try:
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'fixtures')
        
        # Load equity pins
        equity_pins_file = os.path.join(fixtures_dir, 'equities_pins.json')
        if os.path.exists(equity_pins_file):
            with open(equity_pins_file, 'r') as f:
                pins_data["equities"] = json.load(f)

        # Load options pins
        options_pins_file = os.path.join(fixtures_dir, 'options_pins.json')
        if os.path.exists(options_pins_file):
            with open(options_pins_file, 'r') as f:
                pins_data["options"] = json.load(f)

        # Load commodities pins
        commodities_pins_file = os.path.join(fixtures_dir, 'commodities_pins.json')
        if os.path.exists(commodities_pins_file):
            with open(commodities_pins_file, 'r') as f:
                pins_data["commodities"] = json.load(f)
    except Exception as e:
        print(f"Error loading pins data: {e}") # Log the error for debugging
        # Return empty defaults if any error occurs during loading
        pins_data = {"equities": [], "options": [], "commodities": []}
    return pins_data

@fusion_bp.route('/pins')
def get_pins():
    """Get pinned items across all modules"""
    try:
        pins_data = load_pins()
        return jsonify({
            "pinned_equities": pins_data.get("equities", []),
            "pinned_options": pins_data.get("options", []),
            "pinned_commodities": pins_data.get("commodities", []),
            "total_pinned": len(pins_data.get("equities", [])) + len(pins_data.get("options", [])) + len(pins_data.get("commodities", [])),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@fusion_bp.route('/dashboard-data')
def dashboard():
    """Return dashboard data with KPIs and summary"""
    try:
        # Get data from all modules
        equities_data = {"positions": []}
        options_data = {"positions": []}
        commodities_data = {"positions": []}
        agents_data = {"runs": []}

        try:
            # Try to get sample data from fixtures
            fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'fixtures')

            # Load equities data
            equities_file = os.path.join(fixtures_dir, 'equities_sample.json')
            if os.path.exists(equities_file):
                with open(equities_file, 'r') as f:
                    data = json.load(f)
                    equities_data = data if isinstance(data, dict) else {"positions": data}

            # Load options data  
            options_file = os.path.join(fixtures_dir, 'options_sample.json')
            if os.path.exists(options_file):
                with open(options_file, 'r') as f:
                    data = json.load(f)
                    options_data = data if isinstance(data, dict) else {"positions": data}

            # Load commodities data
            commodities_file = os.path.join(fixtures_dir, 'commodities_sample.json')
            if os.path.exists(commodities_file):
                with open(commodities_file, 'r') as f:
                    data = json.load(f)
                    commodities_data = data if isinstance(data, dict) else {"positions": data}

        except Exception as e:
            pass  # Use empty defaults

        # Calculate basic KPIs
        total_positions = len(equities_data.get('positions', [])) + len(options_data.get('positions', [])) + len(commodities_data.get('positions', []))
        total_value = sum(pos.get('market_value', 0) for pos in equities_data.get('positions', [])) + \
                      sum(pos.get('market_value', 0) for pos in options_data.get('positions', [])) + \
                      sum(pos.get('market_value', 0) for pos in commodities_data.get('positions', []))
        total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in equities_data.get('positions', [])) + \
                    sum(pos.get('unrealized_pnl', 0) for pos in options_data.get('positions', [])) + \
                    sum(pos.get('unrealized_pnl', 0) for pos in commodities_data.get('positions', []))

        dashboard_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "kpis": {
                "total_positions": total_positions,
                "total_portfolio_value": total_value,
                "total_pnl": total_pnl,
                "win_rate": 65.4 if total_positions > 0 else 0,
                "sharpe_ratio": 1.23 if total_positions > 0 else 0,
                "max_drawdown": -8.5 if total_positions > 0 else 0
            },
            "summary": {
                "active_positions": total_positions,
                "pinned_items": 0, # This will be populated by the pins endpoint call
                "locked_items": 0,
                "alerts": []
            },
            "recent_activity": [
                {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "action": "position_opened",
                    "symbol": "TCS",
                    "details": "Opened long position"
                }
            ]
        }

        # Fetch pinned items separately if needed for summary
        try:
            pins_summary = load_pins()
            dashboard_data["summary"]["pinned_items"] = len(pins_summary.get("equities", [])) + len(pins_summary.get("options", [])) + len(pins_summary.get("commodities", []))
        except Exception as e:
            print(f"Could not fetch pins for dashboard summary: {e}")
            dashboard_data["summary"]["pinned_items"] = 0 # Default to 0 if error

        return jsonify(dashboard_data)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "summary": {
                "pinned_items": 0,
                "locked_items": 0,
                "active_positions": 0,
                "alerts": []
            },
            "kpis": {
                "total_portfolio_value": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0,
                "total_positions": 0
            },
            "recent_activity": [],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500