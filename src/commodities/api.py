
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

@commodities_bp.get("/correlations")
def get_correlations():
  sym=request.args.get("symbol","GOLD")
  return jsonify({"symbol":sym,"corrUSDINR":-0.22,"corrNIFTY":-0.12})

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
