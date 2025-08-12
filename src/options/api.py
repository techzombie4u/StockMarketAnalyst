
from flask import Blueprint, request, jsonify
from src.core.cache import ttl_cache, now_iso
from .engine import options_engine
import logging

logger = logging.getLogger(__name__)
options_bp = Blueprint("options", __name__)
_cache = ttl_cache(ttl_sec=30, namespace="options")

@options_bp.get("/strangle/candidates")
def get_strangle_candidates():
    """Get strangle strategy candidates with complete metrics"""
    try:
        # Sample candidates with real calculations
        symbols = ['TCS', 'RELIANCE', 'HDFCBANK', 'INFY', 'ICICIBANK']
        candidates = []
        
        for symbol in symbols:
            # Mock spot prices (in real implementation, fetch from market data)
            spot_prices = {'TCS': 4250, 'RELIANCE': 1390, 'HDFCBANK': 1995, 'INFY': 1800, 'ICICIBANK': 1205}
            spot = spot_prices.get(symbol, 1000)
            
            # Calculate strategy metrics
            call_strike = round(spot * 1.05 / 50) * 50  # 5% OTM, rounded to nearest 50
            put_strike = round(spot * 0.95 / 50) * 50   # 5% OTM, rounded to nearest 50
            
            metrics = options_engine.calculate_strangle_metrics(
                symbol=symbol,
                spot=spot,
                call_strike=call_strike,
                put_strike=put_strike,
                days_to_expiry=30,
                implied_vol=0.25
            )
            
            candidate = {
                "symbol": metrics['symbol'],
                "underlying_price": metrics['spot_price'],
                "call_strike": metrics['call_strike'],
                "put_strike": metrics['put_strike'],
                "call_premium": metrics['call_price'],
                "put_premium": metrics['put_price'],
                "total_premium": metrics['credit'],
                "max_profit": metrics['credit'],
                "probability_profit": metrics['probability_profit'],
                "dte": metrics['days_to_expiry'],
                "ai_verdict_normalized": "BUY" if metrics['roi_pct'] > 15 else "HOLD",
                "roi_pct": metrics['roi_pct'],
                "margin": metrics['margin'],
                "breakeven_low": metrics['breakeven_low'],
                "breakeven_high": metrics['breakeven_high'],
                "greeks": metrics['greeks'],
                "payoff": metrics['payoff']
            }
            candidates.append(candidate)
        
        return jsonify({
            "candidates": candidates,
            "metadata": {
                "total_candidates": len(candidates),
                "calculation_method": "black_scholes",
                "risk_free_rate": options_engine.risk_free_rate
            },
            "last_updated_utc": now_iso()
        })
        
    except Exception as e:
        logger.error(f"Error getting strangle candidates: {e}")
        return jsonify({"error": "Failed to calculate candidates"}), 500

@options_bp.post("/strangle/plan")
def create_strangle_plan():
    """Create a new strangle plan and save as position"""
    try:
        data = request.get_json() or {}
        
        symbol = data.get('symbol', 'TCS')
        call_strike = float(data.get('call_strike', 4300))
        put_strike = float(data.get('put_strike', 3900))
        quantity = int(data.get('quantity', 1))
        days_to_expiry = int(data.get('days_to_expiry', 30))
        
        # Mock spot price
        spot_prices = {'TCS': 4250, 'RELIANCE': 1390, 'HDFCBANK': 1995}
        spot = spot_prices.get(symbol, 4250)
        
        # Calculate metrics
        metrics = options_engine.calculate_strangle_metrics(
            symbol=symbol,
            spot=spot,
            call_strike=call_strike,
            put_strike=put_strike,
            days_to_expiry=days_to_expiry
        )
        
        # Save as position
        position_data = {
            **metrics,
            'strategy_type': 'short_strangle',
            'quantity': quantity
        }
        
        position_id = options_engine.save_position(position_data)
        
        return jsonify({
            "success": True,
            "plan_id": position_id,
            "estimated_premium": metrics['credit'],
            "max_profit": metrics['credit'],
            "margin_required": metrics['margin'],
            "roi_pct": metrics['roi_pct'],
            "breakevens": [metrics['breakeven_low'], metrics['breakeven_high']],
            "greeks": metrics['greeks'],
            "payoff": metrics['payoff']
        })
        
    except Exception as e:
        logger.error(f"Error creating strangle plan: {e}")
        return jsonify({"error": "Failed to create plan"}), 500

