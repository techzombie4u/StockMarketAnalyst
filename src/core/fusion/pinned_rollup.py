
"""
Pinned Rollup - Aggregate statistics for pinned predictions
"""

import logging
from typing import Dict, List, Any
from .fusion_schema import PinnedSummary

logger = logging.getLogger(__name__)

class PinnedRollup:
    """Aggregates statistics for pinned predictions"""
    
    def calculate_pinned_summary(self, pinned_symbols: List[str], 
                                predictions_data: List[Dict[str, Any]]) -> PinnedSummary:
        """Calculate summary statistics for pinned predictions"""
        try:
            if not pinned_symbols:
                return PinnedSummary()
            
            # Filter predictions for pinned symbols
            pinned_predictions = [
                pred for pred in predictions_data 
                if pred.get('symbol', '') in pinned_symbols
            ]
            
            if not pinned_predictions:
                return PinnedSummary(total=len(pinned_symbols))
            
            # Count outcomes
            met_count = 0
            not_met_count = 0
            in_progress_count = 0
            
            for pred in pinned_predictions:
                outcome = pred.get('outcome_status', 'IN_PROGRESS')
                if outcome == 'MET':
                    met_count += 1
                elif outcome == 'NOT_MET':
                    not_met_count += 1
                else:
                    in_progress_count += 1
            
            return PinnedSummary(
                total=len(pinned_symbols),
                met=met_count,
                not_met=not_met_count,
                in_progress=in_progress_count
            )
            
        except Exception as e:
            logger.error(f"Error calculating pinned summary: {e}")
            return PinnedSummary()
    
    def get_pinned_details(self, pinned_symbols: List[str], 
                          predictions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get detailed information for pinned predictions"""
        try:
            pinned_details = []
            
            for symbol in pinned_symbols:
                symbol_predictions = [
                    pred for pred in predictions_data 
                    if pred.get('symbol') == symbol
                ]
                
                if symbol_predictions:
                    # Get the most recent/highest confidence prediction
                    best_pred = max(symbol_predictions, 
                                  key=lambda x: (x.get('confidence', 0), x.get('score', 0)))
                    
                    pinned_details.append({
                        'symbol': symbol,
                        'product': best_pred.get('product', 'unknown'),
                        'confidence': best_pred.get('confidence', 0.0),
                        'score': best_pred.get('score', 0.0),
                        'ai_verdict': best_pred.get('ai_verdict', 'HOLD'),
                        'outcome_status': best_pred.get('outcome_status', 'IN_PROGRESS'),
                        'timeframe': best_pred.get('timeframe', 'unknown')
                    })
                else:
                    # Symbol is pinned but no predictions available
                    pinned_details.append({
                        'symbol': symbol,
                        'product': 'unknown',
                        'confidence': 0.0,
                        'score': 0.0,
                        'ai_verdict': 'HOLD',
                        'outcome_status': 'IN_PROGRESS',
                        'timeframe': 'unknown'
                    })
            
            return pinned_details
            
        except Exception as e:
            logger.error(f"Error getting pinned details: {e}")
            return []

# Global instance
pinned_rollup = PinnedRollup()
