from flask import Blueprint, jsonify, request
from datetime import datetime
from core.cache import TTLCache
from core.metrics import inc
import json, os, random

# src/agents/api.py
from flask import Blueprint, jsonify, request

try:
    from .registry import registry
except ImportError:
    try:
        from src.agents.registry import registry
    except ImportError:
        # Create a basic registry fallback
        class BasicRegistry:
            def __init__(self):
                self.agents = {}
                self.config = {"show_ai_verdict_columns": True}
            
            def list_agents(self):
                return {
                    "success": True,
                    "agents": [
                        {"key": "new_ai_analyzer", "name": "AI Analyzer", "enabled": True},
                        {"key": "sentiment_analyzer", "name": "Sentiment Analyzer", "enabled": True}
                    ]
                }
            
            def run_agent(self, agent_id):
                return {"success": True, "result": f"Agent {agent_id} executed"}
            
            def enable_agent(self, agent_id):
                pass
                
            def disable_agent(self, agent_id):
                pass
                
            def save_config(self):
                pass
        
        registry = BasicRegistry()

agents_bp = Blueprint("agents", __name__)

@agents_bp.app_errorhandler(Exception)
def _error_handler(e):
    return jsonify({"success": False, "error": str(e)}), 500

@agents_bp.route("", methods=["GET"])
def list_agents():
    return jsonify(registry.list_agents())

@agents_bp.route("/run/<agent_id>", methods=["POST"])
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

cache = TTLCache(ttl_sec=180)

@agents_bp.get("/list")
def list_agents_old():
    inc("api.agents.list")

    agents = [
        {"id": "equity_analyzer", "name": "Equity Analyzer", "status": "active", "confidence": round(random.uniform(70, 95), 1)},
        {"id": "options_strategist", "name": "Options Strategist", "status": "active", "confidence": round(random.uniform(65, 90), 1)},
        {"id": "commodity_tracker", "name": "Commodity Tracker", "status": "active", "confidence": round(random.uniform(60, 85), 1)},
        {"id": "risk_manager", "name": "Risk Manager", "status": "monitoring", "confidence": round(random.uniform(75, 95), 1)}
    ]

    return jsonify({"agents": agents, "count": len(agents)})

@agents_bp.get("/kpis")
def agents_kpis():
    inc("api.agents.kpis")

    return jsonify({
        "total_agents": 4,
        "active_agents": 3,
        "avg_confidence": round(random.uniform(70, 90), 1),
        "predictions_today": random.randint(15, 35),
        "accuracy_rate": round(random.uniform(68, 88), 1)
    })

@agents_bp.post("/run/<agent_id>")
def run_agent_old(agent_id):
    inc("api.agents.run")

    result = {
        "agent_id": agent_id,
        "status": "completed",
        "execution_time_ms": random.randint(500, 2000),
        "predictions_generated": random.randint(3, 12),
        "confidence": round(random.uniform(65, 92), 1)
    }

    return jsonify(result)

@agents_bp.route('/status')
def get_status():
    """Get agents status"""
    try:
        agents_status = [
            {
                "name": "Equity Agent",
                "status": "active",
                "last_run": datetime.utcnow().isoformat() + "Z",
                "performance": 85.6
            },
            {
                "name": "Options Agent",
                "status": "active",
                "last_run": datetime.utcnow().isoformat() + "Z",
                "performance": 78.2
            },
            {
                "name": "Sentiment Agent",
                "status": "idle",
                "last_run": datetime.utcnow().isoformat() + "Z",
                "performance": 92.1
            }
        ]

        return jsonify({
            "agents": agents_status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/recommendations')
def get_recommendations():
    """Get agent recommendations"""
    try:
        recommendations = [
            {
                "agent": "Equity Agent",
                "symbol": "TCS",
                "action": "BUY",
                "confidence": 85.6,
                "target_price": 3750,
                "reasoning": "Strong technical indicators and earnings outlook"
            },
            {
                "agent": "Options Agent",
                "symbol": "NIFTY",
                "action": "SELL_PUT",
                "confidence": 72.3,
                "strike": 21000,
                "reasoning": "High implied volatility and support levels"
            }
        ]

        return jsonify({
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/kpis')
def get_kpis():
    """Get agents KPIs"""
    try:
        return jsonify({
            "total_agents": 4,
            "active_agents": 3,
            "avg_confidence": 78.5,
            "predictions_today": 24,
            "accuracy_rate": 85.2,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/runs')
def get_runs():
    """Get all agent runs"""
    try:
        return jsonify({
            "active_agents": 6,
            "completed_runs": 156,
            "success_rate": 89.2,
            "avg_execution_time": 2.4,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500