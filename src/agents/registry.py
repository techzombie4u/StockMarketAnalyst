
# src/agents/registry.py
import os, json
from datetime import datetime, timezone
from typing import Dict, Any, Callable

BASE_DIR = os.path.join("data", "agents")
REG_FILE = os.path.join(BASE_DIR, "registry.json")
CFG_FILE = os.path.join(BASE_DIR, "config.json")

def _now_iso():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )

def _default_agent_meta(agent_id: str, name: str, description: str, enabled: bool) -> Dict[str, Any]:
    return {
        "id": agent_id,
        "name": name,
        "enabled": bool(enabled),
        "description": description or "",
        "last_run_utc": None,
        "last_result": None,
    }

class AgentRegistry:
    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self._run_map: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self.config: Dict[str, Any] = {"show_ai_verdict_columns": False}
        self.load_registry()
        self.load_config()
        # Self-heal on startup
        self._repair_registry_on_load()
        self._repair_config_on_load()

    # ---------- Persistence ----------
    def load_registry(self):
        if os.path.exists(REG_FILE):
            with open(REG_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        else:
            data = {}
        # Normalize: ensure dict
        if not isinstance(data, dict):
            data = {}
        self.agents = data
        self.save_registry()

    def save_registry(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(REG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.agents, f, indent=2)

    def load_config(self):
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        else:
            data = {}
        if not isinstance(data, dict):
            data = {}
        # default
        data.setdefault("show_ai_verdict_columns", False)
        self.config = data
        self.save_config()

    def save_config(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        with open(CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    # ---------- Self-heal ----------
    def _repair_registry_on_load(self):
        """Fix any malformed entries (e.g., string values instead of dicts)."""
        changed = False
        fixed = {}
        for aid, val in self.agents.items():
            if isinstance(val, dict):
                # Ensure required keys exist
                val.setdefault("id", aid)
                val.setdefault("name", aid)
                val.setdefault("enabled", True)
                val.setdefault("description", "")
                val.setdefault("last_run_utc", None)
                val.setdefault("last_result", None)
                fixed[aid] = val
            else:
                # Malformed; replace with default meta
                fixed[aid] = _default_agent_meta(aid, aid, "", True)
                changed = True
        if changed or len(fixed) != len(self.agents):
            self.agents = fixed
            self.save_registry()

    def _repair_config_on_load(self):
        if not isinstance(self.config, dict):
            self.config = {"show_ai_verdict_columns": False}
            self.save_config()
        else:
            if "show_ai_verdict_columns" not in self.config:
                self.config["show_ai_verdict_columns"] = False
                self.save_config()

    # ---------- API helpers ----------
    def register_or_bind(self, agent_id: str, name: str, run_fn: Callable[[], Dict[str, Any]],
                         description: str = "", enabled: bool = True):
        """Bind run function and ensure registry entry is a proper dict, repairing if needed."""
        self._run_map[agent_id] = run_fn
        cur = self.agents.get(agent_id)
        if not isinstance(cur, dict):
            # Either not present or malformed -> overwrite with good meta
            self.agents[agent_id] = _default_agent_meta(agent_id, name, description, enabled)
            self.save_registry()
        else:
            # Ensure required keys present; do not flip enabled unless missing
            cur.setdefault("id", agent_id)
            cur.setdefault("name", name)
            cur.setdefault("description", description or "")
            cur.setdefault("enabled", bool(enabled))
            cur.setdefault("last_run_utc", None)
            cur.setdefault("last_result", None)
            self.save_registry()

    def list_agents(self):
        # Return list of dicts (robust against caller assumptions)
        return [dict(v) for _, v in self.agents.items()]

    def enable_agent(self, agent_id: str):
        self._set_enabled(agent_id, True)

    def disable_agent(self, agent_id: str):
        self._set_enabled(agent_id, False)

    def _set_enabled(self, agent_id: str, enabled: bool):
        cur = self.agents.get(agent_id)
        if not isinstance(cur, dict):
            # Repair on the fly
            self.agents[agent_id] = _default_agent_meta(agent_id, agent_id, "", enabled)
        else:
            self.agents[agent_id]["enabled"] = bool(enabled)
        self.save_registry()

    def run_agent(self, agent_id: str):
        meta = self.agents.get(agent_id)
        if not isinstance(meta, dict):
            # Repair
            self.agents[agent_id] = _default_agent_meta(agent_id, agent_id, "", True)
            meta = self.agents[agent_id]
        if agent_id not in self._run_map:
            return {"error": "No run function bound"}
        result = self._run_map[agent_id]()
        meta["last_result"] = result
        meta["last_run_utc"] = _now_iso()
        self.save_registry()
        return result

    def run_all(self, enabled_only: bool = True):
        results: Dict[str, Any] = {}
        for aid, meta in list(self.agents.items()):
            if not isinstance(meta, dict):
                # Repair and continue
                self.agents[aid] = _default_agent_meta(aid, aid, "", True)
                meta = self.agents[aid]
            if enabled_only and not meta.get("enabled", True):
                continue
            results[aid] = self.run_agent(aid)
        return results

registry = AgentRegistry()
from typing import Dict, Any
from .base_agent import BaseAgent
from .new_ai_agent import NewAIAgent
from .sentiment_agent import SentimentAgent
from .storage import load_result

_REGISTRY: Dict[str, BaseAgent] = {}

def init_registry():
    # idempotent
    if "new_ai_analyzer" not in _REGISTRY:
        _REGISTRY["new_ai_analyzer"] = NewAIAgent()
    if "sentiment_analyzer" not in _REGISTRY:
        _REGISTRY["sentiment_analyzer"] = SentimentAgent()

def list_agents():
    init_registry()
    return [agent.to_dict() for agent in _REGISTRY.values()]

def get_agent(agent_id: str) -> BaseAgent | None:
    init_registry()
    return _REGISTRY.get(agent_id)

def register_agent(agent_id: str, agent: BaseAgent):
    init_registry()
    _REGISTRY[agent_id] = agent

def enable_agent(agent_id: str) -> bool:
    agent = get_agent(agent_id)
    if not agent: return False
    agent.enabled = True
    return True

def disable_agent(agent_id: str) -> bool:
    agent = get_agent(agent_id)
    if not agent: return False
    agent.enabled = False
    return True

def run_agent(agent_id: str, **kwargs) -> Dict[str, Any]:
    agent = get_agent(agent_id)
    if not agent:
        return {"success": False, "error": f"Agent {agent_id} not found"}
    if not agent.enabled:
        return {"success": False, "error": f"Agent {agent_id} is disabled"}
    result = agent.run(**kwargs)
    if not isinstance(result, dict) or "success" not in result:
        return {"success": False, "error": "Invalid agent return shape"}
    return result

def run_all_agents() -> Dict[str, Any]:
    init_registry()
    results: Dict[str, Any] = {}
    for aid, agent in _REGISTRY.items():
        if not agent.enabled:
            results[aid] = {"success": False, "error": "Agent disabled"}
            continue
        results[aid] = agent.run()
    return {"success": True, "data": results}

def get_last_result(agent_id: str) -> Dict[str, Any]:
    agent = get_agent(agent_id)
    if not agent:
        return {"success": False, "error": f"Agent {agent_id} not found"}
    # Prefer memory; fallback to disk
    return agent.last_result or load_result(agent_id) or {"success": False, "error": "No result"}
# src/agents/registry.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, Any, Optional
import json, os, time

LOG_DIR = "logs/agents"
os.makedirs(LOG_DIR, exist_ok=True)

@dataclass
class Agent:
    key: str
    name: str
    enabled: bool = True
    run_fn: Optional[Callable[[], Dict[str, Any]]] = None
    last_result: Optional[Dict[str, Any]] = field(default=None)

class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Agent] = {}
        self._config: Dict[str, Any] = {
            "max_runtime_sec": 30,
            "concurrency": 1,
        }

    # ---- public API ----
    def register(self, agent: Agent) -> None:
        self._agents[agent.key] = agent

    def list(self):
        return [
            {
                "key": a.key,
                "name": a.name,
                "enabled": a.enabled,
                "has_result": a.last_result is not None
            }
            for a in self._agents.values()
        ]

    def get(self, key: str) -> Optional[Agent]:
        return self._agents.get(key)

    def enable(self, key: str) -> bool:
        a = self.get(key)
        if not a: return False
        a.enabled = True
        return True

    def disable(self, key: str) -> bool:
        a = self.get(key)
        if not a: return False
        a.enabled = False
        return True

    def run(self, key: str) -> Dict[str, Any]:
        a = self.get(key)
        if not a:
            return {"success": False, "error": f"Agent {key} not found"}
        if not a.enabled:
            return {"success": False, "error": f"Agent {key} is disabled"}
        if not a.run_fn:
            return {"success": False, "error": f"Agent {key} has no runner"}

        result = a.run_fn() or {}
        # normalize minimal schema used by tests
        now = int(time.time())
        result.setdefault("agent", key)
        result.setdefault("timestamp", now)
        result.setdefault("success", True)

        a.last_result = result
        self._persist_result(key, result)
        return {"success": True, "result": result}

    def run_all(self) -> Dict[str, Any]:
        outputs = {}
        for key in list(self._agents.keys()):
            outputs[key] = self.run(key)
        return {"success": True, "results": outputs}

    def get_last_result(self, key: str) -> Optional[Dict[str, Any]]:
        a = self.get(key)
        return a.last_result if a else None

    # config
    def get_config(self) -> Dict[str, Any]:
        return {"success": True, "config": dict(self._config)}

    def set_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        # accept dict only
        if not isinstance(cfg, dict):
            return {"success": False, "error": "config must be an object"}
        self._config.update(cfg)
        return {"success": True, "config": dict(self._config)}

    # history (very light)
    def history(self, key: str) -> Dict[str, Any]:
        path = os.path.join(LOG_DIR, f"{key}.jsonl")
        items = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            items.append(json.loads(line))
                        except Exception:
                            pass
        return {"success": True, "history": items}

    # ---- private ----
    def _persist_result(self, key: str, payload: Dict[str, Any]):
        path = os.path.join(LOG_DIR, f"{key}.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")


# global singleton
REGISTRY = AgentRegistry()
