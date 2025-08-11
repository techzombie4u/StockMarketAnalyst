from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime
from src.core.cache import cache_medium, now_iso

commodities_bp = Blueprint("commodities", __name__)

@commodities_bp.route('/kpis')
def get_kpis():
    """Get commodities KPIs with timeframe support"""
    try:
        timeframe = request.args.get('timeframe', '10D')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        # Adjust KPIs based on timeframe
        timeframe_multiplier = {
            'All': 1.0,
            '30D': 0.9,
            '15D': 0.85,
            '10D': 0.8,
            '5D': 0.75,
            '3D': 0.7
        }.get(timeframe, 0.8)

        base_kpis = {
            "total_contracts": int(25 * timeframe_multiplier),
            "total_value": int(85000 * timeframe_multiplier),
            "pnl": int(6200 * timeframe_multiplier),
            "success_rate": 64.8 * timeframe_multiplier,
            "avg_return": 8.5 * timeframe_multiplier,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        return jsonify(base_kpis)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.route('/positions')
def get_positions():
    """Get all commodities positions"""
    try:
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fixtures')
        commodities_file = os.path.join(fixtures_dir, 'commodities_sample.json')

        if os.path.exists(commodities_file):
            with open(commodities_file, 'r') as f:
                data = json.load(f)
        else:
            # Fallback data if fixture doesn't exist
            data = {
                "positions": [
                    {
                        "commodity": "GOLD",
                        "quantity": 100,
                        "price": 2045.50,
                        "market_value": 204550,
                        "pnl": 12500
                    },
                    {
                        "commodity": "CRUDE_OIL",
                        "quantity": 50,
                        "price": 82.45,
                        "market_value": 4122.50,
                        "pnl": -850
                    }
                ]
            }

        return jsonify({
            "positions": data.get('positions', []),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.route('/analytics')
def get_analytics():
    """Get commodities analytics"""
    try:
        analytics = {
            "sector_exposure": {
                "metals": 45.2,
                "energy": 35.8,
                "agriculture": 19.0
            },
            "performance": {
                "total_return": 8.5,
                "volatility": 12.3,
                "correlation_to_equity": 0.25
            },
            "risk_metrics": {
                "var_95": -12000,
                "expected_shortfall": -18000,
                "maximum_drawdown": -22000
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        return jsonify(analytics)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.route('/signals')
def get_signals():
    """Get commodities signals"""
    try:
        timeframe = request.args.get('timeframe', '10D')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        signals = [
            {
                "symbol": "GOLD",
                "signal_type": "momentum",
                "direction": "bullish",
                "strength": 0.78,
                "price": 2045.50,
                "target": 2120.00,
                "stop_loss": 1980.00,
                "confidence": 0.72,
                "timeframe": timeframe,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            },
            {
                "symbol": "CRUDE_OIL",
                "signal_type": "reversal",
                "direction": "bearish",
                "strength": 0.65,
                "price": 82.45,
                "target": 78.00,
                "stop_loss": 85.50,
                "confidence": 0.68,
                "timeframe": timeframe,
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
        ]

        return jsonify({
            "signals": signals,
            "timeframe": timeframe,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.route('/correlations')
def get_correlations():
    """Get commodities correlations"""
    try:
        symbol = request.args.get('symbol', 'GOLD')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        correlations = {
            "symbol": symbol,
            "correlations": {
                "USD_INR": 0.72,
                "NIFTY": -0.25,
                "DXY": 0.68,
                "10Y_YIELD": 0.45
            },
            "timeframe": "90D",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        return jsonify(correlations)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@commodities_bp.route('/api/commodities', methods=['GET'])
def get_commodities():
    """Get commodities data with caching"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        cache_key = 'commodities_data'

        # Try cache first if not forcing refresh
        if not force_refresh:
            cached_data = cache_medium.get(cache_key)
            if cached_data is not None:
                return jsonify(cached_data)

        # Load fresh data
        sample_file = os.path.join('data', 'fixtures', 'commodities_sample.json')
        if os.path.exists(sample_file):
            with open(sample_file, 'r') as f:
                data = json.load(f)

            # Add timestamp
            data['timestamp'] = now_iso()
            data['cached_at'] = now_iso()

            # Cache the result
            cache_medium.set(cache_key, data)
            return jsonify(data)
        else:
            error_data = {
                "error": "Sample data not found",
                "timestamp": now_iso(), 
                "commodities": []
            }
            return jsonify(error_data), 404

    except Exception as e:
        return jsonify({"error": str(e), "timestamp": now_iso()}), 500