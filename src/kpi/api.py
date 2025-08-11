"""
KPI API endpoints for metrics and dashboard integration
"""

import logging
from flask import Blueprint, jsonify, request
from datetime import datetime

from src.kpi.calculator import kpi_calculator
from src.common_repository.utils.date_utils import get_ist_now

logger = logging.getLogger(__name__)

# Create blueprint
kpi_bp = Blueprint("kpi", __name__)

@kpi_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get KPI metrics for specified timeframe"""
    try:
        timeframe = request.args.get('timeframe', 'All')

        if timeframe not in ['All', '3D', '5D', '10D', '15D', '30D']:
            return jsonify({
                'success': False,
                'error': 'Invalid timeframe. Must be one of: All, 3D, 5D, 10D, 15D, 30D'
            }), 400

        # Calculate KPIs
        kpis = kpi_calculator.calculate_kpis_by_timeframe(timeframe)

        return jsonify({
            'success': True,
            'data': kpis,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting KPI metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/recompute', methods=['POST'])
def recompute():
    """Manually trigger KPI recomputation"""
    try:
        timeframe = request.args.get('timeframe', 'All')

        if timeframe not in ['All', '3D', '5D', '10D', '15D', '30D']:
            return jsonify({
                'success': False,
                'error': 'Invalid timeframe'
            }), 400

        # Force recalculation
        kpis = kpi_calculator.calculate_kpis_by_timeframe(timeframe)

        return jsonify({
            'success': True,
            'message': f'KPIs recomputed for {timeframe}',
            'data': kpis,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error recomputing KPIs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/all-timeframes', methods=['GET'])
def get_all_timeframes():
    """Get KPIs for all timeframes"""
    try:
        timeframes = ['All', '3D', '5D', '10D', '15D', '30D']
        results = {}

        for tf in timeframes:
            results[tf] = kpi_calculator.calculate_kpis_by_timeframe(tf)

        return jsonify({
            'success': True,
            'data': results,
            'timestamp': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting all timeframe KPIs: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@kpi_bp.route('/status', methods=['GET'])
def get_status():
    """Get KPI system status"""
    try:
        # Get sample data info
        predictions = kpi_calculator.load_predictions_data()

        return jsonify({
            'success': True,
            'status': 'active',
            'predictions_loaded': len(predictions),
            'timeframes_available': kpi_calculator.timeframes,
            'last_updated': get_ist_now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting KPI status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500