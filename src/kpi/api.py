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
from flask import Blueprint, jsonify, request
from src.kpi.calculator import compute_all, get_kpi_status

kpi_bp = Blueprint("kpi", __name__)

@kpi_bp.route('/metrics')
def get_metrics():
    """Get KPI metrics for specified timeframe"""
    timeframe = request.args.get('timeframe', 'all')
    force_refresh = request.args.get('forceRefresh', '').lower() in ('1', 'true', 'yes')
    
    result = compute_all(timeframe, force_refresh)
    return jsonify(result['metrics'])

@kpi_bp.route('/recompute', methods=['POST'])
def recompute_kpis():
    """Force recomputation of KPIs"""
    timeframe = request.args.get('timeframe', 'all')
    result = compute_all(timeframe, force_refresh=True)
    return jsonify({"success": True, "recomputed": result})

@kpi_bp.route('/all-timeframes')
def get_all_timeframes():
    """Get KPIs for all timeframes"""
    return jsonify({
        "5D": compute_all("5D")['metrics'],
        "30D": compute_all("30D")['metrics'],
        "all": compute_all("all")['metrics']
    })

@kpi_bp.route('/status')
def kpi_status():
    """Get KPI system status"""
    return jsonify(get_kpi_status())
