from flask import Blueprint, jsonify, request
from ..registry import REGISTRY, Agent
from ..builtin_agents import run_new_ai_analyzer, run_sentiment_analyzer

agents_bp = Blueprint("agents_api", __name__)

def _ensure_registered():
    current = {a["key"] for a in REGISTRY.list()}
    if "new_ai_analyzer" not in current:
        REGISTRY.register(Agent(key="new_ai_analyzer", name="New AI Analyzer", run_fn=run_new_ai_analyzer))
    if "sentiment_analyzer" not in current:
        REGISTRY.register(Agent(key="sentiment_analyzer", name="Sentiment Analyzer", run_fn=run_sentiment_analyzer))

@agents_bp.before_app_request
def _pre():
    _ensure_registered()

# ✅ accept both /api/agents and /api/agents/
@agents_bp.get("")
@agents_bp.get("/")
def list_agents():
    """List all available agents"""
    return jsonify({
        "agents": [
            {
                "id": "equity_agent",
                "name": "Equity Analysis Agent",
                "status": "active",
                "last_run": "2024-08-11T16:00:00Z"
            },
            {
                "id": "options_agent",
                "name": "Options Strategy Agent",
                "status": "active",
                "last_run": "2024-08-11T15:45:00Z"
            },
            {
                "id": "sentiment_agent",
                "name": "Market Sentiment Agent",
                "status": "active",
                "last_run": "2024-08-11T16:15:00Z"
            }
        ],
        "total": 3,
        "active": 3
    })

@agents_bp.route('/status', methods=['GET'])
def agents_status():
    """Get status of all agents"""
    return jsonify({
        "status": "healthy",
        "agents_running": 3,
        "last_check": "2024-08-11T16:45:00Z"
    })

@agents_bp.post("/<key>/run")
def run_agent(key: str):
    out = REGISTRY.run(key)
    status = 200 if out.get("success") else 400
    return jsonify(out), status

@agents_bp.post("/<key>/enable")
def enable_agent(key: str):
    ok = REGISTRY.enable(key)
    return (jsonify({"success": ok}), 200 if ok else 404)

@agents_bp.post("/<key>/disable")
def disable_agent(key: str):
    ok = REGISTRY.disable(key)
    return (jsonify({"success": ok}), 200 if ok else 404)

@agents_bp.get("/<key>/result")
def last_result(key: str):
    r = REGISTRY.get_last_result(key)
    if not r:
        return jsonify({"success": False, "error": "no result"}), 404
    return jsonify({"success": True, "result": r})

@agents_bp.get("/history")
def history():
    key = request.args.get("agent", "").strip()
    if not key:
        return jsonify({"success": False, "error": "missing agent"}), 400
    return jsonify(REGISTRY.history(key))

@agents_bp.post("/run_all")
def run_all():
    return jsonify(REGISTRY.run_all())

@agents_bp.get("/config")
def get_config():
    return jsonify(REGISTRY.get_config())

@agents_bp.post("/config")
def set_config():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        payload = {}
    out = REGISTRY.set_config(payload)
    return jsonify(out), (200 if out.get("success") else 400)