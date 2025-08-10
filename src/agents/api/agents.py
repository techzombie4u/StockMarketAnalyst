
from flask import Blueprint, request, jsonify
from ..registry import (
    list_agents, run_agent, run_all_agents,
    enable_agent, disable_agent, get_last_result, init_registry
)

# Bind prefix here to remove double-prefix mistakes
agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

def _ok(data=None):
    return jsonify({"success": True, "data": data or {}}), 200

def _err(msg, code=500):
    return jsonify({"success": False, "error": str(msg)}), code

@agents_bp.route("/health", methods=["GET"])
def agents_health():
    try:
        init_registry()
        return _ok({"status": "ok"})
    except Exception as e:
        return _err(e)

@agents_bp.route("/", methods=["GET"])
def list_agents_api():
    try:
        init_registry()
        return _ok(list_agents())
    except Exception as e:
        return _err(e)

@agents_bp.route("/<agent_id>/run", methods=["POST"])
def run_agent_api(agent_id):
    try:
        payload = request.get_json(silent=True) or {}
        res = run_agent(agent_id, **payload)
        code = 200 if res.get("success") else 500
        return jsonify(res), code
    except Exception as e:
        return _err(e)

@agents_bp.route("/run_all", methods=["POST"])
def run_all_agents_api():
    try:
        res = run_all_agents()
        code = 200 if res.get("success") else 500
        return jsonify(res), code
    except Exception as e:
        return _err(e)

@agents_bp.route("/<agent_id>/enable", methods=["POST"])
def enable_agent_api(agent_id):
    try:
        ok = enable_agent(agent_id)
        if not ok:
            return _err(f"Agent {agent_id} not found", 404)
        return _ok({"agent_id": agent_id, "enabled": True})
    except Exception as e:
        return _err(e)

@agents_bp.route("/<agent_id>/disable", methods=["POST"])
def disable_agent_api(agent_id):
    try:
        ok = disable_agent(agent_id)
        if not ok:
            return _err(f"Agent {agent_id} not found", 404)
        return _ok({"agent_id": agent_id, "enabled": False})
    except Exception as e:
        return _err(e)

@agents_bp.route("/<agent_id>/result", methods=["GET"])
def get_result_api(agent_id):
    try:
        res = get_last_result(agent_id)
        code = 200 if res.get("success") else 404
        return jsonify(res), code
    except Exception as e:
        return _err(e)

@agents_bp.route("/config", methods=["GET"])
def get_config_api():
    try:
        init_registry()
        return _ok({"agents": list_agents()})
    except Exception as e:
        return _err(e)
