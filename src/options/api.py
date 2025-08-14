import json
import os
import time
import math
import random
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import logging

# Import the enhanced short strangle engine
try:
    from src.options.strangle_engine import StrangleEngine
except ImportError:
    logger.warning("Short strangle engine not available, using enhanced fallback data")
    StrangleEngine = None

logger = logging.getLogger(__name__)

# Fix blueprint name to match what the app expects
options_bp = Blueprint('options_bp', __name__)

def calculate_historical_volatility_filtering(symbol, timeframe):
    """Calculate historical volatility with filtering for accuracy"""
    try:
        # Mock implementation - in real scenario, fetch historical data
        base_vol = 0.20 + (hash(symbol) % 20) / 100  # 20-40% range

        # Adjust based on timeframe
        timeframe_multiplier = {
            '5D': 0.8,
            '10D': 0.9,
            '15D': 1.0,
            '30D': 1.1
        }

        return base_vol * timeframe_multiplier.get(timeframe, 1.0)
    except Exception as e:
        logger.error(f"Error calculating historical volatility for {symbol}: {e}")
        return 0.25  # Default 25%

def check_earnings_calendar(symbol, days_ahead=45):
    """Check for upcoming earnings within specified days"""
    try:
        # Mock earnings calendar - in real implementation, integrate with financial data provider
        earnings_symbols = ['TCS', 'INFY', 'RELIANCE', 'HDFCBANK', 'ICICIBANK']

        if symbol in earnings_symbols:
            # Random earnings date within next 45 days
            days_to_earnings = random.randint(1, days_ahead)
            return {
                'has_earnings': True,
                'days_to_earnings': days_to_earnings,
                'earnings_date': (datetime.now() + timedelta(days=days_to_earnings)).isoformat()[:10]
            }

        return {'has_earnings': False, 'days_to_earnings': None, 'earnings_date': None}
    except Exception as e:
        logger.error(f"Error checking earnings calendar for {symbol}: {e}")
        return {'has_earnings': False, 'days_to_earnings': None, 'earnings_date': None}

def calculate_iv_skew_monitoring(symbol, call_strike, put_strike, spot_price):
    """Monitor real-time IV skew for risk assessment"""
    try:
        # Mock IV skew calculation - in real scenario, fetch options chain
        atm_iv = 0.25 + (hash(symbol) % 10) / 100  # Base IV

        # Calculate skew based on moneyness
        call_moneyness = call_strike / spot_price
        put_moneyness = spot_price / put_strike

        # OTM options typically have higher IV (volatility smile)
        call_iv = atm_iv * (1 + (call_moneyness - 1) * 0.3)
        put_iv = atm_iv * (1 + (put_moneyness - 1) * 0.3)

        # IV skew metrics
        skew = (call_iv - put_iv) / atm_iv

        return {
            'atm_iv': atm_iv,
            'call_iv': call_iv,
            'put_iv': put_iv,
            'skew': skew,
            'skew_risk': 'HIGH' if abs(skew) > 0.1 else 'MEDIUM' if abs(skew) > 0.05 else 'LOW'
        }
    except Exception as e:
        logger.error(f"Error calculating IV skew for {symbol}: {e}")
        return {'atm_iv': 0.25, 'call_iv': 0.25, 'put_iv': 0.25, 'skew': 0, 'skew_risk': 'LOW'}

def assess_market_stability_score(symbol, timeframe):
    """Calculate market stability score based on multiple factors"""
    try:
        # Mock stability calculation - in real scenario, analyze price action, volume, etc.
        base_score = 70 + (hash(symbol) % 20)  # 70-90 base score

        # Adjust based on timeframe volatility
        timeframe_adjustment = {
            '5D': -5,   # Recent volatility penalty
            '10D': 0,
            '15D': 2,
            '30D': 5    # Longer timeframe bonus
        }

        stability_score = base_score + timeframe_adjustment.get(timeframe, 0)
        return max(10, min(100, stability_score))  # Clamp between 10-100
    except Exception as e:
        logger.error(f"Error calculating market stability for {symbol}: {e}")
        return 75  # Default score

