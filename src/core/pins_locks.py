
import os, json, threading
BASE = os.path.join(os.path.dirname(__file__), "../../data/persistent")
os.makedirs(BASE, exist_ok=True)

PINS_PATH  = os.path.join(BASE, "pins.json")
LOCKS_PATH = os.path.join(BASE, "locks.json")
_LOCK = threading.Lock()

def _read(path):
    try:
        with open(path,"r") as f: return json.load(f)
    except Exception:
        return []

def _write(path, data):
    with open(path,"w") as f: json.dump(data, f, indent=2)

def list_pins():  return _read(PINS_PATH)
def list_locks(): return _read(LOCKS_PATH)

def pin(item):
    with _LOCK:
        pins = list_pins()
        if item not in pins:
            pins.append(item); _write(PINS_PATH, pins)
        return pins

def unpin(item):
    with _LOCK:
        pins = [x for x in list_pins() if x != item]
        _write(PINS_PATH, pins); return pins

def lock(item):
    with _LOCK:
        locks = list_locks()
        if item not in locks:
            locks.append(item); _write(LOCKS_PATH, locks)
        return locks

def unlock(item):
    with _LOCK:
        locks = [x for x in list_locks() if x != item]
        _write(LOCKS_PATH, locks); return locks
