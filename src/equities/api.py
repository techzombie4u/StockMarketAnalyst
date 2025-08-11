
from flask import Blueprint, jsonify
from datetime import datetime
import os
import json

equities_bp = Blueprint('equities', __name__)

@equities_bp.route('/positions')
def get_positions():
    """Get all equity positions"""
    try:
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fixtures')
        equities_file = os.path.join(fixtures_dir, 'equities_sample.json')
        
        with open(equities_file, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            "positions": data.get('positions', []),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@equities_bp.route('/analytics')
def get_analytics():
    """Get equity analytics and KPIs"""
    try:
        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fixtures')
        equities_file = os.path.join(fixtures_dir, 'equities_sample.json')
        
        with open(equities_file, 'r') as f:
            data = json.load(f)
        
        positions = data.get('positions', [])
        
        analytics = {
            "portfolio_metrics": {
                "total_value": sum(pos.get('market_value', 0) for pos in positions),
                "total_pnl": sum(pos.get('unrealized_pnl', 0) for pos in positions),
                "position_count": len(positions),
                "avg_position_size": sum(pos.get('market_value', 0) for pos in positions) / len(positions) if positions else 0
            },
            "risk_metrics": {
                "value_at_risk": -15000,
                "beta": 1.2,
                "correlation": 0.85
            },
            "performance": {
                "roi": 12.5,
                "alpha": 2.3,
                "tracking_error": 4.1
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        return jsonify(analytics)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