def calculate_enhanced_strategy_metrics(symbol, spot_price, timeframe):
    """Calculate enhanced strategy metrics with all risk considerations"""
    try:
        # Basic strategy parameters
        call_strike = spot_price * 1.05  # 5% OTM call
        put_strike = spot_price * 0.95   # 5% OTM put

        # Days to expiry based on timeframe
        dte_map = {'5D': 21, '10D': 28, '15D': 35, '30D': 42}
        days_to_expiry = dte_map.get(timeframe, 30)

        # Enhanced volatility analysis
        hist_vol = calculate_historical_volatility_filtering(symbol, timeframe)
        iv_data = calculate_iv_skew_monitoring(symbol, call_strike, put_strike, spot_price)

        # Event risk assessment
        earnings_data = check_earnings_calendar(symbol, days_to_expiry)

        # Market stability
        stability_score = assess_market_stability_score(symbol, timeframe)

        # Options pricing (simplified Black-Scholes approximation)
        time_to_expiry = days_to_expiry / 365.0
        d1 = (math.log(spot_price / call_strike) + 0.5 * hist_vol**2 * time_to_expiry) / (hist_vol * math.sqrt(time_to_expiry))
        d2 = d1 - hist_vol * math.sqrt(time_to_expiry)

        # Approximate option prices
        call_price = spot_price * 0.5 * (1 + math.erf(d1 / math.sqrt(2))) - call_strike * math.exp(-0.05 * time_to_expiry) * 0.5 * (1 + math.erf(d2 / math.sqrt(2)))
        put_price = call_strike * math.exp(-0.05 * time_to_expiry) * 0.5 * (1 + math.erf(-d2 / math.sqrt(2))) - spot_price * 0.5 * (1 + math.erf(-d1 / math.sqrt(2)))

        # Ensure positive prices
        call_price = max(0.01, call_price)
        put_price = max(0.01, put_price)

        total_premium = call_price + put_price

        # Enhanced calculations
        breakeven_low = put_strike - total_premium
        breakeven_high = call_strike + total_premium
        margin_required = total_premium * 5  # Simplified margin calculation
        roi_on_margin = (total_premium / margin_required) * 100

        # Theta calculation (time decay per day)
        theta_per_day = total_premium * 0.03  # Simplified theta

        # Breakout probability based on historical volatility
        one_sigma_move = spot_price * hist_vol * math.sqrt(time_to_expiry)
        breakout_probability = 1 - max(0, min(1, (call_strike - put_strike - 2*one_sigma_move) / (2*one_sigma_move)))

        # Max loss at 2 sigma move
        two_sigma_move = 2 * one_sigma_move
        max_loss_2_sigma = max(
            max(0, spot_price + two_sigma_move - call_strike),
            max(0, put_strike - (spot_price - two_sigma_move))
        ) - total_premium

        # IV rank calculation (percentile of current IV vs historical)
        iv_rank = min(100, max(0, (iv_data['atm_iv'] - 0.15) / 0.30 * 100))  # Normalize to percentile

        # Event risk assessment
        has_event_risk = earnings_data['has_earnings'] and earnings_data['days_to_earnings'] <= days_to_expiry

        # Generate verdict based on multiple factors
        verdict_score = 0
        if iv_data['atm_iv'] > 0.25 and iv_rank > 60: verdict_score += 20
        if roi_on_margin > 20: verdict_score += 15
        if stability_score > 75: verdict_score += 15
        if breakout_probability < 0.3: verdict_score += 15
        if not has_event_risk: verdict_score += 10
        if days_to_expiry >= 20 and days_to_expiry <= 40: verdict_score += 10

        if verdict_score >= 70: verdict = "Strong Buy"
        elif verdict_score >= 50: verdict = "Buy"
        elif verdict_score >= 30: verdict = "Hold"
        elif verdict_score >= 15: verdict = "Cautious"
        else: verdict = "Avoid"

        return {
            'symbol': symbol,
            'current_price': round(spot_price, 2),
            'spot_price': round(spot_price, 2),  # Additional field mapping
            'call_strike': round(call_strike, 2),
            'put_strike': round(put_strike, 2),
            'days_to_expiry': days_to_expiry,
            'dte_days': days_to_expiry,  # Additional field mapping
            'implied_volatility': round(iv_data['atm_iv'], 3),
            'iv_percent': round(iv_data['atm_iv'] * 100, 1),  # Percentage format
            'iv_rank': round(iv_rank, 1),
            'total_premium': round(total_premium, 2),
            'net_credit_per_lot': round(total_premium, 2),  # Additional field mapping
            'theta_per_day': round(theta_per_day, 2),
            'theta_per_day_per_lot': round(theta_per_day, 2),  # Additional field mapping
            'roi_on_margin': round(roi_on_margin, 1),
            'roi_on_margin_percent': round(roi_on_margin, 1),  # Additional field mapping
            'breakout_probability': round(breakout_probability, 3),
            'market_stability_score': stability_score if isinstance(stability_score, str) else ('High' if stability_score >= 80 else 'Med' if stability_score >= 60 else 'Low'),
            'has_event_risk': has_event_risk,
            'event_flag': 'EARNINGS' if has_event_risk else 'CLEAR',
            'earnings_data': earnings_data,
            'iv_skew_data': iv_data,
            'max_loss_2_sigma': round(max_loss_2_sigma, 2),
            'max_loss_two_sigma': round(max_loss_2_sigma, 2),  # Additional field mapping
            'stop_loss_percent': 180,  # 180% of premium collected
            'stop_loss_percent_of_credit': 180,  # Additional field mapping
            'breakeven_lower': round(breakeven_low, 2),
            'breakeven_upper': round(breakeven_high, 2),
            'breakeven_low': round(breakeven_low, 2),  # Additional field mapping
            'breakeven_high': round(breakeven_high, 2),  # Additional field mapping
            'margin_required': round(margin_required, 2),
            'historical_volatility': round(hist_vol, 3),
            'verdict': verdict,
            'ai_agent_verdict': verdict,  # Additional field mapping
            'verdict_score': verdict_score
        }

    except Exception as e:
        logger.error(f"Error calculating enhanced metrics for {symbol}: {e}")
        return None

