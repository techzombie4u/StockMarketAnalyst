"""
Predictions API - Unified predictions endpoint
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from typing import Dict, Any, List

from src.common_repository.storage.json_store import json_store
from src.common_repository.agents.verdict_normalizer import verdict_normalizer

logger = logging.getLogger(__name__)

# Create blueprint
predictions_bp = Blueprint('predictions', __name__, url_prefix='/api/predictions')

@predictions_bp.route('/status', methods=['GET'])
def predictions_status():
    """Get predictions system status"""
    return jsonify({
        "status": "active",
        "module": "predictions",
        "endpoints": [
            "/api/predictions/status",
            "/api/predictions/latest"
        ]
    })

@predictions_bp.route('/latest', methods=['GET'])
def latest_predictions():
    """Get latest predictions"""
    return jsonify({
        "message": "Latest predictions endpoint",
        "predictions": [],
        "count": 0
    })
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from src.services.finalize import FinalizationService

predictions_bp = Blueprint('predictions', __name__)
logger = logging.getLogger(__name__)

# Initialize finalization service
finalize_service = FinalizationService()

@predictions_bp.route('/accuracy', methods=['GET'])
def get_accuracy():
    """Get prediction accuracy statistics"""
    try:
        window = request.args.get('window', '30d').lower()
        
        # Parse window to days
        if window.endswith('d'):
            days = int(window[:-1])
        else:
            days = 30
        
        # Get accuracy stats
        stats = finalize_service.get_accuracy_stats(days)
        
        return jsonify({
            'success': True,
            'micro_accuracy': stats['micro_accuracy'],
            'macro_accuracy': stats['macro_accuracy'],
            'total_predictions': stats['total'],
            'successful_predictions': stats['success'],
            'failed_predictions': stats['failed'],
            'by_timeframe': stats['by_timeframe'],
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting accuracy: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictions_bp.route('/active', methods=['GET'])
def get_active_predictions():
    """Get active predictions"""
    try:
        active_predictions = finalize_service.get_active_predictions()
        
        return jsonify({
            'success': True,
            'items': active_predictions,
            'count': len(active_predictions),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting active predictions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
