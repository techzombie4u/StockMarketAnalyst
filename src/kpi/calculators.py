
"""
Real KPI Calculators - Process prediction/actual arrays into KPI metrics
Takes arrays of {pred, actual, ts} and outputs standardized KPI sets
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PredictionRecord:
    """Single prediction record structure"""
    predicted: float
    actual: float
    timestamp: str
    symbol: Optional[str] = None
    confidence: Optional[float] = None
    timeframe: Optional[str] = None

@dataclass
class KPIResults:
    """Standardized KPI results structure"""
    timeframe: str
    sample_size: int
    
    # Prediction accuracy metrics
    brier_score: float
    directional_accuracy: float
    mape: float  # Mean Absolute Percentage Error
    rmse: float  # Root Mean Square Error
    hit_rate: float  # % predictions within tolerance
    
    # Financial performance metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    information_ratio: float
    
    # Risk metrics
    max_drawdown: float
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    volatility: float
    
    # Quality metrics
    calibration_error: float
    coverage_ratio: float
    bias: float
    
    status: str = "unknown"  # green/amber/red

class KPICalculator:
    """Real KPI calculator using prediction/actual data"""
    
    def __init__(self):
        self.tolerance = 0.05  # 5% tolerance for hit rate
        self.risk_free_rate = 0.05  # 5% annual risk-free rate
        
    def calculate_kpis(self, predictions: List[Dict[str, Any]], timeframe: str) -> KPIResults:
        """Calculate KPIs for a given prediction dataset and timeframe"""
        try:
            # Convert to PredictionRecord objects
            records = self._parse_predictions(predictions)
            
            if len(records) < 5:
                return self._empty_kpi_results(timeframe, len(records))
            
            # Calculate all metrics
            prediction_metrics = self._calculate_prediction_metrics(records)
            financial_metrics = self._calculate_financial_metrics(records)
            risk_metrics = self._calculate_risk_metrics(records)
            quality_metrics = self._calculate_quality_metrics(records)
            
            # Combine into results
            results = KPIResults(
                timeframe=timeframe,
                sample_size=len(records),
                
                # Prediction metrics
                brier_score=prediction_metrics['brier_score'],
                directional_accuracy=prediction_metrics['directional_accuracy'],
                mape=prediction_metrics['mape'],
                rmse=prediction_metrics['rmse'],
                hit_rate=prediction_metrics['hit_rate'],
                
                # Financial metrics
                sharpe_ratio=financial_metrics['sharpe_ratio'],
                sortino_ratio=financial_metrics['sortino_ratio'],
                calmar_ratio=financial_metrics['calmar_ratio'],
                information_ratio=financial_metrics['information_ratio'],
                
                # Risk metrics
                max_drawdown=risk_metrics['max_drawdown'],
                var_95=risk_metrics['var_95'],
                var_99=risk_metrics['var_99'],
                volatility=risk_metrics['volatility'],
                
                # Quality metrics
                calibration_error=quality_metrics['calibration_error'],
                coverage_ratio=quality_metrics['coverage_ratio'],
                bias=quality_metrics['bias']
            )
            
            # Determine overall status
            results.status = self._determine_status(results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error calculating KPIs for {timeframe}: {str(e)}")
            return self._empty_kpi_results(timeframe, 0)
    
    def _parse_predictions(self, predictions: List[Dict[str, Any]]) -> List[PredictionRecord]:
        """Parse prediction dictionaries into PredictionRecord objects"""
        records = []
        
        for pred in predictions:
            try:
                # Handle different input formats
                predicted_val = pred.get('predicted', pred.get('pred', pred.get('prediction', 0)))
                actual_val = pred.get('actual', pred.get('actual_value', 0))
                timestamp = pred.get('timestamp', pred.get('ts', pred.get('date', '')))
                
                if predicted_val != 0 and actual_val != 0:
                    records.append(PredictionRecord(
                        predicted=float(predicted_val),
                        actual=float(actual_val),
                        timestamp=str(timestamp),
                        symbol=pred.get('symbol'),
                        confidence=pred.get('confidence'),
                        timeframe=pred.get('timeframe')
                    ))
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid prediction record: {e}")
                continue
                
        return records
    
    def _calculate_prediction_metrics(self, records: List[PredictionRecord]) -> Dict[str, float]:
        """Calculate prediction accuracy metrics"""
        predictions = np.array([r.predicted for r in records])
        actuals = np.array([r.actual for r in records])
        
        # Brier Score (for probability predictions, convert to binary outcomes)
        prediction_errors = np.abs(predictions - actuals) / np.abs(actuals)
        binary_correct = (prediction_errors <= self.tolerance).astype(int)
        confidences = np.array([r.confidence or 0.7 for r in records]) / 100.0
        brier_score = np.mean((confidences - binary_correct) ** 2)
        
        # Directional Accuracy
        pred_directions = np.sign(predictions)
        actual_directions = np.sign(actuals)
        directional_accuracy = np.mean(pred_directions == actual_directions) * 100
        
        # MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs(prediction_errors)) * 100
        
        # RMSE (Root Mean Square Error)
        rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
        
        # Hit Rate (% within tolerance)
        hit_rate = np.mean(binary_correct) * 100
        
        return {
            'brier_score': round(brier_score, 4),
            'directional_accuracy': round(directional_accuracy, 2),
            'mape': round(mape, 2),
            'rmse': round(rmse, 4),
            'hit_rate': round(hit_rate, 2)
        }
    
    def _calculate_financial_metrics(self, records: List[PredictionRecord]) -> Dict[str, float]:
        """Calculate financial performance metrics"""
        predictions = np.array([r.predicted for r in records])
        actuals = np.array([r.actual for r in records])
        
        # Calculate returns based on predictions vs actuals
        returns = (actuals - predictions) / np.abs(predictions)
        
        if len(returns) == 0:
            return {'sharpe_ratio': 0.0, 'sortino_ratio': 0.0, 'calmar_ratio': 0.0, 'information_ratio': 0.0}
        
        # Mean and std of returns
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe Ratio
        excess_return = mean_return - (self.risk_free_rate / 252)  # Daily risk-free rate
        sharpe_ratio = excess_return / std_return if std_return > 0 else 0.0
        
        # Sortino Ratio (downside deviation)
        negative_returns = returns[returns < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else std_return
        sortino_ratio = excess_return / downside_std if downside_std > 0 else 0.0
        
        # Max Drawdown for Calmar
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0.0
        
        # Calmar Ratio
        calmar_ratio = mean_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
        
        # Information Ratio (vs benchmark of 0)
        tracking_error = std_return
        information_ratio = mean_return / tracking_error if tracking_error > 0 else 0.0
        
        return {
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sortino_ratio': round(sortino_ratio, 3),
            'calmar_ratio': round(calmar_ratio, 3),
            'information_ratio': round(information_ratio, 3)
        }
    
    def _calculate_risk_metrics(self, records: List[PredictionRecord]) -> Dict[str, float]:
        """Calculate risk metrics"""
        predictions = np.array([r.predicted for r in records])
        actuals = np.array([r.actual for r in records])
        
        # Calculate returns
        returns = (actuals - predictions) / np.abs(predictions)
        
        if len(returns) == 0:
            return {'max_drawdown': 0.0, 'var_95': 0.0, 'var_99': 0.0, 'volatility': 0.0}
        
        # Max Drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = (cumulative_returns - running_max) / running_max
        max_drawdown = abs(np.min(drawdowns)) * 100 if len(drawdowns) > 0 else 0.0
        
        # VaR calculations
        var_95 = abs(np.percentile(returns, 5)) * 100
        var_99 = abs(np.percentile(returns, 1)) * 100
        
        # Volatility (annualized)
        volatility = np.std(returns) * np.sqrt(252) * 100
        
        return {
            'max_drawdown': round(max_drawdown, 2),
            'var_95': round(var_95, 2),
            'var_99': round(var_99, 2),
            'volatility': round(volatility, 2)
        }
    
    def _calculate_quality_metrics(self, records: List[PredictionRecord]) -> Dict[str, float]:
        """Calculate prediction quality metrics"""
        predictions = np.array([r.predicted for r in records])
        actuals = np.array([r.actual for r in records])
        
        # Calibration Error (simplified)
        prediction_errors = np.abs(predictions - actuals) / np.abs(actuals)
        confidences = np.array([r.confidence or 70.0 for r in records]) / 100.0
        
        # Bin predictions by confidence and calculate calibration
        calibration_error = np.mean(np.abs(confidences - (prediction_errors <= self.tolerance).astype(float)))
        
        # Coverage Ratio (how often predictions are within reasonable bounds)
        coverage_ratio = np.mean(prediction_errors <= 0.2) * 100  # 20% tolerance
        
        # Bias (systematic over/under prediction)
        bias = np.mean((predictions - actuals) / actuals) * 100
        
        return {
            'calibration_error': round(calibration_error, 3),
            'coverage_ratio': round(coverage_ratio, 2),
            'bias': round(bias, 2)
        }
    
    def _determine_status(self, results: KPIResults) -> str:
        """Determine overall status based on KPI thresholds"""
        score = 0
        total_checks = 0
        
        # Brier Score (lower is better)
        if results.brier_score <= 0.15:
            score += 2
        elif results.brier_score <= 0.25:
            score += 1
        total_checks += 2
        
        # Directional Accuracy (higher is better)
        if results.directional_accuracy >= 70:
            score += 2
        elif results.directional_accuracy >= 60:
            score += 1
        total_checks += 2
        
        # Sharpe Ratio (higher is better)
        if results.sharpe_ratio >= 1.0:
            score += 2
        elif results.sharpe_ratio >= 0.5:
            score += 1
        total_checks += 2
        
        # Max Drawdown (lower is better)
        if results.max_drawdown <= 10:
            score += 2
        elif results.max_drawdown <= 20:
            score += 1
        total_checks += 2
        
        # Hit Rate (higher is better)
        if results.hit_rate >= 75:
            score += 2
        elif results.hit_rate >= 65:
            score += 1
        total_checks += 2
        
        # Calculate percentage
        percentage = (score / total_checks) * 100 if total_checks > 0 else 0
        
        if percentage >= 70:
            return "green"
        elif percentage >= 50:
            return "amber"
        else:
            return "red"
    
    def _empty_kpi_results(self, timeframe: str, sample_size: int) -> KPIResults:
        """Return empty KPI results for error cases"""
        return KPIResults(
            timeframe=timeframe,
            sample_size=sample_size,
            brier_score=1.0,
            directional_accuracy=50.0,
            mape=100.0,
            rmse=0.0,
            hit_rate=0.0,
            sharpe_ratio=0.0,
            sortino_ratio=0.0,
            calmar_ratio=0.0,
            information_ratio=0.0,
            max_drawdown=0.0,
            var_95=0.0,
            var_99=0.0,
            volatility=0.0,
            calibration_error=1.0,
            coverage_ratio=0.0,
            bias=0.0,
            status="insufficient_data"
        )

def calculate_timeframe_kpis(predictions: List[Dict[str, Any]], timeframe: str) -> Dict[str, Any]:
    """Convenience function to calculate KPIs and return as dict"""
    calculator = KPICalculator()
    results = calculator.calculate_kpis(predictions, timeframe)
    
    return {
        'timeframe': results.timeframe,
        'sample_size': results.sample_size,
        'prediction_kpis': {
            'brier_score': results.brier_score,
            'directional_accuracy': results.directional_accuracy,
            'mape': results.mape,
            'rmse': results.rmse,
            'hit_rate': results.hit_rate
        },
        'financial_kpis': {
            'sharpe_ratio': results.sharpe_ratio,
            'sortino_ratio': results.sortino_ratio,
            'calmar_ratio': results.calmar_ratio,
            'information_ratio': results.information_ratio
        },
        'risk_kpis': {
            'max_drawdown': results.max_drawdown,
            'var_95': results.var_95,
            'var_99': results.var_99,
            'volatility': results.volatility
        },
        'quality_kpis': {
            'calibration_error': results.calibration_error,
            'coverage_ratio': results.coverage_ratio,
            'bias': results.bias
        },
        'status': results.status
    }

# Export main classes and functions
__all__ = ['KPICalculator', 'KPIResults', 'PredictionRecord', 'calculate_timeframe_kpis']
