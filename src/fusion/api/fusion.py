
import json
import time
import os
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

fusion_bp = Blueprint('fusion', __name__)

def load_sample_data(filename):
    """Load sample data from fixtures"""
    try:
        filepath = os.path.join('data', 'fixtures', filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
    return {}

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

def load_pins_data():
    """Load pinned items data"""
    try:
        filepath = os.path.join('data', 'persistent', 'pins.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                return data.get('pins', [])
    except Exception as e:
        logger.error(f"Error loading pins data: {e}")
    return []

@fusion_bp.route('/dashboard')
def dashboard():
    """Main fusion dashboard endpoint"""
    start_time = time.time()
    
    try:
        # Load KPI data
        kpi_data = load_kpi_data()
        timeframes = kpi_data.get('metrics', {})
        
        # Load pinned items
        pins = load_pins_data()
        pinned_summary = {
            "total_pinned": len(pins),
            "equity_count": len([p for p in pins if p.get('type') == 'EQUITY']),
            "options_count": len([p for p in pins if p.get('type') == 'OPTIONS']),
            "commodity_count": len([p for p in pins if p.get('type') == 'COMMODITY'])
        }
        
        # Load equities for top signals
        equities_data = load_sample_data('equities_sample.json')
        top_signals = []
        
        if 'items' in equities_data:
            for item in equities_data['items'][:5]:  # Top 5
                top_signals.append({
                    "symbol": item.get('symbol'),
                    "name": item.get('name'),
                    "verdict": item.get('verdict'),
                    "confidence": item.get('confidence', 0),
                    "price": item.get('price'),
                    "change_percent": item.get('change_percent', 0)
                })
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        response = {
            "timeframes": timeframes,
            "pinned_summary": pinned_summary,
            "top_signals": top_signals,
            "generation_time_ms": generation_time_ms,
            "last_updated": datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in fusion dashboard: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "timeframes": {},
            "pinned_summary": {"total_pinned": 0},
            "top_signals": [],
            "generation_time_ms": 0
        }), 500

@fusion_bp.route('/timeframes')
def timeframes():
    """Get available timeframes"""
    kpi_data = load_kpi_data()
    return jsonify({
        "timeframes": list(kpi_data.get('metrics', {}).keys()),
        "default": "5D"
    })
