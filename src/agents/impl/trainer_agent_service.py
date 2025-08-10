
"""
Trainer AI Agent Service
Handles intelligent retraining decisions based on KPI trends and prediction outcomes
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from src.common_repository.config.feature_flags import feature_flags
from src.common_repository.storage.json_store import json_store
from src.common_repository.utils.date_utils import get_ist_now

logger = logging.getLogger(__name__)

@dataclass
class TrainerDecision:
    triggered: bool
    reason: str
    actions: List[str]
    product: str
    timeframe: str
    timestamp: str
    confidence_score: float = 0.0
    force_triggered: bool = False

class TrainerAgentService:
    def __init__(self):
        self.config = self._load_config()
        self.history_file = 'data/tracking/trainer_history.json'
        self.decisions_file = 'data/tracking/trainer_decisions.json'
        
    def _load_config(self) -> Dict[str, Any]:
        """Load trainer agent configuration"""
        try:
            from src.common_repository.config.agents import load_agent_config
            config = load_agent_config('trainer_agent')
            return config if config else self._get_default_config()
        except Exception as e:
            logger.warning(f"Failed to load trainer config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default trainer configuration"""
        return {
            'enabled': True,
            'retrain_cooldown_days': 3,
            'triggers': {
                'hit_rate_drop': 0.10,
                'brier_score_thresholds': {
                    'short_term': 0.18,
                    'medium_term': 0.20,
                    'long_term': 0.22
                },
                'confidence_drift': 0.08,
                'max_days_without_retrain': 14
            },
            'actions': [
                {'name': 'retrain_lstm', 'products': ['equities', 'options', 'comm']},
                {'name': 'retrain_rf', 'products': ['equities', 'options', 'comm']}
            ],
            'notify_on_trigger': True
        }
    
    def evaluate_retrain_need(self, product: str, timeframe: str, force: bool = False) -> TrainerDecision:
        """Evaluate if retraining is needed based on triggers"""
        try:
            logger.info(f"Evaluating retrain need for {product} {timeframe}")
            
            # Check if forced
            if force:
                return TrainerDecision(
                    triggered=True,
                    reason="Manual force retrain requested",
                    actions=self._get_actions_for_product(product),
                    product=product,
                    timeframe=timeframe,
                    timestamp=get_ist_now().isoformat(),
                    force_triggered=True
                )
            
            # Check cooldown period
            if self._is_in_cooldown(product, timeframe):
                return TrainerDecision(
                    triggered=False,
                    reason=f"In cooldown period (last retrain < {self.config['retrain_cooldown_days']} days ago)",
                    actions=[],
                    product=product,
                    timeframe=timeframe,
                    timestamp=get_ist_now().isoformat()
                )
            
            # Load KPI data
            kpi_data = self._load_kpi_data(product, timeframe)
            if not kpi_data:
                return TrainerDecision(
                    triggered=False,
                    reason="Insufficient KPI data for evaluation",
                    actions=[],
                    product=product,
                    timeframe=timeframe,
                    timestamp=get_ist_now().isoformat()
                )
            
            # Check triggers
            trigger_result = self._check_triggers(kpi_data, product, timeframe)
            
            if trigger_result['triggered']:
                return TrainerDecision(
                    triggered=True,
                    reason=trigger_result['reason'],
                    actions=self._get_actions_for_product(product),
                    product=product,
                    timeframe=timeframe,
                    timestamp=get_ist_now().isoformat(),
                    confidence_score=trigger_result.get('confidence', 0.8)
                )
            
            return TrainerDecision(
                triggered=False,
                reason="All triggers within acceptable thresholds",
                actions=[],
                product=product,
                timeframe=timeframe,
                timestamp=get_ist_now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error evaluating retrain need: {e}")
            return TrainerDecision(
                triggered=False,
                reason=f"Error during evaluation: {str(e)}",
                actions=[],
                product=product,
                timeframe=timeframe,
                timestamp=get_ist_now().isoformat()
            )
    
    def _check_triggers(self, kpi_data: Dict, product: str, timeframe: str) -> Dict[str, Any]:
        """Check all trigger conditions"""
        triggers = self.config['triggers']
        
        # 1. Hit Rate Drop Trigger
        hit_rate_trigger = self._check_hit_rate_drop(kpi_data, triggers['hit_rate_drop'])
        if hit_rate_trigger['triggered']:
            return hit_rate_trigger
        
        # 2. Brier Score Trigger
        brier_trigger = self._check_brier_score(kpi_data, triggers['brier_score_thresholds'], timeframe)
        if brier_trigger['triggered']:
            return brier_trigger
        
        # 3. Confidence Drift Trigger
        confidence_trigger = self._check_confidence_drift(kpi_data, triggers['confidence_drift'])
        if confidence_trigger['triggered']:
            return confidence_trigger
        
        # 4. Time-based Trigger
        time_trigger = self._check_time_based_trigger(product, timeframe, triggers['max_days_without_retrain'])
        if time_trigger['triggered']:
            return time_trigger
        
        return {'triggered': False, 'reason': 'No triggers activated'}
    
    def _check_hit_rate_drop(self, kpi_data: Dict, threshold: float) -> Dict[str, Any]:
        """Check if hit rate has dropped significantly"""
        try:
            current_hit_rate = kpi_data.get('hit_rate', 0.0)
            baseline_hit_rate = kpi_data.get('baseline_hit_rate', current_hit_rate)
            
            if baseline_hit_rate > 0:
                drop_percentage = (baseline_hit_rate - current_hit_rate) / baseline_hit_rate
                if drop_percentage > threshold:
                    return {
                        'triggered': True,
                        'reason': f"Hit rate dropped {drop_percentage:.1%} (>{threshold:.1%}) from baseline",
                        'confidence': 0.9
                    }
            
            return {'triggered': False}
        except Exception as e:
            logger.warning(f"Error checking hit rate drop: {e}")
            return {'triggered': False}
    
    def _check_brier_score(self, kpi_data: Dict, thresholds: Dict, timeframe: str) -> Dict[str, Any]:
        """Check if Brier score exceeds threshold"""
        try:
            brier_score = kpi_data.get('brier_score', 0.0)
            
            # Map timeframe to threshold category
            if timeframe in ['1D', '5D']:
                threshold_key = 'short_term'
            elif timeframe in ['30D']:
                threshold_key = 'medium_term'
            else:
                threshold_key = 'long_term'
            
            threshold = thresholds.get(threshold_key, 0.20)
            
            if brier_score > threshold:
                return {
                    'triggered': True,
                    'reason': f"Brier score {brier_score:.3f} exceeds threshold {threshold:.3f} for {timeframe}",
                    'confidence': 0.85
                }
            
            return {'triggered': False}
        except Exception as e:
            logger.warning(f"Error checking Brier score: {e}")
            return {'triggered': False}
    
    def _check_confidence_drift(self, kpi_data: Dict, threshold: float) -> Dict[str, Any]:
        """Check if confidence deviates from actual success rate"""
        try:
            avg_confidence = kpi_data.get('average_confidence', 0.0)
            actual_success_rate = kpi_data.get('hit_rate', 0.0)
            
            if avg_confidence > 0:
                drift = abs(avg_confidence - actual_success_rate)
                if drift > threshold:
                    return {
                        'triggered': True,
                        'reason': f"Confidence drift {drift:.1%} exceeds threshold {threshold:.1%}",
                        'confidence': 0.8
                    }
            
            return {'triggered': False}
        except Exception as e:
            logger.warning(f"Error checking confidence drift: {e}")
            return {'triggered': False}
    
    def _check_time_based_trigger(self, product: str, timeframe: str, max_days: int) -> Dict[str, Any]:
        """Check if too much time has passed since last retrain"""
        try:
            last_retrain = self._get_last_retrain_date(product, timeframe)
            if not last_retrain:
                return {
                    'triggered': True,
                    'reason': f"No previous retrain found for {product} {timeframe}",
                    'confidence': 0.6
                }
            
            days_since = (get_ist_now() - last_retrain).days
            if days_since > max_days:
                return {
                    'triggered': True,
                    'reason': f"{days_since} days since last retrain (max: {max_days})",
                    'confidence': 0.7
                }
            
            return {'triggered': False}
        except Exception as e:
            logger.warning(f"Error checking time-based trigger: {e}")
            return {'triggered': False}
    
    def execute_retrain(self, decision: TrainerDecision) -> Dict[str, Any]:
        """Execute retraining based on decision"""
        try:
            logger.info(f"Executing retrain for {decision.product} {decision.timeframe}")
            
            results = {}
            
            for action in decision.actions:
                if action == 'retrain_lstm':
                    result = self._retrain_lstm_models(decision.product)
                    results['lstm'] = result
                elif action == 'retrain_rf':
                    result = self._retrain_rf_models(decision.product)
                    results['rf'] = result
            
            # Log the retraining
            self._log_retrain_execution(decision, results)
            
            return {
                'success': True,
                'results': results,
                'timestamp': get_ist_now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing retrain: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': get_ist_now().isoformat()
            }
    
    def _retrain_lstm_models(self, product: str) -> Dict[str, Any]:
        """Retrain LSTM models for specified product"""
        try:
            from src.ml.train_models import ModelTrainer
            trainer = ModelTrainer()
            
            # Get symbols for product
            symbols = self._get_symbols_for_product(product)
            results = {}
            
            for symbol in symbols[:5]:  # Limit to 5 symbols to avoid memory issues
                try:
                    result = trainer.train_lstm_model(symbol)
                    results[symbol] = result
                except Exception as e:
                    logger.warning(f"Failed to retrain LSTM for {symbol}: {e}")
                    results[symbol] = {'error': str(e)}
            
            return {
                'model_type': 'lstm',
                'product': product,
                'results': results,
                'trained_count': len([r for r in results.values() if 'error' not in r])
            }
            
        except Exception as e:
            logger.error(f"Error retraining LSTM models: {e}")
            return {'error': str(e)}
    
    def _retrain_rf_models(self, product: str) -> Dict[str, Any]:
        """Retrain Random Forest models for specified product"""
        try:
            from src.ml.train_models import ModelTrainer
            trainer = ModelTrainer()
            
            # Get symbols for product
            symbols = self._get_symbols_for_product(product)
            results = {}
            
            for symbol in symbols[:5]:  # Limit to 5 symbols
                try:
                    result = trainer.train_rf_model(symbol)
                    results[symbol] = result
                except Exception as e:
                    logger.warning(f"Failed to retrain RF for {symbol}: {e}")
                    results[symbol] = {'error': str(e)}
            
            return {
                'model_type': 'rf',
                'product': product,
                'results': results,
                'trained_count': len([r for r in results.values() if 'error' not in r])
            }
            
        except Exception as e:
            logger.error(f"Error retraining RF models: {e}")
            return {'error': str(e)}
    
    def _get_symbols_for_product(self, product: str) -> List[str]:
        """Get symbol list for product type"""
        symbols_map = {
            'equities': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC'],
            'options': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC'],
            'comm': ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC']
        }
        return symbols_map.get(product, ['RELIANCE', 'TCS', 'INFY'])
    
    def _get_actions_for_product(self, product: str) -> List[str]:
        """Get available actions for product"""
        actions = []
        for action_config in self.config['actions']:
            if product in action_config['products']:
                actions.append(action_config['name'])
        return actions
    
    def _is_in_cooldown(self, product: str, timeframe: str) -> bool:
        """Check if product/timeframe is in cooldown period"""
        try:
            last_retrain = self._get_last_retrain_date(product, timeframe)
            if not last_retrain:
                return False
            
            cooldown_days = self.config['retrain_cooldown_days']
            days_since = (get_ist_now() - last_retrain).days
            
            return days_since < cooldown_days
            
        except Exception as e:
            logger.warning(f"Error checking cooldown: {e}")
            return False
    
    def _get_last_retrain_date(self, product: str, timeframe: str) -> Optional[datetime]:
        """Get last retrain date for product/timeframe"""
        try:
            history = json_store.load('trainer_history', [])
            
            for entry in reversed(history):
                if (entry.get('product') == product and 
                    entry.get('timeframe') == timeframe and
                    entry.get('success', False)):
                    return datetime.fromisoformat(entry['timestamp'])
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting last retrain date: {e}")
            return None
    
    def _load_kpi_data(self, product: str, timeframe: str) -> Optional[Dict]:
        """Load KPI data for evaluation"""
        try:
            # Try to get KPI data from API or file
            from src.products.shared.services.kpi_service import KPIService
            kpi_service = KPIService()
            
            kpi_data = kpi_service.get_kpis(product, timeframe)
            return kpi_data
            
        except Exception as e:
            logger.warning(f"Error loading KPI data: {e}")
            # Return mock data for testing
            return {
                'hit_rate': 0.65,
                'baseline_hit_rate': 0.75,
                'brier_score': 0.15,
                'average_confidence': 0.8,
                'total_predictions': 50
            }
    
    def _log_retrain_execution(self, decision: TrainerDecision, results: Dict[str, Any]):
        """Log retraining execution to history"""
        try:
            history = json_store.load('trainer_history', [])
            
            log_entry = {
                'timestamp': get_ist_now().isoformat(),
                'product': decision.product,
                'timeframe': decision.timeframe,
                'reason': decision.reason,
                'actions': decision.actions,
                'results': results,
                'success': results.get('success', False),
                'force_triggered': decision.force_triggered
            }
            
            history.append(log_entry)
            
            # Keep only last 100 entries
            if len(history) > 100:
                history = history[-100:]
            
            json_store.save('trainer_history', history)
            logger.info(f"Logged retrain execution for {decision.product} {decision.timeframe}")
            
        except Exception as e:
            logger.error(f"Error logging retrain execution: {e}")
    
    def get_retrain_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get retraining history"""
        try:
            history = json_store.load('trainer_history', [])
            return history[-limit:] if history else []
        except Exception as e:
            logger.error(f"Error getting retrain history: {e}")
            return []
    
    def get_trainer_status(self, product: str = None) -> Dict[str, Any]:
        """Get current trainer status"""
        try:
            products = [product] if product else ['equities', 'options', 'comm']
            timeframes = ['5D', '30D']
            
            status = {}
            
            for prod in products:
                status[prod] = {}
                for tf in timeframes:
                    last_retrain = self._get_last_retrain_date(prod, tf)
                    in_cooldown = self._is_in_cooldown(prod, tf)
                    
                    status[prod][tf] = {
                        'last_retrain': last_retrain.isoformat() if last_retrain else None,
                        'days_since_retrain': (get_ist_now() - last_retrain).days if last_retrain else None,
                        'in_cooldown': in_cooldown,
                        'status': 'healthy' if last_retrain and (get_ist_now() - last_retrain).days < 7 else 'watchlist'
                    }
            
            return {
                'timestamp': get_ist_now().isoformat(),
                'products': status,
                'config': self.config
            }
            
        except Exception as e:
            logger.error(f"Error getting trainer status: {e}")
            return {'error': str(e)}
