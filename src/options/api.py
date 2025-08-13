import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

# Import the short strangle engine
try:
    from src.analyzers.short_strangle_engine import ShortStrangleEngine
except ImportError:
    logger.warning("Short strangle engine not available, using fallback data")
    ShortStrangleEngine = None

logger = logging.getLogger(__name__)

options_bp = Blueprint('options', __name__)

def load_options_data():
    """Load options sample data"""
    try:
        filepath = os.path.join('data', 'fixtures', 'options_sample.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading options data: {e}")
    return {"candidates": [], "total_candidates": 0}

@options_bp.route('/strangle/candidates', methods=['GET'])
def get_strangle_candidates():
    """Get strangle candidates"""
    try:
        symbol = request.args.get('symbol', 'RELIANCE')
        expiry = request.args.get('expiry', '2024-02-29')

        # Load options data from fixtures
        import os
        import json

        options_path = os.path.join(os.path.dirname(__file__), '../data/fixtures/options_sample.json')
        if os.path.exists(options_path):
            with open(options_path, 'r') as f:
                options_data = json.load(f)
            candidates = options_data.get('strangle_candidates', [])
        else:
            candidates = [
                {
                    'call_strike': 2800,
                    'put_strike': 2600,
                    'premium_collected': 45.0,
                    'max_profit': 45.0,
                    'breakeven_upper': 2845,
                    'breakeven_lower': 2555,
                    'probability_profit': 0.65
                }
            ]

        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'expiry': expiry,
            'candidates': candidates,
            'count': len(candidates),
            'timestamp': time.time()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@options_bp.route('/strategies', methods=['GET'])
def get_options_strategies():
    """Get short strangle options strategies with real-time data"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # Import and use the short strangle engine
        from src.analyzers.short_strangle_engine import ShortStrangleEngine
        
        engine = ShortStrangleEngine()
        strategies = engine.generate_strategies(timeframe=timeframe, force_refresh=force_refresh)
        
        logger.info(f"Generated {len(strategies)} options strategies for timeframe {timeframe}")
        
        return jsonify({
            'status': 'success',
            'strategies': strategies,
            'timeframe': timeframe,
            'count': len(strategies),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'short_strangle_engine'
        })
        
    except Exception as e:
        logger.error(f"Error generating options strategies: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'strategies': [],
            'count': 0
        }), 500

@options_bp.route('/positions')
def positions():
    """Get options positions"""
    start_time = time.time()

    try:
        # Sample positions data
        positions = [
            {
                "id": "pos_001",
                "underlying": "RELIANCE",
                "strategy": "strangle",
                "status": "open",
                "entry_date": "2025-01-10",
                "pnl": 2500,
                "pnl_percent": 5.6
            }
        ]

        generation_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "positions": positions,
            "total_positions": len(positions),
            "generation_time_ms": generation_time_ms
        })

    except Exception as e:
        logger.error(f"Error in options positions: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "positions": [],
            "total_positions": 0
        }), 500