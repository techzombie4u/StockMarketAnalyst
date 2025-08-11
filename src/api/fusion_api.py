import json
import time
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from pathlib import Path
import traceback

# Try to import from src.core, fall back to local if not found
try:
    from src.core.cache import ttl_cache, now_iso
except ImportError:
    # Mock implementations if the core modules are not available
    def ttl_cache(ttl_sec, namespace):
        def decorator(func):
            cache = {}
            def wrapper(*args, **kwargs):
                if args not in cache or time.time() - cache[args]['timestamp'] > ttl_sec:
                    cache[args] = {'value': func(*args, **kwargs), 'timestamp': time.time()}
                return cache[args]['value']
            return wrapper
        return decorator

    def now_iso():
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Create blueprint
fusion_bp = Blueprint("fusion", __name__)

# Try to import KPI calculator functions, fall back to mock if not found
try:
    from src.kpi.calculator import get_kpi_summary, compute_all
except ImportError:
    # Mock implementations if the KPI calculator modules are not available
    def get_kpi_summary(timeframe):
        # Mock data for the KPI summary
        return {
            "acc": 0.72, "sharpe": 1.35, "sortino": 1.48, "mdd": -0.08, "winExp": 1.42, "coverage": 0.89
        }
    def compute_all(*args, **kwargs):
        pass # Mock function does nothing


# Use ttl_cache for the dashboard endpoint
_cache = ttl_cache(ttl_sec=60, namespace="fusion")

VALID_TIMEFRAMES = ["All", "3D", "5D", "10D", "15D", "30D"]
VALID_VERDICTS = ['STRONG_BUY', 'BUY', 'HOLD', 'CAUTIOUS', 'AVOID']


@fusion_bp.route("/dashboard", methods=["GET"])
def fusion_dashboard():
    """Main fusion dashboard endpoint"""
    try:
        force_refresh = request.args.get("forceRefresh", "false").lower() == "true"

        print(f"🔄 Fusion dashboard request - force refresh: {force_refresh}")

        # Check cache
        if not force_refresh:
            cached_payload = _cache.get("dashboard")
            if cached_payload:
                print("💾 Returning cached payload")
                return jsonify(cached_payload)

        # Build fresh payload
        print("🔨 Building fresh payload")

        # Get timeframe-specific KPIs using calculator
        timeframes = {}
        for tf in VALID_TIMEFRAMES:
            kpi_data = get_kpi_summary(tf)
            timeframes[tf] = {
                "predictionAccuracy": kpi_data.get("acc", 0.0),
                "sharpe": kpi_data.get("sharpe", 0.0),
                "sortino": kpi_data.get("sortino", 0.0),
                "maxDrawdown": kpi_data.get("mdd", 0.0),
                "expectancy": kpi_data.get("winExp", 0.0),
                "coverage": kpi_data.get("coverage", 0.0)
            }

        # Placeholder for AI verdict summary (can be computed or fetched)
        ai_verdict_summary = {
            "STRONG_BUY": 2,
            "BUY": 5,
            "HOLD": 7,
            "CAUTIOUS": 1,
            "AVOID": 0
        }

        # Placeholder for product breakdown
        product_breakdown = {
            "equities": 10,
            "options": 5
        }

        # Placeholder for pinned summary
        pinned_summary = {
            "total": 8,
            "met": 5,
            "not_met": 2,
            "in_progress": 1
        }

        # Placeholder for top signals (can be derived from KPIs or other sources)
        top_signals = [
            {
                "symbol": "TCS",
                "product": "equity",
                "score": 0.87,
                "ai_verdict_normalized": "BUY"
            },
            {
                "symbol": "INFY",
                "product": "equity",
                "score": 0.91,
                "ai_verdict_normalized": "STRONG_BUY"
            },
            {
                "symbol": "RELIANCE",
                "product": "equity",
                "score": 0.83,
                "ai_verdict_normalized": "BUY"
            },
            {
                "symbol": "HDFCBANK",
                "product": "equity",
                "score": 0.75,
                "ai_verdict_normalized": "HOLD"
            }
        ]

        # Placeholder for alerts
        alerts = [
            "Market volatility above normal levels",
            "3 positions approaching stop loss"
        ]

        # Placeholder for agent insights
        agent_insights = [
            {"message": "AI sentiment analysis shows bullish trend"},
            {"message": "Options flow indicates institutional buying"}
        ]

        payload = {
            "last_updated_utc": now_iso(),
            "market_session": "CLOSED",
            "timeframes": timeframes,
            "ai_verdict_summary": ai_verdict_summary,
            "product_breakdown": product_breakdown,
            "pinned_summary": pinned_summary,
            "top_signals": top_signals,
            "alerts": alerts,
            "insights": "Strong buy signals in IT sector. Consider increasing allocation.",
            "agent_insights": agent_insights,
            "generation_time_ms": 42.0 # Placeholder, ideally measured
        }

        # Cache the payload
        _cache.set("dashboard", payload)

        print(f"✅ Returning payload with generation time: {payload.get('generation_time_ms')}ms")
        return jsonify(payload)

    except Exception as e:
        print(f"❌ Error in fusion dashboard endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "error": "Internal server error",
            "details": str(e),
            "status": "error"
        }), 500

# Add a test route for debugging
@fusion_bp.route("/test", methods=["GET"])
def fusion_test():
    """Test endpoint for fusion API"""
    return jsonify({
        "message": "Fusion API is working",
        "timestamp": now_iso(),
        "status": "ok"
    })

print("✅ Fusion API blueprint created successfully")