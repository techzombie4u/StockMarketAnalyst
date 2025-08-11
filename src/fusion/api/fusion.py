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

@fusion_bp.route("/api/fusion/dashboard")
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

@fusion_bp.route('/dashboard')
def dashboard():
    """Return dashboard data with KPIs and summary"""
    try:
        # Load sample data from fixtures
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'fixtures')

        # Load equities sample data
        equities_file = os.path.join(fixtures_dir, 'equities_sample.json')
        with open(equities_file, 'r') as f:
            equities_data = json.load(f)

        # Calculate basic KPIs
        total_positions = len(equities_data.get('positions', []))
        total_value = sum(pos.get('market_value', 0) for pos in equities_data.get('positions', []))
        total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in equities_data.get('positions', []))

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
                "pinned_items": 0,
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

        return jsonify(dashboard_data)

    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "kpis": {
                "total_positions": 0,
                "total_portfolio_value": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "sharpe_ratio": 0,
                "max_drawdown": 0
            },
            "summary": {
                "active_positions": 0,
                "pinned_items": 0,
                "locked_items": 0,
                "alerts": []
            },
            "recent_activity": []
        }), 500