
"""
Options API Endpoints
"""

from flask import Blueprint, jsonify, request
import logging
from products.options.service import options_service
from common_repository.utils.error_handler import ErrorContext

logger = logging.getLogger(__name__)

# Create blueprint for options endpoints
options_bp = Blueprint('options', __name__, url_prefix='/api/options')

@options_bp.route('/short-strangle/<symbol>', methods=['GET'])
def analyze_short_strangle(symbol):
    """Analyze short strangle strategy for a symbol"""
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        with ErrorContext("short strangle analysis"):
            result = options_service.analyze_short_strangle(symbol.upper(), force_refresh)
            
            if result:
                return jsonify({
                    'success': True,
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failed to analyze short strangle for {symbol}'
                }), 404
                
    except Exception as e:
        logger.error(f"Error in short strangle analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@options_bp.route('/strategies', methods=['GET'])
def get_options_strategies():
    """Get options strategies data"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        
        with ErrorContext("options strategies"):
            result = options_service.get_options_strategies_data(timeframe)
            
            if result and result.get('success'):
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to get strategies data',
                    'timeframe': timeframe
                }), 500
                
    except Exception as e:
        logger.error(f"Error in options strategies endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@options_bp.route('/active-predictions', methods=['GET'])
def get_active_predictions():
    """Get active options predictions"""
    try:
        with ErrorContext("active options predictions"):
            predictions = options_service.get_active_options_predictions()
            
            return jsonify({
                'success': True,
                'predictions': predictions,
                'count': len(predictions)
            })
            
    except Exception as e:
        logger.error(f"Error in active predictions endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'predictions': []
        }), 500

@options_bp.route('/health', methods=['GET'])
def options_service_health():
    """Health check for options service"""
    try:
        return jsonify({
            'service': 'options',
            'status': 'healthy',
            'supported_strategies': options_service.supported_strategies,
            'timestamp': options_service.get_options_strategies_data('5D') is not None
        })
    except Exception as e:
        return jsonify({
            'service': 'options',
            'status': 'unhealthy',
            'error': str(e)
        }), 500
