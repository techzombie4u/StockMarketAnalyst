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
    """Get prediction accuracy metrics"""
    try:
        window = request.args.get('window', '30D')
        instrument = request.args.get('instrument', 'all')  # option, equity, commodity, all

        # Calculate accuracy from finalized predictions
        finalized = finalize_service.get_finalized_predictions()

        # Filter by instrument if specified
        if instrument and instrument != 'all':
            if instrument == 'option':
                finalized = [p for p in finalized if p.get('instrument', '').upper() in ['OPTIONS', 'OPTION']]
            elif instrument == 'equity':
                finalized = [p for p in finalized if p.get('instrument', '').upper() in ['EQUITIES', 'EQUITY']]
            elif instrument == 'commodity':
                finalized = [p for p in finalized if p.get('instrument', '').upper() in ['COMMODITIES', 'COMMODITY']]

        if not finalized:
            return jsonify({
                'success': True,
                'data': {
                    'by_timeframe': [
                        {'timeframe': window, 'micro_accuracy': 0.0, 'macro_accuracy': 0.0}
                    ],
                    'micro_accuracy': 0.0,
                    'macro_accuracy': 0.0
                }
            })

        # Calculate accuracy metrics
        correct_predictions = [p for p in finalized if p.get('outcome') == 'CORRECT']
        total_predictions = len(finalized)

        micro_accuracy = len(correct_predictions) / total_predictions if total_predictions > 0 else 0.0
        macro_accuracy = micro_accuracy  # Simplified for now

        return jsonify({
            'success': True,
            'data': {
                'by_timeframe': [
                    {
                        'timeframe': window,
                        'micro_accuracy': round(micro_accuracy, 3),
                        'macro_accuracy': round(macro_accuracy, 3)
                    }
                ],
                'micro_accuracy': round(micro_accuracy, 3),
                'macro_accuracy': round(macro_accuracy, 3)
            }
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