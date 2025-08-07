
#!/usr/bin/env python3
"""
Hyper-Personalized Signal Optimizer (HPSO)

This module maintains per-stock, per-user profiles and dynamically optimizes:
1. Past signal success tracking
2. Confidence zone ranges
3. Preferred timeframes and volatility tolerance
4. Entry zones optimization based on success clusters
5. Signal retention duration
6. Lock expiry durations for volatile stocks
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class PersonalSignalAgent:
    def __init__(self):
        self.personal_signals_path = "data/personal_signals"
        self.user_profiles_path = "data/personal_signals/user_profiles.json"
        self.optimization_logs_path = "logs/goahead/personal_optimization"
        
        # Ensure directories exist
        os.makedirs(self.personal_signals_path, exist_ok=True)
        os.makedirs(self.optimization_logs_path, exist_ok=True)
        
        # Optimization parameters
        self.optimization_params = {
            'min_signals_for_optimization': 15,
            'success_threshold': 0.70,
            'confidence_adjustment_step': 0.05,
            'entry_zone_adjustment_step': 0.01,
            'volatility_tolerance_levels': [0.01, 0.02, 0.03, 0.04, 0.05],
            'timeframe_preferences': ['3D', '5D', '10D', '30D'],
            'lock_duration_options': [1, 3, 5, 7, 10]  # days
        }
        
        # Default user profile template
        self.default_profile = {
            'user_id': 'default_user',
            'preferences': {
                'risk_tolerance': 'medium',
                'preferred_timeframes': ['5D', '10D'],
                'volatility_tolerance': 0.025,
                'confidence_threshold': 0.75,
                'entry_zone_size': 0.10
            },
            'performance_history': {
                'total_signals': 0,
                'successful_signals': 0,
                'avg_returns': 0.0,
                'best_timeframes': [],
                'worst_timeframes': []
            },
            'learning_parameters': {
                'adaptation_rate': 0.1,
                'last_optimization': datetime.now().isoformat()
            }
        }
        
        # Initialize agent
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize Personal Signal Agent"""
        try:
            if not os.path.exists(self.user_profiles_path):
                initial_profiles = {
                    'default_user': self.default_profile.copy(),
                    'profiles_count': 1,
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.user_profiles_path, initial_profiles)
                
        except Exception as e:
            logger.error(f"Error initializing Personal Signal Agent: {str(e)}")

    def get_or_create_stock_profile(self, stock: str, user_id: str = 'default_user') -> Dict[str, Any]:
        """Get or create personalized profile for specific stock"""
        try:
            stock_profile_path = os.path.join(self.personal_signals_path, f"{stock}.json")
            
            if os.path.exists(stock_profile_path):
                stock_profile = self._load_json(stock_profile_path)
            else:
                stock_profile = self._create_new_stock_profile(stock, user_id)
                self._save_json(stock_profile_path, stock_profile)
            
            return stock_profile
            
        except Exception as e:
            logger.error(f"Error getting stock profile for {stock}: {str(e)}")
            return self._create_new_stock_profile(stock, user_id)

    def _create_new_stock_profile(self, stock: str, user_id: str) -> Dict[str, Any]:
        """Create new personalized profile for stock"""
        try:
            # Get user's base preferences
            user_profiles = self._load_json(self.user_profiles_path)
            user_profile = user_profiles.get(user_id, self.default_profile)
            
            stock_profile = {
                'stock': stock,
                'user_id': user_id,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'signal_history': [],
                'optimization_results': {},
                'current_settings': {
                    'entry_zones': {
                        'buy_zone': user_profile['preferences']['entry_zone_size'],
                        'sell_zone': user_profile['preferences']['entry_zone_size']
                    },
                    'confidence_thresholds': {
                        'minimum': user_profile['preferences']['confidence_threshold'],
                        'preferred': user_profile['preferences']['confidence_threshold'] + 0.1
                    },
                    'timeframe_preferences': user_profile['preferences']['preferred_timeframes'].copy(),
                    'volatility_tolerance': user_profile['preferences']['volatility_tolerance'],
                    'lock_durations': {
                        'low_volatility': 7,
                        'medium_volatility': 5,
                        'high_volatility': 3
                    }
                },
                'performance_metrics': {
                    'total_signals': 0,
                    'successful_signals': 0,
                    'success_rate': 0.0,
                    'avg_returns': 0.0,
                    'best_entry_zones': [],
                    'best_timeframes': [],
                    'volatility_performance': {}
                },
                'learning_state': {
                    'optimization_cycles': 0,
                    'last_optimization': datetime.now().isoformat(),
                    'adaptation_enabled': True,
                    'confidence_trend': 'stable'
                }
            }
            
            return stock_profile
            
        except Exception as e:
            logger.error(f"Error creating stock profile for {stock}: {str(e)}")
            return {}

    def record_signal_outcome(self, stock: str, signal_data: Dict, outcome_data: Dict, 
                            user_id: str = 'default_user'):
        """Record signal outcome for learning and optimization"""
        try:
            stock_profile = self.get_or_create_stock_profile(stock, user_id)
            
            # Create signal record
            signal_record = {
                'signal_id': signal_data.get('signal_id', f"signal_{len(stock_profile['signal_history'])}"),
                'timestamp': signal_data.get('timestamp', datetime.now().isoformat()),
                'signal_type': signal_data.get('signal_type', 'prediction'),
                'timeframe': signal_data.get('timeframe', '5D'),
                'entry_zone': signal_data.get('entry_zone', 0.10),
                'confidence': signal_data.get('confidence', 0.75),
                'predicted_price': signal_data.get('predicted_price', 0),
                'actual_price': outcome_data.get('actual_price', 0),
                'success': outcome_data.get('success', False),
                'returns': outcome_data.get('returns', 0.0),
                'lock_duration': outcome_data.get('lock_duration', 5),
                'market_volatility': outcome_data.get('volatility', 0.02)
            }
            
            # Add to signal history
            stock_profile['signal_history'].append(signal_record)
            
            # Keep only last 100 signals for efficiency
            stock_profile['signal_history'] = stock_profile['signal_history'][-100:]
            
            # Update performance metrics
            self._update_performance_metrics(stock_profile)
            
            # Trigger optimization if enough data
            if len(stock_profile['signal_history']) >= self.optimization_params['min_signals_for_optimization']:
                self._optimize_signal_parameters(stock_profile)
            
            # Save updated profile
            stock_profile['last_updated'] = datetime.now().isoformat()
            stock_profile_path = os.path.join(self.personal_signals_path, f"{stock}.json")
            self._save_json(stock_profile_path, stock_profile)
            
        except Exception as e:
            logger.error(f"Error recording signal outcome for {stock}: {str(e)}")

    def _update_performance_metrics(self, stock_profile: Dict):
        """Update performance metrics based on signal history"""
        try:
            signal_history = stock_profile['signal_history']
            if not signal_history:
                return
            
            metrics = stock_profile['performance_metrics']
            
            # Basic metrics
            metrics['total_signals'] = len(signal_history)
            successful_signals = [s for s in signal_history if s.get('success', False)]
            metrics['successful_signals'] = len(successful_signals)
            metrics['success_rate'] = len(successful_signals) / len(signal_history)
            
            # Average returns
            returns = [s.get('returns', 0) for s in signal_history]
            metrics['avg_returns'] = np.mean(returns) if returns else 0.0
            
            # Best entry zones analysis
            entry_zone_performance = defaultdict(list)
            for signal in signal_history:
                zone = signal.get('entry_zone', 0.10)
                success = signal.get('success', False)
                entry_zone_performance[zone].append(success)
            
            best_zones = []
            for zone, successes in entry_zone_performance.items():
                success_rate = sum(successes) / len(successes)
                if success_rate > self.optimization_params['success_threshold']:
                    best_zones.append({'zone': zone, 'success_rate': success_rate})
            
            metrics['best_entry_zones'] = sorted(best_zones, key=lambda x: x['success_rate'], reverse=True)[:3]
            
            # Best timeframes analysis
            timeframe_performance = defaultdict(list)
            for signal in signal_history:
                timeframe = signal.get('timeframe', '5D')
                success = signal.get('success', False)
                timeframe_performance[timeframe].append(success)
            
            best_timeframes = []
            for timeframe, successes in timeframe_performance.items():
                success_rate = sum(successes) / len(successes)
                if success_rate > self.optimization_params['success_threshold']:
                    best_timeframes.append({'timeframe': timeframe, 'success_rate': success_rate})
            
            metrics['best_timeframes'] = sorted(best_timeframes, key=lambda x: x['success_rate'], reverse=True)[:3]
            
            # Volatility performance analysis
            volatility_buckets = {'low': [], 'medium': [], 'high': []}
            for signal in signal_history:
                volatility = signal.get('market_volatility', 0.02)
                success = signal.get('success', False)
                
                if volatility < 0.02:
                    volatility_buckets['low'].append(success)
                elif volatility < 0.04:
                    volatility_buckets['medium'].append(success)
                else:
                    volatility_buckets['high'].append(success)
            
            for bucket, successes in volatility_buckets.items():
                if successes:
                    metrics['volatility_performance'][bucket] = sum(successes) / len(successes)
                else:
                    metrics['volatility_performance'][bucket] = 0.0
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")

    def _optimize_signal_parameters(self, stock_profile: Dict):
        """Optimize signal parameters based on performance history"""
        try:
            signal_history = stock_profile['signal_history']
            current_settings = stock_profile['current_settings']
            
            optimization_results = {
                'optimization_id': f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'changes_made': [],
                'expected_improvements': {}
            }
            
            # Optimize entry zones
            entry_zone_optimization = self._optimize_entry_zones(signal_history)
            if entry_zone_optimization:
                current_settings['entry_zones'].update(entry_zone_optimization['new_zones'])
                optimization_results['changes_made'].append('entry_zones')
                optimization_results['expected_improvements']['entry_zones'] = entry_zone_optimization['expected_improvement']
            
            # Optimize confidence thresholds
            confidence_optimization = self._optimize_confidence_thresholds(signal_history)
            if confidence_optimization:
                current_settings['confidence_thresholds'].update(confidence_optimization['new_thresholds'])
                optimization_results['changes_made'].append('confidence_thresholds')
                optimization_results['expected_improvements']['confidence_thresholds'] = confidence_optimization['expected_improvement']
            
            # Optimize timeframe preferences
            timeframe_optimization = self._optimize_timeframe_preferences(signal_history)
            if timeframe_optimization:
                current_settings['timeframe_preferences'] = timeframe_optimization['new_preferences']
                optimization_results['changes_made'].append('timeframe_preferences')
                optimization_results['expected_improvements']['timeframe_preferences'] = timeframe_optimization['expected_improvement']
            
            # Optimize lock durations based on volatility
            lock_duration_optimization = self._optimize_lock_durations(signal_history)
            if lock_duration_optimization:
                current_settings['lock_durations'].update(lock_duration_optimization['new_durations'])
                optimization_results['changes_made'].append('lock_durations')
                optimization_results['expected_improvements']['lock_durations'] = lock_duration_optimization['expected_improvement']
            
            # Save optimization results
            stock_profile['optimization_results'][optimization_results['optimization_id']] = optimization_results
            stock_profile['learning_state']['optimization_cycles'] += 1
            stock_profile['learning_state']['last_optimization'] = datetime.now().isoformat()
            
            # Log optimization
            self._log_optimization(stock_profile['stock'], optimization_results)
            
        except Exception as e:
            logger.error(f"Error optimizing signal parameters: {str(e)}")

    def _optimize_entry_zones(self, signal_history: List[Dict]) -> Optional[Dict]:
        """Optimize entry zone sizes based on success clusters"""
        try:
            # Analyze success rates by entry zone size
            zone_performance = defaultdict(list)
            for signal in signal_history:
                zone = round(signal.get('entry_zone', 0.10), 3)
                success = signal.get('success', False)
                returns = signal.get('returns', 0.0)
                zone_performance[zone].append({'success': success, 'returns': returns})
            
            if len(zone_performance) < 2:
                return None  # Need multiple zones to optimize
            
            # Find best performing zone
            best_zone = None
            best_performance = 0
            
            for zone, results in zone_performance.items():
                if len(results) >= 3:  # Minimum samples
                    success_rate = sum(r['success'] for r in results) / len(results)
                    avg_returns = np.mean([r['returns'] for r in results])
                    
                    # Combined score (success rate + returns)
                    performance_score = success_rate * 0.7 + (avg_returns * 10) * 0.3
                    
                    if performance_score > best_performance:
                        best_performance = performance_score
                        best_zone = zone
            
            if best_zone and best_zone != 0.10:  # Different from default
                return {
                    'new_zones': {
                        'buy_zone': best_zone,
                        'sell_zone': best_zone
                    },
                    'expected_improvement': best_performance - 0.6,  # Baseline comparison
                    'reason': f'Zone {best_zone} shows {best_performance:.2f} performance score'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing entry zones: {str(e)}")
            return None

    def _optimize_confidence_thresholds(self, signal_history: List[Dict]) -> Optional[Dict]:
        """Optimize confidence thresholds based on success patterns"""
        try:
            # Analyze success rates by confidence levels
            confidence_buckets = {
                'low': [],    # 0.60-0.75
                'medium': [], # 0.75-0.85
                'high': []    # 0.85+
            }
            
            for signal in signal_history:
                confidence = signal.get('confidence', 0.75)
                success = signal.get('success', False)
                
                if confidence < 0.75:
                    confidence_buckets['low'].append(success)
                elif confidence < 0.85:
                    confidence_buckets['medium'].append(success)
                else:
                    confidence_buckets['high'].append(success)
            
            # Calculate success rates for each bucket
            bucket_performance = {}
            for bucket, successes in confidence_buckets.items():
                if successes:
                    bucket_performance[bucket] = sum(successes) / len(successes)
            
            # Find optimal threshold
            if bucket_performance.get('high', 0) > bucket_performance.get('medium', 0) + 0.1:
                # High confidence significantly better
                new_threshold = 0.85
                expected_improvement = bucket_performance['high'] - bucket_performance.get('medium', 0.6)
            elif bucket_performance.get('medium', 0) > bucket_performance.get('low', 0) + 0.1:
                # Medium confidence significantly better
                new_threshold = 0.75
                expected_improvement = bucket_performance['medium'] - bucket_performance.get('low', 0.5)
            else:
                return None  # No clear optimization
            
            return {
                'new_thresholds': {
                    'minimum': new_threshold,
                    'preferred': new_threshold + 0.05
                },
                'expected_improvement': expected_improvement,
                'reason': f'Confidence threshold {new_threshold} shows better performance'
            }
            
        except Exception as e:
            logger.error(f"Error optimizing confidence thresholds: {str(e)}")
            return None

    def _optimize_timeframe_preferences(self, signal_history: List[Dict]) -> Optional[Dict]:
        """Optimize timeframe preferences based on success patterns"""
        try:
            timeframe_performance = defaultdict(list)
            
            for signal in signal_history:
                timeframe = signal.get('timeframe', '5D')
                success = signal.get('success', False)
                returns = signal.get('returns', 0.0)
                timeframe_performance[timeframe].append({'success': success, 'returns': returns})
            
            # Calculate performance scores for timeframes
            timeframe_scores = {}
            for timeframe, results in timeframe_performance.items():
                if len(results) >= 3:  # Minimum samples
                    success_rate = sum(r['success'] for r in results) / len(results)
                    avg_returns = np.mean([r['returns'] for r in results])
                    
                    # Combined score
                    performance_score = success_rate * 0.8 + (avg_returns * 10) * 0.2
                    timeframe_scores[timeframe] = performance_score
            
            if len(timeframe_scores) < 2:
                return None
            
            # Select top 2 timeframes
            sorted_timeframes = sorted(timeframe_scores.items(), key=lambda x: x[1], reverse=True)
            top_timeframes = [tf for tf, score in sorted_timeframes[:2]]
            
            # Check if this is different from current preferences
            current_prefs = ['5D', '10D']  # Default
            if set(top_timeframes) != set(current_prefs):
                best_score = sorted_timeframes[0][1]
                return {
                    'new_preferences': top_timeframes,
                    'expected_improvement': best_score - 0.6,
                    'reason': f'Timeframes {top_timeframes} show best performance'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing timeframe preferences: {str(e)}")
            return None

    def _optimize_lock_durations(self, signal_history: List[Dict]) -> Optional[Dict]:
        """Optimize lock durations based on volatility and success patterns"""
        try:
            volatility_duration_performance = defaultdict(lambda: defaultdict(list))
            
            for signal in signal_history:
                volatility = signal.get('market_volatility', 0.02)
                duration = signal.get('lock_duration', 5)
                success = signal.get('success', False)
                
                # Categorize volatility
                vol_category = 'low' if volatility < 0.02 else 'medium' if volatility < 0.04 else 'high'
                volatility_duration_performance[vol_category][duration].append(success)
            
            new_durations = {}
            expected_improvement = 0
            
            for vol_category, duration_data in volatility_duration_performance.items():
                if not duration_data:
                    continue
                
                # Find best duration for this volatility category
                best_duration = None
                best_success_rate = 0
                
                for duration, successes in duration_data.items():
                    if len(successes) >= 3:  # Minimum samples
                        success_rate = sum(successes) / len(successes)
                        if success_rate > best_success_rate:
                            best_success_rate = success_rate
                            best_duration = duration
                
                if best_duration:
                    new_durations[f'{vol_category}_volatility'] = best_duration
                    expected_improvement += best_success_rate - 0.6  # Baseline
            
            if new_durations:
                return {
                    'new_durations': new_durations,
                    'expected_improvement': expected_improvement / len(new_durations),
                    'reason': 'Optimized lock durations based on volatility patterns'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error optimizing lock durations: {str(e)}")
            return None

    def get_personalized_signal_settings(self, stock: str, market_conditions: Dict, 
                                       user_id: str = 'default_user') -> Dict[str, Any]:
        """Get personalized signal settings for specific stock and market conditions"""
        try:
            stock_profile = self.get_or_create_stock_profile(stock, user_id)
            current_settings = stock_profile['current_settings']
            
            # Adjust settings based on current market conditions
            adjusted_settings = current_settings.copy()
            
            # Adjust for current volatility
            current_volatility = market_conditions.get('volatility', 0.02)
            if current_volatility < 0.02:
                vol_category = 'low_volatility'
            elif current_volatility < 0.04:
                vol_category = 'medium_volatility'
            else:
                vol_category = 'high_volatility'
            
            # Apply volatility-specific lock duration
            if vol_category in current_settings['lock_durations']:
                adjusted_settings['recommended_lock_duration'] = current_settings['lock_durations'][vol_category]
            else:
                adjusted_settings['recommended_lock_duration'] = 5  # Default
            
            # Adjust confidence threshold based on market regime
            market_regime = market_conditions.get('regime', 'neutral')
            if market_regime == 'volatile':
                adjusted_settings['confidence_thresholds']['minimum'] += 0.05  # Be more conservative
            elif market_regime == 'stable':
                adjusted_settings['confidence_thresholds']['minimum'] -= 0.02  # Can be slightly less conservative
            
            # Add performance context
            adjusted_settings['performance_context'] = {
                'success_rate': stock_profile['performance_metrics']['success_rate'],
                'best_timeframes': [tf['timeframe'] for tf in stock_profile['performance_metrics']['best_timeframes']],
                'optimization_cycles': stock_profile['learning_state']['optimization_cycles'],
                'last_optimization': stock_profile['learning_state']['last_optimization']
            }
            
            return adjusted_settings
            
        except Exception as e:
            logger.error(f"Error getting personalized signal settings for {stock}: {str(e)}")
            return self.default_profile['preferences']

    def get_optimization_summary(self, user_id: str = 'default_user') -> Dict[str, Any]:
        """Get optimization summary across all stocks for user"""
        try:
            summary = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'total_stocks': 0,
                'optimized_stocks': 0,
                'avg_success_rate': 0.0,
                'best_performing_stocks': [],
                'recent_optimizations': [],
                'optimization_trends': {}
            }
            
            stock_files = [f for f in os.listdir(self.personal_signals_path) if f.endswith('.json') and f != 'user_profiles.json']
            all_success_rates = []
            optimized_count = 0
            
            for stock_file in stock_files:
                stock = stock_file.replace('.json', '')
                stock_profile = self._load_json(os.path.join(self.personal_signals_path, stock_file))
                
                if stock_profile.get('user_id') == user_id:
                    summary['total_stocks'] += 1
                    
                    success_rate = stock_profile.get('performance_metrics', {}).get('success_rate', 0)
                    all_success_rates.append(success_rate)
                    
                    if stock_profile.get('learning_state', {}).get('optimization_cycles', 0) > 0:
                        optimized_count += 1
                        
                        # Add to best performing if success rate > 70%
                        if success_rate > 0.70:
                            summary['best_performing_stocks'].append({
                                'stock': stock,
                                'success_rate': success_rate,
                                'total_signals': stock_profile.get('performance_metrics', {}).get('total_signals', 0)
                            })
            
            summary['optimized_stocks'] = optimized_count
            summary['avg_success_rate'] = np.mean(all_success_rates) if all_success_rates else 0.0
            
            # Sort best performing stocks
            summary['best_performing_stocks'].sort(key=lambda x: x['success_rate'], reverse=True)
            summary['best_performing_stocks'] = summary['best_performing_stocks'][:5]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting optimization summary: {str(e)}")
            return {'error': str(e)}

    def _log_optimization(self, stock: str, optimization_results: Dict):
        """Log optimization results"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.optimization_logs_path, f"optimization_{timestamp}.json")
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'stock': stock,
                'optimization_results': optimization_results
            }
            
            # Load existing logs or create new
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = {'date': timestamp, 'optimizations': []}
            
            logs['optimizations'].append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error logging optimization: {str(e)}")

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

def main():
    """Test Personal Signal Agent functionality"""
    agent = PersonalSignalAgent()
    
    print("=== Testing Personal Signal Agent ===")
    
    # Test signal recording
    test_signal = {
        'signal_id': 'test_signal_1',
        'timeframe': '5D',
        'entry_zone': 0.10,
        'confidence': 0.80,
        'predicted_price': 650.0
    }
    
    test_outcome = {
        'actual_price': 655.0,
        'success': True,
        'returns': 0.008,
        'lock_duration': 5,
        'volatility': 0.025
    }
    
    agent.record_signal_outcome('SBIN', test_signal, test_outcome)
    print("✅ Signal outcome recorded")
    
    # Test personalized settings
    market_conditions = {'volatility': 0.025, 'regime': 'neutral'}
    settings = agent.get_personalized_signal_settings('SBIN', market_conditions)
    print(f"✅ Retrieved personalized settings for SBIN")
    
    # Test optimization summary
    summary = agent.get_optimization_summary()
    print(f"✅ Generated optimization summary: {summary['total_stocks']} stocks tracked")
    
    print("\n✅ Personal Signal Agent testing completed!")

if __name__ == "__main__":
    main()
