
"""
Options Service Orchestrator
Coordinates options analysis using shared core components
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from common_repository.utils.date_utils import get_ist_now
from common_repository.utils.error_handler import safe_execute, ErrorContext
from common_repository.models.instrument import Instrument, InstrumentType, MarketSegment
from common_repository.storage.json_store import json_store
from common_repository.config.feature_flags import feature_flags

logger = logging.getLogger(__name__)

class OptionsService:
    """Main service for options analysis and strategies"""
    
    def __init__(self):
        self.name = "options_service"
        self.supported_strategies = ["short_strangle", "covered_call", "protective_put"]
        
    def analyze_short_strangle(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Analyze short strangle strategy for a symbol
        This will coordinate with existing short_strangle_engine.py
        """
        try:
            logger.info(f"Starting short strangle analysis for {symbol}")
            
            # Integrate with existing short strangle engine
            analysis_result = self._perform_short_strangle_analysis(symbol, force_refresh)
            
            if analysis_result:
                # Enhance with shared core features
                enhanced_result = self._enhance_with_core_features(analysis_result)
                
                logger.info(f"Completed short strangle analysis for {symbol}")
                return enhanced_result
            else:
                logger.warning(f"Short strangle analysis failed for {symbol}")
                return None
            
        except Exception as e:
            logger.error(f"Error in short strangle analysis for {symbol}: {str(e)}")
            return None
    
    def get_options_strategies_data(self, timeframe: str = '30D') -> Optional[Dict[str, Any]]:
        """
        Get options strategies data for dashboard
        This will integrate with existing options strategy logic
        """
        try:
            logger.info(f"Getting options strategies data for timeframe: {timeframe}")
            
            # This will integrate with existing options_math.py and options strategy logic
            strategies_data = self._get_strategies_data(timeframe)
            
            if strategies_data:
                return {
                    'success': True,
                    'timeframe': timeframe,
                    'data': strategies_data,
                    'timestamp': get_ist_now().isoformat(),
                    'service': self.name
                }
            else:
                return {
                    'success': False,
                    'message': 'No strategies data available',
                    'timeframe': timeframe,
                    'timestamp': get_ist_now().isoformat(),
                    'service': self.name
                }
                
        except Exception as e:
            logger.error(f"Error getting options strategies data: {str(e)}")
            return None
    
    def get_active_options_predictions(self) -> List[Dict[str, Any]]:
        """
        Get active options predictions
        This will integrate with existing prediction tracking
        """
        try:
            # This will integrate with existing prediction tracking logic
            from src.analyzers.smart_go_agent import SmartGoAgent
            
            agent = SmartGoAgent()
            active_predictions = agent.get_active_options_predictions()
            
            return active_predictions
            
        except Exception as e:
            logger.error(f"Error getting active options predictions: {str(e)}")
            return []
    
    def _perform_short_strangle_analysis(self, symbol: str, force_refresh: bool) -> Optional[Dict[str, Any]]:
        """Perform short strangle analysis using existing engine"""
        try:
            # Import and use existing short strangle engine
            from src.analyzers.short_strangle_engine import ShortStrangleEngine
            
            engine = ShortStrangleEngine()
            result = engine.analyze_short_strangle(symbol, force_realtime=force_refresh)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in short strangle analysis for {symbol}: {str(e)}")
            return None
    
    def _enhance_with_core_features(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance analysis result with shared core features"""
        try:
            # Add service metadata
            analysis_result['service'] = self.name
            analysis_result['enhanced_timestamp'] = get_ist_now().isoformat()
            
            # Add feature flags context
            analysis_result['features_enabled'] = {
                'dynamic_confidence': feature_flags.is_enabled('enable_dynamic_confidence'),
                'real_time_trends': feature_flags.is_enabled('enable_real_time_trends')
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error enhancing analysis result: {str(e)}")
            return analysis_result
    
    def _get_strategies_data(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """Get strategies data using existing logic"""
        try:
            # This will integrate with existing options strategy computation
            from src.compute.options_math import load_min_inputs, compute_row, now_iso
            
            # Load minimal input set per symbol
            raw_rows = load_min_inputs(timeframe)
            
            if not raw_rows:
                return None
            
            # Compute final rows from minimal inputs
            rows = [compute_row(r).__dict__ for r in raw_rows]
            
            # Calculate summary
            summary = {
                "total_premium_collected": round(sum(r["total_premium"] for r in rows), 2),
                "avg_roi_pct": round(sum(r["roi_pct"] for r in rows) / len(rows), 2) if rows else 0.0,
                "total_count": len(rows),
                "success_count": len([r for r in rows if r["result"] == "success"]),
                "in_progress_count": len([r for r in rows if r["result"] == "in_progress"]),
                "failed_count": len([r for r in rows if r["result"] == "failed"])
            }
            
            return {
                "rows": rows,
                "summary": summary,
                "generated_at": now_iso()
            }
            
        except Exception as e:
            logger.error(f"Error getting strategies data: {str(e)}")
            return None

# Global service instance
options_service = OptionsService()
