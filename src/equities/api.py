from flask import Blueprint, jsonify, request
import json
import os
from ..core.cache import cache_medium, now_iso

equities_bp = Blueprint('equities', __name__)

@equities_bp.route('/list')
def get_equities_list():
    """Get paginated equities list with filters"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 25, type=int)
        sector = request.args.get('sector', '')
        score_min = request.args.get('scoreMin', 0.0, type=float)
        timeframe = request.args.get('timeframe', 'All')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        cache_key = f"equities_list_page_{page}_pageSize_{page_size}_sector_{sector}_scoreMin_{score_min}_timeframe_{timeframe}"

        if not force_refresh:
            cached_data = cache_medium.get(cache_key)
            if cached_data is not None:
                return jsonify(cached_data)

        # Sample equities data
        all_equities = [
            {
                "symbol": "TCS",
                "name": "Tata Consultancy Services",
                "sector": "IT",
                "price": 4275.3,
                "volRegime": "MEDIUM",
                "verdict": "STRONG_BUY",
                "confidence": 0.74,
                "kpis": {"winRate": 0.67, "sharpe": 1.2, "mdd": -0.08},
                "updated": datetime.utcnow().isoformat() + "Z"
            },
            {
                "symbol": "INFY",
                "name": "Infosys Limited",
                "sector": "IT",
                "price": 1825.45,
                "volRegime": "HIGH",
                "verdict": "BUY",
                "confidence": 0.68,
                "kpis": {"winRate": 0.62, "sharpe": 1.1, "mdd": -0.12},
                "updated": datetime.utcnow().isoformat() + "Z"
            },
            {
                "symbol": "RELIANCE",
                "name": "Reliance Industries",
                "sector": "Energy",
                "price": 2890.75,
                "volRegime": "MEDIUM",
                "verdict": "HOLD",
                "confidence": 0.55,
                "kpis": {"winRate": 0.58, "sharpe": 0.9, "mdd": -0.15},
                "updated": datetime.utcnow().isoformat() + "Z"
            },
            {
                "symbol": "HDFCBANK",
                "name": "HDFC Bank Limited",
                "sector": "Banking",
                "price": 1678.20,
                "volRegime": "LOW",
                "verdict": "BUY",
                "confidence": 0.71,
                "kpis": {"winRate": 0.65, "sharpe": 1.3, "mdd": -0.09},
                "updated": datetime.utcnow().isoformat() + "Z"
            }
        ]

        # Apply filters
        filtered_equities = all_equities

        if sector:
            filtered_equities = [eq for eq in filtered_equities if eq['sector'].lower() == sector.lower()]

        if score_min > 0:
            filtered_equities = [eq for eq in filtered_equities if eq['confidence'] >= score_min]

        # Pagination
        total = len(filtered_equities)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = filtered_equities[start_idx:end_idx]

        result = {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": items,
            "timestamp": now_iso()
        }

        cache_medium.set(cache_key, result)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e), "timestamp": now_iso()}), 500

@equities_bp.route('/positions')
def get_positions():
    """Get all equity positions"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        cache_key = 'equities_positions'

        if not force_refresh:
            cached_data = cache_medium.get(cache_key)
            if cached_data is not None:
                return jsonify(cached_data)

        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fixtures')
        equities_file = os.path.join(fixtures_dir, 'equities_sample.json')

        with open(equities_file, 'r') as f:
            data = json.load(f)

        result = {
            "positions": data.get('positions', []),
            "timestamp": now_iso()
        }

        cache_medium.set(cache_key, result)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e), "timestamp": now_iso()}), 500

@equities_bp.route('/kpis')
def get_kpis():
    """Get equities KPIs with timeframe support"""
    try:
        timeframe = request.args.get('timeframe', 'All')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        cache_key = f"equities_kpis_timeframe_{timeframe}"

        if not force_refresh:
            cached_data = cache_medium.get(cache_key)
            if cached_data is not None:
                return jsonify(cached_data)

        # Adjust KPIs based on timeframe
        timeframe_multiplier = {
            'All': 1.0,
            '30D': 0.9,
            '15D': 0.85,
            '10D': 0.8,
            '5D': 0.75,
            '3D': 0.7
        }.get(timeframe, 1.0)

        base_kpis = {
            "total_positions": int(15 * timeframe_multiplier),
            "total_value": int(125000 * timeframe_multiplier),
            "pnl": int(8500 * timeframe_multiplier),
            "win_rate": 68.5 * timeframe_multiplier,
            "sharpe_ratio": 1.25 * timeframe_multiplier,
            "max_drawdown": -0.08,
            "avg_return": 12.5 * timeframe_multiplier,
            "volatility": 15.2
        }

        base_kpis["timestamp"] = now_iso()
        base_kpis["timeframe"] = timeframe

        cache_medium.set(cache_key, base_kpis)

        return jsonify(base_kpis)
    except Exception as e:
        return jsonify({"error": str(e), "timestamp": now_iso()}), 500

@equities_bp.route('/analytics')
def get_analytics():
    """Get equity analytics and KPIs"""
    try:
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'
        cache_key = 'equities_analytics'

        if not force_refresh:
            cached_data = cache_medium.get(cache_key)
            if cached_data is not None:
                return jsonify(cached_data)

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
            "timestamp": now_iso()
        }

        cache_medium.set(cache_key, analytics)

        return jsonify(analytics)

    except Exception as e:
        return jsonify({"error": str(e), "timestamp": now_iso()}), 500