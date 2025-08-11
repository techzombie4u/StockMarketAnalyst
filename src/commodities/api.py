
from flask import Blueprint, jsonify, request
from datetime import datetime
import os
import json

commodities_bp = Blueprint('commodities', __name__)

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
        
        with open(commodities_file, 'r') as f:
            data = json.load(f)
        
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
