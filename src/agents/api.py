from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

try:
    from .registry import registry
except Exception:
    # Fallback if imported as src.agents.api
    from src.agents.registry import registry

agents_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

@agents_bp.route("", methods=["GET"])
def list_agents():
    """List all registered agents and their statuses"""
    try:
        agents = registry.list_agents()
        config = {
            "show_ai_verdict_columns": registry.get_config("show_ai_verdict_columns", False)
        }
        return jsonify({
            "success": True,
            "agents": agents,
            "config": config
        })
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/<agent_id>/run", methods=["POST"])
def run_agent(agent_id):
    """Run a specific agent"""
    try:
        result = registry.run_agent(agent_id)
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "result": result
        })
    except Exception as e:
        logger.error(f"Error running agent {agent_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/run_all", methods=["POST"])
def run_all_agents():
    """Run all enabled agents"""
    try:
        enabled_only = request.json.get("enabled_only", True) if request.json else True
        results = registry.run_all(enabled_only=enabled_only)
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error running all agents: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/<agent_id>/enable", methods=["POST"])
def enable_agent(agent_id):
    """Enable a specific agent"""
    try:
        registry.enable_agent(agent_id)
        return jsonify({
            "success": True,
            "status": "enabled",
            "agent_id": agent_id
        })
    except Exception as e:
        logger.error(f"Error enabling agent {agent_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/<agent_id>/disable", methods=["POST"])
def disable_agent(agent_id):
    """Disable a specific agent"""
    try:
        registry.disable_agent(agent_id)
        return jsonify({
            "success": True,
            "status": "disabled",
            "agent_id": agent_id
        })
    except Exception as e:
        logger.error(f"Error disabling agent {agent_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/config", methods=["GET"])
def get_config():
    """Get agent system configuration"""
    try:
        return jsonify({
            "success": True,
            "config": {
                "show_ai_verdict_columns": registry.get_config("show_ai_verdict_columns", False)
            }
        })
    except Exception as e:
        logger.error(f"Error getting config: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/config", methods=["POST"])
def set_config(key):
    """Set configuration value"""
    try:
        data = request.get_json()
        if not data or "value" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'value' in request body"
            }), 400

        registry.set_config(key, data["value"])
        return jsonify({
            "success": True,
            "key": key,
            "value": data["value"]
        })
    except Exception as e:
        logger.error(f"Error setting config {key}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agents_bp.route("/<agent_id>/result", methods=["GET"])
def get_agent_result(agent_id):
    """Get the last result from a specific agent"""
    try:
        result = registry.get_agent_result(agent_id)
        if result is None:
            return jsonify({
                "success": False,
                "error": "No result found for agent"
            }), 404

        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "result": result
        })
    except Exception as e:
        logger.error(f"Error getting result for agent {agent_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500