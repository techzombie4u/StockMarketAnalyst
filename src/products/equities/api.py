"""
Equity API endpoints
"""

from flask import Blueprint, jsonify, request
from .service import equity_service
from src.common_repository.utils.pinned_manager import pinned_manager

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
    """Get risk metrics for a symbol"""
    try:
        # This would integrate with actual risk calculation
        return jsonify({
            'symbol': symbol,
            'risk_score': 65,
            'volatility': 0.25,
            'beta': 1.2,
            'var_95': -0.08
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@equity_bp.route('/pinned_stats')
def get_pinned_stats():
    """Get aggregated stats for pinned equity symbols"""
    try:
        # Get sample equity data (in real implementation, this would come from current market data)
        sample_data = []
        pinned_symbols = pinned_manager.get_pinned_symbols('equity')

        for symbol in pinned_symbols:
            analysis = equity_service.analyze_equity(symbol)
            if analysis:
                sample_data.append(analysis)

        stats = pinned_manager.get_pinned_stats('equity', sample_data)

        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': equity_service._get_current_time().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@equity_bp.route('/pin/<symbol>', methods=['POST'])
def pin_symbol(symbol):
    """Pin a symbol"""
    try:
        success = pinned_manager.add_pinned_symbol(symbol, 'equity')
        return jsonify({
            'success': success,
            'message': f'Symbol {symbol} {"pinned" if success else "failed to pin"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@equity_bp.route('/unpin/<symbol>', methods=['POST'])
def unpin_symbol(symbol):
    """Unpin a symbol"""
    try:
        success = pinned_manager.remove_pinned_symbol(symbol, 'equity')
        return jsonify({
            'success': success,
            'message': f'Symbol {symbol} {"unpinned" if success else "failed to unpin"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500