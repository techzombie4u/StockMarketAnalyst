
"""
KPI Calculator - Multi-timeframe prediction and financial metrics
Computes Brier Score, Hit-Rate, Calibration Error, Sharpe, Sortino, VaR, etc.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, asdict

from src.common_repository.config.runtime import (
    KPI_ROLLING_WINDOW_DAYS, KPI_MIN_SAMPLES, get_market_tz
)
from src.common_repository.storage.json_store import json_store

logger = logging.getLogger(__name__)

@dataclass
class KPIMetrics:
    """Data class for KPI metrics structure"""
    timeframe: str
    total_predictions: int
    closed_predictions: int
    insufficient_data: bool
    brier_score: Optional[float] = None
    directional_hit_rate: Optional[float] = None
    calibration_error: Optional[float] = None
    top_decile_hit_rate: Optional[float] = None
    top_decile_avg_edge: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    win_loss_expectancy: Optional[float] = None
    max_drawdown: Optional[float] = None
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    exposure_per_trade: Optional[float] = None
    status: str = "unknown"  # green/amber/red

@dataclass
class OpenPredictionSignal:
    """Data class for open prediction monitoring"""
    symbol: str
    timeframe: str
    predicted_path_deviation: float
    percent_to_sl: float
    elapsed_vs_due: float
    early_warning: bool

class KPICalculator:
    """Multi-timeframe KPI calculator with atomic writes and version retention"""
    
    def __init__(self):
        self.kpi_file = 'data/runtime/kpi_metrics.json'
        self.open_signals_file = 'data/runtime/kpi_open_signals.json'
        self.backup_dir = 'data/backup/kpi'
        self.max_versions = 7
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.kpi_file), exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def load_predictions_data(self) -> List[Dict[str, Any]]:
        """Load prediction data from various sources"""
        try:
            predictions = []
            
            # Load from tracking data
            tracking_data = json_store.load('interactive_tracking', {})
            for symbol, data in tracking_data.items():
                if isinstance(data, dict):
                    predictions.extend(self._extract_predictions_from_tracking(symbol, data))
            
            # Load from prediction history
            history_data = json_store.load('predictions_history', [])
            if isinstance(history_data, list):
                predictions.extend(history_data)
            
            # Load from backtesting data
            backtest_data = json_store.load('backtesting_results', {})
            if isinstance(backtest_data, dict) and 'predictions' in backtest_data:
                predictions.extend(backtest_data['predictions'])
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error loading predictions data: {str(e)}")
            return []
    
    def _extract_predictions_from_tracking(self, symbol: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract predictions from tracking data"""
        predictions = []
        
        try:
            # Extract 5D predictions
            if data.get('predicted_5d') and data.get('actual_progress_5d'):
                pred_5d = data['predicted_5d']
                actual_5d = data['actual_progress_5d']
                
                if len(actual_5d) >= 5 and actual_5d[4] is not None:
                    predictions.append({
                        'symbol': symbol,
                        'timeframe': '5D',
                        'predicted_value': pred_5d[-1] if pred_5d else 0,
                        'actual_value': actual_5d[4],
                        'start_date': data.get('lock_start_date_5d'),
                        'due_date': self._calculate_due_date(data.get('lock_start_date_5d'), 5),
                        'resolved': True,
                        'confidence': data.get('confidence', 75.0)
                    })
            
            # Extract 30D predictions
            if data.get('predicted_30d') and data.get('actual_progress_30d'):
                pred_30d = data['predicted_30d']
                actual_30d = data['actual_progress_30d']
                
                if len(actual_30d) >= 30 and actual_30d[29] is not None:
                    predictions.append({
                        'symbol': symbol,
                        'timeframe': '30D',
                        'predicted_value': pred_30d[-1] if pred_30d else 0,
                        'actual_value': actual_30d[29],
                        'start_date': data.get('lock_start_date_30d'),
                        'due_date': self._calculate_due_date(data.get('lock_start_date_30d'), 30),
                        'resolved': True,
                        'confidence': data.get('confidence', 75.0)
                    })
                        
        except Exception as e:
            logger.error(f"Error extracting predictions for {symbol}: {str(e)}")
        
        return predictions
    
    def _calculate_due_date(self, start_date_str: Optional[str], days: int) -> Optional[str]:
        """Calculate due date from start date"""
        if not start_date_str:
            return None
        
        try:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            due_date = start_date + timedelta(days=days)
            return due_date.isoformat()
        except Exception:
            return None
    
    def calculate_brier_score(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate Brier Score for probability predictions"""
        try:
            if not predictions:
                return 1.0  # Worst possible score
            
            total_score = 0.0
            count = 0
            
            for pred in predictions:
                confidence = pred.get('confidence', 50.0) / 100.0  # Convert to probability
                predicted_val = pred.get('predicted_value', 0)
                actual_val = pred.get('actual_value', 0)
                
                if predicted_val != 0 and actual_val != 0:
                    # Binary outcome: prediction was correct (1) or not (0)
                    correct = 1 if abs(actual_val - predicted_val) / abs(predicted_val) <= 0.05 else 0
                    total_score += (confidence - correct) ** 2
                    count += 1
            
            return total_score / count if count > 0 else 1.0
            
        except Exception as e:
            logger.error(f"Error calculating Brier score: {str(e)}")
            return 1.0
    
    def calculate_directional_hit_rate(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate directional hit rate"""
        try:
            if not predictions:
                return 0.0
            
            correct_direction = 0
            total = 0
            
            for pred in predictions:
                predicted_val = pred.get('predicted_value', 0)
                actual_val = pred.get('actual_value', 0)
                start_val = pred.get('start_value', predicted_val * 0.95)  # Estimate if not available
                
                if predicted_val != 0 and actual_val != 0 and start_val != 0:
                    predicted_direction = 1 if predicted_val > start_val else -1
                    actual_direction = 1 if actual_val > start_val else -1
                    
                    if predicted_direction == actual_direction:
                        correct_direction += 1
                    total += 1
            
            return (correct_direction / total * 100) if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating directional hit rate: {str(e)}")
            return 0.0
    
    def calculate_financial_metrics(self, predictions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate Sharpe, Sortino, Win/Loss expectancy, Max Drawdown"""
        try:
            if not predictions:
                return {'sharpe': 0.0, 'sortino': 0.0, 'win_loss_expectancy': 0.0, 'max_drawdown': 0.0}
            
            returns = []
            cumulative_returns = [0]
            
            for pred in predictions:
                predicted_val = pred.get('predicted_value', 0)
                actual_val = pred.get('actual_value', 0)
                start_val = pred.get('start_value', predicted_val * 0.95)
                
                if predicted_val != 0 and actual_val != 0 and start_val != 0:
                    actual_return = (actual_val - start_val) / start_val
                    returns.append(actual_return)
                    cumulative_returns.append(cumulative_returns[-1] + actual_return)
            
            if not returns:
                return {'sharpe': 0.0, 'sortino': 0.0, 'win_loss_expectancy': 0.0, 'max_drawdown': 0.0}
            
            # Sharpe ratio (assuming 5% risk-free rate)
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe = (mean_return - 0.05) / std_return if std_return > 0 else 0.0
            
            # Sortino ratio (downside deviation)
            negative_returns = [r for r in returns if r < 0]
            downside_std = np.std(negative_returns) if negative_returns else std_return
            sortino = (mean_return - 0.05) / downside_std if downside_std > 0 else 0.0
            
            # Win/Loss expectancy
            wins = [r for r in returns if r > 0]
            losses = [r for r in returns if r < 0]
            win_rate = len(wins) / len(returns) if returns else 0
            avg_win = np.mean(wins) if wins else 0
            avg_loss = abs(np.mean(losses)) if losses else 1
            win_loss_expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
            
            # Max drawdown
            peak = cumulative_returns[0]
            max_drawdown = 0
            for value in cumulative_returns:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak != 0 else 0
                max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'sharpe': sharpe,
                'sortino': sortino,
                'win_loss_expectancy': win_loss_expectancy,
                'max_drawdown': max_drawdown * 100  # Convert to percentage
            }
            
        except Exception as e:
            logger.error(f"Error calculating financial metrics: {str(e)}")
            return {'sharpe': 0.0, 'sortino': 0.0, 'win_loss_expectancy': 0.0, 'max_drawdown': 0.0}
    
    def calculate_risk_metrics(self, predictions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate VaR and exposure metrics"""
        try:
            if not predictions:
                return {'var_95': 0.0, 'var_99': 0.0, 'exposure_per_trade': 0.0}
            
            returns = []
            exposures = []
            
            for pred in predictions:
                predicted_val = pred.get('predicted_value', 0)
                actual_val = pred.get('actual_value', 0)
                start_val = pred.get('start_value', predicted_val * 0.95)
                exposure = pred.get('exposure', start_val)
                
                if predicted_val != 0 and actual_val != 0 and start_val != 0:
                    actual_return = (actual_val - start_val) / start_val
                    returns.append(actual_return)
                    exposures.append(exposure)
            
            if not returns:
                return {'var_95': 0.0, 'var_99': 0.0, 'exposure_per_trade': 0.0}
            
            # VaR calculations
            var_95 = np.percentile(returns, 5) * 100  # 5th percentile (95% VaR)
            var_99 = np.percentile(returns, 1) * 100  # 1st percentile (99% VaR)
            
            # Average exposure per trade
            avg_exposure = np.mean(exposures)
            
            return {
                'var_95': abs(var_95),  # Make positive for clarity
                'var_99': abs(var_99),
                'exposure_per_trade': avg_exposure
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {str(e)}")
            return {'var_95': 0.0, 'var_99': 0.0, 'exposure_per_trade': 0.0}
    
    def determine_status(self, metrics: KPIMetrics) -> str:
        """Determine status color based on thresholds"""
        try:
            # Define thresholds
            thresholds = {
                'brier_score': {'green': 0.15, 'amber': 0.25},  # Lower is better
                'directional_hit_rate': {'green': 70, 'amber': 60},  # Higher is better
                'sharpe_ratio': {'green': 1.0, 'amber': 0.5},  # Higher is better
                'max_drawdown': {'green': 10, 'amber': 20}  # Lower is better
            }
            
            scores = []
            
            # Brier Score
            if metrics.brier_score is not None:
                if metrics.brier_score <= thresholds['brier_score']['green']:
                    scores.append(2)  # Green
                elif metrics.brier_score <= thresholds['brier_score']['amber']:
                    scores.append(1)  # Amber
                else:
                    scores.append(0)  # Red
            
            # Directional Hit Rate
            if metrics.directional_hit_rate is not None:
                if metrics.directional_hit_rate >= thresholds['directional_hit_rate']['green']:
                    scores.append(2)
                elif metrics.directional_hit_rate >= thresholds['directional_hit_rate']['amber']:
                    scores.append(1)
                else:
                    scores.append(0)
            
            # Sharpe Ratio
            if metrics.sharpe_ratio is not None:
                if metrics.sharpe_ratio >= thresholds['sharpe_ratio']['green']:
                    scores.append(2)
                elif metrics.sharpe_ratio >= thresholds['sharpe_ratio']['amber']:
                    scores.append(1)
                else:
                    scores.append(0)
            
            # Max Drawdown
            if metrics.max_drawdown is not None:
                if metrics.max_drawdown <= thresholds['max_drawdown']['green']:
                    scores.append(2)
                elif metrics.max_drawdown <= thresholds['max_drawdown']['amber']:
                    scores.append(1)
                else:
                    scores.append(0)
            
            if not scores:
                return "unknown"
            
            avg_score = sum(scores) / len(scores)
            
            if avg_score >= 1.5:
                return "green"
            elif avg_score >= 0.5:
                return "amber"
            else:
                return "red"
                
        except Exception as e:
            logger.error(f"Error determining status: {str(e)}")
            return "unknown"
    
    def calculate_timeframe_metrics(self, timeframe: str, predictions: List[Dict[str, Any]]) -> KPIMetrics:
        """Calculate metrics for a specific timeframe"""
        try:
            # Filter predictions for this timeframe
            tf_predictions = [p for p in predictions if p.get('timeframe') == timeframe]
            closed_predictions = [p for p in tf_predictions if p.get('resolved', False)]
            
            min_samples = KPI_MIN_SAMPLES.get(timeframe, 5)
            insufficient_data = len(closed_predictions) < min_samples
            
            metrics = KPIMetrics(
                timeframe=timeframe,
                total_predictions=len(tf_predictions),
                closed_predictions=len(closed_predictions),
                insufficient_data=insufficient_data
            )
            
            if not insufficient_data and closed_predictions:
                # Calculate prediction metrics
                metrics.brier_score = self.calculate_brier_score(closed_predictions)
                metrics.directional_hit_rate = self.calculate_directional_hit_rate(closed_predictions)
                
                # Calculate financial metrics
                financial_metrics = self.calculate_financial_metrics(closed_predictions)
                metrics.sharpe_ratio = financial_metrics['sharpe']
                metrics.sortino_ratio = financial_metrics['sortino']
                metrics.win_loss_expectancy = financial_metrics['win_loss_expectancy']
                metrics.max_drawdown = financial_metrics['max_drawdown']
                
                # Calculate risk metrics
                risk_metrics = self.calculate_risk_metrics(closed_predictions)
                metrics.var_95 = risk_metrics['var_95']
                metrics.var_99 = risk_metrics['var_99']
                metrics.exposure_per_trade = risk_metrics['exposure_per_trade']
                
                # Determine status
                metrics.status = self.determine_status(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating metrics for {timeframe}: {str(e)}")
            return KPIMetrics(
                timeframe=timeframe,
                total_predictions=0,
                closed_predictions=0,
                insufficient_data=True,
                status="error"
            )
    
    def backup_previous_version(self):
        """Backup previous KPI file version"""
        try:
            if os.path.exists(self.kpi_file):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = os.path.join(self.backup_dir, f'kpi_metrics_{timestamp}.json')
                shutil.copy2(self.kpi_file, backup_file)
                
                # Clean old backups (keep only last 7)
                backups = sorted([f for f in os.listdir(self.backup_dir) if f.startswith('kpi_metrics_')])
                while len(backups) > self.max_versions:
                    old_backup = backups.pop(0)
                    os.remove(os.path.join(self.backup_dir, old_backup))
                    
        except Exception as e:
            logger.error(f"Error backing up KPI file: {str(e)}")
    
    def write_kpi_metrics_atomic(self, kpi_data: Dict[str, Any]):
        """Write KPI metrics atomically using temp file + rename"""
        try:
            temp_file = self.kpi_file + '.tmp'
            
            with open(temp_file, 'w') as f:
                json.dump(kpi_data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            os.rename(temp_file, self.kpi_file)
            
            logger.info(f"KPI metrics written atomically to {self.kpi_file}")
            
        except Exception as e:
            logger.error(f"Error writing KPI metrics: {str(e)}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def full_recompute(self) -> bool:
        """Full KPI recomputation (heavy job, after market hours)"""
        try:
            logger.info("Starting full KPI recompute...")
            
            # Backup previous version
            self.backup_previous_version()
            
            # Load all prediction data
            predictions = self.load_predictions_data()
            
            if not predictions:
                logger.warning("No prediction data found for KPI calculation")
                return False
            
            # Calculate metrics for each timeframe
            timeframes = ["3D", "5D", "10D", "15D", "30D"]
            timeframe_metrics = {}
            
            for tf in timeframes:
                metrics = self.calculate_timeframe_metrics(tf, predictions)
                timeframe_metrics[tf] = asdict(metrics)
            
            # Calculate overall metrics
            overall_metrics = self.calculate_timeframe_metrics("overall", predictions)
            
            # Create final KPI data structure
            kpi_data = {
                'timestamp': datetime.now(get_market_tz()).isoformat(),
                'last_updated': datetime.now(get_market_tz()).strftime('%Y-%m-%d %H:%M:%S IST'),
                'timeframes': timeframe_metrics,
                'overall': asdict(overall_metrics),
                'summary': {
                    'total_predictions': len(predictions),
                    'closed_predictions': len([p for p in predictions if p.get('resolved', False)]),
                    'data_quality': 'excellent' if len(predictions) > 100 else 'good' if len(predictions) > 50 else 'building'
                }
            }
            
            # Write atomically
            self.write_kpi_metrics_atomic(kpi_data)
            
            logger.info(f"✅ Full KPI recompute completed: {len(predictions)} predictions processed")
            return True
            
        except Exception as e:
            logger.error(f"Error in full KPI recompute: {str(e)}")
            return False
    
    def incremental_update(self) -> bool:
        """Incremental KPI update (light job, market hours)"""
        try:
            logger.info("Starting incremental KPI update...")
            
            # Load existing KPI data
            existing_data = {}
            if os.path.exists(self.kpi_file):
                with open(self.kpi_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Update timestamp
            existing_data['last_incremental_update'] = datetime.now(get_market_tz()).isoformat()
            
            # Write back (light update)
            self.write_kpi_metrics_atomic(existing_data)
            
            logger.info("✅ Incremental KPI update completed")
            return True
            
        except Exception as e:
            logger.error(f"Error in incremental KPI update: {str(e)}")
            return False

# Global instance
kpi_calculator = KPICalculator()
