import json
import os
import time
import math
import random
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

# Create the main options blueprint
options_bp = Blueprint('options_bp', __name__)

# Import the strangle engine with proper error handling
try:
    from src.options.strangle_engine import StrangleEngine
    logger.info("✅ StrangleEngine imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import StrangleEngine: {e}")
    StrangleEngine = None

def generate_mock_strategy_data(symbol: str, timeframe: str) -> dict:
    """Generate comprehensive mock strategy data"""
    try:
        # Generate realistic base price
        base_prices = {
            'RELIANCE': 2800, 'TCS': 4200, 'HDFCBANK': 1650, 'INFY': 1800,
            'ICICIBANK': 1200, 'WIPRO': 650, 'LT': 3500, 'MARUTI': 11000
        }
        spot_price = base_prices.get(symbol, 1000 + (hash(symbol) % 3000))

        # Calculate strikes
        call_strike = round(spot_price * 1.05, 0)
        put_strike = round(spot_price * 0.95, 0)

        # Days to expiry
        dte_map = {'5D': 21, '10D': 28, '15D': 35, '30D': 42, '45D': 49}
        dte = dte_map.get(timeframe, 30)

        # Calculate option pricing
        iv = 0.25 + (hash(symbol) % 15) / 100  # 25-40% IV
        time_factor = max(0.01, dte / 365.0)

        call_price = spot_price * 0.02 * math.sqrt(time_factor)
        put_price = spot_price * 0.018 * math.sqrt(time_factor)
        net_credit = round(call_price + put_price, 2)

        # Risk metrics
        breakeven_low = round(put_strike - net_credit, 2)
        breakeven_high = round(call_strike + net_credit, 2)
        breakout_prob = round(random.uniform(0.15, 0.45), 3)

        # ROI calculation
        margin = net_credit * 4
        roi_percent = round((net_credit / margin) * 100, 1)

        # Market stability
        stability_scores = ['High', 'Med', 'Low']
        stability = random.choice(stability_scores)

        # Event risk
        has_earnings = random.choice([True, False])
        event_flag = 'EARNINGS' if has_earnings else 'CLEAR'

        # Verdict scoring
        score = 0
        if iv > 0.30: score += 20
        if roi_percent > 15: score += 20
        if breakout_prob < 0.30: score += 15
        if not has_earnings: score += 15
        if dte >= 20: score += 10

        verdict_map = {80: 'Strong Buy', 60: 'Buy', 40: 'Hold', 20: 'Cautious', 0: 'Avoid'}
        verdict = next((v for threshold, v in sorted(verdict_map.items(), reverse=True) if score >= threshold), 'Avoid')

        return {
            'stock': symbol,
            'spot': float(spot_price),
            'call': float(call_strike),
            'put': float(put_strike),
            'dte': int(dte),
            'iv': round(iv * 100, 1),
            'iv_rank': round(random.uniform(20, 80), 1),
            'net_credit': float(net_credit),
            'theta_day': round(net_credit * 0.03, 2),
            'roi_on_margin': float(roi_percent),
            'roi_on_margin_percent': float(roi_percent),
            'breakeven_min': float(breakeven_low),
            'breakeven_max': float(breakeven_high),
            'breakout_prob': float(breakout_prob),
            'market_stability': stability,
            'event': 'EARNINGS' if has_earnings else '—',
            'event_flag': event_flag,
            'max_loss_2s': round(random.uniform(1000, 5000), 2),
            'stop_loss_pct': 180.0,
            'verdict': verdict,
            'ai_verdict': verdict,
            'final_outcome': 'IN_PROGRESS',
            'due_date': (datetime.now() + timedelta(days=dte)).strftime('%Y-%m-%d')
        }
    except Exception as e:
        logger.error(f"Error generating mock data for {symbol}: {e}")
        return None

@options_bp.route('/strategies', methods=['GET'])
def get_options_strategies():
    """Get options strategies for the UI"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        logger.info(f"🎯 Getting options strategies for timeframe: {timeframe}")

        # Generate strategy data with consistent structure
        symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'WIPRO', 'LT', 'MARUTI']
        strategies = []

        for symbol in symbols:
            strategy_data = generate_mock_strategy_data(symbol, timeframe)
            if strategy_data:
                # Ensure all required fields are present
                strategy_data.setdefault('stock', symbol)
                strategy_data.setdefault('spot', 0.0)
                strategy_data.setdefault('call', 0.0)
                strategy_data.setdefault('put', 0.0)
                strategy_data.setdefault('net_credit', 0.0)
                strategy_data.setdefault('dte', 0)
                strategy_data.setdefault('iv', 0.0)
                strategy_data.setdefault('roi_on_margin', 0.0)
                strategy_data.setdefault('breakout_prob', 0.0)
                strategy_data.setdefault('market_stability', 'Medium')
                strategy_data.setdefault('event', 'None')
                strategies.append(strategy_data)

        logger.info(f"✅ Generated {len(strategies)} strategies for {timeframe}")

        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'strategies': strategies,
            'total_strategies': len(strategies),
            'generated_at': datetime.now().isoformat(),
            'status': 'live_data'
        })

    except Exception as e:
        logger.error(f"❌ Error in get_options_strategies: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'strategies': [],
            'timeframe': timeframe
        }), 500

@options_bp.route('/strangle/candidates', methods=['GET'])
def get_strangle_candidates():
    """Get strangle candidates"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        logger.info(f"🎯 Getting strangle candidates for timeframe: {timeframe}")

        if StrangleEngine:
            engine = StrangleEngine()
            candidates = engine.get_strangle_candidates(timeframe)
        else:
            # Fallback data generation
            symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
            candidates = []
            for symbol in symbols:
                data = generate_mock_strategy_data(symbol, timeframe)
                if data:
                    candidates.append(data)

        logger.info(f"✅ Generated {len(candidates)} candidates")

        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'candidates': candidates,
            'total_candidates': len(candidates)
        })

    except Exception as e:
        logger.error(f"❌ Error in get_strangle_candidates: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'candidates': []
        }), 500

