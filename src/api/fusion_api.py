
from flask import Blueprint, jsonify, request
from datetime import datetime, timezone

fusion_bp = Blueprint("fusion", __name__, url_prefix="/api/fusion")

_CACHE = {"ts": None, "payload": None}
VALID_TIMEFRAMES = ["All", "3D", "5D", "10D", "15D", "30D"]

def _now_utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _build_payload():
    tfs = []
    for tf in VALID_TIMEFRAMES:
        tfs.append({
            "timeframe": tf,
            "prediction_kpis": {"brier": 0.18, "hit_rate": 0.65, "calibration_error": 0.03},
            "financial_kpis": {"sharpe": 1.3, "sortino": 2.1, "drawdown": 0.04},
            "risk_kpis": {"var_95": 0.0045, "var_99": 0.012},
        })
    return {
        "last_updated_utc": _now_utc_iso(),
        "market_session": "CLOSED",
        "timeframes": tfs,
        "ai_verdict_summary": {"STRONG_BUY": 2, "BUY": 5, "HOLD": 7, "CAUTIOUS": 1, "AVOID": 0},
        "product_breakdown": {"equities": 10, "options": 5},
        "pinned_summary": {"total": 5, "met": 2, "not_met": 1, "in_progress": 1},
        "top_signals": [
            {"symbol": "TCS", "product": "equity", "score": 0.87, "ai_verdict_normalized": "BUY"},
            {"symbol": "INFY", "product": "equity", "score": 0.91, "ai_verdict_normalized": "STRONG_BUY"},
        ],
        "alerts": [],
        "generation_time_ms": 42.0,
    }

def _is_cache_valid():
    # keep same stamp until forceRefresh is requested
    return _CACHE["payload"] is not None

@fusion_bp.route("/dashboard", methods=["GET"])
def fusion_dashboard():
    force = request.args.get("forceRefresh", "false").lower() == "true"
    if _is_cache_valid() and not force:
        return jsonify(_CACHE["payload"])
    payload = _build_payload()
    _CACHE["payload"] = payload
    _CACHE["ts"] = payload["last_updated_utc"]
    return jsonify(payload)