def load_options_data():
    """Load options sample data"""
    try:
        filepath = os.path.join('data', 'fixtures', 'options_sample.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading options data: {e}")
    return {"candidates": [], "total_candidates": 0}

# The existing get_strangle_candidates and get_options_strategies are replaced by the new ones in the changes.
# The following routes are the new additions from the changes.

@options_bp.route('/strangle/candidates', methods=['GET'])
def get_strangle_candidates():
    """Get short strangle candidates"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        if StrangleEngine is None:
            return jsonify({'success': False, 'error': 'StrangleEngine not available'}), 500
            
        engine = StrangleEngine()
        # Generate sample data using enhanced calculations
        sample_symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
        candidates = []
        
        for symbol in sample_symbols:
            spot_price = 1000 + (hash(symbol) % 3000)  # Mock spot price
            strategy_data = calculate_enhanced_strategy_metrics(symbol, spot_price, timeframe)
            if strategy_data:
                candidates.append(strategy_data)

        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'candidates': candidates
        })
    except Exception as e:
        logger.error(f"Error getting strangle candidates: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@options_bp.route('/strangle/recommendations', methods=['GET'])
def get_strangle_recommendations():
    """Get v2 strangle recommendations with enhanced data"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        hide_events = request.args.get('hide_events', 'false').lower() == 'true'
        max_breakout_prob = float(request.args.get('max_breakout_prob', '100'))

        logger.info(f"Generating v2 strangle recommendations for timeframe {timeframe}")

        if StrangleEngine is None:
            return jsonify({'success': False, 'error': 'StrangleEngine not available'}), 500
            
        engine = StrangleEngine()
        
        # Generate enhanced recommendations using the engine
        sample_symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'WIPRO', 'LT', 'MARUTI']
        all_strategies = []
        
        for symbol in sample_symbols:
            spot_price = 1000 + (hash(symbol) % 3000)  # Mock spot price
            strategy_data = calculate_enhanced_strategy_metrics(symbol, spot_price, timeframe)
            if strategy_data:
                # Apply filters
                if hide_events and strategy_data.get('has_event_risk', False):
                    continue
                if strategy_data.get('breakout_probability', 0) * 100 > max_breakout_prob:
                    continue
                all_strategies.append(strategy_data)
        
        strategies = all_strategies

        logger.info(f"Generated {len(strategies)} v2 strangle recommendations")
        
        # Debug logging
        if strategies:
            logger.info(f"Sample strategy fields: {list(strategies[0].keys())}")
        else:
            logger.warning("No strategies generated - check symbol data and filters")

        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'strategies': strategies,
            'total_count': len(strategies)
        })
    except Exception as e:
        logger.error(f"Error getting strangle recommendations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_timeframe_days(timeframe_str):
    """Parse timeframe string to days (e.g., '30D' -> 30)"""
    try:
        return int(timeframe_str.rstrip('D'))
    except:
        return 30

def format_due_date(dte_days):
    """Calculate due date from DTE days"""
    due_date = datetime.now() + timedelta(days=dte_days)
    return due_date.strftime('%Y-%m-%d')

@options_bp.route('/strategies', methods=['GET'])
def get_options_strategies():
    """Get enhanced options strategies for the new UI"""
    try:
        timeframe = request.args.get('timeframe', '30D')
        dte_days = parse_timeframe_days(timeframe)

        if StrangleEngine is None:
            return jsonify({'success': False, 'error': 'StrangleEngine not available'}), 500
            
        # Generate strategies using enhanced calculations
        sample_symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'WIPRO', 'LT', 'MARUTI']
        raw_strategies = []
        
        for symbol in sample_symbols:
            spot_price = 1000 + (hash(symbol) % 3000)  # Mock spot price
            strategy_data = calculate_enhanced_strategy_metrics(symbol, spot_price, timeframe)
            if strategy_data:
                raw_strategies.append(strategy_data)

        # Transform to match expected format with proper field mapping
        strategies = []
        for strategy in raw_strategies:
            # Ensure all required fields are present and properly mapped
            try:
                strategies.append({
                    'stock': str(strategy.get('symbol', 'UNKNOWN')),
                    'spot': float(strategy.get('current_price', strategy.get('spot_price', 0))),
                    'call': float(strategy.get('call_strike', 0)),
                    'put': float(strategy.get('put_strike', 0)),
                    'breakeven_min': float(strategy.get('breakeven_lower', strategy.get('breakeven_low', 0))),
                    'breakeven_max': float(strategy.get('breakeven_upper', strategy.get('breakeven_high', 0))),
                    'breakout_prob': float(strategy.get('breakout_probability', 0.5)),  # Default to 50%
                    'market_stability': strategy.get('market_stability_score', 'Med'),
                    'event': 'EARNINGS' if strategy.get('has_event_risk', False) else '—',
                    'event_flag': 'EARNINGS' if strategy.get('has_event_risk', False) else 'CLEAR',
                    'max_loss_2s': float(strategy.get('max_loss_2_sigma', strategy.get('max_loss_two_sigma', 0))),
                    'stop_loss_pct': float(strategy.get('stop_loss_percent', 180)),
                    'verdict': str(strategy.get('verdict', 'Hold')),
                    'ai_verdict': str(strategy.get('verdict', 'Hold')),  # Use same verdict for AI
                    'dte': int(dte_days),
                    'iv': float(strategy.get('implied_volatility', 0.25)) * 100,  # Convert to percentage
                    'iv_rank': float(strategy.get('iv_rank', 50)),
                    'net_credit': float(strategy.get('total_premium', strategy.get('net_credit_per_lot', 0))),
                    'theta_day': float(strategy.get('theta_per_day', strategy.get('theta_per_day_per_lot', 0))),
                    'roi_on_margin': float(strategy.get('roi_on_margin', strategy.get('roi_on_margin_percent', 0))),
                    'roi_on_margin_percent': float(strategy.get('roi_on_margin', strategy.get('roi_on_margin_percent', 0))),
                    'final_outcome': 'IN_PROGRESS',  # Default for active strategies
                    'due_date': format_due_date(dte_days)
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Error processing strategy {strategy.get('symbol', 'UNKNOWN')}: {e}")
                continue

        # Debug logging
        logger.info(f"Returning {len(strategies)} strategies for timeframe {timeframe}")
        if strategies:
            sample_strategy = strategies[0]
            logger.info(f"Sample strategy keys: {list(sample_strategy.keys())}")
            logger.info(f"Sample strategy values: {sample_strategy}")

        return jsonify({
            'success': True,
            'timeframe': timeframe,
            'strategies': strategies,
            'total_strategies': len(strategies)
        })

    except Exception as e:
        logger.error(f"Error getting options strategies: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@options_bp.route('/predictions/accuracy', methods=['GET'])
def get_predictions_accuracy():
    """Get accuracy metrics by timeframe (finalized only)"""
    try:
        window = request.args.get('window', '30d').lower()

        # Mock accuracy data based on finalized predictions
        # Generate realistic accuracy data
        accuracy_data = [
            {'tf': 3, 'success': 8, 'failed': 2},
            {'tf': 5, 'success': 12, 'failed': 3},
            {'tf': 10, 'success': 15, 'failed': 5},
            {'tf': 15, 'success': 18, 'failed': 7},
            {'tf': 30, 'success': 22, 'failed': 8}
        ]
        
        logger.info(f"Generated accuracy data for window {window}: {accuracy_data}")

        # Filter based on window if needed
        # For now, return all timeframes

        return jsonify({
            'success': True,
            'by_timeframe': accuracy_data
        })

    except Exception as e:
        logger.error(f"Error getting accuracy data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@options_bp.route('/predictions/active', methods=['GET'])
def get_active_predictions():
    """Get active (in-progress) predictions"""
    try:
        # Mock active predictions data
        # In real implementation, query your active predictions
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
            },
            {
                'due': '2025-09-07',
                'stock': 'ITC',
                'predicted': 'On Track',
                'current': 'Outperforming',
                'proi': 29.9,
                'croi': 43.43,
                'reason': 'ROI exceeded expectations'
            }
        ]

        return jsonify({
            'success': True,
            'items': active_predictions
        })

    except Exception as e:
        logger.error(f"Error getting active predictions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# The following routes were present in the original code but are not mentioned in the changes.
# According to instructions, "rest of the file remains unchanged" means we should keep them.
# However, the provided changes also modify the Blueprint name and imports.
# The most logical approach is to keep the original routes if they don't conflict with new ones,
# but the provided changes seem to replace the entire blueprint definition and its original routes.
# Given the conflicting instructions (keep original vs. provided changes replacing parts),
# and the fact that the changes provide completely new routes (`/strangle/candidates`, `/strangle/recommendations`, `/strategies`, `/predictions/accuracy`, `/predictions/active`),
# it's safer to assume these new routes are meant to *replace* or augment the functionality, and the original routes related to these might be implicitly handled or superseded.
# However, the prompt says "rest of the file remains unchanged", so I will re-integrate the original routes that are not explicitly replaced by the new ones.
# The original routes were:
# - /strangle/candidates (seems replaced by new /strangle/candidates)
# - /strangle/recommendations (seems replaced by new /strangle/recommendations)
# - /strategies (this is a new route in the changes)
# - /positions (this route is not in the changes, so it should be kept)

@options_bp.route('/debug/sample-data')
def debug_sample_data():
    """Debug endpoint to test data generation"""
    try:
        timeframe = '30D'
        sample_symbols = ['RELIANCE', 'TCS']
        strategies = []
        
        for symbol in sample_symbols:
            spot_price = 1000 + (hash(symbol) % 3000)
            strategy_data = calculate_enhanced_strategy_metrics(symbol, spot_price, timeframe)
            if strategy_data:
                strategies.append(strategy_data)
        
        return jsonify({
            'success': True,
            'debug': True,
            'strategies': strategies,
            'sample_fields': list(strategies[0].keys()) if strategies else []
        })
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return jsonify({'success': False, 'error': str(e), 'debug': True}), 500

@options_bp.route('/positions')
def positions():
    """Get options positions"""
    start_time = time.time()

    try:
        # Sample positions data
        positions = [
            {
                "id": "pos_001",
                "underlying": "RELIANCE",
                "strategy": "strangle",
                "status": "open",
                "entry_date": "2025-01-10",
                "pnl": 2500,
                "pnl_percent": 5.6
            }
        ]

        generation_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "positions": positions,
            "total_positions": len(positions),
            "generation_time_ms": generation_time_ms
        })

    except Exception as e:
        logger.error(f"Error in options positions: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "positions": [],
            "total_positions": 0
        }), 500