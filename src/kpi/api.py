
import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

kpi_bp = Blueprint('kpi', __name__)

def load_kpi_data():
    """Load KPI metrics data"""
    try:
        filepath = os.path.join('data', 'kpi', 'kpi_metrics.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading KPI data: {e}")
    return {"metrics": {}}

@kpi_bp.route('/metrics')
def metrics():
    """Get KPI metrics"""
    start_time = time.time()
    
    try:
        # Get query parameters
        timeframe = request.args.get('timeframe', '5D')
        
        # Load data
        data = load_kpi_data()
        all_metrics = data.get('metrics', {})
        
        if timeframe in all_metrics:
            metrics = all_metrics[timeframe]
        else:
            metrics = {}
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        return jsonify({
            "timeframe": timeframe,
            "metrics": metrics,
            "available_timeframes": list(all_metrics.keys()),
            "generation_time_ms": generation_time_ms
        })
        
    except Exception as e:
        logger.error(f"Error in KPI metrics: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "metrics": {}
        }), 500

@kpi_bp.route('/status')
def status():
    """Get KPI system status"""
    return jsonify({
        "status": "active",
        "last_calculation": datetime.now().isoformat(),
        "calculation_count": 1250,
        "avg_calculation_time_ms": 89
    })
