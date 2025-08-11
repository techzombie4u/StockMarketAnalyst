
from flask import Blueprint, request, jsonify
from src.core.cache import ttl_cache, now_iso

options_bp = Blueprint("options", __name__)
_cache = ttl_cache(ttl_sec=30, namespace="options")

_PLAN = {
  "id":"plan-1","underlying":"TCS","spot":4250,"ceStrike":4300,"peStrike":3900,"credit":39.5,"iv":0.22,"dte":14,
  "stopLoss":"SL at 1.8x credit per leg","status":"Open","roiPct":0.062,"margin":64000,"pop":0.68,
  "breakevens":[3860.5,4339.5],
  "payoff":{"x":[3600,3700,3800,3900,4000,4100,4200,4300,4400],"y":[-20000,-12000,-4000,0,12000,8000,0,-4000,-16000]},
  "greeks":{"delta":0.01,"gamma":0.02,"theta":-0.23,"vega":0.17},"updated": now_iso()
}

@options_bp.get("/strangle/candidates")
def get_strangle_candidates():
  return jsonify([_PLAN])

@options_bp.post("/strangle/plan")
def create_strangle_plan():
  return jsonify({"success":True,"id":_PLAN["id"],"plan":_PLAN})

@options_bp.get("/positions")
def get_positions():
  status = request.args.get("status","open").lower()
  return jsonify({"items":[_PLAN] if status in ("open","all") else []})

@options_bp.get("/positions/<pid>")
def get_position_detail(pid):
  return jsonify(_PLAN if pid==_PLAN["id"] else {})

@options_bp.get("/kpis")
def get_kpis():
  return jsonify({"expectedRoi":_PLAN["roiPct"],"pop":_PLAN["pop"],"breakevens":_PLAN["breakevens"],"margin":_PLAN["margin"]})

@options_bp.get("/strategies")
def get_strategies():
  return jsonify({"items": [_PLAN]})

@options_bp.get("/analytics")
def get_analytics():
  return jsonify({"totalPremium": 125000, "totalPnL": 15000, "successRate": 0.72})

@options_bp.get("/calculators")
def get_calculators():
  return jsonify({"blackScholes": "available", "greeks": "available", "impliedVol": "available"})
