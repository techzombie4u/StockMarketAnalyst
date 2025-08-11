
from flask import Blueprint, request, jsonify
from src.core.cache import ttl_cache, now_iso
from src.kpi.calculator import compute_all

fusion_api_bp = Blueprint("fusion_api", __name__, url_prefix="/api/fusion")

@fusion_api_bp.get("/dashboard")
def get_dashboard():
    timeframes = {
        "All": compute_all("All"),
        "3D": compute_all("3D"), 
        "5D": compute_all("5D"),
        "10D": compute_all("10D"),
        "15D": compute_all("15D"),
        "30D": compute_all("30D")
    }
    
    # Top signals across all products
    signals = [
        {"product": "Equities", "symbol": "TCS", "verdict": "STRONG_BUY", "confidence": 0.74, "rationale": "Strong earnings momentum", "updated": now_iso()},
        {"product": "Options", "symbol": "TCS", "verdict": "SELL_STRANGLE", "confidence": 0.68, "rationale": "High IV, range-bound", "updated": now_iso()},
        {"product": "Commodities", "symbol": "GOLD", "verdict": "HOLD", "confidence": 0.58, "rationale": "Mixed technicals", "updated": now_iso()}
    ]
    
    # Pinned rollup
    pinned_rollup = {
        "total": 12,
        "met": 8,
        "not_met": 2,
        "in_progress": 2
    }
    
    # Alerts
    alerts = [
        "High volatility detected in IT sector",
        "Options IV spike in banking stocks",
        "Gold breaking key resistance"
    ]
    
    # GoAhead insights
    insights = "Market showing strong momentum in technology sector with favorable risk-reward setup for equity positions."
    
    return jsonify({
        "timeframes": timeframes,
        "signals": signals,
        "pinned_rollup": pinned_rollup,
        "alerts": alerts,
        "insights": insights,
        "updated": now_iso()
    })

@fusion_api_bp.get("/test")
def test_endpoint():
    return jsonify({"status": "ok", "message": "Fusion API is working", "timestamp": now_iso()})
