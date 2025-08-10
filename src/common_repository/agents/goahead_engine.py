
"""
GoAhead Decision Engine
Automated decision-making system for KPI-based triggers
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class GoAheadDecision:
    """Represents a GoAhead decision"""
    decision_id: str
    timestamp: str
    trigger_type: str  # 'retrain', 'throttle', 'tighten_risk'
    confidence: float
    reasoning: List[str]
    kpi_context: Dict[str, Any]
    recommended_actions: List[str]
    urgency: str  # 'low', 'medium', 'high', 'critical'

class GoAheadEngine:
    """Core GoAhead decision-making engine"""
    
    def __init__(self):
        self.decisions_file = "data/runtime/goahead_decisions.json"
        self.thresholds = self._load_thresholds()
        
    def _load_thresholds(self) -> Dict[str, Any]:
        """Load KPI thresholds for decision making"""
        try:
            with open("src/common_repository/config/kpi_thresholds.json", 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading thresholds: {e}")
            return {"targets": {}, "colors": {}, "warn_bands": {"pct": 0.1}}
    
    def analyze_kpis_and_decide(self, kpi_data: Dict[str, Any]) -> List[GoAheadDecision]:
        """Analyze KPIs and make GoAhead decisions"""
        decisions = []
        
        for timeframe, metrics in kpi_data.items():
            if not isinstance(metrics, dict):
                continue
                
            # Check for retrain triggers
            retrain_decision = self._check_retrain_triggers(timeframe, metrics)
            if retrain_decision:
                decisions.append(retrain_decision)
                
            # Check for throttle triggers
            throttle_decision = self._check_throttle_triggers(timeframe, metrics)
            if throttle_decision:
                decisions.append(throttle_decision)
                
            # Check for risk tightening triggers
            risk_decision = self._check_risk_triggers(timeframe, metrics)
            if risk_decision:
                decisions.append(risk_decision)
        
        # Save decisions
        self._save_decisions(decisions)
        return decisions
    
    def _check_retrain_triggers(self, timeframe: str, metrics: Dict[str, Any]) -> Optional[GoAheadDecision]:
        """Check if retraining is needed"""
        reasoning = []
        confidence = 0.0
        
        # Check accuracy degradation
        accuracy = metrics.get('accuracy', 0)
        target_accuracy = self.thresholds.get('targets', {}).get('hit_rate', {}).get('all', 62)
        
        if accuracy < target_accuracy * 0.8:  # 80% of target
            reasoning.append(f"Accuracy {accuracy:.1f}% below 80% of target ({target_accuracy}%)")
            confidence += 0.4
            
        # Check Brier score degradation
        brier = metrics.get('brier_score', 0)
        target_brier = self.thresholds.get('targets', {}).get('brier', {}).get(timeframe, 0.22)
        
        if brier > target_brier * 1.3:  # 30% worse than target
            reasoning.append(f"Brier score {brier:.3f} significantly above target ({target_brier:.3f})")
            confidence += 0.3
            
        # Check prediction staleness
        last_update = metrics.get('last_model_update', '')
        if last_update:
            try:
                update_time = datetime.fromisoformat(last_update)
                days_old = (datetime.now() - update_time).days
                if days_old > 30:
                    reasoning.append(f"Models are {days_old} days old")
                    confidence += 0.2
            except:
                pass
        
        if confidence >= 0.5:  # Threshold for retrain decision
            urgency = 'critical' if confidence > 0.8 else 'high' if confidence > 0.6 else 'medium'
            
            return GoAheadDecision(
                decision_id=f"retrain_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                trigger_type='retrain',
                confidence=confidence,
                reasoning=reasoning,
                kpi_context={'timeframe': timeframe, 'metrics': metrics},
                recommended_actions=[
                    "Initiate model retraining with latest data",
                    "Update feature engineering pipeline",
                    "Validate new models before deployment"
                ],
                urgency=urgency
            )
        
        return None
    
    def _check_throttle_triggers(self, timeframe: str, metrics: Dict[str, Any]) -> Optional[GoAheadDecision]:
        """Check if prediction throttling is needed"""
        reasoning = []
        confidence = 0.0
        
        # Check high error rate
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 0.25:  # 25% error rate
            reasoning.append(f"High error rate: {error_rate:.1%}")
            confidence += 0.4
            
        # Check low confidence predictions
        avg_confidence = metrics.get('avg_confidence', 100)
        if avg_confidence < 60:
            reasoning.append(f"Low average confidence: {avg_confidence:.1f}%")
            confidence += 0.3
            
        # Check volatility spike
        volatility = metrics.get('market_volatility', 0)
        if volatility > 0.3:  # High volatility
            reasoning.append(f"High market volatility: {volatility:.2f}")
            confidence += 0.2
            
        if confidence >= 0.4:
            urgency = 'high' if confidence > 0.7 else 'medium'
            
            return GoAheadDecision(
                decision_id=f"throttle_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                trigger_type='throttle',
                confidence=confidence,
                reasoning=reasoning,
                kpi_context={'timeframe': timeframe, 'metrics': metrics},
                recommended_actions=[
                    "Reduce prediction frequency",
                    "Increase confidence thresholds",
                    "Add manual review for low-confidence predictions"
                ],
                urgency=urgency
            )
        
        return None
    
    def _check_risk_triggers(self, timeframe: str, metrics: Dict[str, Any]) -> Optional[GoAheadDecision]:
        """Check if risk parameters need tightening"""
        reasoning = []
        confidence = 0.0
        
        # Check drawdown
        max_drawdown = metrics.get('max_drawdown', 0)
        target_drawdown = self.thresholds.get('targets', {}).get('max_dd', {}).get('all', 0.05)
        
        if max_drawdown > target_drawdown * 1.5:
            reasoning.append(f"Drawdown {max_drawdown:.1%} exceeds safe limits")
            confidence += 0.4
            
        # Check Sharpe ratio degradation
        sharpe = metrics.get('sharpe_ratio', 0)
        target_sharpe = self.thresholds.get('targets', {}).get('sharpe', {}).get('all', 1.2)
        
        if sharpe < target_sharpe * 0.7:
            reasoning.append(f"Sharpe ratio {sharpe:.2f} below acceptable level")
            confidence += 0.3
            
        # Check VaR breach
        var_95 = metrics.get('var_95', 0)
        target_var = self.thresholds.get('targets', {}).get('var_95', {}).get('all', 0.005)
        
        if var_95 > target_var * 1.2:
            reasoning.append(f"VaR breach: {var_95:.3f} above target")
            confidence += 0.2
            
        if confidence >= 0.4:
            urgency = 'high' if confidence > 0.7 else 'medium'
            
            return GoAheadDecision(
                decision_id=f"risk_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                trigger_type='tighten_risk',
                confidence=confidence,
                reasoning=reasoning,
                kpi_context={'timeframe': timeframe, 'metrics': metrics},
                recommended_actions=[
                    "Tighten position sizing",
                    "Reduce maximum exposure limits",
                    "Implement stricter stop-loss rules"
                ],
                urgency=urgency
            )
        
        return None
    
    def _save_decisions(self, decisions: List[GoAheadDecision]):
        """Save decisions to file"""
        try:
            import os
            os.makedirs(os.path.dirname(self.decisions_file), exist_ok=True)
            
            # Load existing decisions
            existing = []
            if os.path.exists(self.decisions_file):
                with open(self.decisions_file, 'r') as f:
                    existing = json.load(f)
            
            # Add new decisions
            for decision in decisions:
                existing.append(asdict(decision))
            
            # Keep only last 100 decisions
            existing = existing[-100:]
            
            # Save
            with open(self.decisions_file, 'w') as f:
                json.dump(existing, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving decisions: {e}")
    
    def get_recent_decisions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent decisions"""
        try:
            if not os.path.exists(self.decisions_file):
                return []
                
            with open(self.decisions_file, 'r') as f:
                all_decisions = json.load(f)
            
            # Filter by time
            cutoff = datetime.now() - timedelta(hours=hours)
            recent = []
            
            for decision in all_decisions:
                try:
                    decision_time = datetime.fromisoformat(decision['timestamp'])
                    if decision_time >= cutoff:
                        recent.append(decision)
                except:
                    continue
            
            return recent
            
        except Exception as e:
            logger.error(f"Error loading recent decisions: {e}")
            return []

# Global instance
goahead_engine = GoAheadEngine()
