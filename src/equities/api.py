
from flask import Blueprint, request, jsonify
from src.core.cache import ttl_cache, now_iso

equities_bp = Blueprint("equities", __name__)
_cache = ttl_cache(ttl_sec=30, namespace="equities")

_FIX = [
  {"symbol":"TCS","name":"Tata Consultancy Services","sector":"IT","price":4275.3,"volRegime":"MEDIUM","verdict":"STRONG_BUY","confidence":0.74,"kpis":{"winRate":0.67,"sharpe":1.2,"mdd":-0.08},"updated":now_iso()},
  {"symbol":"RELIANCE","name":"Reliance Industries","sector":"Energy","price":2904.1,"volRegime":"LOW","verdict":"BUY","confidence":0.68,"kpis":{"winRate":0.61,"sharpe":1.05,"mdd":-0.10},"updated":now_iso()},
  {"symbol":"INFY","name":"Infosys","sector":"IT","price":1588.2,"volRegime":"MEDIUM","verdict":"HOLD","confidence":0.61,"kpis":{"winRate":0.55,"sharpe":0.92,"mdd":-0.12},"updated":now_iso()}
]

@equities_bp.get("/list")
def list_equities():
  force = request.args.get("forceRefresh","").lower() in ("1","true","yes")
  if not force:
    c=_cache.get("list"); 
    if c is not None: return jsonify(c)
  sector = request.args.get("sector","")
  scoreMin = float(request.args.get("scoreMin","0") or 0)
  items = [x for x in _FIX if (not sector or x["sector"]==sector) and (x["confidence"]>=scoreMin)]
  payload = {"page":1,"pageSize":len(items),"total":len(items),"items":items}
  _cache.set("list", payload)
  return jsonify(payload)

@equities_bp.get("/positions")
def get_positions():
  return jsonify({"items": _FIX})

@equities_bp.get("/kpis")
def eq_kpis():
  tf = request.args.get("timeframe","All")
  return jsonify({"timeframe":tf,"momentum":72,"volatility":"MEDIUM","trendADX":23,"breakoutProb":0.58,"earningsDays":12,"modelAcc":0.67,"avgHoldDays":9,"hitRate":0.64})

@equities_bp.get("/analytics")
def get_analytics():
  return jsonify({"portfolioValue": 1250000, "totalPnL": 85000, "winRate": 0.65, "sharpeRatio": 1.12})
