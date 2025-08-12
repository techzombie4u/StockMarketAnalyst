
from flask import Blueprint, request, jsonify
from src.core.cache import ttl_cache, now_iso

commodities_bp = Blueprint("commodities", __name__)
_cache = ttl_cache(ttl_sec=30, namespace="commodities")

_SIGS=[
  {"ticker":"GOLD","contract":"AUG","verdict":"HOLD","confidence":0.58,"atrPct":0.012,"rsi":51,"breakout":46,"updated":now_iso()},
  {"ticker":"SILVER","contract":"AUG","verdict":"BUY","confidence":0.62,"atrPct":0.016,"rsi":57,"breakout":61,"updated":now_iso()}
]

@commodities_bp.get("/signals")
def get_signals():
  return jsonify(_SIGS)

@commodities_bp.get("/kpis")
def get_kpis():
  tf=request.args.get("timeframe","10D")
  return jsonify({"timeframe":tf,"trendScore":57,"volRegime":"MEDIUM","seasonality90d":0.3,"usdCorr":-0.18,"eqCorr":-0.12})

@commodities_bp.get("/<symbol>/detail")
def get_commodity_detail(symbol):
  tf = request.args.get("tf", "30D")
  
  # Generate price data for the timeframe
  import random
  from datetime import datetime, timedelta
  
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

@commodities_bp.get("/correlations")
def get_correlations():
  sym = request.args.get("symbol", "GOLD")
  
  # Correlation data for different commodities
  correlations_data = {
    "GOLD": {"usdInr": -0.22, "nifty": -0.12},
    "SILVER": {"usdInr": -0.18, "nifty": -0.08},
    "CRUDE": {"usdInr": 0.15, "nifty": 0.25},
    "COPPER": {"usdInr": -0.05, "nifty": 0.18}
  }
  
  return jsonify(correlations_data.get(sym, {"usdInr": -0.15, "nifty": -0.10}))

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
