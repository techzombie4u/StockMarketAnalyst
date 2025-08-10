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