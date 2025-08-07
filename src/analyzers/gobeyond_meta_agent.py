
#!/usr/bin/env python3
"""
GoBeyond Meta-Agent - Self-Optimizing Feedback Loop System

This module continuously monitors prediction failures and learns patterns to:
1. Identify repeated failure patterns by stock, indicator, and timeframe
2. Suggest dynamic rule-based overrides
3. Learn from correction patterns and auto-suggest prediction strategy shifts
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class GoBeyondMetaAgent:
    def __init__(self):
        self.failure_patterns_path = "data/tracking/failure_patterns.json"
        self.meta_rules_path = "data/tracking/meta_rules.json"
        self.pattern_learning_path = "data/tracking/pattern_learning.json"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.failure_patterns_path), exist_ok=True)
        
        # Initialize data structures
        self._initialize_meta_agent()
        
        # Pattern detection thresholds
        self.failure_threshold = 3  # Number of failures to trigger pattern detection
        self.confidence_threshold = 0.7  # Confidence level for pattern suggestions
        
    def _initialize_meta_agent(self):
        """Initialize meta-agent data structures"""
        try:
            # Initialize failure patterns tracking
            if not os.path.exists(self.failure_patterns_path):
                initial_patterns = {
                    'failure_by_stock': {},
                    'failure_by_timeframe': {},
                    'failure_by_indicator': {},
                    'combined_patterns': {},
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.failure_patterns_path, initial_patterns)
            
            # Initialize meta rules
            if not os.path.exists(self.meta_rules_path):
                initial_rules = {
                    'dynamic_overrides': {},
                    'strategy_shifts': {},
                    'learned_patterns': {},
                    'active_rules': [],
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.meta_rules_path, initial_rules)
                
            # Initialize pattern learning
            if not os.path.exists(self.pattern_learning_path):
                initial_learning = {
                    'correction_patterns': {},
                    'success_patterns': {},
                    'learning_insights': [],
                    'last_analysis': datetime.now().isoformat()
                }
                self._save_json(self.pattern_learning_path, initial_learning)
                
        except Exception as e:
            logger.error(f"Error initializing GoBeyond Meta-Agent: {str(e)}")

    def record_prediction_failure(self, stock: str, timeframe: str, prediction_data: Dict[str, Any], 
                                actual_data: Dict[str, Any], failure_reason: str):
        """Record a prediction failure for pattern analysis"""
        try:
            failure_patterns = self._load_json(self.failure_patterns_path)
            
            # Record failure by stock
            if stock not in failure_patterns['failure_by_stock']:
                failure_patterns['failure_by_stock'][stock] = []
            
            failure_entry = {
                'timestamp': datetime.now().isoformat(),
                'timeframe': timeframe,
                'predicted_price': prediction_data.get('predicted_price', 0),
                'actual_price': actual_data.get('actual_price', 0),
                'confidence': prediction_data.get('confidence', 0),
                'failure_reason': failure_reason,
                'indicators': prediction_data.get('indicators', {}),
                'market_conditions': prediction_data.get('market_conditions', {})
            }
            
            failure_patterns['failure_by_stock'][stock].append(failure_entry)
            
            # Record failure by timeframe
            if timeframe not in failure_patterns['failure_by_timeframe']:
                failure_patterns['failure_by_timeframe'][timeframe] = []
            failure_patterns['failure_by_timeframe'][timeframe].append(failure_entry)
            
            # Analyze indicators involved in failure
            for indicator, value in prediction_data.get('indicators', {}).items():
                if indicator not in failure_patterns['failure_by_indicator']:
                    failure_patterns['failure_by_indicator'][indicator] = []
                failure_patterns['failure_by_indicator'][indicator].append({
                    'stock': stock,
                    'timeframe': timeframe,
                    'indicator_value': value,
                    'failure_reason': failure_reason,
                    'timestamp': datetime.now().isoformat()
                })
            
            failure_patterns['last_updated'] = datetime.now().isoformat()
            self._save_json(self.failure_patterns_path, failure_patterns)
            
            # Trigger pattern analysis if enough failures recorded
            self._analyze_failure_patterns()
            
        except Exception as e:
            logger.error(f"Error recording prediction failure: {str(e)}")

    def _analyze_failure_patterns(self):
        """Analyze failure patterns and generate dynamic rules"""
        try:
            failure_patterns = self._load_json(self.failure_patterns_path)
            meta_rules = self._load_json(self.meta_rules_path)
            
            # Analyze stock-specific patterns
            for stock, failures in failure_patterns['failure_by_stock'].items():
                if len(failures) >= self.failure_threshold:
                    pattern = self._detect_stock_pattern(stock, failures)
                    if pattern:
                        self._generate_dynamic_override(stock, pattern, meta_rules)
            
            # Analyze timeframe patterns
            for timeframe, failures in failure_patterns['failure_by_timeframe'].items():
                if len(failures) >= self.failure_threshold:
                    pattern = self._detect_timeframe_pattern(timeframe, failures)
                    if pattern:
                        self._generate_timeframe_rule(timeframe, pattern, meta_rules)
            
            # Analyze indicator patterns
            self._analyze_indicator_failures(failure_patterns, meta_rules)
            
            meta_rules['last_updated'] = datetime.now().isoformat()
            self._save_json(self.meta_rules_path, meta_rules)
            
        except Exception as e:
            logger.error(f"Error analyzing failure patterns: {str(e)}")

    def _detect_stock_pattern(self, stock: str, failures: List[Dict]) -> Optional[Dict]:
        """Detect patterns in stock-specific failures"""
        try:
            recent_failures = [f for f in failures if self._is_recent(f['timestamp'], days=30)]
            
            if len(recent_failures) < self.failure_threshold:
                return None
            
            # Analyze timeframe distribution
            timeframe_failures = defaultdict(int)
            volatility_failures = 0
            confidence_issues = 0
            
            for failure in recent_failures:
                timeframe_failures[failure['timeframe']] += 1
                if 'volatility' in failure['failure_reason'].lower():
                    volatility_failures += 1
                if failure['confidence'] < 70:
                    confidence_issues += 1
            
            # Detect patterns
            pattern = {
                'stock': stock,
                'total_failures': len(recent_failures),
                'problematic_timeframes': [tf for tf, count in timeframe_failures.items() if count >= 2],
                'volatility_related': volatility_failures / len(recent_failures) > 0.5,
                'low_confidence_issues': confidence_issues / len(recent_failures) > 0.6,
                'pattern_confidence': self._calculate_pattern_confidence(recent_failures)
            }
            
            return pattern if pattern['pattern_confidence'] > self.confidence_threshold else None
            
        except Exception as e:
            logger.error(f"Error detecting stock pattern for {stock}: {str(e)}")
            return None

    def _detect_timeframe_pattern(self, timeframe: str, failures: List[Dict]) -> Optional[Dict]:
        """Detect patterns in timeframe-specific failures"""
        try:
            recent_failures = [f for f in failures if self._is_recent(f['timestamp'], days=30)]
            
            if len(recent_failures) < self.failure_threshold:
                return None
            
            # Analyze stock distribution
            stock_failures = defaultdict(int)
            market_condition_failures = defaultdict(int)
            
            for failure in recent_failures:
                stock_failures[failure.get('stock', 'unknown')] += 1
                market_condition = failure.get('market_conditions', {}).get('volatility', 'medium')
                market_condition_failures[market_condition] += 1
            
            pattern = {
                'timeframe': timeframe,
                'total_failures': len(recent_failures),
                'frequently_failing_stocks': [stock for stock, count in stock_failures.items() if count >= 2],
                'problematic_conditions': dict(market_condition_failures),
                'pattern_confidence': self._calculate_pattern_confidence(recent_failures)
            }
            
            return pattern if pattern['pattern_confidence'] > self.confidence_threshold else None
            
        except Exception as e:
            logger.error(f"Error detecting timeframe pattern for {timeframe}: {str(e)}")
            return None

    def _generate_dynamic_override(self, stock: str, pattern: Dict, meta_rules: Dict):
        """Generate dynamic rule-based overrides"""
        try:
            override_key = f"stock_{stock}"
            
            # Generate specific overrides based on pattern
            overrides = []
            
            if pattern['volatility_related']:
                overrides.append({
                    'rule_type': 'volatility_check',
                    'condition': f'volatility > high AND stock == {stock}',
                    'action': 'reduce_confidence_by_20',
                    'reason': 'High volatility correlation with failures detected'
                })
            
            if pattern['problematic_timeframes']:
                for tf in pattern['problematic_timeframes']:
                    overrides.append({
                        'rule_type': 'timeframe_restriction',
                        'condition': f'stock == {stock} AND timeframe == {tf}',
                        'action': 'suggest_alternative_timeframe',
                        'alternative_timeframe': self._suggest_alternative_timeframe(tf),
                        'reason': f'Repeated failures in {tf} predictions for {stock}'
                    })
            
            if pattern['low_confidence_issues']:
                overrides.append({
                    'rule_type': 'confidence_boost',
                    'condition': f'stock == {stock} AND confidence < 70',
                    'action': 'skip_prediction',
                    'reason': 'Low confidence predictions frequently fail for this stock'
                })
            
            meta_rules['dynamic_overrides'][override_key] = {
                'overrides': overrides,
                'pattern_source': pattern,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
        except Exception as e:
            logger.error(f"Error generating dynamic override for {stock}: {str(e)}")

    def _generate_timeframe_rule(self, timeframe: str, pattern: Dict, meta_rules: Dict):
        """Generate timeframe-specific rules"""
        try:
            rule_key = f"timeframe_{timeframe}"
            
            rules = []
            
            if pattern['frequently_failing_stocks']:
                rules.append({
                    'rule_type': 'stock_exclusion',
                    'condition': f'timeframe == {timeframe} AND stock IN {pattern["frequently_failing_stocks"]}',
                    'action': 'use_alternative_model',
                    'alternative_model': 'ensemble',
                    'reason': f'Specific stocks frequently fail in {timeframe} predictions'
                })
            
            if 'high' in pattern['problematic_conditions'] and pattern['problematic_conditions']['high'] > 2:
                rules.append({
                    'rule_type': 'market_condition_check',
                    'condition': f'timeframe == {timeframe} AND market_volatility == high',
                    'action': 'reduce_prediction_window',
                    'reason': 'High volatility conditions problematic for this timeframe'
                })
            
            meta_rules['strategy_shifts'][rule_key] = {
                'rules': rules,
                'pattern_source': pattern,
                'created_at': datetime.now().isoformat(),
                'active': True
            }
            
        except Exception as e:
            logger.error(f"Error generating timeframe rule for {timeframe}: {str(e)}")

    def _analyze_indicator_failures(self, failure_patterns: Dict, meta_rules: Dict):
        """Analyze indicator-related failure patterns"""
        try:
            for indicator, failures in failure_patterns['failure_by_indicator'].items():
                if len(failures) >= self.failure_threshold:
                    # Analyze if specific indicator values correlate with failures
                    indicator_values = [f['indicator_value'] for f in failures if 'indicator_value' in f]
                    
                    if len(indicator_values) >= 3:
                        # Calculate problematic ranges
                        values_array = np.array(indicator_values)
                        mean_val = np.mean(values_array)
                        std_val = np.std(values_array)
                        
                        problematic_range = {
                            'indicator': indicator,
                            'failure_range_low': mean_val - std_val,
                            'failure_range_high': mean_val + std_val,
                            'failure_count': len(failures),
                            'pattern_confidence': min(1.0, len(failures) / 10)
                        }
                        
                        if problematic_range['pattern_confidence'] > self.confidence_threshold:
                            rule_key = f"indicator_{indicator}"
                            meta_rules['learned_patterns'][rule_key] = {
                                'pattern': problematic_range,
                                'created_at': datetime.now().isoformat(),
                                'active': True
                            }
                            
        except Exception as e:
            logger.error(f"Error analyzing indicator failures: {str(e)}")

    def get_prediction_overrides(self, stock: str, timeframe: str, prediction_data: Dict) -> List[Dict]:
        """Get active overrides for a prediction"""
        try:
            meta_rules = self._load_json(self.meta_rules_path)
            active_overrides = []
            
            # Check stock-specific overrides
            stock_key = f"stock_{stock}"
            if stock_key in meta_rules.get('dynamic_overrides', {}):
                override_data = meta_rules['dynamic_overrides'][stock_key]
                if override_data.get('active', False):
                    for override in override_data.get('overrides', []):
                        if self._check_override_condition(override, stock, timeframe, prediction_data):
                            active_overrides.append(override)
            
            # Check timeframe-specific rules
            timeframe_key = f"timeframe_{timeframe}"
            if timeframe_key in meta_rules.get('strategy_shifts', {}):
                rule_data = meta_rules['strategy_shifts'][timeframe_key]
                if rule_data.get('active', False):
                    for rule in rule_data.get('rules', []):
                        if self._check_override_condition(rule, stock, timeframe, prediction_data):
                            active_overrides.append(rule)
            
            return active_overrides
            
        except Exception as e:
            logger.error(f"Error getting prediction overrides: {str(e)}")
            return []

    def learn_from_corrections(self, correction_data: Dict):
        """Learn from correction patterns to improve future suggestions"""
        try:
            pattern_learning = self._load_json(self.pattern_learning_path)
            
            correction_entry = {
                'timestamp': datetime.now().isoformat(),
                'original_prediction': correction_data.get('original_prediction', {}),
                'correction_applied': correction_data.get('correction_applied', {}),
                'improvement_observed': correction_data.get('improvement_observed', False),
                'correction_type': correction_data.get('correction_type', 'unknown')
            }
            
            # Store correction pattern
            correction_type = correction_data.get('correction_type', 'unknown')
            if correction_type not in pattern_learning['correction_patterns']:
                pattern_learning['correction_patterns'][correction_type] = []
            
            pattern_learning['correction_patterns'][correction_type].append(correction_entry)
            
            # Generate learning insights
            self._generate_learning_insights(pattern_learning)
            
            pattern_learning['last_analysis'] = datetime.now().isoformat()
            self._save_json(self.pattern_learning_path, pattern_learning)
            
        except Exception as e:
            logger.error(f"Error learning from corrections: {str(e)}")

    def _generate_learning_insights(self, pattern_learning: Dict):
        """Generate insights from correction patterns"""
        try:
            insights = []
            
            for correction_type, corrections in pattern_learning['correction_patterns'].items():
                if len(corrections) >= 3:
                    successful_corrections = [c for c in corrections if c.get('improvement_observed', False)]
                    success_rate = len(successful_corrections) / len(corrections)
                    
                    if success_rate > 0.7:
                        insights.append({
                            'type': 'successful_correction_pattern',
                            'correction_type': correction_type,
                            'success_rate': success_rate,
                            'recommendation': f'Continue applying {correction_type} corrections - high success rate observed',
                            'confidence': success_rate
                        })
                    elif success_rate < 0.3:
                        insights.append({
                            'type': 'ineffective_correction_pattern',
                            'correction_type': correction_type,
                            'success_rate': success_rate,
                            'recommendation': f'Reconsider {correction_type} corrections - low success rate observed',
                            'confidence': 1 - success_rate
                        })
            
            pattern_learning['learning_insights'] = insights
            
        except Exception as e:
            logger.error(f"Error generating learning insights: {str(e)}")

    def get_meta_agent_status(self) -> Dict[str, Any]:
        """Get current status of the meta-agent"""
        try:
            failure_patterns = self._load_json(self.failure_patterns_path)
            meta_rules = self._load_json(self.meta_rules_path)
            pattern_learning = self._load_json(self.pattern_learning_path)
            
            # Count active rules
            active_overrides = sum(1 for override in meta_rules.get('dynamic_overrides', {}).values() 
                                 if override.get('active', False))
            active_rules = sum(1 for rule in meta_rules.get('strategy_shifts', {}).values() 
                             if rule.get('active', False))
            
            # Count recent failures
            recent_failures = 0
            for stock_failures in failure_patterns.get('failure_by_stock', {}).values():
                recent_failures += len([f for f in stock_failures if self._is_recent(f['timestamp'], days=7)])
            
            return {
                'status': 'active',
                'active_overrides': active_overrides,
                'active_strategy_rules': active_rules,
                'recent_failures_analyzed': recent_failures,
                'learning_insights_count': len(pattern_learning.get('learning_insights', [])),
                'last_pattern_analysis': meta_rules.get('last_updated'),
                'last_learning_update': pattern_learning.get('last_analysis')
            }
            
        except Exception as e:
            logger.error(f"Error getting meta-agent status: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    # Helper methods
    def _load_json(self, file_path: str) -> Dict:
        """Load JSON data from file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {str(e)}")
            return {}

    def _save_json(self, file_path: str, data: Dict):
        """Save JSON data to file"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {str(e)}")

    def _is_recent(self, timestamp_str: str, days: int = 30) -> bool:
        """Check if timestamp is within recent days"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return (datetime.now() - timestamp).days <= days
        except:
            return False

    def _calculate_pattern_confidence(self, failures: List[Dict]) -> float:
        """Calculate confidence level for detected patterns"""
        try:
            if len(failures) < 2:
                return 0.0
            
            # Base confidence on number of failures and consistency
            base_confidence = min(1.0, len(failures) / 5)
            
            # Adjust for recency
            recent_count = len([f for f in failures if self._is_recent(f['timestamp'], days=7)])
            recency_boost = min(0.3, recent_count / len(failures))
            
            return min(1.0, base_confidence + recency_boost)
            
        except:
            return 0.0

    def _suggest_alternative_timeframe(self, problematic_timeframe: str) -> str:
        """Suggest alternative timeframe based on problems detected"""
        timeframe_alternatives = {
            '3D': '5D',
            '5D': '10D',
            '10D': '15D',
            '15D': '30D',
            '30D': '15D'
        }
        return timeframe_alternatives.get(problematic_timeframe, '5D')

    def _check_override_condition(self, override: Dict, stock: str, timeframe: str, prediction_data: Dict) -> bool:
        """Check if override condition is met"""
        try:
            condition = override.get('condition', '')
            
            # Simple condition checking (can be enhanced with proper expression parsing)
            if f'stock == {stock}' in condition:
                if f'timeframe == {timeframe}' in condition:
                    return True
                if 'volatility > high' in condition:
                    volatility = prediction_data.get('market_conditions', {}).get('volatility', 'medium')
                    return volatility == 'high'
                if 'confidence <' in condition:
                    confidence_threshold = float(condition.split('confidence < ')[1].split(' ')[0])
                    return prediction_data.get('confidence', 100) < confidence_threshold
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking override condition: {str(e)}")
            return False

def main():
    """Test GoBeyond Meta-Agent functionality"""
    meta_agent = GoBeyondMetaAgent()
    
    # Test failure recording
    print("=== Testing Failure Recording ===")
    meta_agent.record_prediction_failure(
        stock='SBIN',
        timeframe='5D',
        prediction_data={
            'predicted_price': 650.0,
            'confidence': 75,
            'indicators': {'RSI': 68, 'MACD': 1.2},
            'market_conditions': {'volatility': 'high'}
        },
        actual_data={'actual_price': 620.0},
        failure_reason='High volatility exceeded prediction bounds'
    )
    
    # Test status
    status = meta_agent.get_meta_agent_status()
    print(f"Meta-agent status: {status}")
    
    print("\n✅ GoBeyond Meta-Agent testing completed!")

if __name__ == "__main__":
    main()
