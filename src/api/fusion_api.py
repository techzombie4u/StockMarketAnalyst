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

        start_time = time.time()

        # Check cache
        if not force_refresh:
            cached_payload = _cache.get("dashboard")
            if cached_payload:
                print("💾 Returning cached payload")
                cached_payload["served_from_cache"] = True
                cached_payload["cache_hit_time_ms"] = round((time.time() - start_time) * 1000, 1)
                return jsonify(cached_payload)

        # Build fresh payload
        print("🔨 Building fresh payload")

        # Get timeframe-specific KPIs using calculator with complete families
        timeframes = {}
        for tf in VALID_TIMEFRAMES:
            kpi_data = get_kpi_summary(tf)

            # Prediction KPIs
            prediction_accuracy = round(kpi_data.get("acc", 0.72), 3)
            coverage = round(kpi_data.get("coverage", 0.89), 2)

            # Financial KPIs  
            sharpe = round(kpi_data.get("sharpe", 1.35), 2)
            sortino = round(kpi_data.get("sortino", 1.48), 2)
            expectancy = round(kpi_data.get("winExp", 1.42), 3)

            # Risk KPIs
            max_drawdown = round(kpi_data.get("mdd", -0.08), 3)
            volatility = round(kpi_data.get("volatility", 0.15), 3)
            var_95 = round(kpi_data.get("var_95", -0.12), 3)

            timeframes[tf] = {
                # Prediction Family
                "predictionAccuracy": prediction_accuracy,
                "coverage": coverage,
                "signalQuality": round(prediction_accuracy * coverage, 3),

                # Financial Family
                "sharpe": sharpe,
                "sortino": sortino,
                "expectancy": expectancy,
                "calmarRatio": round(abs(sharpe / max_drawdown) if max_drawdown != 0 else 0, 2),

                # Risk Family
                "maxDrawdown": max_drawdown,
                "volatility": volatility,
                "var95": var_95,
                "riskScore": round((1 + max_drawdown) * (1 - volatility), 3)
            }

        # Use KPI data for main dashboard metrics as well
        default_kpis = get_kpi_summary("All")
        kpis = {
            "predictionAccuracy": round(default_kpis.get("acc", 0.0), 3),
            "sharpe": round(default_kpis.get("sharpe", 0.0), 2),
            "sortino": round(default_kpis.get("sortino", 0.0), 2),
            "maxDrawdown": round(default_kpis.get("mdd", 0.0), 3),
            "expectancy": round(default_kpis.get("winExp", 0.0), 3),
            "coverage": round(default_kpis.get("coverage", 0.0), 2)
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

        # Complete top signals with strict validation
        def validate_verdict(verdict):
            return verdict if verdict in VALID_VERDICTS else "HOLD"

        def generate_rationale(symbol, verdict, score):
            if score > 0.85:
                return f"Strong technical momentum in {symbol} with high conviction AI signals"
            elif score > 0.75:
                return f"Positive trend analysis for {symbol} with favorable risk-reward"
            elif score > 0.65:
                return f"Moderate signals for {symbol}, suitable for conservative allocation"
            else:
                return f"Mixed signals for {symbol}, requires careful monitoring"

        raw_signals = [
            {"symbol": "TCS", "product": "equity", "score": 0.87, "verdict": "BUY", "confidence": 0.85},
            {"symbol": "INFY", "product": "equity", "score": 0.91, "verdict": "STRONG_BUY", "confidence": 0.91},
            {"symbol": "RELIANCE", "product": "equity", "score": 0.83, "verdict": "BUY", "confidence": 0.78},
            {"symbol": "HDFCBANK", "product": "equity", "score": 0.75, "verdict": "HOLD", "confidence": 0.72},
            {"symbol": "ICICIBANK", "product": "equity", "score": 0.69, "verdict": "HOLD", "confidence": 0.65},
            {"symbol": "WIPRO", "product": "equity", "score": 0.58, "verdict": "CAUTIOUS", "confidence": 0.55}
        ]

        top_signals = []
        for signal in raw_signals:
            validated_verdict = validate_verdict(signal["verdict"])
            top_signals.append({
                "symbol": signal["symbol"],
                "product": signal["product"],
                "score": signal["score"],
                "ai_verdict_normalized": validated_verdict,
                "confidence": signal["confidence"],
                "rationale": generate_rationale(signal["symbol"], validated_verdict, signal["score"]),
                "updated": now_iso()
            })

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

        generation_time_ms = round((time.time() - start_time) * 1000, 1)

        payload = {
            "last_updated_utc": now_iso(),
            "market_session": "CLOSED",
            "kpis": kpis,
            "timeframes": timeframes,
            "ai_verdict_summary": ai_verdict_summary,
            "product_breakdown": product_breakdown,
            "pinned_summary": pinned_summary,
            "top_signals": top_signals,
            "alerts": alerts,
            "insights": "Strong buy signals in IT sector. Consider increasing allocation.",
            "agent_insights": agent_insights,
            "generation_time_ms": generation_time_ms,
            "served_from_cache": False,
            "cache_ttl_sec": 60,
            "api_version": "2.0"
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