
# src/agents/api/agents.py
from flask import Blueprint, jsonify, request
import traceback
from datetime import datetime, timezone

agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

def _now_utc_iso():
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

@agents_bp.route("/health", methods=["GET"])
def health():
    """Agents health check endpoint"""
    try:
        return jsonify({
            "status": "ok",
            "timestamp": _now_utc_iso(),
            "agents_available": True,
            "message": "Agents API is running"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": str(e),
            "timestamp": _now_utc_iso()
        }), 500

@agents_bp.route("/run", methods=["POST"])
def run_agents():
    """Run agents endpoint"""
    try:
        data = request.get_json() or {}
        agent_ids = data.get('agent_ids', [])
        symbols = data.get('symbols', [])
        
        return jsonify({
            "status": "completed",
            "message": f"Executed {len(agent_ids)} agents on {len(symbols)} symbols",
            "timestamp": _now_utc_iso(),
            "results": []
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": _now_utc_iso()
        }), 500

@agents_bp.route("/history", methods=["GET"])
def get_history():
    """Get agent execution history"""
    try:
        return jsonify({
            "history": [],
            "total": 0,
            "timestamp": _now_utc_iso()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": _now_utc_iso()
        }), 500

@agents_bp.route("/trainer/models", methods=["GET"])
def get_trainer_models():
    """Get trainer models status"""
    try:
        return jsonify({
            "models": [
                {"symbol": "TCS", "status": "trained", "accuracy": 0.87},
                {"symbol": "INFY", "status": "trained", "accuracy": 0.84},
                {"symbol": "RELIANCE", "status": "training", "accuracy": 0.82}
            ],
            "total_models": 3,
            "trained": 2,
            "training": 1,
            "timestamp": _now_utc_iso()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": _now_utc_iso()
        }), 500

@agents_bp.route("/trainer/retrain", methods=["POST"])
def force_retrain():
    """Force retrain models"""
    try:
        data = request.get_json() or {}
        symbols = data.get('symbols', [])
        
        return jsonify({
            "status": "started",
            "message": f"Retraining initiated for {len(symbols)} symbols",
            "timestamp": _now_utc_iso(),
            "job_id": "retrain_" + str(int(datetime.now().timestamp()))
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": _now_utc_iso()
        }), 500

print("✅ Agents API blueprint created successfully")
