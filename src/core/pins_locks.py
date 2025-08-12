from flask import Blueprint, jsonify, request, g
from src.core.validation import validate_request_data, PinsLocksUpdateSchema, get_validated_data
import os, json, threading
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

BASE = os.path.join(os.path.dirname(__file__), "../../data/persistent")
os.makedirs(BASE, exist_ok=True)

PINS_PATH  = os.path.join(BASE, "pins.json")
LOCKS_PATH = os.path.join(BASE, "locks.json")
_LOCK = threading.Lock()

pins_locks_bp = Blueprint('pins_locks', __name__, url_prefix='/api')

# Initialize Flask-Limiter
limiter = Limiter(key_func=get_remote_address, default_limits="60 per minute")

def _read(path):
    try:
        with open(path,"r") as f: return json.load(f)
    except Exception:
        return {}

def _write(path, data):
    with open(path,"w") as f: json.dump(data, f, indent=2)

def list_pins():
    data = _read(PINS_PATH)
    return data if isinstance(data, dict) else {}

def list_locks():
    data = _read(LOCKS_PATH)
    return data if isinstance(data, dict) else {}

def pin(product_type, symbol):
    with _LOCK:
        pins = list_pins()
        if product_type not in pins:
            pins[product_type] = []
        if symbol not in pins[product_type]:
            pins[product_type].append(symbol)
            _write(PINS_PATH, pins)
        return pins

def unpin(product_type, symbol):
    with _LOCK:
        pins = list_pins()
        if product_type in pins and symbol in pins[product_type]:
            pins[product_type].remove(symbol)
            if not pins[product_type]:
                del pins[product_type]
            _write(PINS_PATH, pins)
        return pins

def lock(product_type, item_id):
    with _LOCK:
        locks = list_locks()
        if product_type not in locks:
            locks[product_type] = []
        if item_id not in locks[product_type]:
            locks[product_type].append(item_id)
            _write(LOCKS_PATH, locks)
        return locks

def unlock(product_type, item_id):
    with _LOCK:
        locks = list_locks()
        if product_type in locks and item_id in locks[product_type]:
            locks[product_type].remove(item_id)
            if not locks[product_type]:
                del locks[product_type]
            _write(LOCKS_PATH, locks)
        return locks

def is_locked(product_type, item_id):
    locks = list_locks()
    return product_type in locks and item_id in locks[product_type]

@pins_locks_bp.route('/status', methods=['GET'])
@limiter.limit("60 per minute")
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
@limiter.limit("60 per minute")
def get_pins():
    """Get all pinned items in structured format"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        pins = list_pins()
        return jsonify({"pins": pins})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/pins', methods=['POST'])
@limiter.limit("60 per minute")
@validate_request_data(PinsLocksUpdateSchema, location='json')
def update_pins():
    """Update pinned items"""
    validated_data = get_validated_data()
    try:
        product_type = validated_data.get('type', '').upper()
        symbol = validated_data.get('symbol', '')

        if not product_type or not symbol:
            return jsonify({"error": "Missing type or symbol"}), 400

        current_pins = list_pins()

        # Check if item is already pinned
        is_already_pinned = (product_type in current_pins and
                           symbol in current_pins[product_type])

        if is_already_pinned:
            # Remove from pins (toggle off)
            pins = unpin(product_type, symbol)
        else:
            # Add to pins
            pins = pin(product_type, symbol)

        return jsonify({
            "success": True,
            "pins": pins,
            "action": "unpinned" if is_already_pinned else "pinned"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks', methods=['GET'])
@limiter.limit("60 per minute")
def get_locks():
    """Get all locked items in structured format"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        locks = list_locks()
        return jsonify({"locks": locks})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks', methods=['POST'])
@limiter.limit("60 per minute")
@validate_request_data(PinsLocksUpdateSchema, location='json')
def update_locks():
    """Update locked items"""
    validated_data = get_validated_data()
    try:
        product_type = validated_data.get('type', '').upper()
        item_id = validated_data.get('id', '') or validated_data.get('symbol', '')

        if not product_type or not item_id:
            return jsonify({"error": "Missing type or id/symbol"}), 400

        current_locks = list_locks()

        # Check if item is already locked
        is_already_locked = (product_type in current_locks and
                           item_id in current_locks[product_type])

        if is_already_locked:
            # Remove from locks (toggle off)
            locks = unlock(product_type, item_id)
        else:
            # Add to locks
            locks = lock(product_type, item_id)

        return jsonify({
            "success": True,
            "locks": locks,
            "action": "unlocked" if is_already_locked else "locked"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks/check', methods=['POST'])
@limiter.limit("60 per minute")
def check_lock():
    """Check if an action is blocked by lock - returns 423 if locked"""
    try:
        data = request.get_json()
        product_type = data.get('type', '').upper()
        item_id = data.get('id', '') or data.get('symbol', '')

        if is_locked(product_type, item_id):
            return jsonify({
                "error": "Action blocked - item is locked",
                "locked": True,
                "product_type": product_type,
                "item_id": item_id
            }), 423

        return jsonify({"locked": False})

    except Exception as e:
        return jsonify({"error": str(e)}), 500