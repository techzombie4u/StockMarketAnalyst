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
options_bp = Blueprint('options', __name__)

# Import the strangle engine with proper error handling
try:
    from src.options.strangle_engine import StrangleEngine
    logger.info("✅ StrangleEngine imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import StrangleEngine: {e}")
    StrangleEngine = None

def generate_mock_strategy_data(symbol: str, timeframe: str) -> dict:
    """Generate consistent mock data for strategies table"""
    try:
        # Simulate realistic data based on symbol hash for consistency
        symbol_hash = hash(symbol) % 1000

        base_spot = 1500 + (symbol_hash % 500)  # 1500-2000 range
        call_strike = base_spot + 100
        put_strike = base_spot - 100

        # DTE based on timeframe
        dte_map = {'45D': 45, '30D': 30, '21D': 21, '14D': 14, '10D': 10, '7D': 7}
        dte = dte_map.get(timeframe, 30)

        # Generate due date
        due_date = (datetime.datetime.now() + datetime.timedelta(days=dte)).strftime('%Y-%m-%d')

        # Calculate realistic option premiums
        call_premium = max(10, 50 - (symbol_hash % 30))
        put_premium = max(10, 45 - (symbol_hash % 25))
        net_credit = call_premium + put_premium

        # Breakeven calculations
        breakeven_min = put_strike - net_credit
        breakeven_max = call_strike + net_credit

        # Other metrics
        iv = 20 + (symbol_hash % 20)  # 20-40%
        iv_rank = 30 + (symbol_hash % 40)  # 30-70%
        roi_on_margin = (net_credit / (base_spot * 0.2)) * 100  # Assuming 20% margin
        theta_day = -(net_credit * 0.05)  # Rough theta estimate

        # Market metrics
        breakout_prob = min(0.4, (symbol_hash % 40) / 100)
        market_stability = ['Low', 'Medium', 'High'][symbol_hash % 3]

        return {
            'stock': symbol,
            'verdict': 'Hold' if symbol_hash % 2 == 0 else 'Bullish',
            'ai_verdict': 'On Track',
            'final_outcome': 'IN_PROGRESS',
            'spot': base_spot,
            'call': call_strike,
            'put': put_strike,
            'due_date': due_date,
            'breakeven_min': breakeven_min,
            'breakeven_max': breakeven_max,
            'breakout_prob': breakout_prob,
            'market_stability': market_stability,
            'event': 'None' if symbol_hash % 3 == 0 else 'Earnings',
            'max_loss_2s': 'Moderate',
            'stop_loss_pct': 50,
            'dte': dte,
            'iv': iv,
            'iv_rank': iv_rank,
            'net_credit': net_credit,
            'theta_day': theta_day,
            'roi_on_margin': roi_on_margin
        }

    except Exception as e:
        logger.error(f"Error generating strategy data for {symbol}: {e}")
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
            'strategies': strategies,
            'count': len(strategies),
            'timeframe': timeframe,
            'timestamp': datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Error getting options strategies: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'strategies': [],
            'count': 0
        }), 500

@options_bp.route('/chain/<symbol>', methods=['GET'])
def get_options_chain(symbol):
    """Get options chain data for a symbol"""
    try:
        logger.info(f"🔗 Getting options chain for {symbol}")

        # Generate mock options chain data
        symbol_hash = hash(symbol) % 1000
        base_spot = 1500 + (symbol_hash % 500)  # 1500-2000 range

        # Get lot size
        lot_sizes = {
            'RELIANCE': 505, 'TCS': 300, 'HDFCBANK': 550, 'INFY': 300,
            'ICICIBANK': 1375, 'WIPRO': 3000, 'LT': 225, 'MARUTI': 100
        }
        lot_size = lot_sizes.get(symbol, 1000)
        
        # Generate expiry dates (next 3 weekly expiries)
        expiries = []
        base_date = datetime.datetime.now()
        for i in range(3):
            # Find next Thursday
            days_ahead = (3 - base_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_thursday = base_date + datetime.timedelta(days=days_ahead + (i * 7))
            expiries.append(next_thursday.strftime('%Y-%m-%d'))

        # Generate strikes around spot
        strikes = []
        base_strike = round(base_spot / 50) * 50
        for i in range(-10, 11):
            strikes.append(base_strike + (i * 50))

        # Generate CE and PE prices
        ce_data = {}
        pe_data = {}

        for expiry in expiries:
            ce_data[expiry] = {}
            pe_data[expiry] = {}

            for strike in strikes:
                # Simple option pricing simulation
                if strike > base_spot:  # OTM calls
                    ce_price = max(1, 50 - (strike - base_spot) / 10)
                else:  # ITM calls
                    ce_price = (base_spot - strike) + max(5, 30 - (base_spot - strike) / 20)

                if strike < base_spot:  # OTM puts
                    pe_price = max(1, 50 - (base_spot - strike) / 10)
                else:  # ITM puts
                    pe_price = (strike - base_spot) + max(5, 30 - (strike - base_spot) / 20)

                ce_data[expiry][str(strike)] = round(ce_price, 2)
                pe_data[expiry][str(strike)] = round(pe_price, 2)

        # Calculate IV and IV Rank
        iv = 18 + (hash(symbol) % 20)
        iv_rank = 30 + (hash(symbol) % 40)

        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'spot': float(base_spot),
                'lotSize': lot_size,
                'expiries': expiries,
                'strikes': strikes,
                'ce': ce_data,
                'pe': pe_data,
                'iv': float(iv),
                'ivRank': float(iv_rank)
            },
            'timestamp': datetime.datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Error getting options chain for {symbol}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
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

