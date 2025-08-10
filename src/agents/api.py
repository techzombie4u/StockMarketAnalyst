
# src/agents/api.py
from flask import Blueprint, jsonify, request

try:
    from .registry import registry
except Exception:
    from src.agents.registry import registry

agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

@agents_bp.app_errorhandler(Exception)
def _error_handler(e):
    return jsonify({"success": False, "error": str(e)}), 500

@agents_bp.route("", methods=["GET"])
def list_agents():
    return jsonify(registry.list_agents())

@agents_bp.route("/<agent_id>/run", methods=["POST"])
def run_agent(agent_id):
    out = registry.run_agent(agent_id)
    if isinstance(out, dict) and out.get("error"):
        return jsonify({"success": False, "error": out["error"]}), 400
    return jsonify({"success": True, "result": out})

@agents_bp.route("/run_all", methods=["POST"])
def run_all():
    return jsonify({"success": True, "results": registry.run_all(enabled_only=True)})

@agents_bp.route("/<agent_id>/enable", methods=["POST"])
def enable(agent_id):
    registry.enable_agent(agent_id)
    return jsonify({"success": True, "status": "enabled", "id": agent_id})

@agents_bp.route("/<agent_id>/disable", methods=["POST"])
def disable(agent_id):
    registry.disable_agent(agent_id)
    return jsonify({"success": True, "status": "disabled", "id": agent_id})

@agents_bp.route("/config", methods=["GET"])
def get_config():
    return jsonify({"success": True, "config": registry.config})

@agents_bp.route("/config", methods=["POST"])
def update_config():
    body = request.get_json(silent=True) or {}
    if "show_ai_verdict_columns" in body:
        registry.config["show_ai_verdict_columns"] = bool(body["show_ai_verdict_columns"])
    registry.save_config()
    return jsonify({"success": True, "config": registry.config})
