
from flask import Blueprint, jsonify, request
import time

fusion_bp = Blueprint('fusion', __name__)

@fusion_bp.route('/dashboard')
def dashboard():
    """Main dashboard endpoint with KPIs and signals"""
    try:
        # Get timeframe parameter
        timeframe = request.args.get('timeframe', '10D')
        
        # Mock data for now - replace with actual data service
        dashboard_data = {
            "timeframes": {
                "1D": {"active": timeframe == "1D"},
                "5D": {"active": timeframe == "5D"},
                "10D": {"active": timeframe == "10D"},
                "30D": {"active": timeframe == "30D"}
            },
            "pinned_summary": {
                "total_pinned": 5,
                "alerts": 2,
                "watchlist": 8
            },
            "top_signals": [
                {
                    "symbol": "TCS",
                    "signal": "BUY",
                    "confidence": 0.85,
                    "price": 3950.0,
                    "target": 4200.0
                },
                {
                    "symbol": "RELIANCE",
                    "signal": "HOLD",
                    "confidence": 0.72,
                    "price": 2450.0,
                    "target": 2600.0
                }
            ],
            "kpis": {
                "portfolio_value": 125000,
                "day_pnl": 2350,
                "total_pnl": 15600,
                "win_rate": 68.5,
                "active_positions": 12,
                "alerts": 3
            },
            "generation_time_ms": 45
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
