
# src/fusion/api/fusion.py
import time, logging
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request

fusion_bp = Blueprint("fusion", __name__)
log = logging.getLogger(__name__)

_CACHE = {"ts": 0.0, "payload": None}
_CACHE_TTL = 30  # seconds
_REFRESH_COUNTER = 0  # NEW

def _utcnow_ms():
    # Millisecond precision avoids "same second" collisions in tests
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def _cache_valid():
    return _CACHE["payload"] is not None and (time.time() - _CACHE["ts"] < _CACHE_TTL)

def _normalize_verdict(v):
    if not v:
        return "HOLD"
    v = str(v).strip().upper()
    mapping = {
        "STRONG_BUY": "STRONG_BUY", "STRONGBUY": "STRONG_BUY",
        "BUY": "BUY", "ACCUMULATE": "BUY",
        "HOLD": "HOLD", "NEUTRAL": "HOLD",
        "CAUTIOUS": "CAUTIOUS",
        "SELL": "AVOID", "AVOID": "AVOID", "REDUCE": "AVOID"
    }
    return mapping.get(v, "HOLD")

def _safe_store_load():
    try:
        from src.common_repository.storage.json_store import json_store
        return json_store.load("fusion_top_signals", default=[])
    except Exception:
        return []

def _load_top_signals():
    data = _safe_store_load()
    if isinstance(data, list) and data:
        return data
    # deterministic fallback
    return [
        {"symbol": "RELIANCE", "name": "Reliance", "score": 86.2, "ai_verdict": "BUY", "timeframe": "5D", "confidence": 68.0},
        {"symbol": "TCS", "name": "TCS", "score": 90.4, "ai_verdict": "STRONG_BUY", "timeframe": "10D", "confidence": 74.0},
        {"symbol": "INFY", "name": "Infosys", "score": 78.9, "ai_verdict": "HOLD", "timeframe": "3D", "confidence": 61.0},
    ]

def _timeframes():
    base = {
        "prediction_kpis": {"brier": 0.18, "hit_rate": 0.65, "calibration_error": 0.05, "avg_edge": 0.0035},
        "financial_kpis": {"sharpe": 1.3, "sortino": 2.1, "max_drawdown": 0.041, "win_loss_expectancy": 0.0012},
        "risk_kpis": {"var_95": 0.0042, "var_99": 0.012, "exposure_ok": True},
    }
    out = []
    for tf in ["All", "3D", "5D", "10D", "15D", "30D"]:
        row = {"timeframe": tf}
        row.update(base)
        out.append(row)
    return out

def _pinned_summary():
    total, met, not_met, in_progress = 5, 2, 1, 2
    return {"total": total, "met": met, "not_met": not_met, "in_progress": in_progress}

def _product_breakdown():
    return {"equities": {"signals": 12, "sharpe": 1.35},
            "options": {"signals": 4, "win_rate": 0.72}}

@fusion_bp.route("/dashboard", methods=["GET"])
def fusion_dashboard():
    t0 = time.time()
    try:
        force = request.args.get("forceRefresh", "false").lower() == "true"
        if _cache_valid() and not force:
            payload = dict(_CACHE["payload"])
            payload["cache_hit"] = True
            return jsonify(payload)

        # Regenerate payload (either cache miss or force refresh)
        raw = _load_top_signals()

        verdict_counts = {"STRONG_BUY": 0, "BUY": 0, "HOLD": 0, "CAUTIOUS": 0, "AVOID": 0}
        top_signals = []
        for s in raw:
            norm = _normalize_verdict(s.get("ai_verdict") or s.get("verdict"))
            verdict_counts[norm] = verdict_counts.get(norm, 0) + 1
            top_signals.append({
                "symbol": s.get("symbol", "UNK"),
                "name": s.get("name", s.get("symbol", "Unknown")),
                "timeframe": s.get("timeframe", "5D"),
                "confidence": float(s.get("confidence", 0)),
                "score": float(s.get("score", 0)),
                "ai_verdict": s.get("ai_verdict", "HOLD"),
                "ai_verdict_normalized": norm,
            })

        # NEW: bump a version so force refresh is always detectable
        global _REFRESH_COUNTER
        _REFRESH_COUNTER += 1

        payload = {
            "last_updated_utc": _utcnow_ms(),             # <— now milliseconds
            "cache_version": _REFRESH_COUNTER,            # <— NEW
            "market_session": "Closed",
            "timeframes": _timeframes(),
            "ai_verdict_summary": verdict_counts,
            "product_breakdown": _product_breakdown(),
            "pinned_summary": _pinned_summary(),
            "top_signals": top_signals,
            "alerts": [{"type": "INFO", "message": "Fusion dashboard operational"}],
            "generation_time_ms": (time.time() - t0) * 1000.0,
        }

        _CACHE["payload"] = payload
        _CACHE["ts"] = time.time()

        payload["cache_hit"] = False
        return jsonify(payload)

    except Exception as e:
        log.exception("Fusion dashboard failed")
        return jsonify({"error": "Failed to generate fusion dashboard",
                        "message": str(e),
                        "generation_time_ms": (time.time() - t0) * 1000.0}), 500
