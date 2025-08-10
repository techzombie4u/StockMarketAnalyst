
import os, json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

BASE_DIR = os.path.join("data", "kpi")
SNAPSHOT = os.path.join(BASE_DIR, "kpi_metrics.json")

def _utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def ensure_dirs():
    os.makedirs(BASE_DIR, exist_ok=True)

def load_snapshot() -> Optional[Dict[str, Any]]:
    try:
        if not os.path.exists(SNAPSHOT):
            return None
        with open(SNAPSHOT, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_snapshot(payload: Dict[str, Any]) -> bool:
    try:
        ensure_dirs()
        with open(SNAPSHOT, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False
