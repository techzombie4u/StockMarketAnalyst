
import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

equities_bp = Blueprint('equities', __name__)

def load_equities_data():
    """Load equities sample data"""
    try:
        filepath = os.path.join('data', 'fixtures', 'equities_sample.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading equities data: {e}")
    return {"items": [], "total_count": 0}

@equities_bp.route('/list')
def list_equities():
    """List equity items with optional filtering"""
    start_time = time.time()
    
    try:
        # Get query parameters
        sector = request.args.get('sector')
        min_price = request.args.get('minPrice', type=float)
        max_price = request.args.get('maxPrice', type=float)
        limit = request.args.get('limit', 50, type=int)
        
        # Load data
        data = load_equities_data()
        items = data.get('items', [])
        
        # Apply filters
        filtered_items = []
        for item in items:
            # Sector filter
            if sector and item.get('sector', '').upper() != sector.upper():
                continue
            
            # Price filters
            price = item.get('price', 0)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            
            filtered_items.append(item)
        
        # Apply limit
        filtered_items = filtered_items[:limit]
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        return jsonify({
            "items": filtered_items,
            "total_count": len(filtered_items),
            "generation_time_ms": generation_time_ms,
            "filters_applied": {
                "sector": sector,
                "min_price": min_price,
                "max_price": max_price,
                "limit": limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error in equities list: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "items": [],
            "total_count": 0
        }), 500

@equities_bp.route('/kpis')
def equities_kpis():
    """Get equity KPIs by timeframe"""
    start_time = time.time()
    
    try:
        timeframe = request.args.get('timeframe', '5D')
        
        # Load KPI data
        kpi_file = os.path.join('data', 'kpi', 'kpi_metrics.json')
        kpi_data = {}
        
        if os.path.exists(kpi_file):
            with open(kpi_file, 'r') as f:
                kpi_data = json.load(f)
        
        metrics = kpi_data.get('metrics', {}).get(timeframe, {})
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        return jsonify({
            "timeframe": timeframe,
            "metrics": metrics,
            "generation_time_ms": generation_time_ms
        })
        
    except Exception as e:
        logger.error(f"Error in equities KPIs: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "metrics": {}
        }), 500
