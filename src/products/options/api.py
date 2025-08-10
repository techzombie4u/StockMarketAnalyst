
"""
Options API endpoints
"""

from flask import Blueprint, jsonify, request
from .service import options_service

# Create blueprint with correct name
options_bp = Blueprint('options', __name__, url_prefix='/api/options')

@options_bp.route('/short-strangle/<symbol>', methods=['GET'])
def analyze_short_strangle_endpoint(symbol):
    """Analyze short strangle strategy"""
    try:
        analysis = options_service.analyze_short_strangle(symbol)
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@options_bp.route('/covered-call/<symbol>', methods=['GET'])
def analyze_covered_call_endpoint(symbol):
    """Analyze covered call strategy"""
    try:
        analysis = options_service.analyze_covered_call(symbol)
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@options_bp.route('/greeks', methods=['POST'])
def calculate_greeks_endpoint():
    """Calculate option Greeks"""
    try:
        option_data = request.get_json()
        greeks = options_service.calculate_greeks(option_data)
        return jsonify({
            'success': True,
            'data': greeks
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
