
from flask import Blueprint, jsonify, request
from ..registry import REGISTRY, Agent
from ..builtin_agents import run_new_ai_analyzer, run_sentiment_analyzer
import json
import os
import time
from datetime import datetime

agents_bp = Blueprint("agents_api", __name__)

# Ensure logs directory exists
LOG_DIR = "logs/agents"
os.makedirs(LOG_DIR, exist_ok=True)

def _ensure_registered():
    current = {a["key"] for a in REGISTRY.list()}
    if "new_ai_analyzer" not in current:
        REGISTRY.register(Agent(key="new_ai_analyzer", name="New AI Analyzer", run_fn=run_new_ai_analyzer))
    if "sentiment_analyzer" not in current:
        REGISTRY.register(Agent(key="sentiment_analyzer", name="Sentiment Analyzer", run_fn=run_sentiment_analyzer))

@agents_bp.before_app_request
def _pre():
    _ensure_registered()

def _json_error(message, status_code=500):
    """Consistent JSON error format"""
    return jsonify({
        "success": False,
        "error": message,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), status_code

def _persist_agent_run(agent_key, started_at, finished_at, success, items, summary):
    """Persist agent run history to JSON file"""
    history_entry = {
        "agent": agent_key,
        "started_at": started_at,
        "finished_at": finished_at,
        "success": success,
        "items": items or [],
        "summary": summary,
        "duration_ms": int((finished_at - started_at) * 1000) if finished_at and started_at else 0
    }
    
    history_file = os.path.join(LOG_DIR, f"{agent_key}_history.json")
    history = []
    
    # Load existing history
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # Add new entry and keep last 100 entries
    history.append(history_entry)
    history = history[-100:]
    
    # Save updated history
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

@agents_bp.route("/", methods=["GET"])
def list_agents():
    """List all available agents"""
    try:
        agents_list = REGISTRY.list()
        return jsonify({
            "success": True,
            "agents": agents_list,
            "total": len(agents_list),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to list agents: {str(e)}")

@agents_bp.route("/<agent_key>/run", methods=["POST"])
def run_agent(agent_key):
    """Run a specific agent"""
    try:
        agent = REGISTRY.get(agent_key)
        if not agent:
            return _json_error(f"Agent '{agent_key}' not found", 404)
        
        started_at = time.time()
        result = REGISTRY.run(agent_key)
        finished_at = time.time()
        
        success = result.get("success", False)
        items = result.get("result", {}).get("items", [])
        summary = result.get("result", {}).get("summary", f"Agent {agent_key} executed")
        
        # Persist run history
        _persist_agent_run(agent_key, started_at, finished_at, success, items, summary)
        
        if success:
            return jsonify({
                "success": True,
                "result": result.get("result"),
                "agent": agent_key,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return _json_error(result.get("error", "Agent execution failed"), 400)
            
    except Exception as e:
        return _json_error(f"Failed to run agent {agent_key}: {str(e)}")

@agents_bp.route("/run_all", methods=["POST"])
def run_all_agents():
    """Run all enabled agents"""
    try:
        result = REGISTRY.run_all()
        
        # Persist run history for each agent
        for agent_key, agent_result in result.get("results", {}).items():
            started_at = time.time()
            finished_at = time.time()
            success = agent_result.get("success", False)
            items = agent_result.get("result", {}).get("items", [])
            summary = f"Batch run of {agent_key}"
            _persist_agent_run(agent_key, started_at, finished_at, success, items, summary)
        
        return jsonify({
            "success": True,
            "results": result.get("results", {}),
            "total_agents": len(result.get("results", {})),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to run all agents: {str(e)}")

@agents_bp.route("/<agent_key>/enable", methods=["POST"])
def enable_agent(agent_key):
    """Enable an agent"""
    try:
        success = REGISTRY.enable(agent_key)
        if success:
            return jsonify({
                "success": True,
                "agent": agent_key,
                "status": "enabled",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return _json_error(f"Agent '{agent_key}' not found", 404)
    except Exception as e:
        return _json_error(f"Failed to enable agent {agent_key}: {str(e)}")

@agents_bp.route("/<agent_key>/disable", methods=["POST"])
def disable_agent(agent_key):
    """Disable an agent"""
    try:
        success = REGISTRY.disable(agent_key)
        if success:
            return jsonify({
                "success": True,
                "agent": agent_key,
                "status": "disabled",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return _json_error(f"Agent '{agent_key}' not found", 404)
    except Exception as e:
        return _json_error(f"Failed to disable agent {agent_key}: {str(e)}")

@agents_bp.route("/config", methods=["GET"])
def get_config():
    """Get agent configuration"""
    try:
        config_result = REGISTRY.get_config()
        return jsonify({
            "success": True,
            "config": config_result.get("config", {}),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to get config: {str(e)}")

@agents_bp.route("/config", methods=["POST"])
def set_config():
    """Set agent configuration"""
    try:
        payload = request.get_json()
        if not payload:
            return _json_error("Invalid JSON payload", 400)
        
        result = REGISTRY.set_config(payload)
        if result.get("success"):
            return jsonify({
                "success": True,
                "config": result.get("config", {}),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        else:
            return _json_error(result.get("error", "Failed to set config"), 400)
    except Exception as e:
        return _json_error(f"Failed to set config: {str(e)}")

@agents_bp.route("/<agent_key>/history", methods=["GET"])
def get_agent_history(agent_key):
    """Get agent execution history"""
    try:
        history_file = os.path.join(LOG_DIR, f"{agent_key}_history.json")
        history = []
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # Also get from registry
        registry_history = REGISTRY.history(agent_key)
        
        return jsonify({
            "success": True,
            "agent": agent_key,
            "history": history,
            "registry_history": registry_history.get("history", []),
            "total_runs": len(history),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to get history for {agent_key}: {str(e)}")

@agents_bp.route("/history", methods=["GET"])
def get_all_history():
    """Get execution history for all agents"""
    try:
        agent_key = request.args.get("agent", "").strip()
        if agent_key:
            return get_agent_history(agent_key)
        
        # Get history for all agents
        all_history = {}
        for agent_data in REGISTRY.list():
            agent_key = agent_data["key"]
            history_file = os.path.join(LOG_DIR, f"{agent_key}_history.json")
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        all_history[agent_key] = json.load(f)
                except:
                    all_history[agent_key] = []
            else:
                all_history[agent_key] = []
        
        return jsonify({
            "success": True,
            "history": all_history,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to get all history: {str(e)}")

@agents_bp.route("/kpis", methods=["GET"])
def get_agent_kpis():
    """Get agent KPIs and performance metrics"""
    try:
        agents_list = REGISTRY.list()
        total_agents = len(agents_list)
        active_agents = len([a for a in agents_list if a.get("enabled", True)])
        
        # Calculate performance metrics from history
        total_runs = 0
        successful_runs = 0
        avg_duration = 0
        
        for agent_data in agents_list:
            agent_key = agent_data["key"]
            history_file = os.path.join(LOG_DIR, f"{agent_key}_history.json")
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                        total_runs += len(history)
                        successful_runs += len([h for h in history if h.get("success", False)])
                        if history:
                            avg_duration += sum(h.get("duration_ms", 0) for h in history) / len(history)
                except:
                    pass
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        avg_duration = avg_duration / total_agents if total_agents > 0 else 0
        
        return jsonify({
            "success": True,
            "kpis": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "success_rate": round(success_rate, 2),
                "avg_duration_ms": round(avg_duration, 2),
                "predictions_today": successful_runs,  # Approximate
                "accuracy_rate": round(success_rate, 2),
                "avg_confidence": 78.5  # Mock value
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to get agent KPIs: {str(e)}")

@agents_bp.route("/status", methods=["GET"])
def get_agents_status():
    """Get status of all agents"""
    try:
        agents_list = REGISTRY.list()
        agents_status = []
        
        for agent_data in agents_list:
            agent_key = agent_data["key"]
            
            # Get last run info
            last_run = None
            performance = 0
            history_file = os.path.join(LOG_DIR, f"{agent_key}_history.json")
            if os.path.exists(history_file):
                try:
                    with open(history_file, 'r') as f:
                        history = json.load(f)
                        if history:
                            last_entry = history[-1]
                            last_run = last_entry.get("finished_at")
                            if isinstance(last_run, (int, float)):
                                last_run = datetime.fromtimestamp(last_run).isoformat() + "Z"
                            
                            # Calculate performance as success rate
                            recent_history = history[-10:]  # Last 10 runs
                            successful = len([h for h in recent_history if h.get("success", False)])
                            performance = (successful / len(recent_history) * 100) if recent_history else 0
                except:
                    pass
            
            if not last_run:
                last_run = datetime.utcnow().isoformat() + "Z"
            
            agents_status.append({
                "name": agent_data.get("name", agent_key),
                "key": agent_key,
                "status": "active" if agent_data.get("enabled", True) else "disabled",
                "last_run": last_run,
                "performance": round(performance, 1)
            })
        
        return jsonify({
            "success": True,
            "agents": agents_status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return _json_error(f"Failed to get agents status: {str(e)}")
