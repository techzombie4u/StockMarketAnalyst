
# src/fusion/api/fusion.py
from flask import Blueprint, jsonify, render_template, request
import time
from datetime import datetime, timezone

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
