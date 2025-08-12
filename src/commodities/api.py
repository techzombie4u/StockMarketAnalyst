from flask import Blueprint, request, jsonify, g
from src.core.cache import ttl_cache, now_iso
from src.core.validation import validate_request_data, CommoditiesDetailSchema, CommoditiesCorrelationsSchema, get_validated_data
import random
import time
from datetime import datetime, timedelta

commodities_bp = Blueprint("commodities", __name__)
_cache = ttl_cache(ttl_sec=30, namespace="commodities")
_SIGS=[
  {"ticker":"GOLD","contract":"AUG","verdict":"HOLD","confidence":0.58,"atrPct":0.012,"rsi":51,"breakout":46,"updated":now_iso()},
  {"ticker":"SILVER","contract":"AUG","verdict":"BUY","confidence":0.62,"atrPct":0.016,"rsi":57,"breakout":61,"updated":now_iso()}
]

@commodities_bp.route('/signals')
def commodity_signals():
    """Get commodity trading signals"""
    try:
        signals_data = {
            "signals": [
                {
                    "commodity": "GOLD",
                    "signal": "BUY",
                    "strength": 0.82,
                    "price": 62500,
                    "target": 65000,
                    "stop_loss": 61000,
                    "timeframe": "5D",
                    "confidence": 0.78
                },
                {
                    "commodity": "CRUDE_OIL",
                    "signal": "SELL",
                    "strength": 0.75,
                    "price": 6850,
                    "target": 6600,
                    "stop_loss": 7000,
                    "timeframe": "3D",
                    "confidence": 0.71
                },
                {
                    "commodity": "SILVER",
                    "signal": "HOLD",
                    "strength": 0.65,
                    "price": 74500,
                    "target": 76000,
                    "stop_loss": 73000,
                    "timeframe": "10D",
                    "confidence": 0.68
                }
            ],
            "total_signals": 3,
            "last_updated": "2025-01-12T06:00:00Z"
        }

        return jsonify(signals_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.route('/correlations')
def commodity_correlations():
    """Get commodity correlation matrix"""
    try:
        correlations_data = {
            "correlations": {
                "GOLD": {
                    "SILVER": 0.78,
                    "CRUDE_OIL": -0.12,
                    "COPPER": 0.35,
                    "USD_INDEX": -0.68
                },
                "CRUDE_OIL": {
                    "GOLD": -0.12,
                    "NATURAL_GAS": 0.45,
                    "USD_INDEX": -0.32
                },
                "SILVER": {
                    "GOLD": 0.78,
                    "COPPER": 0.62,
                    "USD_INDEX": -0.55
                }
            },
            "timeframe": "30D",
            "last_updated": "2025-01-12T06:00:00Z"
        }

        return jsonify(correlations_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.get("/kpis")
def get_kpis():
  tf=request.args.get("timeframe","10D")
  return jsonify({"timeframe":tf,"trendScore":57,"volRegime":"MEDIUM","seasonality90d":0.3,"usdCorr":-0.18,"eqCorr":-0.12})

@commodities_bp.route("/<symbol>/detail", methods=["GET"])
@validate_request_data(CommoditiesDetailSchema, location='args')
@_cache
def get_commodity_detail(symbol):
    """Get detailed commodity data with seasonality and ATR bands"""
    validated_data = get_validated_data()
    tf = validated_data.get("tf", "30D")

    # Generate price data for the timeframe
    days = 30 if tf == "30D" else 10
    base_price = 65000 if symbol == "GOLD" else 82000

    # Price series
    prices = []
    current_date = datetime.now() - timedelta(days=days)
    for i in range(days):
        price = base_price + random.uniform(-2000, 2000)
        prices.append({
            "date": (current_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "price": round(price, 2)
        })

    # Seasonality data (average by month)
    seasonality = [
        {"month": 1, "avg_return": 0.023},
        {"month": 2, "avg_return": -0.012},
        {"month": 3, "avg_return": 0.045},
        {"month": 4, "avg_return": 0.018},
        {"month": 5, "avg_return": -0.008},
        {"month": 6, "avg_return": 0.032},
        {"month": 7, "avg_return": 0.015},
        {"month": 8, "avg_return": -0.025},
        {"month": 9, "avg_return": 0.038},
        {"month": 10, "avg_return": 0.028},
        {"month": 11, "avg_return": 0.042},
        {"month": 12, "avg_return": 0.035}
    ]

    # ATR regime bands
    current_price = prices[-1]["price"]
    atr_value = current_price * 0.02  # 2% ATR

    atr_bands = {
        "upper": round(current_price + atr_value, 2),
        "middle": round(current_price, 2),
        "lower": round(current_price - atr_value, 2),
        "atr_value": round(atr_value, 2),
        "regime": "MEDIUM"
    }

    return jsonify({
        "symbol": symbol,
        "timeframe": tf,
        "prices": prices,
        "seasonality": seasonality,
        "atr_bands": atr_bands,
        "last_updated_utc": now_iso()
    })

@commodities_bp.route("/correlations", methods=["GET"])
@validate_request_data(CommoditiesCorrelationsSchema, location='args')
@_cache
def get_commodity_correlations():
    """Get commodity correlations with other assets"""
    validated_data = get_validated_data()
    symbol = validated_data.get("symbol", "GOLD")

    # Correlation data for different commodities
    correlations_data = {
        "GOLD": {"usdInr": -0.22, "nifty": -0.12},
        "SILVER": {"usdInr": -0.18, "nifty": -0.08},
        "CRUDE": {"usdInr": 0.15, "nifty": 0.25},
        "COPPER": {"usdInr": -0.05, "nifty": 0.18}
    }

    return jsonify(correlations_data.get(symbol, {"usdInr": -0.15, "nifty": -0.10}))

@commodities_bp.get("/positions")
def get_positions():
  return jsonify({"items": [
    {"commodity": "GOLD", "quantity": 100, "price": 65000, "marketValue": 6500000, "pnl": 125000, "signal": "HOLD", "confidence": 0.58, "updated": now_iso()},
    {"commodity": "SILVER", "quantity": 500, "price": 82000, "marketValue": 41000000, "pnl": 850000, "signal": "BUY", "confidence": 0.62, "updated": now_iso()}
  ]})

@commodities_bp.get("/analytics")
def get_analytics():
  return jsonify({"totalValue": 47500000, "totalPnL": 975000, "successRate": 0.68})

@commodities_bp.get("/api/commodities")
def get_commodities():
  return jsonify({"signals": _SIGS, "correlations": {"GOLD": -0.22, "SILVER": -0.18}})