from flask import Blueprint, request, jsonify
from src.core.cache import now_iso
from src.kpi.calculator import compute_all

kpi_bp = Blueprint("kpi", __name__)

@kpi_bp.get("/metrics")
def get_metrics():
  tf=request.args.get("timeframe","All")
  return jsonify({"timeframe":tf, **compute_all(tf)})

@kpi_bp.post("/recompute")
def recompute():
  tf = request.json.get("timeframe", "All") if request.json else "All"
  metrics = compute_all(tf)
  return jsonify({"success": True, "timeframe": tf, "recomputed": now_iso(), **metrics})

@kpi_bp.get("/all-timeframes")
def get_all_timeframes():
  timeframes = ["All", "3D", "5D", "10D", "15D", "30D"]
  result = {}
  for tf in timeframes:
    result[tf] = compute_all(tf)
  return jsonify(result)

@kpi_bp.get("/status")
def get_status():
  return jsonify({
    "status": "active",
    "lastUpdate": now_iso(),
    "metricsCount": 6,
    "timeframes": ["All", "3D", "5D", "10D", "15D", "30D"]
  })