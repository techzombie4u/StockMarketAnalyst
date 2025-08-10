
"""
Verdict Aggregator - Aggregate AI verdicts across products and timeframes
"""

import logging
from typing import Dict, List, Any
from collections import defaultdict
from .fusion_schema import AIVerdictCount, ProductBreakdown

logger = logging.getLogger(__name__)

class VerdictAggregator:
    """Aggregates AI verdicts from predictions data"""
    
    # Verdict normalization mapping
    VERDICT_MAPPING = {
        # Equity Agent mappings
        'STRONG_BUY': 'STRONG_BUY',
        'BUY': 'BUY', 
        'HOLD': 'HOLD',
        'SELL': 'CAUTIOUS',
        'STRONG_SELL': 'AVOID',
        
        # Options Agent mappings
        'EXECUTE': 'STRONG_BUY',
        'FAVORABLE': 'BUY',
        'NEUTRAL': 'HOLD',
        'CAUTION': 'CAUTIOUS',
        'AVOID': 'AVOID',
        
        # Sentiment Agent mappings
        'VERY_BULLISH': 'STRONG_BUY',
        'BULLISH': 'BUY',
        'NEUTRAL': 'HOLD',
        'BEARISH': 'CAUTIOUS',
        'VERY_BEARISH': 'AVOID',
        
        # Comm Agent mappings
        'HIGH_CONFIDENCE': 'STRONG_BUY',
        'CONFIDENT': 'BUY',
        'MODERATE': 'HOLD',
        'LOW_CONFIDENCE': 'CAUTIOUS',
        'NO_CONFIDENCE': 'AVOID',
        
        # Trainer Agent mappings  
        'RETRAIN_SUCCESS': 'BUY',
        'RETRAIN_NEEDED': 'CAUTIOUS',
        'MODEL_STABLE': 'HOLD',
        
        # Default/fallback mappings
        'POSITIVE': 'BUY',
        'NEGATIVE': 'CAUTIOUS',
        'UNKNOWN': 'HOLD'
    }
    
    def aggregate_verdicts(self, predictions_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate verdicts from predictions list"""
        try:
            # Initialize aggregation structures
            verdict_summary = defaultdict(lambda: AIVerdictCount())
            product_breakdown = {}
            
            # Group by product
            by_product = defaultdict(list)
            for pred in predictions_data:
                product = pred.get('product', 'unknown')
                by_product[product].append(pred)
            
            # Process each product
            for product, product_preds in by_product.items():
                verdict_counts = AIVerdictCount()
                total_confidence = 0.0
                success_count = 0
                completed_count = 0
                
                for pred in product_preds:
                    # Normalize verdict
                    raw_verdict = pred.get('ai_verdict', 'UNKNOWN')
                    normalized_verdict = self.normalize_verdict(raw_verdict)
                    
                    # Count verdicts
                    if hasattr(verdict_counts, normalized_verdict):
                        current_count = getattr(verdict_counts, normalized_verdict)
                        setattr(verdict_counts, normalized_verdict, current_count + 1)
                    
                    # Aggregate other metrics
                    total_confidence += pred.get('confidence', 0.0)
                    
                    # Count outcomes
                    outcome = pred.get('outcome_status', 'IN_PROGRESS')
                    if outcome in ['MET', 'NOT_MET']:
                        completed_count += 1
                        if outcome == 'MET':
                            success_count += 1
                
                # Calculate success rate
                success_rate = (success_count / completed_count * 100) if completed_count > 0 else 0.0
                avg_confidence = (total_confidence / len(product_preds)) if product_preds else 0.0
                
                # Store product breakdown
                product_breakdown[product] = ProductBreakdown(
                    total_predictions=len(product_preds),
                    active_predictions=len([p for p in product_preds if p.get('outcome_status') == 'IN_PROGRESS']),
                    success_rate=success_rate,
                    avg_confidence=avg_confidence,
                    verdict_distribution=verdict_counts
                )
                
                # Store in summary
                verdict_summary[product] = verdict_counts
            
            return {
                'verdict_summary': dict(verdict_summary),
                'product_breakdown': product_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error aggregating verdicts: {e}")
            return {
                'verdict_summary': {},
                'product_breakdown': {}
            }
    
    def normalize_verdict(self, raw_verdict: str) -> str:
        """Normalize verdict to standard 5-level scale"""
        if not raw_verdict:
            return 'HOLD'
            
        raw_verdict = raw_verdict.upper().strip()
        return self.VERDICT_MAPPING.get(raw_verdict, 'HOLD')
    
    def aggregate_by_timeframe(self, predictions_data: List[Dict[str, Any]]) -> Dict[str, AIVerdictCount]:
        """Aggregate verdicts by timeframe"""
        try:
            by_timeframe = defaultdict(lambda: AIVerdictCount())
            
            for pred in predictions_data:
                timeframe = pred.get('timeframe', 'unknown')
                raw_verdict = pred.get('ai_verdict', 'UNKNOWN')
                normalized_verdict = self.normalize_verdict(raw_verdict)
                
                verdict_counts = by_timeframe[timeframe]
                if hasattr(verdict_counts, normalized_verdict):
                    current_count = getattr(verdict_counts, normalized_verdict)
                    setattr(verdict_counts, normalized_verdict, current_count + 1)
            
            return dict(by_timeframe)
            
        except Exception as e:
            logger.error(f"Error aggregating verdicts by timeframe: {e}")
            return {}

# Global instance
verdict_aggregator = VerdictAggregator()