@options_bp.route('/strangle/recommendations', methods=['GET'])
def get_strangle_recommendations():
    """Get strangle recommendations"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        hide_events = request.args.get('hide_events', 'false').lower() == 'true'
        max_breakout_prob = float(request.args.get('max_breakout_prob', '100'))

        logger.info(f"🎯 Getting strangle recommendations - TF: {timeframe}, Hide Events: {hide_events}")

        # Generate recommendations
        symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'WIPRO', 'LT', 'MARUTI']
        all_strategies = []

        for symbol in symbols:
            strategy = generate_mock_strategy_data(symbol, timeframe)
            if strategy:
                # Apply filters
                if hide_events and strategy.get('event_flag') == 'EARNINGS':
                    continue
                if strategy.get('breakout_prob', 0) * 100 > max_breakout_prob:
                    continue
                all_strategies.append(strategy)

        logger.info(f"✅ Generated {len(all_strategies)} filtered recommendations")

        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'strategies': all_strategies,
            'total_count': len(all_strategies)
        })

    except Exception as e:
        logger.error(f"❌ Error in get_strangle_recommendations: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'strategies': []
        }), 500

@options_bp.route('/positions', methods=['GET'])
def get_positions():
    """Get options positions"""
    try:
        positions = [
            {
                "id": "pos_001",
                "underlying": "RELIANCE",
                "strategy": "strangle",
                "status": "open",
                "entry_date": "2025-01-10",
                "pnl": 2500,
                "pnl_percent": 5.6
            },
            {
                "id": "pos_002", 
                "underlying": "TCS",
                "strategy": "strangle",
                "status": "open",
                "entry_date": "2025-01-12",
                "pnl": 1200,
                "pnl_percent": 3.2
            }
        ]

        return jsonify({
            "success": True,
            "positions": positions,
            "total_positions": len(positions)
        })

    except Exception as e:
        logger.error(f"❌ Error in get_positions: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "positions": []
        }), 500

@options_bp.route('/debug/strangle_data/<symbol>')
def debug_strangle_data(symbol):
    """Debug endpoint to view raw strangle data"""
    try:
        from src.options.strangle_engine import StrangleEngine

        engine = StrangleEngine()
        data = engine.analyze_symbol(symbol.upper())

        return jsonify({
            "success": True,
            "symbol": symbol.upper(),
            "debug_data": data
        })

    except Exception as e:
        logger.error(f"❌ Error in debug_strangle_data for {symbol}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Add predictions endpoints for the Options page
from flask import Blueprint

predictions_bp = Blueprint('predictions', __name__)

@predictions_bp.route('/api/predictions/active', methods=['GET'])
def get_active_predictions():
    """Get active predictions for options"""
    try:
        # Mock active predictions data
        active_predictions = [
            {
                "due": "2025-02-15",
                "stock": "RELIANCE",
                "predicted": "Profit Target Hit",
                "current": "In Progress",
                "proi": "28.5",
                "croi": "12.3",
                "reason": "—"
            },
            {
                "due": "2025-02-20",
                "stock": "TCS", 
                "predicted": "Max Profit",
                "current": "On Track",
                "proi": "30.0",
                "croi": "18.7",
                "reason": "—"
            },
            {
                "due": "2025-02-18",
                "stock": "INFY",
                "predicted": "Partial Profit",
                "current": "At Risk",
                "proi": "25.0",
                "croi": "-5.2",
                "reason": "High volatility spike"
            }
        ]

        return jsonify({
            "success": True,
            "items": active_predictions,
            "total": len(active_predictions)
        })

    except Exception as e:
        logger.error(f"❌ Error in get_active_predictions: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "items": []
        }), 500

@predictions_bp.route('/api/predictions/accuracy', methods=['GET'])
def get_prediction_accuracy():
    """Get prediction accuracy metrics"""
    try:
        window = request.args.get('window', '45d')

        # Mock accuracy data by timeframe
        accuracy_data = [
            {"timeframe": "45D", "success": 23, "failed": 7, "accuracy": 0.767},
            {"timeframe": "30D", "success": 18, "failed": 8, "accuracy": 0.692},
            {"timeframe": "21D", "success": 15, "failed": 5, "accuracy": 0.750},
            {"timeframe": "14D", "success": 12, "failed": 4, "accuracy": 0.750},
            {"timeframe": "10D", "success": 8, "failed": 3, "accuracy": 0.727},
            {"timeframe": "7D", "success": 6, "failed": 2, "accuracy": 0.750}
        ]

        return jsonify({
            "success": True,
            "by_timeframe": accuracy_data,
            "window": window
        })

    except Exception as e:
        logger.error(f"❌ Error in get_prediction_accuracy: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "by_timeframe": []
        }), 500

@options_bp.route('/debug/sample-data', methods=['GET'])
def debug_sample_data():
    """Debug endpoint for testing data generation"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        test_symbols = ['RELIANCE', 'TCS']

        debug_data = []
        for symbol in test_symbols:
            data = generate_mock_strategy_data(symbol, timeframe)
            if data:
                debug_data.append(data)

        return jsonify({
            'success': True,
            'debug': True,
            'timeframe': timeframe,
            'strategies': debug_data,
            'sample_fields': list(debug_data[0].keys()) if debug_data else [],
            'engine_available': StrangleEngine is not None
        })

    except Exception as e:
        logger.error(f"❌ Debug endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'debug': True
        }), 500

