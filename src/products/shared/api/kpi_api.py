
"""
KPI API Endpoints
Provides REST endpoints for KPI dashboard functionality
"""

import time
from flask import Blueprint, jsonify, request
from typing import Dict, Any

from products.shared.services.kpi_service import kpi_service
from common_repository.config.feature_flags import feature_flags
from common_repository.utils.date_utils import get_ist_now

# Create blueprint
kpi_bp = Blueprint('kpi', __name__, url_prefix='/api/kpi')

# Rate limiting for manual refresh (simple in-memory store)
_last_manual_refresh = {}

@kpi_bp.route('/summary', methods=['GET'])
def get_kpi_summary():
    """Get KPI summary with overall and by-product breakdowns"""
    try:
        timeframe = request.args.get('timeframe', 'All')
        
        if timeframe not in ['All', '3D', '5D', '10D', '15D', '30D']:
            return jsonify({
                'success': False,
                'error': 'Invalid timeframe'
            }), 400
        
        # Compute overall KPIs
        overall_kpis = kpi_service.compute(timeframe=timeframe)
        
        # Compute by-product KPIs
        by_product = {}
        products = ['equities', 'options', 'commodities']
        
        for product in products:
            if feature_flags.is_enabled(f'enable_{product}') or product == 'equities':
                by_product[product] = kpi_service.compute(timeframe=timeframe, product=product)
        
        # Evaluate triggers
        triggers = []
        if feature_flags.is_enabled('enable_goahead_triggers'):
            # Get triggers from overall and each product
            triggers.extend(kpi_service.evaluate_triggers(overall_kpis))
            for product_kpis in by_product.values():
                triggers.extend(kpi_service.evaluate_triggers(product_kpis))
        
        # Get last refresh timestamps
        last_auto_refresh = overall_kpis.get('last_updated')
        last_manual_refresh = _get_last_manual_refresh(timeframe)
        
        response = {
            'success': True,
            'data': {
                'timeframe': timeframe,
                'last_auto_refresh': last_auto_refresh,
                'last_manual_refresh': last_manual_refresh,
                'overall': overall_kpis,
                'by_product': by_product,
                'triggers': [_trigger_to_dict(t) for t in triggers],
                'trigger_count': len(triggers)
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/product/<product>', methods=['GET'])
def get_product_kpis(product):
    """Get KPIs for specific product"""
    try:
        if product not in ['equities', 'options', 'commodities']:
            return jsonify({
                'success': False,
                'error': 'Invalid product'
            }), 400
        
        timeframe = request.args.get('timeframe', 'All')
        
        if timeframe not in ['All', '3D', '5D', '10D', '15D', '30D']:
            return jsonify({
                'success': False,
                'error': 'Invalid timeframe'
            }), 400
        
        # Compute product-specific KPIs
        kpis = kpi_service.compute(timeframe=timeframe, product=product)
        
        # Evaluate triggers for this product
        triggers = []
        if feature_flags.is_enabled('enable_goahead_triggers'):
            triggers = kpi_service.evaluate_triggers(kpis)
        
        response = {
            'success': True,
            'data': {
                'product': product,
                'timeframe': timeframe,
                'kpis': kpis,
                'triggers': [_trigger_to_dict(t) for t in triggers],
                'last_updated': kpis.get('last_updated')
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/recompute', methods=['POST'])
def recompute_kpis():
    """Manually trigger KPI recomputation"""
    try:
        scope = request.args.get('scope', 'overall')  # overall|product
        timeframe = request.args.get('timeframe', 'All')
        product = request.args.get('product') if scope == 'product' else None
        
        # Rate limiting check
        rate_limit_key = f"{scope}_{timeframe}_{product or 'all'}"
        if not _check_rate_limit(rate_limit_key):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please wait before triggering another manual refresh.',
                'retry_after': 120
            }), 429
        
        # Recompute KPIs
        if scope == 'overall':
            kpis = kpi_service.compute(timeframe=timeframe)
            by_product = {}
            for prod in ['equities', 'options', 'commodities']:
                by_product[prod] = kpi_service.compute(timeframe=timeframe, product=prod)
            
            result_data = {
                'overall': kpis,
                'by_product': by_product
            }
        else:
            if not product or product not in ['equities', 'options', 'commodities']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or missing product for product scope'
                }), 400
            
            kpis = kpi_service.compute(timeframe=timeframe, product=product)
            result_data = {
                'product_kpis': kpis
            }
        
        # Update manual refresh timestamp
        _update_manual_refresh_timestamp(timeframe)
        
        response = {
            'success': True,
            'message': f'KPIs recomputed for {scope} scope',
            'data': result_data,
            'last_manual_refresh': get_ist_now().isoformat(),
            'scope': scope,
            'timeframe': timeframe
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/thresholds', methods=['GET'])
def get_kpi_thresholds():
    """Get KPI thresholds configuration"""
    try:
        return jsonify({
            'success': True,
            'data': kpi_service.thresholds
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/triggers/acknowledge', methods=['POST'])
def acknowledge_trigger():
    """Acknowledge a GoAhead trigger"""
    try:
        trigger_id = request.json.get('trigger_id')
        if not trigger_id:
            return jsonify({
                'success': False,
                'error': 'Missing trigger_id'
            }), 400
        
        # For now, just return success
        # In future prompts, this will integrate with agent execution
        return jsonify({
            'success': True,
            'message': f'Trigger {trigger_id} acknowledged',
            'timestamp': get_ist_now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _trigger_to_dict(trigger) -> Dict[str, Any]:
    """Convert KPITrigger to dictionary"""
    return {
        'id': f"{trigger.type}_{trigger.product}_{trigger.timeframe}_{int(time.time())}",
        'type': trigger.type,
        'product': trigger.product,
        'timeframe': trigger.timeframe,
        'reason': trigger.reason,
        'severity': trigger.severity,
        'timestamp': trigger.timestamp or get_ist_now().isoformat()
    }

def _check_rate_limit(key: str) -> bool:
    """Check if rate limit allows manual refresh"""
    current_time = time.time()
    last_refresh = _last_manual_refresh.get(key, 0)
    
    # Allow if more than 2 minutes have passed
    if current_time - last_refresh > 120:
        _last_manual_refresh[key] = current_time
        return True
    
    return False

def _get_last_manual_refresh(timeframe: str) -> str:
    """Get last manual refresh timestamp"""
    key = f"manual_refresh_{timeframe}"
    timestamp = _last_manual_refresh.get(key, 0)
    if timestamp:
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).isoformat()
    return None

def _update_manual_refresh_timestamp(timeframe: str):
    """Update manual refresh timestamp"""
    key = f"manual_refresh_{timeframe}"
    _last_manual_refresh[key] = time.time()
