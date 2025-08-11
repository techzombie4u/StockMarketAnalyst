
from flask import Blueprint, jsonify
from datetime import datetime
import os
import json

commodities_bp = Blueprint('commodities', __name__)

@commodities_bp.route('/kpis')
def get_kpis():
    """Get commodities KPIs"""
    try:
        return jsonify({
            "total_contracts": 25,
            "total_value": 85000,
            "pnl": 6200,
            "success_rate": 64.8,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
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
