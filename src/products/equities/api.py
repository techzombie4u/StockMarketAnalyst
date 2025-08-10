
"""
Equity API endpoints
"""

from flask import Blueprint, jsonify, request
from .service import equity_service

# Create blueprint with correct name
equity_bp = Blueprint('equity', __name__, url_prefix='/api/equity')

@equity_bp.route('/analyze/<symbol>', methods=['GET'])
def analyze_equity_endpoint(symbol):
    """Analyze equity symbol"""
    try:
        analysis = equity_service.analyze_equity(symbol)
        return jsonify({
            'success': True,
            'data': analysis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@equity_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get equity recommendations"""
    try:
        count = request.args.get('count', 10, type=int)
        recommendations = equity_service.get_equity_recommendations(count)
        return jsonify({
            'success': True,
            'data': recommendations
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@equity_bp.route('/risk/<symbol>', methods=['GET'])
def get_risk_metrics(symbol):
    """Get risk metrics for equity"""
    try:
        metrics = equity_service.calculate_risk_metrics(symbol)
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
