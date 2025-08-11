from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
from .store import load_snapshot, save_snapshot
from .calculator import compute

kpi_bp = Blueprint("kpi", __name__, url_prefix="/api/kpi")

def _utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

@kpi_bp.route("/metrics", methods=["GET"])
def get_metrics():
    snap = load_snapshot()
    if snap:
        return jsonify(snap)
    # first-time compute
    fresh = compute()
    save_snapshot(fresh)
    return jsonify(fresh)

@kpi_bp.route("/recompute", methods=["POST"])
def recompute():
    fresh = compute()
    save_snapshot(fresh)
    return jsonify(fresh)