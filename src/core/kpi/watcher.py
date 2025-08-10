
"""
KPI Watcher - Monitors KPI metrics and triggers agent actions
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from src.common_repository.config.feature_flags import feature_flags
from src.common_repository.storage.json_store import json_store
from src.common_repository.config.runtime import get_market_tz

logger = logging.getLogger(__name__)

class KPIWatcher:
    """Watches KPI metrics for threshold breaches and triggers agent actions"""
    
    def __init__(self):
        self.trigger_events_file = 'data/runtime/kpi_trigger_events.json'
        self.baseline_thresholds = {
            'brier_score_increase': 0.05,  # If Brier score increases by more than 0.05
            'hit_rate_decrease': 10.0,     # If hit rate decreases by more than 10%
            'sharpe_decrease': 0.5,        # If Sharpe ratio decreases by more than 0.5
            'drawdown_increase': 10.0      # If max drawdown increases by more than 10%
        }
    
    def load_kpi_metrics(self) -> Dict[str, Any]:
        """Load current KPI metrics"""
        try:
            return json_store.load('kpi_metrics', {})
        except Exception as e:
            logger.error(f"Error loading KPI metrics: {str(e)}")
            return {}
    
    def load_baseline_metrics(self) -> Dict[str, Any]:
        """Load baseline KPI metrics for comparison"""
        try:
            return json_store.load('kpi_baseline', {})
        except Exception as e:
            logger.warning(f"No baseline KPI metrics found: {str(e)}")
            return {}
    
    def create_trigger_event(self, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a trigger event record"""
        event = {
            'id': f"{event_type}_{int(datetime.now().timestamp())}",
            'type': event_type,
            'timestamp': datetime.now(get_market_tz()).isoformat(),
            'details': details,
            'status': 'created',
            'agent_actions': []
        }
        
        return event
    
    def save_trigger_event(self, event: Dict[str, Any]):
        """Save trigger event to storage"""
        try:
            # Load existing events
            events = json_store.load('kpi_trigger_events', [])
            
            # Add new event
            events.append(event)
            
            # Keep only last 100 events
            events = events[-100:]
            
            # Save back
            json_store.save('kpi_trigger_events', events)
            
            logger.info(f"Trigger event saved: {event['id']}")
            
        except Exception as e:
            logger.error(f"Error saving trigger event: {str(e)}")
    
    def check_brier_score_breach(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for Brier score threshold breaches"""
        breaches = []
        
        try:
            for timeframe in ["3D", "5D", "10D", "15D", "30D", "overall"]:
                current_tf = current.get('timeframes', {}).get(timeframe, {})
                baseline_tf = baseline.get('timeframes', {}).get(timeframe, {})
                
                if timeframe == "overall":
                    current_tf = current.get('overall', {})
                    baseline_tf = baseline.get('overall', {})
                
                current_brier = current_tf.get('brier_score')
                baseline_brier = baseline_tf.get('brier_score')
                
                if current_brier is not None and baseline_brier is not None:
                    increase = current_brier - baseline_brier
                    
                    if increase > self.baseline_thresholds['brier_score_increase']:
                        breaches.append({
                            'metric': 'brier_score',
                            'timeframe': timeframe,
                            'current_value': current_brier,
                            'baseline_value': baseline_brier,
                            'increase': increase,
                            'threshold': self.baseline_thresholds['brier_score_increase']
                        })
        
        except Exception as e:
            logger.error(f"Error checking Brier score breach: {str(e)}")
        
        return breaches
    
    def check_hit_rate_breach(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for hit rate threshold breaches"""
        breaches = []
        
        try:
            for timeframe in ["3D", "5D", "10D", "15D", "30D", "overall"]:
                current_tf = current.get('timeframes', {}).get(timeframe, {})
                baseline_tf = baseline.get('timeframes', {}).get(timeframe, {})
                
                if timeframe == "overall":
                    current_tf = current.get('overall', {})
                    baseline_tf = baseline.get('overall', {})
                
                current_hit_rate = current_tf.get('directional_hit_rate')
                baseline_hit_rate = baseline_tf.get('directional_hit_rate')
                
                if current_hit_rate is not None and baseline_hit_rate is not None:
                    decrease = baseline_hit_rate - current_hit_rate
                    
                    if decrease > self.baseline_thresholds['hit_rate_decrease']:
                        breaches.append({
                            'metric': 'directional_hit_rate',
                            'timeframe': timeframe,
                            'current_value': current_hit_rate,
                            'baseline_value': baseline_hit_rate,
                            'decrease': decrease,
                            'threshold': self.baseline_thresholds['hit_rate_decrease']
                        })
        
        except Exception as e:
            logger.error(f"Error checking hit rate breach: {str(e)}")
        
        return breaches
    
    def check_all_thresholds(self, current_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check all KPI thresholds for breaches"""
        all_breaches = []
        
        try:
            baseline_metrics = self.load_baseline_metrics()
            
            if not baseline_metrics:
                logger.info("No baseline metrics found, skipping threshold checks")
                return all_breaches
            
            # Check Brier score
            brier_breaches = self.check_brier_score_breach(current_metrics, baseline_metrics)
            all_breaches.extend(brier_breaches)
            
            # Check hit rate
            hit_rate_breaches = self.check_hit_rate_breach(current_metrics, baseline_metrics)
            all_breaches.extend(hit_rate_breaches)
            
            # Log all breaches
            if all_breaches:
                logger.warning(f"KPI threshold breaches detected: {len(all_breaches)} breaches")
                for breach in all_breaches:
                    logger.warning(f"  {breach['metric']} ({breach['timeframe']}): {breach}")
            else:
                logger.info("No KPI threshold breaches detected")
        
        except Exception as e:
            logger.error(f"Error checking thresholds: {str(e)}")
        
        return all_breaches
    
    def trigger_agent_actions(self, breaches: List[Dict[str, Any]]) -> bool:
        """Trigger agent actions based on breaches"""
        try:
            if not breaches:
                return True
            
            kpi_triggers_enabled = feature_flags.is_enabled('enable_kpi_triggers')
            realtime_agents_enabled = feature_flags.is_enabled('enable_realtime_agents')
            
            for breach in breaches:
                # Create trigger event
                event = self.create_trigger_event('kpi_breach', breach)
                
                if kpi_triggers_enabled and realtime_agents_enabled:
                    # Queue trainer agent action (future implementation)
                    event['agent_actions'].append({
                        'agent': 'trainer',
                        'action': 'retrain_evaluation',
                        'queued_at': datetime.now(get_market_tz()).isoformat(),
                        'status': 'queued'
                    })
                    
                    logger.info(f"Trainer agent action queued for breach: {breach['metric']}")
                
                elif kpi_triggers_enabled:
                    logger.info(f"KPI breach detected but realtime agents disabled: {breach['metric']}")
                    event['agent_actions'].append({
                        'agent': 'none',
                        'action': 'log_only',
                        'status': 'agents_disabled'
                    })
                
                else:
                    logger.info(f"KPI breach detected but triggers disabled: {breach['metric']}")
                    event['agent_actions'].append({
                        'agent': 'none',
                        'action': 'log_only',
                        'status': 'triggers_disabled'
                    })
                
                # Save trigger event
                self.save_trigger_event(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Error triggering agent actions: {str(e)}")
            return False
    
    def watch_kpi_changes(self) -> bool:
        """Main method to watch for KPI changes and trigger actions"""
        try:
            logger.info("Watching KPI changes...")
            
            # Load current metrics
            current_metrics = self.load_kpi_metrics()
            
            if not current_metrics:
                logger.info("No current KPI metrics found")
                return True
            
            # Check for threshold breaches
            breaches = self.check_all_thresholds(current_metrics)
            
            # Trigger agent actions if breaches found
            if breaches:
                self.trigger_agent_actions(breaches)
            
            return True
            
        except Exception as e:
            logger.error(f"Error watching KPI changes: {str(e)}")
            return False

# Global instance
kpi_watcher = KPIWatcher()
