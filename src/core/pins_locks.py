from flask import Blueprint, jsonify, request
import json
from pathlib import Path

pins_locks_bp = Blueprint('pins_locks', __name__)

def get_data_file(filename):
    """Get path to data file"""
    return Path(__file__).parent.parent.parent / "data" / "persistent" / filename

def load_json_data(filename, default=None):
    """Load JSON data from file"""
    try:
        file_path = get_data_file(filename)
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return default or {}
    except:
        return default or {}

def save_json_data(filename, data):
    """Save JSON data to file"""
    try:
        file_path = get_data_file(filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

@pins_locks_bp.route('/pins', methods=['GET'])
def get_pins():
    """Get pinned items"""
    try:
        pins_data = load_json_data('pins.json', {"pinned": []})
        return jsonify(pins_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/pins', methods=['POST'])
def manage_pins():
    """Add or remove pinned items"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        action = data.get('action')  # 'pin' or 'unpin'

        if not symbol or not action:
            return jsonify({"error": "Missing symbol or action"}), 400

        pins_data = load_json_data('pins.json', {"pinned": []})
        pinned_list = pins_data.get('pinned', [])

        if action == 'pin' and symbol not in pinned_list:
            pinned_list.append(symbol)
        elif action == 'unpin' and symbol in pinned_list:
            pinned_list.remove(symbol)

        pins_data['pinned'] = pinned_list
        save_json_data('pins.json', pins_data)

        return jsonify({
            "success": True,
            "action": action,
            "symbol": symbol,
            "total_pinned": len(pinned_list)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks', methods=['GET'])
def get_locks():
    """Get locked items"""
    try:
        locks_data = load_json_data('locks.json', {"locked": []})
        return jsonify(locks_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pins_locks_bp.route('/locks', methods=['POST'])
def manage_locks():
    """Add or remove locked items"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        action = data.get('action')  # 'lock' or 'unlock'

        if not symbol or not action:
            return jsonify({"error": "Missing symbol or action"}), 400

        locks_data = load_json_data('locks.json', {"locked": []})
        locked_list = locks_data.get('locked', [])

        if action == 'lock' and symbol not in locked_list:
            locked_list.append(symbol)
        elif action == 'unlock' and symbol in locked_list:
            locked_list.remove(symbol)

        locks_data['locked'] = locked_list
        save_json_data('locks.json', locks_data)

        return jsonify({
            "success": True,
            "action": action,
            "symbol": symbol,
            "total_locked": len(locked_list)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500