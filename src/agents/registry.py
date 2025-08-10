
# src/agents/registry.py
import os, json
from datetime import datetime, timezone
from typing import Dict, Any, Callable

BASE_DIR = os.path.join("data", "agents")
REG_FILE = os.path.join(BASE_DIR, "registry.json")
CFG_FILE = os.path.join(BASE_DIR, "config.json")

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

class AgentRegistry:
    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._run_map: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self.config = {"show_ai_verdict_columns": False}
        self.load_registry()
        self.load_config()

    def load_registry(self):
        if os.path.exists(REG_FILE):
            with open(REG_FILE, "r", encoding="utf-8") as f:
                self.agents = json.load(f)
        else:
            self.agents = {}
            self.save_registry()

    def save_registry(self):
        with open(REG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.agents, f, indent=2)

    def register_or_bind(self, agent_id: str, name: str, run_fn: Callable, description: str = "", enabled: bool = True):
        self._run_map[agent_id] = run_fn
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "id": agent_id,
                "name": name,
                "enabled": enabled,
                "description": description,
                "last_run_utc": None,
                "last_result": None
            }
            self.save_registry()

    def list_agents(self):
        return [dict((k, v) for k, v in a.items()) for a in self.agents.values()]

    def enable_agent(self, agent_id: str): self._set_enabled(agent_id, True)
    def disable_agent(self, agent_id: str): self._set_enabled(agent_id, False)

    def _set_enabled(self, agent_id: str, enabled: bool):
        if agent_id in self.agents:
            self.agents[agent_id]["enabled"] = enabled
            self.save_registry()

    def run_agent(self, agent_id: str):
        if agent_id not in self.agents:
            return {"error": "Agent not found"}
        if agent_id not in self._run_map:
            return {"error": "No run function bound"}
        result = self._run_map[agent_id]()
        self.agents[agent_id]["last_result"] = result
        self.agents[agent_id]["last_run_utc"] = _now()
        self.save_registry()
        return result

    def run_all(self, enabled_only: bool = True):
        results = {}
        for aid, meta in self.agents.items():
            if enabled_only and not meta.get("enabled", True):
                continue
            results[aid] = self.run_agent(aid)
        return results

    def load_config(self):
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.save_config()

    def save_config(self):
        with open(CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

registry = AgentRegistry()
