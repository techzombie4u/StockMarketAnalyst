
"""
Equity API Endpoints
"""

from flask import Blueprint, jsonify, request
import logging
from products.equities.service import equity_service
from common_repository.utils.error_handler import ErrorContext

logger = logging.getLogger(__name__)

# Create blueprint for equity endpoints
equity_bp = Blueprint('equity', __name__, url_prefix='/api/equity')

@equity_bp.route('/analyze/<symbol>', methods=['GET'])
def analyze_equity(symbol):
    """Analyze a specific equity symbol"""
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        with ErrorContext("equity analysis"):
            result = equity_service.analyze_equity(symbol.upper(), force_refresh)
            
            if result:
                return jsonify({
                    'success': True,
                    'data': result
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Failed to analyze {symbol}'
                }), 404
                
    except Exception as e:
        logger.error(f"Error in equity analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@equity_bp.route('/screen', methods=['GET', 'POST'])
def screen_equities():
    """Run equity screening"""
    try:
        with ErrorContext("equity screening"):
            result = equity_service.get_equity_screening_results()
            
            if result and result.get('success'):
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Screening failed'
                }), 500
                
    except Exception as e:
        logger.error(f"Error in equity screening endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@equity_bp.route('/batch-analyze', methods=['POST'])
def batch_analyze_equities():
    """Analyze multiple equities in batch"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        max_concurrent = data.get('max_concurrent', 5)
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'No symbols provided'
            }), 400
        
        with ErrorContext("batch equity analysis"):
            result = equity_service.analyze_multiple_equities(symbols, max_concurrent)
            
            return jsonify({
                'success': True,
                'data': result
            })
            
    except Exception as e:
        logger.error(f"Error in batch equity analysis endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@equity_bp.route('/health', methods=['GET'])
def equity_service_health():
    """Health check for equity service"""
    try:
        return jsonify({
            'service': 'equity',
            'status': 'healthy',
            'timestamp': equity_service._get_market_data('TEST', False) is not None
        })
    except Exception as e:
        return jsonify({
            'service': 'equity',
            'status': 'unhealthy',
            'error': str(e)
        }), 500
