
from flask import Blueprint, jsonify, request

equities_bp = Blueprint('equities', __name__)

@equities_bp.route('/list')
def list_equities():
    """List equity items with filtering"""
    try:
        # Get filter parameters
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        sector = request.args.get('sector')
        limit = request.args.get('limit', 50, type=int)
        
        # Mock equity data
        equity_items = [
            {
                "symbol": "TCS",
                "name": "Tata Consultancy Services",
                "price": 3950.0,
                "change": 2.3,
                "change_percent": 0.58,
                "sector": "IT",
                "market_cap": 1500000,
                "volume": 125000
            },
            {
                "symbol": "RELIANCE",
                "name": "Reliance Industries",
                "price": 2450.0,
                "change": -15.2,
                "change_percent": -0.62,
                "sector": "Energy",
                "market_cap": 1650000,
                "volume": 225000
            },
            {
                "symbol": "HDFCBANK",
                "name": "HDFC Bank",
                "price": 1680.0,
                "change": 8.5,
                "change_percent": 0.51,
                "sector": "Banking",
                "market_cap": 1280000,
                "volume": 185000
            }
        ]
        
        # Apply filters
        if min_price:
            equity_items = [item for item in equity_items if item['price'] >= min_price]
        if max_price:
            equity_items = [item for item in equity_items if item['price'] <= max_price]
        if sector:
            equity_items = [item for item in equity_items if item['sector'].lower() == sector.lower()]
        
        # Apply limit
        equity_items = equity_items[:limit]
        
        return jsonify({
            "items": equity_items,
            "total": len(equity_items),
            "filters_applied": {
                "min_price": min_price,
                "max_price": max_price,
                "sector": sector,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@equities_bp.route('/kpis')
def equity_kpis():
    """Get equity KPI metrics"""
    try:
        timeframe = request.args.get('timeframe', '10D')
        
        kpi_data = {
            "timeframes": {
                timeframe: {
                    "total_value": 450000,
                    "day_change": 2350,
                    "total_return": 15.6,
                    "active_positions": 8,
                    "winners": 5,
                    "losers": 3
                }
            },
            "generation_time": "2025-01-12T06:00:00Z"
        }
        
        return jsonify(kpi_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
