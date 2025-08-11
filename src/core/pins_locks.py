from flask import Blueprint, jsonify, request
import os, json, threading
from datetime import datetime

BASE = os.path.join(os.path.dirname(__file__), "../../data/persistent")
os.makedirs(BASE, exist_ok=True)

PINS_PATH  = os.path.join(BASE, "pins.json")
LOCKS_PATH = os.path.join(BASE, "locks.json")
_LOCK = threading.Lock()

pins_locks_bp = Blueprint('pins_locks', __name__, url_prefix='/api')

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

@pins_locks_bp.route('/status', methods=['GET'])
def pins_locks_status():
    """Get pins and locks system status"""
    return jsonify({
        "status": "active",
        "module": "pins_locks",
        "endpoints": [
            "/api/pins-locks/status",
            "/api/pins-locks/pins",
            "/api/pins-locks/locks"
        ]
    })

@pins_locks_bp.route('/pins', methods=['GET'])
def get_pins():
    """Get all pinned items"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        return jsonify({"items": list_pins()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/pins', methods=['POST'])
def add_pin():
    """Add or toggle a pinned item"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        data = request.get_json()

        # Handle single item or bulk items
        if 'items' in data:
            items = data['items']
            current_pins = list_pins()
            
            for item in items:
                item_key = f"{item.get('type')}_{item.get('symbol')}"
                
                # Check if item is already pinned
                is_already_pinned = any(
                    isinstance(p, dict) and p.get('type') == item.get('type') and p.get('symbol') == item.get('symbol')
                    for p in current_pins
                )
                
                if is_already_pinned:
                    # Remove from pins (toggle off)
                    unpin(item_key)
                else:
                    # Add to pins
                    new_pin = {
                        "type": item.get('type'),
                        "symbol": item.get('symbol'),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    pin(new_pin)
        else:
            item_key = f"{data.get('type')}_{data.get('symbol')}"
            current_pins = list_pins()
            
            # Check if item is already pinned
            is_already_pinned = any(
                isinstance(p, dict) and p.get('type') == data.get('type') and p.get('symbol') == data.get('symbol')
                for p in current_pins
            )
            
            if is_already_pinned:
                unpin(item_key)
            else:
                new_pin = {
                    "type": data.get('type'),
                    "symbol": data.get('symbol'),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                pin(new_pin)

        return jsonify({
            "success": True,
            "items": list_pins()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks', methods=['GET'])
def get_locks():
    """Get all locked items"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        return jsonify({"items": list_locks()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks', methods=['POST'])
def add_lock():
    """Add or toggle a locked item"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        data = request.get_json()

        # Handle single item or bulk items
        if 'items' in data:
            items = data['items']
            current_locks = list_locks()
            
            for item in items:
                item_key = f"{item.get('type')}_{item.get('symbol')}"
                
                # Check if item is already locked
                is_already_locked = any(
                    isinstance(l, dict) and l.get('type') == item.get('type') and l.get('symbol') == item.get('symbol')
                    for l in current_locks
                )
                
                if is_already_locked:
                    # Remove from locks (toggle off)
                    unlock(item_key)
                else:
                    # Add to locks
                    new_lock = {
                        "type": item.get('type'),
                        "symbol": item.get('symbol'),
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    lock(new_lock)
        else:
            item_key = f"{data.get('type')}_{data.get('symbol')}"
            current_locks = list_locks()
            
            # Check if item is already locked
            is_already_locked = any(
                isinstance(l, dict) and l.get('type') == data.get('type') and l.get('symbol') == data.get('symbol')
                for l in current_locks
            )
            
            if is_already_locked:
                unlock(item_key)
            else:
                new_lock = {
                    "type": data.get('type'),
                    "symbol": data.get('symbol'),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                lock(new_lock)

        return jsonify({
            "success": True,
            "items": list_locks()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500