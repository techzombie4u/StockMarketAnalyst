
import json, os, threading
from typing import Optional, Dict, Any

_LOCK = threading.Lock()
_DATA_DIR = os.path.join(os.getcwd(), "data")
_FILE = os.path.join(_DATA_DIR, "agents_results.json")

def _ensure_paths():
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_FILE):
        with open(_FILE, "w") as f:
            json.dump({}, f)

def save_result(agent_id: str, result: Dict[str, Any]) -> None:
    _ensure_paths()
    with _LOCK:
        with open(_FILE, "r") as f:
            try:
                store = json.load(f)
                if not isinstance(store, dict):
                    store = {}
            except Exception:
                store = {}
        store[agent_id] = result
        with open(_FILE, "w") as f:
            json.dump(store, f)

def load_result(agent_id: str) -> Optional[Dict[str, Any]]:
    _ensure_paths()
    with _LOCK:
        with open(_FILE, "r") as f:
            try:
                store = json.load(f)
                if not isinstance(store, dict):
                    return None
                return store.get(agent_id)
            except Exception:
                return None