@options_bp.get("/positions")
def get_positions():
    """Get all positions with complete data"""
    try:
        status = request.args.get("status", "all").lower()
        positions = options_engine.get_positions(status)
        
        # Format for API response
        formatted_positions = []
        for pos in positions:
            formatted_pos = {
                "position_id": pos.get('position_id'),
                "symbol": pos.get('symbol'),
                "strategy_type": pos.get('strategy_type'),
                "entry_date": pos.get('entry_date'),
                "status": pos.get('status'),
                "pnl": pos.get('pnl', 0.0),
                "current_value": pos.get('current_value', 0.0),
                "roi_pct": pos.get('roi_pct', 0.0),
                "margin": pos.get('margin', 0.0),
                "payoff": pos.get('payoff', {'x': [], 'y': []}),
                "greeks": pos.get('greeks', {}),
                "call_strike": pos.get('call_strike', 0.0),
                "put_strike": pos.get('put_strike', 0.0),
                "credit": pos.get('credit', 0.0),
                "breakeven_low": pos.get('breakeven_low', 0.0),
                "breakeven_high": pos.get('breakeven_high', 0.0)
            }
            formatted_positions.append(formatted_pos)
        
        return jsonify({
            "positions": formatted_positions,
            "summary": {
                "total_positions": len(formatted_positions),
                "open_positions": len([p for p in positions if p.get('status') == 'open']),
                "total_pnl": sum(p.get('pnl', 0) for p in positions),
                "total_margin": sum(p.get('margin', 0) for p in positions)
            },
            "last_updated_utc": now_iso()
        })
        
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({"error": "Failed to get positions"}), 500

@options_bp.get("/positions/<pid>")
def get_position_detail(pid):
    """Get detailed position information"""
    try:
        positions = options_engine.get_positions()
        position = next((p for p in positions if p.get('position_id') == pid), None)
        
        if not position:
            return jsonify({"error": "Position not found"}), 404
        
        return jsonify(position)
        
    except Exception as e:
        logger.error(f"Error getting position detail: {e}")
        return jsonify({"error": "Failed to get position"}), 500

@options_bp.post("/positions/<pid>/update")
def update_position(pid):
    """Update position with current market data"""
    try:
        data = request.get_json() or {}
        current_spot = float(data.get('current_spot', 0))
        
        if current_spot <= 0:
            return jsonify({"error": "Invalid spot price"}), 400
        
        success = options_engine.update_position_pnl(pid, current_spot)
        
        if success:
            return jsonify({"success": True, "message": "Position updated"})
        else:
            return jsonify({"error": "Failed to update position"}), 500
            
    except Exception as e:
        logger.error(f"Error updating position: {e}")
        return jsonify({"error": "Failed to update position"}), 500

@options_bp.get("/kpis")
def get_kpis():
    """Get options KPIs and summary metrics"""
    try:
        positions = options_engine.get_positions()
        open_positions = [p for p in positions if p.get('status') == 'open']
        
        total_margin = sum(p.get('margin', 0) for p in open_positions)
        total_credit = sum(p.get('credit', 0) for p in open_positions)
        avg_roi = (total_credit / total_margin * 100) if total_margin > 0 else 0
        
        # Calculate average PoP (simplified)
        avg_pop = sum(p.get('probability_profit', 0.5) for p in open_positions) / len(open_positions) if open_positions else 0.5
        
        return jsonify({
            "expectedRoi": round(avg_roi, 2),
            "pop": round(avg_pop, 3),
            "totalMargin": round(total_margin, 2),
            "totalCredit": round(total_credit, 2),
            "activePositions": len(open_positions),
            "totalPnl": round(sum(p.get('pnl', 0) for p in positions), 2)
        })
        
    except Exception as e:
        logger.error(f"Error getting KPIs: {e}")
        return jsonify({"error": "Failed to get KPIs"}), 500

@options_bp.get("/strategies")
def get_strategies():
    return jsonify({"items": options_engine.get_positions()})

@options_bp.get("/analytics")
def get_analytics():
  return jsonify({"totalPremium": 125000, "totalPnL": 15000, "successRate": 0.72})

@options_bp.get("/calculators")
def get_calculators():
  return jsonify({"blackScholes": "available", "greeks": "available", "impliedVol": "available"})
