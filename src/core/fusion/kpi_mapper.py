
"""
KPI Mapper - Transform raw KPI data into fusion schema with coloring and trends
"""

import logging
from typing import Dict, List, Optional, Any
from .fusion_schema import KPIMetric, TimeframeKPIs, create_kpi_metric

logger = logging.getLogger(__name__)

class KPIMapper:
    """Maps raw KPI data to fusion dashboard format"""
    
    # KPI Targets (from our configuration)
    TARGETS = {
        'brier_score': 0.15,        # Lower is better
        'hit_rate': 0.70,           # Higher is better  
        'calibration_error': 0.05,  # Lower is better
        'sharpe_ratio': 1.5,        # Higher is better
        'sortino_ratio': 2.0,       # Higher is better
        'max_drawdown': 0.10,       # Lower is better (10%)
        'var_95': 0.05,            # Lower is better (5%)
        'var_99': 0.02,            # Lower is better (2%)
    }
    
    def __init__(self):
        self.historical_values = {}  # Store for trend calculation
    
    def map_timeframe_kpis(self, raw_kpi_data: Dict[str, Any], timeframe: str) -> TimeframeKPIs:
        """Map raw KPI data for a specific timeframe"""
        try:
            tf_data = raw_kpi_data.get(timeframe, {})
            
            # Extract prediction KPIs
            prediction_kpis = [
                create_kpi_metric(
                    "Brier Score",
                    tf_data.get('brier_score', 0.0),
                    self.TARGETS['brier_score'],
                    self._get_trend_values('brier_score', timeframe)
                ),
                create_kpi_metric(
                    "Hit Rate",
                    tf_data.get('hit_rate', 0.0),
                    self.TARGETS['hit_rate'],
                    self._get_trend_values('hit_rate', timeframe)
                ),
                create_kpi_metric(
                    "Calibration Error",
                    tf_data.get('calibration_error', 0.0),
                    self.TARGETS['calibration_error'],
                    self._get_trend_values('calibration_error', timeframe)
                )
            ]
            
            # Extract financial KPIs
            financial_kpis = [
                create_kpi_metric(
                    "Sharpe Ratio",
                    tf_data.get('sharpe_ratio', 0.0),
                    self.TARGETS['sharpe_ratio'],
                    self._get_trend_values('sharpe_ratio', timeframe)
                ),
                create_kpi_metric(
                    "Sortino Ratio",
                    tf_data.get('sortino_ratio', 0.0),
                    self.TARGETS['sortino_ratio'],
                    self._get_trend_values('sortino_ratio', timeframe)
                ),
                create_kpi_metric(
                    "Max Drawdown",
                    tf_data.get('max_drawdown', 0.0),
                    self.TARGETS['max_drawdown'],
                    self._get_trend_values('max_drawdown', timeframe)
                )
            ]
            
            # Extract risk KPIs
            risk_kpis = [
                create_kpi_metric(
                    "VaR 95%",
                    tf_data.get('var_95', 0.0),
                    self.TARGETS['var_95'],
                    self._get_trend_values('var_95', timeframe)
                ),
                create_kpi_metric(
                    "VaR 99%",
                    tf_data.get('var_99', 0.0),
                    self.TARGETS['var_99'],
                    self._get_trend_values('var_99', timeframe)
                )
            ]
            
            return TimeframeKPIs(
                timeframe=timeframe,
                prediction_kpis=prediction_kpis,
                financial_kpis=financial_kpis,
                risk_kpis=risk_kpis,
                total_predictions=tf_data.get('total_predictions', 0),
                active_predictions=tf_data.get('active_predictions', 0)
            )
            
        except Exception as e:
            logger.error(f"Error mapping KPIs for timeframe {timeframe}: {e}")
            return self._create_empty_timeframe_kpis(timeframe)
    
    def _get_trend_values(self, metric: str, timeframe: str) -> Optional[List[float]]:
        """Get historical values for trend calculation"""
        key = f"{metric}_{timeframe}"
        return self.historical_values.get(key, [])
    
    def _store_trend_value(self, metric: str, timeframe: str, value: float):
        """Store value for trend calculation (keep last 5 values)"""
        key = f"{metric}_{timeframe}"
        if key not in self.historical_values:
            self.historical_values[key] = []
        
        self.historical_values[key].append(value)
        # Keep only last 5 values
        self.historical_values[key] = self.historical_values[key][-5:]
    
    def _create_empty_timeframe_kpis(self, timeframe: str) -> TimeframeKPIs:
        """Create empty KPI structure for error cases"""
        return TimeframeKPIs(
            timeframe=timeframe,
            prediction_kpis=[
                KPIMetric("Brier Score", 0.0, color="neutral"),
                KPIMetric("Hit Rate", 0.0, color="neutral"),
                KPIMetric("Calibration Error", 0.0, color="neutral")
            ],
            financial_kpis=[
                KPIMetric("Sharpe Ratio", 0.0, color="neutral"),
                KPIMetric("Sortino Ratio", 0.0, color="neutral"),
                KPIMetric("Max Drawdown", 0.0, color="neutral")
            ],
            risk_kpis=[
                KPIMetric("VaR 95%", 0.0, color="neutral"),
                KPIMetric("VaR 99%", 0.0, color="neutral")
            ]
        )

# Global instance
kpi_mapper = KPIMapper()
