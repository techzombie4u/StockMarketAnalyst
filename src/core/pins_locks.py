import os, json, threading
from datetime import datetime
from flask import Blueprint, request, jsonify

BASE = os.path.join(os.path.dirname(__file__), "../../data/persistent")
os.makedirs(BASE, exist_ok=True)

PINS_PATH  = os.path.join(BASE, "pins.json")
LOCKS_PATH = os.path.join(BASE, "locks.json")
_LOCK = threading.Lock()

pins_locks_bp = Blueprint('pins_locks', __name__)

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

@pins_locks_bp.route('/pins', methods=['GET'])
def get_pins():
    """Get all pinned items"""
    return jsonify({"pins": list_pins()})

@pins_locks_bp.route('/pins', methods=['POST'])
def add_pin():
    """Add a pinned item"""
    data = request.get_json()
    
    new_pin = {
        "id": data.get('id'),
        "type": data.get('type'),
        "symbol": data.get('symbol'),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    pin(new_pin)

    return jsonify({"success": True, "pin": new_pin})

@pins_locks_bp.route('/locks', methods=['GET'])
def get_locks():
    """Get all locked items"""
    return jsonify({"locks": list_locks()})

@pins_locks_bp.route('/locks', methods=['POST'])
def add_lock():
    """Add a locked item"""
    data = request.get_json()

    new_lock = {
        "id": data.get('id'),
        "type": data.get('type'),
        "symbol": data.get('symbol'),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    lock(new_lock)

    return jsonify({"success": True, "lock": new_lock})