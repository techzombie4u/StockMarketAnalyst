
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Optional

BASE_DIR = os.path.join("data", "agents")
REG_FILE = os.path.join(BASE_DIR, "registry.json")

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")

class AgentRegistry:
    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.config = {}
        self.load_registry()
        self._register_default_agents()

    def load_registry(self):
        if os.path.exists(REG_FILE):
            try:
                with open(REG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.agents = data.get("agents", {})
                    self.config = data.get("config", {})
            except Exception:
                self.agents = {}
                self.config = {}
        else:
            self.agents = {}
            self.config = {}
            
        # Set default config values
        if "show_ai_verdict_columns" not in self.config:
            self.config["show_ai_verdict_columns"] = False
            
        self.save_registry()

    def save_registry(self):
        data = {
            "agents": {k: {key: val for key, val in v.items() if not key.startswith("_")} for k, v in self.agents.items()},
            "config": self.config,
            "last_updated": _now()
        }
        with open(REG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def register_agent(self, agent_id: str, name: str, run_fn: Callable, description: str = "", enabled: bool = True):
        self.agents[agent_id] = {
            "id": agent_id,
            "name": name,
            "enabled": enabled,
            "description": description,
            "last_run_utc": None,
            "last_result": None
        }
        self.agents[agent_id]["_run_fn"] = run_fn
        self.save_registry()

    def _register_default_agents(self):
        # Register new AI agent
        from .new_ai_agent import run as new_ai_run
        if "new_ai_analyzer" not in self.agents:
            self.register_agent(
                "new_ai_analyzer",
                "New AI Analyzer Agent",
                new_ai_run,
                "Placeholder for future predictive or analytical capabilities",
                True
            )

        # Register sentiment agent
        from .sentiment_agent import run as sentiment_run
        if "sentiment_analyzer" not in self.agents:
            self.register_agent(
                "sentiment_analyzer", 
                "Sentiment Analyzer Agent",
                sentiment_run,
                "Processes news, social sentiment, and related indicators",
                True
            )

    def list_agents(self):
        return [{k: v for k, v in a.items() if not k.startswith("_")} for a in self.agents.values()]

    def get_config(self, key: str, default=None):
        return self.config.get(key, default)

    def set_config(self, key: str, value):
        self.config[key] = value
        self.save_registry()

    def enable_agent(self, agent_id: str):
        self._set_enabled(agent_id, True)

    def disable_agent(self, agent_id: str):
        self._set_enabled(agent_id, False)

    def _set_enabled(self, agent_id: str, enabled: bool):
        if agent_id in self.agents:
            self.agents[agent_id]["enabled"] = enabled
            self.save_registry()

    def run_agent(self, agent_id: str):
        if agent_id not in self.agents:
            return {"error": "Agent not found"}
        
        agent = self.agents[agent_id]
        if "_run_fn" not in agent:
            return {"error": "No run function bound"}
        
        try:
            result = agent["_run_fn"]()
            agent["last_result"] = result
            agent["last_run_utc"] = _now()
            self.save_registry()
            return result
        except Exception as e:
            error_result = {"error": str(e), "status": "failed"}
            agent["last_result"] = error_result
            agent["last_run_utc"] = _now()
            self.save_registry()
            return error_result

    def run_all(self, enabled_only: bool = True):
        results = {}
        for aid, agent in self.agents.items():
            if enabled_only and not agent.get("enabled"):
                continue
            results[aid] = self.run_agent(aid)
        return results

    def get_agent_result(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if agent_id in self.agents:
            return self.agents[agent_id].get("last_result")
        return None

# Global instance
registry = AgentRegistry()
