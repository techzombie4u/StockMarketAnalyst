
"""
Shared KPI Service
Computes prediction quality, financial, and risk KPIs per timeframe
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from common_repository.config.feature_flags import feature_flags
from common_repository.utils.date_utils import get_ist_now
from common_repository.utils.math_utils import safe_divide
from common_repository.storage.json_store import json_store

logger = logging.getLogger(__name__)

@dataclass
class KPITrigger:
    """Represents a GoAhead trigger"""
    type: str  # RETRAIN, TIGHTEN_RISK, THROTTLE
    product: str
    timeframe: str
    reason: str
    severity: str = "medium"
    timestamp: str = None

class KPIService:
    """Shared KPI calculation service"""
    
    def __init__(self):
        self.name = "kpi_service"
        self.timeframes = ["3D", "5D", "10D", "15D", "30D"]
        self.thresholds = self._load_thresholds()
        
    def _load_thresholds(self) -> Dict[str, Any]:
        """Load KPI thresholds from config"""
        try:
            with open("src/common_repository/config/kpi_thresholds.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading KPI thresholds: {e}")
            return {
                "targets": {
                    "brier": {"3D": 0.18, "5D": 0.18, "10D": 0.22, "15D": 0.22, "30D": 0.22},
                    "hit_rate": {"all": 0.62},
                    "sharpe": {"all": 1.2},
                    "sortino": {"all": 2.0},
                    "max_dd": {"all": 0.05},
                    "var_95": {"all": 0.005}
                },
                "colors": {"good": "green", "warn": "amber", "bad": "red"},
                "warn_bands": {"pct": 0.1}
            }
    
    def compute(self, timeframe: str = "All", product: Optional[str] = None) -> Dict[str, Any]:
        """Compute KPIs for given timeframe and product"""
        try:
            logger.info(f"Computing KPIs for timeframe={timeframe}, product={product}")
            
            # Load prediction and trade data
            predictions = self._load_predictions(timeframe, product)
            trades = self._load_trades(timeframe, product)
            
            # Compute KPI categories
            prediction_kpis = self._compute_prediction_kpis(predictions, timeframe)
            financial_kpis = self._compute_financial_kpis(trades, timeframe)
            risk_kpis = self._compute_risk_kpis(trades, timeframe)
            
            # Combine results
            kpis = {
                "timeframe": timeframe,
                "product": product or "all",
                "last_updated": get_ist_now().isoformat(),
                "prediction_quality": prediction_kpis,
                "financial": financial_kpis,
                "risk": risk_kpis,
                "sample_size": len(predictions)
            }
            
            # Add trend information
            kpis = self._add_trend_data(kpis, timeframe, product)
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error computing KPIs: {e}")
            return self._get_empty_kpis(timeframe, product)
    
    def _load_predictions(self, timeframe: str, product: Optional[str]) -> List[Dict]:
        """Load predictions for KPI calculation"""
        try:
            # Load from predictions history or tracking data
            predictions_data = json_store.load('predictions_history') or []
            
            # Filter by timeframe and product if specified
            filtered = []
            cutoff_date = self._get_timeframe_cutoff(timeframe)
            
            for pred in predictions_data:
                if cutoff_date and pred.get('timestamp'):
                    pred_date = datetime.fromisoformat(pred['timestamp'].replace('Z', '+00:00'))
                    if pred_date < cutoff_date:
                        continue
                
                if product and pred.get('product', '').lower() != product.lower():
                    continue
                    
                filtered.append(pred)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error loading predictions: {e}")
            return []
    
    def _load_trades(self, timeframe: str, product: Optional[str]) -> List[Dict]:
        """Load trade data for financial KPIs"""
        try:
            # Load from trade history (stubbed for now)
            trades_data = json_store.load('trades_history') or []
            
            # Filter similar to predictions
            filtered = []
            cutoff_date = self._get_timeframe_cutoff(timeframe)
            
            for trade in trades_data:
                if cutoff_date and trade.get('timestamp'):
                    trade_date = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                    if trade_date < cutoff_date:
                        continue
                
                if product and trade.get('product', '').lower() != product.lower():
                    continue
                    
                filtered.append(trade)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            return []
    
    def _get_timeframe_cutoff(self, timeframe: str) -> Optional[datetime]:
        """Get cutoff date for timeframe filtering"""
        if timeframe == "All":
            return None
            
        days_map = {"3D": 3, "5D": 5, "10D": 10, "15D": 15, "30D": 30}
        days = days_map.get(timeframe)
        
        if days:
            return get_ist_now() - timedelta(days=days)
        
        return None
    
    def _compute_prediction_kpis(self, predictions: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Compute prediction quality KPIs"""
        if not predictions:
            return {
                "brier_score": 0.0,
                "hit_rate": 0.0,
                "calibration_error": 0.0,
                "top_decile_hit_rate": 0.0,
                "top_decile_edge": 0.0,
                "status": "insufficient_data"
            }
        
        # Calculate Brier Score (simplified)
        brier_scores = []
        correct_predictions = 0
        high_confidence_correct = 0
        high_confidence_total = 0
        
        for pred in predictions:
            confidence = pred.get('confidence', 50) / 100.0
            actual = pred.get('actual_direction', pred.get('predicted_direction', 'HOLD'))
            predicted = pred.get('predicted_direction', 'HOLD')
            
            # Brier score calculation (simplified)
            if actual in ['BUY', 'SELL'] and predicted in ['BUY', 'SELL']:
                prob = confidence if predicted == actual else (1 - confidence)
                outcome = 1 if predicted == actual else 0
                brier_scores.append((prob - outcome) ** 2)
                
                if predicted == actual:
                    correct_predictions += 1
                
                # Top decile (high confidence predictions)
                if confidence >= 0.8:
                    high_confidence_total += 1
                    if predicted == actual:
                        high_confidence_correct += 1
        
        brier_score = sum(brier_scores) / len(brier_scores) if brier_scores else 0.0
        hit_rate = correct_predictions / len(predictions) if predictions else 0.0
        top_decile_hit_rate = safe_divide(high_confidence_correct, high_confidence_total, 0.0)
        
        return {
            "brier_score": round(brier_score, 4),
            "hit_rate": round(hit_rate, 4),
            "calibration_error": 0.05,  # Stub for now
            "top_decile_hit_rate": round(top_decile_hit_rate, 4),
            "top_decile_edge": round(top_decile_hit_rate - hit_rate, 4),
            "sample_size": len(predictions),
            "status": "computed"
        }
    
    def _compute_financial_kpis(self, trades: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Compute financial performance KPIs"""
        if not trades:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "win_loss_expectancy": 0.0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
                "status": "insufficient_data"
            }
        
        # Calculate returns and P&L
        returns = []
        pnl_values = []
        wins = 0
        
        for trade in trades:
            pnl = trade.get('pnl', 0.0)
            if pnl != 0:
                pnl_values.append(pnl)
                returns.append(pnl / trade.get('entry_price', 100.0))  # Normalized return
                if pnl > 0:
                    wins += 1
        
        if not returns:
            return self._get_empty_financial_kpis()
        
        # Sharpe ratio (simplified)
        avg_return = sum(returns) / len(returns)
        return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe = safe_divide(avg_return, return_std, 0.0) * (252 ** 0.5)  # Annualized
        
        # Sortino ratio (downside deviation only)
        downside_returns = [r for r in returns if r < 0]
        downside_std = (sum(r ** 2 for r in downside_returns) / len(downside_returns)) ** 0.5 if downside_returns else 0.0
        sortino = safe_divide(avg_return, downside_std, 0.0) * (252 ** 0.5)
        
        return {
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "win_loss_expectancy": round(avg_return, 4),
            "total_pnl": round(sum(pnl_values), 2),
            "win_rate": round(wins / len(trades), 4),
            "avg_return": round(avg_return * 100, 2),
            "status": "computed"
        }
    
    def _compute_risk_kpis(self, trades: List[Dict], timeframe: str) -> Dict[str, Any]:
        """Compute risk management KPIs"""
        if not trades:
            return {
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "var_99": 0.0,
                "avg_exposure": 0.0,
                "status": "insufficient_data"
            }
        
        # Calculate drawdowns
        pnl_values = [trade.get('pnl', 0.0) for trade in trades]
        cumulative_pnl = []
        running_sum = 0
        
        for pnl in pnl_values:
            running_sum += pnl
            cumulative_pnl.append(running_sum)
        
        # Max drawdown
        max_dd = 0.0
        peak = 0.0
        for pnl in cumulative_pnl:
            peak = max(peak, pnl)
            drawdown = (peak - pnl) / abs(peak) if peak != 0 else 0.0
            max_dd = max(max_dd, drawdown)
        
        # VaR calculation (simplified percentile)
        if len(pnl_values) >= 20:
            sorted_pnl = sorted(pnl_values)
            var_95_idx = int(0.05 * len(sorted_pnl))
            var_99_idx = int(0.01 * len(sorted_pnl))
            var_95 = abs(sorted_pnl[var_95_idx]) if var_95_idx < len(sorted_pnl) else 0.0
            var_99 = abs(sorted_pnl[var_99_idx]) if var_99_idx < len(sorted_pnl) else 0.0
        else:
            var_95 = var_99 = 0.0
        
        return {
            "max_drawdown": round(max_dd, 4),
            "var_95": round(var_95, 4),
            "var_99": round(var_99, 4),
            "avg_exposure": round(sum(trade.get('exposure', 0.0) for trade in trades) / len(trades), 2),
            "sample_size": len(trades),
            "status": "computed"
        }
    
    def _add_trend_data(self, kpis: Dict[str, Any], timeframe: str, product: Optional[str]) -> Dict[str, Any]:
        """Add trend arrows and delta information"""
        try:
            # Load historical KPIs
            history_key = f"kpi_history_{timeframe}_{product or 'all'}"
            history = json_store.load(history_key) or []
            
            # Add current snapshot to history
            history.append({
                "timestamp": kpis["last_updated"],
                "kpis": kpis.copy()
            })
            
            # Keep only last 10 snapshots
            history = history[-10:]
            json_store.save(history_key, history)
            
            # Calculate trends if we have previous data
            if len(history) >= 2:
                current = history[-1]["kpis"]
                previous = history[-2]["kpis"]
                
                kpis["trends"] = self._calculate_trends(current, previous)
            else:
                kpis["trends"] = {}
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error adding trend data: {e}")
            kpis["trends"] = {}
            return kpis
    
    def _calculate_trends(self, current: Dict, previous: Dict) -> Dict[str, Dict]:
        """Calculate trend direction and delta for KPIs"""
        trends = {}
        
        # Define KPIs to track trends for
        kpi_paths = [
            ("prediction_quality.hit_rate", "up_is_better"),
            ("prediction_quality.brier_score", "down_is_better"),
            ("financial.sharpe_ratio", "up_is_better"),
            ("financial.win_rate", "up_is_better"),
            ("risk.max_drawdown", "down_is_better"),
            ("risk.var_95", "down_is_better")
        ]
        
        for path, direction_preference in kpi_paths:
            try:
                current_val = self._get_nested_value(current, path)
                previous_val = self._get_nested_value(previous, path)
                
                if current_val is not None and previous_val is not None:
                    delta = current_val - previous_val
                    
                    if abs(delta) < 0.001:  # Minimal change threshold
                        trend = "flat"
                        arrow = "→"
                    elif delta > 0:
                        trend = "up"
                        arrow = "↑"
                    else:
                        trend = "down"
                        arrow = "↓"
                    
                    trends[path.replace(".", "_")] = {
                        "direction": trend,
                        "arrow": arrow,
                        "delta": round(delta, 4),
                        "delta_pct": round((delta / abs(previous_val)) * 100, 2) if previous_val != 0 else 0
                    }
                    
            except Exception as e:
                logger.error(f"Error calculating trend for {path}: {e}")
                continue
        
        return trends
    
    def _get_nested_value(self, data: Dict, path: str) -> Optional[float]:
        """Get nested dictionary value by dot notation path"""
        try:
            keys = path.split('.')
            value = data
            for key in keys:
                value = value[key]
            return float(value) if value is not None else None
        except (KeyError, TypeError, ValueError):
            return None
    
    def evaluate_triggers(self, kpis: Dict[str, Any]) -> List[KPITrigger]:
        """Evaluate GoAhead triggers based on KPI values"""
        if not feature_flags.is_enabled('enable_goahead_triggers'):
            return []
        
        triggers = []
        timeframe = kpis.get("timeframe", "All")
        product = kpis.get("product", "all")
        
        try:
            # Check retrain triggers
            prediction_kpis = kpis.get("prediction_quality", {})
            hit_rate = prediction_kpis.get("hit_rate", 0.0)
            brier_score = prediction_kpis.get("brier_score", 0.0)
            
            # Hit rate drop trigger
            target_hit_rate = self.thresholds["targets"]["hit_rate"]["all"]
            if hit_rate < (target_hit_rate * 0.9):  # 10% below target
                triggers.append(KPITrigger(
                    type="RETRAIN",
                    product=product,
                    timeframe=timeframe,
                    reason=f"Hit rate {hit_rate:.1%} below target {target_hit_rate:.1%}",
                    severity="high",
                    timestamp=get_ist_now().isoformat()
                ))
            
            # Brier score deterioration
            target_brier = self.thresholds["targets"]["brier"].get(timeframe, 0.22)
            if brier_score > (target_brier * 1.2):  # 20% above target
                triggers.append(KPITrigger(
                    type="RETRAIN",
                    product=product,
                    timeframe=timeframe,
                    reason=f"Brier score {brier_score:.3f} above target {target_brier:.3f}",
                    severity="medium",
                    timestamp=get_ist_now().isoformat()
                ))
            
            # Risk triggers
            risk_kpis = kpis.get("risk", {})
            max_dd = risk_kpis.get("max_drawdown", 0.0)
            var_95 = risk_kpis.get("var_95", 0.0)
            
            target_max_dd = self.thresholds["targets"]["max_dd"]["all"]
            target_var_95 = self.thresholds["targets"]["var_95"]["all"]
            
            if max_dd > target_max_dd:
                triggers.append(KPITrigger(
                    type="TIGHTEN_RISK",
                    product=product,
                    timeframe=timeframe,
                    reason=f"Max drawdown {max_dd:.1%} exceeds limit {target_max_dd:.1%}",
                    severity="high",
                    timestamp=get_ist_now().isoformat()
                ))
            
            if var_95 > target_var_95:
                triggers.append(KPITrigger(
                    type="TIGHTEN_RISK",
                    product=product,
                    timeframe=timeframe,
                    reason=f"VaR 95% {var_95:.3f} exceeds limit {target_var_95:.3f}",
                    severity="medium",
                    timestamp=get_ist_now().isoformat()
                ))
            
            # Throttling triggers
            financial_kpis = kpis.get("financial", {})
            sharpe = financial_kpis.get("sharpe_ratio", 0.0)
            target_sharpe = self.thresholds["targets"]["sharpe"]["all"]
            
            if sharpe < target_sharpe:
                triggers.append(KPITrigger(
                    type="THROTTLE",
                    product=product,
                    timeframe=timeframe,
                    reason=f"Sharpe ratio {sharpe:.2f} below target {target_sharpe:.2f}",
                    severity="low",
                    timestamp=get_ist_now().isoformat()
                ))
            
        except Exception as e:
            logger.error(f"Error evaluating triggers: {e}")
        
        return triggers
    
    def _get_empty_kpis(self, timeframe: str, product: Optional[str]) -> Dict[str, Any]:
        """Return empty KPI structure"""
        return {
            "timeframe": timeframe,
            "product": product or "all",
            "last_updated": get_ist_now().isoformat(),
            "prediction_quality": {
                "brier_score": 0.0,
                "hit_rate": 0.0,
                "calibration_error": 0.0,
                "top_decile_hit_rate": 0.0,
                "top_decile_edge": 0.0,
                "status": "no_data"
            },
            "financial": self._get_empty_financial_kpis(),
            "risk": {
                "max_drawdown": 0.0,
                "var_95": 0.0,
                "var_99": 0.0,
                "avg_exposure": 0.0,
                "status": "no_data"
            },
            "sample_size": 0,
            "trends": {}
        }
    
    def _get_empty_financial_kpis(self) -> Dict[str, Any]:
        """Return empty financial KPIs"""
        return {
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "win_loss_expectancy": 0.0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "status": "no_data"
        }

# Global singleton
kpi_service = KPIService()
