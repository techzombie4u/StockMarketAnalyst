import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

agents_api_bp = Blueprint('agents_api', __name__)

def load_agents_registry():
    """Load agents registry data"""
    try:
        filepath = os.path.join('data', 'agents', 'registry.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading agents registry: {e}")
    return {"agents": {}}

@agents_api_bp.route('/config', methods=['GET'])
def get_config():
    """Get agents configuration"""
    try:
        registry = load_agents_registry()
        agents = registry.get('agents', {})

        return jsonify({
            "agents": agents,
            "total_agents": len(agents),
            "active_agents": len([a for a in agents.values() if a.get('enabled', False)])
        })

    except Exception as e:
        logger.error(f"Error getting agents config: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "agents": {}
        }), 500

@agents_api_bp.route('/config', methods=['POST'])
def update_config():
    """Update agent configuration"""
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')

        if not agent_id:
            return jsonify({
                "error": "validation_error",
                "message": "agent_id is required"
            }), 400

        # For now, just return success
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "message": "Agent configuration updated"
        })

    except Exception as e:
        logger.error(f"Error updating agent config: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500

@agents_api_bp.route('/run', methods=['POST'])
def run_agent():
    """Run an agent"""
    try:
        data = request.get_json() or {}
        agent_id = data.get('agent_id')

        if not agent_id:
            return jsonify({
                "error": "validation_error",
                "message": "agent_id is required"
            }), 400

        # Simulate agent run
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "run_id": f"run_{int(time.time())}",
            "status": "completed",
            "duration_ms": 1250,
            "results": {
                "signals_generated": 5,
                "confidence_avg": 0.78
            }
        })

    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500