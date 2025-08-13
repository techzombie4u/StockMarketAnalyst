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

        # Get real-time data for top signals with trained stocks
        from src.data.realtime_data_fetcher import get_multiple_realtime_prices
        
        trained_stocks = [
            "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTIM", "LTTS",
            "HDFCBANK", "ICICIBANK", "KOTAKBANK", "SBIN", "AXISBANK", "INDUSINDBK",
            "RELIANCE", "LT", "ITC", "HINDUNILVR", "BHARTIARTL", "ASIANPAINT",
            "TITAN", "MARUTI", "TATASTEEL", "JSWSTEEL", "HINDALCO"
        ]
        
        # Get real-time prices for analysis
        try:
            print(f"🔄 Fetching real-time data for {len(trained_stocks)} stocks...")
            realtime_data = get_multiple_realtime_prices(trained_stocks)
            print(f"✅ Retrieved real-time data for {len(realtime_data)} stocks")
            
            # If no real-time data, try individual fetches
            if not realtime_data:
                from src.data.realtime_data_fetcher import get_realtime_price
                realtime_data = {}
                for symbol in trained_stocks[:10]:  # Limit to prevent timeout
                    try:
                        data = get_realtime_price(symbol)
                        if data and data.get('current_price'):
                            realtime_data[symbol] = data
                    except Exception as e:
                        print(f"Failed to get data for {symbol}: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error fetching real-time data: {e}")
            realtime_data = {}

        def validate_verdict(verdict):
            return verdict if verdict in VALID_VERDICTS else "HOLD"

        def generate_rationale(symbol, verdict, score, price_data=None):
            base_rationale = {
                0.85: f"Strong technical momentum in {symbol} with high conviction AI signals",
                0.75: f"Positive trend analysis for {symbol} with favorable risk-reward",
                0.65: f"Moderate signals for {symbol}, suitable for conservative allocation"
            }
            
            rationale = next((r for threshold, r in base_rationale.items() if score > threshold), 
                           f"Mixed signals for {symbol}, requires careful monitoring")
            
            if price_data and price_data.get('change_percent'):
                change = price_data['change_percent']
                if abs(change) > 2:
                    direction = "gaining" if change > 0 else "declining"
                    rationale += f" • Currently {direction} {abs(change):.1f}% today"
            
            return rationale

        # Generate signals with real-time price integration
        signal_templates = [
            {"symbol": "TCS", "score": 0.87, "verdict": "BUY", "confidence": 0.85},
            {"symbol": "INFY", "score": 0.91, "verdict": "STRONG_BUY", "confidence": 0.91},
            {"symbol": "RELIANCE", "score": 0.83, "verdict": "BUY", "confidence": 0.78},
            {"symbol": "HDFCBANK", "score": 0.75, "verdict": "HOLD", "confidence": 0.72},
            {"symbol": "ICICIBANK", "score": 0.69, "verdict": "HOLD", "confidence": 0.65},
            {"symbol": "BHARTIARTL", "score": 0.72, "verdict": "BUY", "confidence": 0.68},
            {"symbol": "LT", "score": 0.79, "verdict": "BUY", "confidence": 0.74},
            {"symbol": "ASIANPAINT", "score": 0.65, "verdict": "HOLD", "confidence": 0.62}
        ]

        top_signals = []
        for signal in signal_templates:
            symbol = signal["symbol"]
            price_data = realtime_data.get(symbol, {})
            validated_verdict = validate_verdict(signal["verdict"])
            
            # Add price information to signals
            signal_entry = {
                "symbol": symbol,
                "product": "equity",
                "signal_score": signal["score"],
                "ai_verdict": validated_verdict,
                "confidence": signal["confidence"],
                "rationale": generate_rationale(symbol, validated_verdict, signal["score"], price_data),
                "updated": now_iso()
            }
            
            # Add price data if available
            if price_data and price_data.get('current_price'):
                signal_entry.update({
                    "current_price": price_data['current_price'],
                    "target_price": price_data['current_price'] * (1 + signal["score"] * 0.1),  # Estimated target
                    "potential_roi": signal["score"] * 0.1,  # ROI based on signal strength
                    "price_change": price_data.get('change', 0),
                    "price_change_percent": price_data.get('change_percent', 0)
                })
            else:
                # Fallback values
                signal_entry.update({
                    "current_price": 1000.0,
                    "target_price": 1000.0 * (1 + signal["score"] * 0.1),
                    "potential_roi": signal["score"] * 0.1,
                    "price_change": 0,
                    "price_change_percent": 0
                })
            
            top_signals.append(signal_entry)

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