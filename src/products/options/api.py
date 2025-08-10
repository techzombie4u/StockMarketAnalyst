"""
Options API endpoints
"""

from flask import Blueprint, jsonify, request
from .service import options_service
from src.common_repository.utils.pinned_manager import pinned_manager

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

@options_bp.route('/pinned_stats')
def get_pinned_stats():
    """Get aggregated stats for pinned options symbols"""
    try:
        sample_data = []
        pinned_symbols = pinned_manager.get_pinned_symbols('options')

        for symbol in pinned_symbols:
            analysis = options_service.analyze_short_strangle(symbol)
            if analysis:
                sample_data.append(analysis)

        stats = pinned_manager.get_pinned_stats('options', sample_data)

        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': options_service._get_current_time().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@options_bp.route('/pin/<symbol>', methods=['POST'])
def pin_symbol(symbol):
    """Pin an options symbol"""
    try:
        success = pinned_manager.add_pinned_symbol(symbol, 'options')
        return jsonify({
            'success': success,
            'message': f'Symbol {symbol} {"pinned" if success else "failed to pin"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@options_bp.route('/unpin/<symbol>', methods=['POST']) 
def unpin_symbol(symbol):
    """Unpin an options symbol"""
    try:
        success = pinned_manager.remove_pinned_symbol(symbol, 'options')
        return jsonify({
            'success': success,
            'message': f'Symbol {symbol} {"unpinned" if success else "failed to unpin"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500