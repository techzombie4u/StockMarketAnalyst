
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

@predictions_bp.route('/list', methods=['GET'])
def get_predictions_list():
    """Get unified list of all predictions across products"""
    try:
        predictions = []
        
        # Load equity predictions from stock data
        stock_data = json_store.load('top10', {})
        stocks = stock_data.get('stocks', [])
        
        for stock in stocks:
            # Normalize AI verdict
            raw_verdict = stock.get('ai_verdict', 'HOLD')
            normalized_verdict = verdict_normalizer.normalize_verdict('equity_agent', raw_verdict)
            
            predictions.append({
                'symbol': stock.get('symbol', ''),
                'product': 'equities',
                'timeframe': '5D',
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'due_date': datetime.now().strftime('%Y-%m-%d'),
                'predicted_value': stock.get('predicted_price'),
                'predicted_prob': stock.get('confidence', 0.0) / 100.0,
                'actuals': stock.get('current_price'),
                'outcome_status': _determine_outcome_status(stock),
                'ai_verdict': raw_verdict,
                'ai_verdict_normalized': normalized_verdict,
                'confidence': stock.get('confidence', 0.0),
                'score': stock.get('score', 0.0)
            })
        
        # Load options predictions from tracking data
        tracking_data = json_store.load('interactive_tracking', {})
        if isinstance(tracking_data, list):
            for entry in tracking_data:
                if isinstance(entry, dict):
                    raw_verdict = entry.get('ai_verdict', 'HOLD')
                    normalized_verdict = verdict_normalizer.normalize_verdict('options_agent', raw_verdict)
                    
                    predictions.append({
                        'symbol': entry.get('symbol', ''),
                        'product': 'options',
                        'timeframe': entry.get('timeframe', '5D'),
                        'start_date': entry.get('start_date', ''),
                        'due_date': entry.get('expiry_date', ''),
                        'predicted_value': entry.get('predicted_roi'),
                        'predicted_prob': entry.get('confidence', 0.0) / 100.0,
                        'actuals': entry.get('actual_roi'),
                        'outcome_status': entry.get('status', 'IN_PROGRESS').upper(),
                        'ai_verdict': raw_verdict,
                        'ai_verdict_normalized': normalized_verdict,
                        'confidence': entry.get('confidence', 0.0),
                        'score': entry.get('score', 0.0)
                    })
        
        # Load communication agent predictions (if any)
        # This would come from communication/sentiment analysis
        
        # Apply filters
        product_filter = request.args.get('product')
        timeframe_filter = request.args.get('timeframe')
        status_filter = request.args.get('status')
        
        if product_filter:
            predictions = [p for p in predictions if p['product'] == product_filter]
        
        if timeframe_filter:
            predictions = [p for p in predictions if p['timeframe'] == timeframe_filter]
        
        if status_filter:
            predictions = [p for p in predictions if p['outcome_status'] == status_filter.upper()]
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'total_count': len(predictions),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting predictions list: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'predictions': [],
            'total_count': 0
        }), 500

def _determine_outcome_status(stock: Dict[str, Any]) -> str:
    """Determine outcome status for a stock prediction"""
    try:
        # Simple heuristic based on score and confidence
        score = stock.get('score', 0.0)
        confidence = stock.get('confidence', 0.0)
        
        # If high score and high confidence, likely met
        if score >= 70 and confidence >= 70:
            return 'MET'
        elif score <= 40 or confidence <= 40:
            return 'NOT_MET'
        else:
            return 'IN_PROGRESS'
            
    except Exception:
        return 'IN_PROGRESS'
