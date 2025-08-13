import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents_api', __name__)
agents_api_bp = agents_bp  # Alias for backward compatibility

@agents_api_bp.route('/', methods=['GET'])
def get_agents():
    """Get list of agents"""
    try:
        # Load agents from registry file
        registry_path = os.path.join(os.path.dirname(__file__), '../data/agents/registry.json')
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                registry_data = json.load(f)
            agents = registry_data.get('agents', [])
        else:
            # Provide dummy data if registry file is not found
            agents = [
                {'id': 'equity_agent', 'name': 'Equity Agent', 'status': 'active'},
                {'id': 'options_agent', 'name': 'Options Agent', 'status': 'active'},
                {'id': 'sentiment_agent', 'name': 'Sentiment Agent', 'status': 'active'}
            ]

        return jsonify({
            "status": "success",
            "agents": agents,
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.get('status') == 'active']),
            "timestamp": time.time()
        })

    except Exception as e:
        logger.error(f"Error getting agents: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "agents": {}
        }), 500

# This function was intended to load the registry, but the route was defined above.
# Keeping it for potential internal use if needed, but the API route now handles loading.
def load_agents_registry():
    """Load agents registry data"""
    try:
        filepath = os.path.join('data', 'agents', 'registry.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading agents registry: {e}")
    return {"agents": []}


@agents_api_bp.route('/config', methods=['GET'])
def get_config():
    """Get agents configuration"""
    try:
        registry_path = os.path.join(os.path.dirname(__file__), '../data/agents/registry.json')
        if os.path.exists(registry_path):
            with open(registry_path, 'r') as f:
                registry_data = json.load(f)
            agents = registry_data.get('agents', [])
        else:
            # Provide dummy data if registry file is not found
            agents = [
                {'id': 'equity_agent', 'name': 'Equity Agent', 'status': 'active', 'config': {'threshold': 0.8}},
                {'id': 'options_agent', 'name': 'Options Agent', 'status': 'active', 'config': {'strike': 100}},
                {'id': 'sentiment_agent', 'name': 'Sentiment Agent', 'status': 'active', 'config': {'model': 'bert'}}
            ]

        return jsonify({
            "status": "success",
            "agents": agents,
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.get('status') == 'active']),
            "timestamp": time.time()
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
        new_config = data.get('config')

        if not agent_id:
            return jsonify({
                "error": "validation_error",
                "message": "agent_id is required"
            }), 400
        if not new_config:
            return jsonify({
                "error": "validation_error",
                "message": "config is required"
            }), 400

        # In a real application, you would load the registry, find the agent,
        # update its configuration, and save the registry.
        # For this example, we'll just simulate a successful update.

        logger.info(f"Simulating update for agent {agent_id} with config: {new_config}")

        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent '{agent_id}' configuration updated successfully."
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
        agent_params = data.get('params', {})

        if not agent_id:
            return jsonify({
                "error": "validation_error",
                "message": "agent_id is required"
            }), 400

        # Simulate agent run - in a real scenario, this would trigger the agent execution
        logger.info(f"Simulating run for agent {agent_id} with params: {agent_params}")

        # Example of a simulated response
        return jsonify({
            "success": True,
            "agent_id": agent_id,
            "run_id": f"run_{int(time.time())}",
            "status": "completed", # Could be 'running', 'failed', 'completed'
            "duration_ms": 1250,
            "results": {
                "signals_generated": 5,
                "confidence_avg": 0.78,
                "output_data": f"Data processed by {agent_id}"
            }
        })

    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500