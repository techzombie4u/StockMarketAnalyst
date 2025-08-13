import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

pins_locks_bp = Blueprint('pins_locks', __name__)

def load_pins():
    """Load pins data"""
    try:
        filepath = os.path.join('data', 'persistent', 'pins.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('pins', [])
    except Exception as e:
        logger.error(f"Error loading pins: {e}")
    return []

def save_pins(pins):
    """Save pins data"""
    try:
        filepath = os.path.join('data', 'persistent', 'pins.json')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "pins": pins,
            "last_updated": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving pins: {e}")
        return False

def load_locks():
    """Load locks data"""
    try:
        filepath = os.path.join('data', 'persistent', 'locks.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('locks', [])
    except Exception as e:
        logger.error(f"Error loading locks: {e}")
    return []

def save_locks(locks):
    """Save locks data"""
    try:
        filepath = os.path.join('data', 'persistent', 'locks.json')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "locks": locks,
            "last_updated": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving locks: {e}")
        return False

@pins_locks_bp.route('/pins', methods=['GET'])
def get_pins():
    """Get all pinned items"""
    try:
        pins = load_pins()
        return jsonify({
            "pins": pins,
            "total_pins": len(pins)
        })
    except Exception as e:
        logger.error(f"Error getting pins: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "pins": []
        }), 500

@pins_locks_bp.route('/pins', methods=['POST'])
def update_pins():
    """Update pins"""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')
        action = data.get('action')  # 'pin' or 'unpin'
        item_type = data.get('type', 'EQUITY')

        if not symbol or not action:
            return jsonify({
                "error": "validation_error",
                "message": "Symbol and action are required"
            }), 400

        pins = load_pins()

        if action == 'pin':
            # Add pin if not exists
            existing = next((p for p in pins if p.get('symbol') == symbol), None)
            if not existing:
                pins.append({
                    "type": item_type,
                    "symbol": symbol,
                    "pinned_at": datetime.now().isoformat(),
                    "reason": "User pinned"
                })
        elif action == 'unpin':
            # Remove pin if exists
            pins = [p for p in pins if p.get('symbol') != symbol]

        if save_pins(pins):
            return jsonify({
                "success": True,
                "action": action,
                "symbol": symbol,
                "total_pins": len(pins)
            })
        else:
            return jsonify({
                "error": "save_failed",
                "message": "Failed to save pins"
            }), 500

    except Exception as e:
        logger.error(f"Error updating pins: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500

@pins_locks_bp.route('/locks', methods=['GET'])
def get_locks():
    """Get all locked items"""
    try:
        locks = load_locks()
        return jsonify({
            "locks": locks,
            "total_locks": len(locks)
        })
    except Exception as e:
        logger.error(f"Error getting locks: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "locks": []
        }), 500

@pins_locks_bp.route('/locks', methods=['POST'])
def update_locks():
    """Update locks"""
    try:
        data = request.get_json() or {}
        symbol = data.get('symbol')
        action = data.get('action')  # 'lock' or 'unlock'
        item_type = data.get('type', 'EQUITY')

        if not symbol or not action:
            return jsonify({
                "error": "validation_error",
                "message": "Symbol and action are required"
            }), 400

        locks = load_locks()

        if action == 'lock':
            # Add lock if not exists
            existing = next((l for l in locks if l.get('symbol') == symbol), None)
            if not existing:
                locks.append({
                    "type": item_type,
                    "symbol": symbol,
                    "locked_at": datetime.now().isoformat(),
                    "reason": "User locked"
                })
        elif action == 'unlock':
            # Remove lock if exists
            locks = [l for l in locks if l.get('symbol') != symbol]

        if save_locks(locks):
            return jsonify({
                "success": True,
                "action": action,
                "symbol": symbol,
                "total_locks": len(locks)
            })
        else:
            return jsonify({
                "error": "save_failed",
                "message": "Failed to save locks"
            }), 500

    except Exception as e:
        logger.error(f"Error updating locks: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500