import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

commodities_bp = Blueprint('commodities', __name__)

def load_commodities_data():
    """Load commodities sample data"""
    try:
        filepath = os.path.join('data', 'fixtures', 'commodities_sample.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading commodities data: {e}")
    return {"signals": [], "correlations": {}}

@commodities_bp.route('/signals')
def signals():
    """Get commodity signals"""
    start_time = time.time()

    try:
        # Load data
        data = load_commodities_data()
        signals = data.get('signals', [])

        generation_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "signals": signals,
            "total_signals": len(signals),
            "generation_time_ms": generation_time_ms
        })

    except Exception as e:
        logger.error(f"Error in commodity signals: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "signals": [],
            "total_signals": 0
        }), 500

@commodities_bp.route('/correlations')
def correlations():
    """Get commodity correlations"""
    start_time = time.time()

    try:
        # Get query parameters
        symbol = request.args.get('symbol', 'GOLD')

        # Load data
        data = load_commodities_data()
        correlations = data.get('correlations', {})

        symbol_correlations = correlations.get(symbol, {})

        generation_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "symbol": symbol,
            "correlations": symbol_correlations,
            "generation_time_ms": generation_time_ms
        })

    except Exception as e:
        logger.error(f"Error in commodity correlations: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "correlations": {}
        }), 500