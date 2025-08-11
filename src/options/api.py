from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime
import uuid
from src.core.cache import TTLCache
from src.core.guardrails import check_feature_enabled, get_degraded_status

options_bp = Blueprint('options', __name__)

@options_bp.route('/kpis')
def get_kpis():
    """Get options KPIs"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        return jsonify({
            "total_strategies": 8,
            "total_premium": 45000,
            "pnl": 12500,
            "success_rate": 72.3,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/positions')
def get_positions():
    """Get all options positions"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        fixtures_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'fixtures')
        options_file = os.path.join(fixtures_dir, 'options_sample.json')

        with open(options_file, 'r') as f:
            data = json.load(f)

        return jsonify({
            "positions": data.get('positions', []),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/strategies')
def get_strategies():
    """Get options strategies and analytics"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        strategies = [
            {
                "name": "Bull Call Spread",
                "symbol": "NIFTY",
                "expiry": "2024-02-29",
                "pnl": 2500,
                "max_profit": 5000,
                "max_loss": -2000,
                "probability": 68.5
            },
            {
                "name": "Iron Condor",
                "symbol": "BANKNIFTY",
                "expiry": "2024-02-22",
                "pnl": -800,
                "max_profit": 3000,
                "max_loss": -7000,
                "probability": 45.2
            }
        ]

        return jsonify({
            "strategies": strategies,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/analytics')
def get_analytics():
    """Get options analytics"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        analytics = {
            "greeks_summary": {
                "total_delta": 125.6,
                "total_gamma": 45.2,
                "total_theta": -23.8,
                "total_vega": 156.3
            },
            "volatility_metrics": {
                "implied_vol": 18.5,
                "historical_vol": 16.2,
                "vol_skew": 2.3
            },
            "payoff_analysis": {
                "max_profit": 25000,
                "max_loss": -15000,
                "breakeven_points": [18500, 19200]
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        return jsonify(analytics)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/calculators')
def get_calculators():
    """Get options pricing calculators"""
    # Check degraded mode
    degraded = get_degraded_status()
    if degraded['degraded']:
        return jsonify({
            'success': False,
            'degraded': True,
            'reason': degraded['reason'],
            'message': 'Service temporarily degraded due to performance constraints'
        }), 503
    return jsonify({
        "black_scholes": {
            "price": 125.50,
            "delta": 0.65,
            "gamma": 0.025,
            "theta": -0.15,
            "vega": 0.35
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })

@options_bp.route('/strangle/candidates')
def get_strangle_candidates():
    """Get short strangle candidates"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        underlying = request.args.get('underlying', 'TCS')
        expiry = request.args.get('expiry', '2024-02-29')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        candidates = [
            {
                "underlying": underlying,
                "expiry": expiry,
                "call_strike": 4400,
                "put_strike": 4200,
                "call_premium": 85.5,
                "put_premium": 78.2,
                "total_credit": 163.7,
                "margin_required": 45000,
                "roi": 0.364,
                "breakeven_upper": 4563.7,
                "breakeven_lower": 4036.3,
                "pop": 0.68,
                "max_profit": 16370,
                "max_loss": -28630,
                "dte": 25,
                "iv_rank": 45.2
            },
            {
                "underlying": underlying,
                "expiry": expiry,
                "call_strike": 4350,
                "put_strike": 4150,
                "call_premium": 95.8,
                "put_premium": 88.9,
                "total_credit": 184.7,
                "margin_required": 42000,
                "roi": 0.44,
                "breakeven_upper": 4534.7,
                "breakeven_lower": 4065.3,
                "pop": 0.64,
                "max_profit": 18470,
                "max_loss": -21530,
                "dte": 25,
                "iv_rank": 48.7
            }
        ]

        return jsonify({
            "underlying": underlying,
            "expiry": expiry,
            "candidates": candidates,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/strangle/plan', methods=['POST'])
def create_strangle_plan():
    """Create short strangle execution plan"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        data = request.get_json()

        plan_id = str(uuid.uuid4())[:8]

        plan = {
            "plan_id": plan_id,
            "underlying": data.get('underlying'),
            "call_strike": data.get('strikes', {}).get('call'),
            "put_strike": data.get('strikes', {}).get('put'),
            "expiry": data.get('expiry'),
            "sl_rules": data.get('sl_rules', {}),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "estimated_credit": data.get('estimated_credit', 0),
            "margin_required": data.get('margin_required', 0)
        }

        # In real implementation, save to database

        return jsonify({
            "success": True,
            "plan_id": plan_id,
            "plan": plan
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/positions')
def get_positions_list():
    """Get options positions with status filter"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        status = request.args.get('status', 'all')
        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        positions = [
            {
                "id": "pos_001",
                "underlying": "TCS",
                "strategy": "short_strangle",
                "call_strike": 4400,
                "put_strike": 4200,
                "expiry": "2024-02-29",
                "status": "open",
                "entry_credit": 163.7,
                "current_value": 145.2,
                "pnl": 1850,
                "margin_used": 45000,
                "roi": 0.041,
                "dte": 15,
                "breakevens": [4036.3, 4563.7],
                "pop": 0.72
            },
            {
                "id": "pos_002",
                "underlying": "INFY",
                "strategy": "short_strangle",
                "call_strike": 1900,
                "put_strike": 1750,
                "expiry": "2024-02-22",
                "status": "closed",
                "entry_credit": 142.5,
                "exit_value": 45.8,
                "pnl": 9670,
                "margin_used": 38000,
                "roi": 0.255,
                "dte": 0,
                "breakevens": [1607.5, 2042.5],
                "pop": 0.85
            }
        ]

        if status != 'all':
            positions = [p for p in positions if p['status'] == status]

        return jsonify({
            "positions": positions,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@options_bp.route('/positions/<position_id>')
def get_position_detail(position_id):
    """Get detailed options position"""
    try:
        # Check degraded mode
        degraded = get_degraded_status()
        if degraded['degraded']:
            return jsonify({
                'success': False,
                'degraded': True,
                'reason': degraded['reason'],
                'message': 'Service temporarily degraded due to performance constraints'
            }), 503

        force_refresh = request.args.get('forceRefresh', 'false').lower() == 'true'

        # Sample detailed position
        position = {
            "id": position_id,
            "underlying": "TCS",
            "strategy": "short_strangle",
            "call_strike": 4400,
            "put_strike": 4200,
            "expiry": "2024-02-29",
            "status": "open",
            "entry_credit": 163.7,
            "current_value": 145.2,
            "pnl": 1850,
            "margin_used": 45000,
            "roi": 0.041,
            "dte": 15,
            "breakevens": [4036.3, 4563.7],
            "pop": 0.72,
            "greeks": {
                "delta": -0.05,
                "gamma": 0.08,
                "theta": 2.4,
                "vega": -15.6
            },
            "payoff": {
                "x": [3800, 3900, 4000, 4100, 4200, 4300, 4400, 4500, 4600, 4700, 4800],
                "y": [-28630, -18630, -8630, 1370, 11370, 16370, 16370, 16370, 6370, -3630, -13630]
            }
        }

        return jsonify(position)

    except Exception as e:
        return jsonify({"error": str(e)}), 500