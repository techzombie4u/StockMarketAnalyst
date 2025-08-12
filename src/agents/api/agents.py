
from flask import Blueprint, jsonify, request
import json
import time
from pathlib import Path

agents_bp = Blueprint('agents', __name__)

def get_agents_data_file(filename):
    """Get path to agents data file"""
    return Path(__file__).parent.parent.parent.parent / "data" / "agents" / filename

@agents_bp.route('/config')
def agents_config():
    """Get agents configuration"""
    try:
        config_data = {
            "agents": {
                "sentiment": {
                    "enabled": True,
                    "model": "sentiment_v1",
                    "confidence_threshold": 0.7,
                    "refresh_interval": "5m"
                },
                "equity": {
                    "enabled": True,
                    "model": "equity_analyzer_v2",
                    "confidence_threshold": 0.75,
                    "refresh_interval": "10m"
                },
                "options": {
                    "enabled": True,
                    "model": "options_engine_v1",
                    "confidence_threshold": 0.8,
                    "refresh_interval": "15m"
                },
                "commodities": {
                    "enabled": True,
                    "model": "comm_signals_v1",
                    "confidence_threshold": 0.72,
                    "refresh_interval": "20m"
                }
            },
            "global_settings": {
                "max_concurrent_runs": 3,
                "timeout_seconds": 300,
                "retry_attempts": 2
            }
        }
        
        return jsonify(config_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/run', methods=['GET'])
def get_agent_runs():
    """Get recent agent runs"""
    try:
        runs_data = {
            "recent_runs": [
                {
                    "agent_type": "sentiment",
                    "symbol": "TCS",
                    "status": "completed",
                    "start_time": "2025-01-12T05:45:00Z",
                    "duration_ms": 2350,
                    "result": {
                        "sentiment": "positive",
                        "confidence": 0.82,
                        "recommendation": "BUY"
                    }
                },
                {
                    "agent_type": "equity",
                    "symbol": "RELIANCE",
                    "status": "completed",
                    "start_time": "2025-01-12T05:40:00Z",
                    "duration_ms": 1850,
                    "result": {
                        "verdict": "HOLD",
                        "confidence": 0.76,
                        "target_price": 2600
                    }
                }
            ],
            "summary": {
                "total_runs_today": 24,
                "success_rate": 95.8,
                "avg_duration_ms": 2150
            }
        }
        
        return jsonify(runs_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agents_bp.route('/run', methods=['POST'])
def run_agent():
    """Run an agent on demand"""
    try:
        data = request.get_json()
        agent_type = data.get('agent_type')
        symbol = data.get('symbol')
        
        if not agent_type:
            return jsonify({"error": "Missing agent_type"}), 400
        
        # Mock agent execution
        result_data = {
            "run_id": f"run_{int(time.time())}",
            "agent_type": agent_type,
            "symbol": symbol,
            "status": "completed",
            "start_time": "2025-01-12T06:00:00Z",
            "duration_ms": 1250,
            "result": {
                "verdict": "BUY" if agent_type == "sentiment" else "HOLD",
                "confidence": 0.78,
                "reasoning": f"Analysis completed for {symbol} using {agent_type} agent"
            }
        }
        
        return jsonify(result_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