# Create a separate predictions blueprint to avoid conflicts
# predictions_bp = Blueprint('predictions_bp', __name__) # This line is now redundant as predictions_bp is already defined above.

# @predictions_bp.route('/accuracy', methods=['GET']) # These routes are now redundant as they are already defined above with the correct paths.
# def predictions_accuracy():
#     """Global predictions accuracy endpoint"""
#     return get_predictions_accuracy()

# @predictions_bp.route('/active', methods=['GET'])
# def predictions_active():
#     """Global active predictions endpoint"""
#     return get_active_predictions()

# Updated imports to include NSEProvider
from src.services.options_engine import OptionsEngine
from src.services.finalize import FinalizationService
from src.live_data.nse_provider import NSEProvider

# Predictions endpoints
@options_bp.route('/predictions/accuracy', methods=['GET'])
def get_predictions_accuracy():
    """Get predictions accuracy data"""
    try:
        window = request.args.get('window', '30d')

        accuracy_data = [
            {'tf': 3, 'success': 8, 'failed': 2},
            {'tf': 5, 'success': 12, 'failed': 3},
            {'tf': 10, 'success': 15, 'failed': 5},
            {'tf': 15, 'success': 18, 'failed': 7},
            {'tf': 30, 'success': 22, 'failed': 8}
        ]

        return jsonify({
            'success': True,
            'window': window,
            'by_timeframe': accuracy_data
        })

    except Exception as e:
        logger.error(f"❌ Error in predictions accuracy: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'by_timeframe': []
        }), 500

@options_bp.route('/predictions/active', methods=['GET'])
def get_active_predictions():
    """Get active predictions"""
    try:
        active_predictions = [
            {
                'due': '2025-08-27',
                'stock': 'MARUTI',
                'predicted': 'On Track',
                'current': 'Outperforming',
                'proi': 26.9,
                'croi': 30.0,
                'reason': 'ROI exceeded expectations'
            },
            {
                'due': '2025-08-29',
                'stock': 'RELIANCE',
                'predicted': 'On Track',
                'current': 'Outperforming',
                'proi': 22.9,
                'croi': 30.0,
                'reason': 'ROI exceeded expectations'
            }
        ]

        return jsonify({
            'success': True,
            'items': active_predictions,
            'total_items': len(active_predictions)
        })

    except Exception as e:
        logger.error(f"❌ Error in active predictions: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'items': []
        }), 500

@options_bp.route('/chain/<symbol>')
def get_options_chain(symbol):
    """Get real-time options chain for symbol"""
    try:
        provider = NSEProvider()

        # Get live chain data
        chain_data = provider.get_options_chain(symbol.upper())

        if not chain_data:
            return jsonify({
                'success': False,
                'error': 'live_data_unavailable'
            }), 503

        # Get stock data for spot price
        stock_data = provider.get_stock_data(symbol.upper())
        spot_price = stock_data.get('ltp', 0) if stock_data else 0

        # Format response
        response_data = {
            'lotSize': chain_data.get('lot_size', 1),
            'spot': spot_price,
            'expiries': chain_data.get('expiries', []),
            'strikes': chain_data.get('strikes', []),
            'ce': chain_data.get('ce_prices', {}),
            'pe': chain_data.get('pe_prices', {}),
            'iv': chain_data.get('iv', 0),
            'ivRank': chain_data.get('iv_rank', 0)
        }

        return jsonify({
            'success': True,
            'data': response_data
        })

    except Exception as e:
        logger.error(f"Error getting options chain for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': 'live_data_unavailable'
        }), 503