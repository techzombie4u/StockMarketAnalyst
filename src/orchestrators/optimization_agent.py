
#!/usr/bin/env python3
"""
Autonomous Optimization Orchestrator (AOO)

This module schedules nightly jobs to:
1. Analyze prediction logs and outcome diffs
2. Launch selective re-training or hyperparameter tuning jobs
3. Adjust internal strategy thresholds
4. Track meta_config.json for auto-adjustments and explanations
5. Version-control model/strategy iterations for explainability
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import schedule
import time
import threading

logger = logging.getLogger(__name__)

class OptimizationAgent:
    def __init__(self):
        self.meta_config_path = "data/orchestration/meta_config.json"
        self.optimization_queue_path = "data/orchestration/optimization_queue.json"
        self.version_control_path = "data/orchestration/version_control.json"
        self.orchestration_logs_path = "logs/goahead/orchestration"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.meta_config_path), exist_ok=True)
        os.makedirs(self.orchestration_logs_path, exist_ok=True)
        
        # Optimization thresholds and settings
        self.optimization_settings = {
            'accuracy_degradation_threshold': 0.05,  # 5% drop triggers optimization
            'confidence_drift_threshold': 0.10,      # 10% confidence drift
            'prediction_volume_threshold': 50,       # Minimum predictions for analysis
            'retraining_cooldown_days': 7,          # Days between retraining attempts
            'hyperparameter_tuning_frequency': 14,   # Days between tuning cycles
            'strategy_adjustment_threshold': 0.08,   # 8% performance change for strategy adjustment
            'auto_adjustment_confidence': 0.80       # Confidence required for auto-adjustments
        }
        
        # Optimization job types
        self.job_types = {
            'model_retraining': {
                'priority': 'high',
                'execution_time_hours': 2,
                'resource_requirements': 'moderate'
            },
            'hyperparameter_tuning': {
                'priority': 'medium',
                'execution_time_hours': 4,
                'resource_requirements': 'high'
            },
            'strategy_threshold_adjustment': {
                'priority': 'low',
                'execution_time_hours': 0.5,
                'resource_requirements': 'low'
            },
            'data_quality_enhancement': {
                'priority': 'medium',
                'execution_time_hours': 1,
                'resource_requirements': 'low'
            }
        }
        
        # Scheduler state
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # Initialize orchestrator
        self._initialize_orchestrator()

    def _initialize_orchestrator(self):
        """Initialize Autonomous Optimization Orchestrator"""
        try:
            if not os.path.exists(self.meta_config_path):
                initial_meta_config = {
                    'version': '1.0.0',
                    'last_updated': datetime.now().isoformat(),
                    'auto_adjustments_history': [],
                    'current_model_versions': {
                        'LSTM': '1.0.0',
                        'RandomForest': '1.0.0',
                        'Ensemble': '1.0.0'
                    },
                    'current_strategy_thresholds': {
                        'confidence_minimum': 0.75,
                        'entry_zone_default': 0.10,
                        'volatility_threshold': 0.025,
                        'signal_strength_minimum': 0.60
                    },
                    'optimization_settings': self.optimization_settings.copy(),
                    'active_experiments': [],
                    'performance_baselines': {}
                }
                self._save_json(self.meta_config_path, initial_meta_config)
                
            if not os.path.exists(self.optimization_queue_path):
                initial_queue = {
                    'pending_jobs': [],
                    'active_jobs': [],
                    'completed_jobs': [],
                    'failed_jobs': [],
                    'queue_stats': {
                        'total_jobs_created': 0,
                        'total_jobs_completed': 0,
                        'total_jobs_failed': 0,
                        'avg_execution_time_minutes': 0
                    }
                }
                self._save_json(self.optimization_queue_path, initial_queue)
                
            if not os.path.exists(self.version_control_path):
                initial_version_control = {
                    'model_versions': {},
                    'strategy_versions': {},
                    'experiment_versions': {},
                    'rollback_points': [],
                    'version_performance_tracking': {}
                }
                self._save_json(self.version_control_path, initial_version_control)
                
        except Exception as e:
            logger.error(f"Error initializing Optimization Orchestrator: {str(e)}")

    def start_autonomous_scheduler(self):
        """Start the autonomous optimization scheduler"""
        try:
            if self.scheduler_running:
                logger.info("Scheduler already running")
                return
            
            # Schedule nightly analysis at 2 AM
            schedule.every().day.at("02:00").do(self._run_nightly_optimization_cycle)
            
            # Schedule hourly light analysis
            schedule.every().hour.do(self._run_hourly_health_check)
            
            # Schedule weekly deep analysis
            schedule.every().sunday.at("03:00").do(self._run_weekly_deep_analysis)
            
            self.scheduler_running = True
            
            # Run scheduler in separate thread
            def run_scheduler():
                while self.scheduler_running:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
            
            self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
            logger.info("✅ Autonomous optimization scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting autonomous scheduler: {str(e)}")

    def stop_autonomous_scheduler(self):
        """Stop the autonomous optimization scheduler"""
        try:
            self.scheduler_running = False
            schedule.clear()
            
            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)
            
            logger.info("✅ Autonomous optimization scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping autonomous scheduler: {str(e)}")

    def _run_nightly_optimization_cycle(self):
        """Run comprehensive nightly optimization cycle"""
        try:
            logger.info("🌙 Starting nightly optimization cycle")
            
            cycle_results = {
                'cycle_id': f"nightly_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'start_time': datetime.now().isoformat(),
                'analysis_results': {},
                'optimization_jobs_created': [],
                'auto_adjustments_made': [],
                'recommendations': []
            }
            
            # 1. Analyze prediction logs and outcomes
            prediction_analysis = self._analyze_prediction_performance()
            cycle_results['analysis_results']['prediction_performance'] = prediction_analysis
            
            # 2. Detect performance degradation
            degradation_analysis = self._detect_performance_degradation(prediction_analysis)
            cycle_results['analysis_results']['degradation_analysis'] = degradation_analysis
            
            # 3. Queue optimization jobs based on analysis
            optimization_jobs = self._queue_optimization_jobs(degradation_analysis)
            cycle_results['optimization_jobs_created'] = optimization_jobs
            
            # 4. Make safe automatic adjustments
            auto_adjustments = self._make_automatic_adjustments(degradation_analysis)
            cycle_results['auto_adjustments_made'] = auto_adjustments
            
            # 5. Generate recommendations for manual review
            recommendations = self._generate_optimization_recommendations(degradation_analysis)
            cycle_results['recommendations'] = recommendations
            
            # 6. Update version control
            self._update_version_control(cycle_results)
            
            cycle_results['end_time'] = datetime.now().isoformat()
            cycle_results['status'] = 'completed'
            
            # Log cycle results
            self._log_optimization_cycle(cycle_results)
            
            logger.info(f"✅ Nightly optimization cycle completed: {len(optimization_jobs)} jobs queued, {len(auto_adjustments)} auto-adjustments made")
            
        except Exception as e:
            logger.error(f"Error in nightly optimization cycle: {str(e)}")

    def _run_hourly_health_check(self):
        """Run lightweight hourly health check"""
        try:
            health_check = {
                'timestamp': datetime.now().isoformat(),
                'system_health': 'unknown',
                'critical_issues': [],
                'warnings': []
            }
            
            # Check recent prediction accuracy
            recent_accuracy = self._check_recent_accuracy()
            if recent_accuracy < 0.60:
                health_check['critical_issues'].append(f"Recent accuracy dropped to {recent_accuracy:.2%}")
            elif recent_accuracy < 0.70:
                health_check['warnings'].append(f"Recent accuracy at {recent_accuracy:.2%}")
            
            # Check system resources
            resource_status = self._check_system_resources()
            if resource_status['status'] == 'critical':
                health_check['critical_issues'].append("System resources critically low")
            elif resource_status['status'] == 'warning':
                health_check['warnings'].append("System resources under pressure")
            
            # Check job queue status
            queue_status = self._check_optimization_queue_status()
            if queue_status['failed_jobs'] > 3:
                health_check['warnings'].append("Multiple optimization jobs failing")
            
            # Determine overall health
            if health_check['critical_issues']:
                health_check['system_health'] = 'critical'
                # Trigger immediate attention
                self._handle_critical_health_issues(health_check['critical_issues'])
            elif health_check['warnings']:
                health_check['system_health'] = 'warning'
            else:
                health_check['system_health'] = 'healthy'
            
            # Log health check (only if issues found)
            if health_check['critical_issues'] or health_check['warnings']:
                self._log_health_check(health_check)
            
        except Exception as e:
            logger.error(f"Error in hourly health check: {str(e)}")

    def _run_weekly_deep_analysis(self):
        """Run comprehensive weekly deep analysis"""
        try:
            logger.info("📊 Starting weekly deep analysis")
            
            deep_analysis = {
                'analysis_id': f"weekly_{datetime.now().strftime('%Y%m%d')}",
                'start_time': datetime.now().isoformat(),
                'performance_trends': {},
                'model_comparison': {},
                'strategy_effectiveness': {},
                'recommendations': []
            }
            
            # Analyze performance trends over the week
            performance_trends = self._analyze_weekly_performance_trends()
            deep_analysis['performance_trends'] = performance_trends
            
            # Compare model performances
            model_comparison = self._compare_model_performances()
            deep_analysis['model_comparison'] = model_comparison
            
            # Analyze strategy effectiveness
            strategy_effectiveness = self._analyze_strategy_effectiveness()
            deep_analysis['strategy_effectiveness'] = strategy_effectiveness
            
            # Generate strategic recommendations
            strategic_recommendations = self._generate_strategic_recommendations(deep_analysis)
            deep_analysis['recommendations'] = strategic_recommendations
            
            deep_analysis['end_time'] = datetime.now().isoformat()
            
            # Save deep analysis results
            self._save_deep_analysis(deep_analysis)
            
            logger.info("✅ Weekly deep analysis completed")
            
        except Exception as e:
            logger.error(f"Error in weekly deep analysis: {str(e)}")

    def _analyze_prediction_performance(self) -> Dict[str, Any]:
        """Analyze recent prediction performance"""
        try:
            # Load recent prediction data
            prediction_history = self._load_recent_predictions(days=7)
            
            if not prediction_history:
                return {'status': 'no_data', 'message': 'No recent predictions to analyze'}
            
            analysis = {
                'total_predictions': len(prediction_history),
                'accuracy_by_model': {},
                'accuracy_by_timeframe': {},
                'accuracy_by_stock': {},
                'confidence_analysis': {},
                'trend_analysis': {}
            }
            
            # Analyze by model
            model_performance = defaultdict(list)
            for pred in prediction_history:
                model = pred.get('model', 'unknown')
                accuracy = self._calculate_prediction_accuracy(pred)
                model_performance[model].append(accuracy)
            
            for model, accuracies in model_performance.items():
                analysis['accuracy_by_model'][model] = {
                    'avg_accuracy': np.mean(accuracies),
                    'std_accuracy': np.std(accuracies),
                    'sample_count': len(accuracies),
                    'trend': self._calculate_trend(accuracies)
                }
            
            # Analyze by timeframe
            timeframe_performance = defaultdict(list)
            for pred in prediction_history:
                timeframe = pred.get('timeframe', '5D')
                accuracy = self._calculate_prediction_accuracy(pred)
                timeframe_performance[timeframe].append(accuracy)
            
            for timeframe, accuracies in timeframe_performance.items():
                analysis['accuracy_by_timeframe'][timeframe] = {
                    'avg_accuracy': np.mean(accuracies),
                    'sample_count': len(accuracies)
                }
            
            # Analyze confidence vs accuracy correlation
            confidences = [pred.get('confidence', 0) / 100.0 for pred in prediction_history]
            accuracies = [self._calculate_prediction_accuracy(pred) for pred in prediction_history]
            
            if len(confidences) > 5:
                correlation = np.corrcoef(confidences, accuracies)[0, 1]
                analysis['confidence_analysis'] = {
                    'confidence_accuracy_correlation': correlation,
                    'avg_confidence': np.mean(confidences),
                    'avg_accuracy': np.mean(accuracies)
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing prediction performance: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def _detect_performance_degradation(self, prediction_analysis: Dict) -> Dict[str, Any]:
        """Detect performance degradation patterns"""
        try:
            degradation_analysis = {
                'overall_degradation': False,
                'degraded_models': [],
                'degraded_timeframes': [],
                'degraded_stocks': [],
                'severity': 'none',
                'recommended_actions': []
            }
            
            # Load baseline performance
            meta_config = self._load_json(self.meta_config_path)
            baselines = meta_config.get('performance_baselines', {})
            
            threshold = self.optimization_settings['accuracy_degradation_threshold']
            
            # Check model degradation
            for model, performance in prediction_analysis.get('accuracy_by_model', {}).items():
                current_accuracy = performance['avg_accuracy']
                baseline_accuracy = baselines.get(f'model_{model}', 0.75)  # Default baseline
                
                degradation = baseline_accuracy - current_accuracy
                if degradation > threshold:
                    degradation_analysis['degraded_models'].append({
                        'model': model,
                        'current_accuracy': current_accuracy,
                        'baseline_accuracy': baseline_accuracy,
                        'degradation': degradation,
                        'sample_count': performance['sample_count']
                    })
            
            # Check timeframe degradation
            for timeframe, performance in prediction_analysis.get('accuracy_by_timeframe', {}).items():
                current_accuracy = performance['avg_accuracy']
                baseline_accuracy = baselines.get(f'timeframe_{timeframe}', 0.70)
                
                degradation = baseline_accuracy - current_accuracy
                if degradation > threshold:
                    degradation_analysis['degraded_timeframes'].append({
                        'timeframe': timeframe,
                        'current_accuracy': current_accuracy,
                        'baseline_accuracy': baseline_accuracy,
                        'degradation': degradation
                    })
            
            # Determine overall degradation and severity
            total_degraded = len(degradation_analysis['degraded_models']) + len(degradation_analysis['degraded_timeframes'])
            
            if total_degraded > 0:
                degradation_analysis['overall_degradation'] = True
                
                # Calculate severity
                max_degradation = 0
                if degradation_analysis['degraded_models']:
                    max_degradation = max(max_degradation, max(d['degradation'] for d in degradation_analysis['degraded_models']))
                if degradation_analysis['degraded_timeframes']:
                    max_degradation = max(max_degradation, max(d['degradation'] for d in degradation_analysis['degraded_timeframes']))
                
                if max_degradation > 0.15:  # 15% degradation
                    degradation_analysis['severity'] = 'critical'
                elif max_degradation > 0.10:  # 10% degradation
                    degradation_analysis['severity'] = 'high'
                else:
                    degradation_analysis['severity'] = 'medium'
            
            return degradation_analysis
            
        except Exception as e:
            logger.error(f"Error detecting performance degradation: {str(e)}")
            return {'overall_degradation': False, 'error': str(e)}

    def _queue_optimization_jobs(self, degradation_analysis: Dict) -> List[Dict]:
        """Queue optimization jobs based on degradation analysis"""
        try:
            optimization_queue = self._load_json(self.optimization_queue_path)
            queued_jobs = []
            
            # Queue model retraining jobs for degraded models
            for degraded_model in degradation_analysis.get('degraded_models', []):
                job = {
                    'job_id': f"retrain_{degraded_model['model']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'job_type': 'model_retraining',
                    'priority': 'high' if degraded_model['degradation'] > 0.10 else 'medium',
                    'target_model': degraded_model['model'],
                    'reason': f"Performance degraded by {degraded_model['degradation']:.2%}",
                    'created_at': datetime.now().isoformat(),
                    'status': 'pending',
                    'parameters': {
                        'model_type': degraded_model['model'],
                        'training_window_days': 180,
                        'validation_split': 0.2,
                        'hyperparameter_optimization': True
                    }
                }
                
                optimization_queue['pending_jobs'].append(job)
                queued_jobs.append(job)
            
            # Queue hyperparameter tuning for models with medium degradation
            for degraded_model in degradation_analysis.get('degraded_models', []):
                if degraded_model['degradation'] < 0.10:  # Medium degradation
                    job = {
                        'job_id': f"tune_{degraded_model['model']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'job_type': 'hyperparameter_tuning',
                        'priority': 'medium',
                        'target_model': degraded_model['model'],
                        'reason': f"Medium performance degradation: {degraded_model['degradation']:.2%}",
                        'created_at': datetime.now().isoformat(),
                        'status': 'pending',
                        'parameters': {
                            'model_type': degraded_model['model'],
                            'tuning_iterations': 50,
                            'optimization_metric': 'accuracy'
                        }
                    }
                    
                    optimization_queue['pending_jobs'].append(job)
                    queued_jobs.append(job)
            
            # Update queue statistics
            optimization_queue['queue_stats']['total_jobs_created'] += len(queued_jobs)
            
            # Save updated queue
            self._save_json(self.optimization_queue_path, optimization_queue)
            
            return queued_jobs
            
        except Exception as e:
            logger.error(f"Error queueing optimization jobs: {str(e)}")
            return []

    def _make_automatic_adjustments(self, degradation_analysis: Dict) -> List[Dict]:
        """Make safe automatic adjustments to strategy thresholds"""
        try:
            meta_config = self._load_json(self.meta_config_path)
            auto_adjustments = []
            
            # Only make adjustments if we have high confidence
            if degradation_analysis.get('severity') not in ['critical', 'high']:
                return auto_adjustments  # Too risky for auto-adjustment
            
            current_thresholds = meta_config['current_strategy_thresholds']
            
            # Adjust confidence threshold if multiple models are degraded
            degraded_models_count = len(degradation_analysis.get('degraded_models', []))
            if degraded_models_count >= 2:
                current_confidence = current_thresholds['confidence_minimum']
                if current_confidence < 0.85:  # Safety limit
                    new_confidence = min(0.85, current_confidence + 0.05)
                    
                    adjustment = {
                        'adjustment_id': f"auto_conf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'timestamp': datetime.now().isoformat(),
                        'adjustment_type': 'confidence_threshold',
                        'parameter': 'confidence_minimum',
                        'old_value': current_confidence,
                        'new_value': new_confidence,
                        'reason': f"Multiple models degraded ({degraded_models_count}), increasing confidence threshold",
                        'expected_impact': 'Reduce false positives by being more selective'
                    }
                    
                    current_thresholds['confidence_minimum'] = new_confidence
                    auto_adjustments.append(adjustment)
            
            # Adjust entry zone if timeframe accuracy is degraded
            degraded_timeframes = degradation_analysis.get('degraded_timeframes', [])
            if degraded_timeframes:
                current_entry_zone = current_thresholds['entry_zone_default']
                if current_entry_zone > 0.05:  # Safety limit
                    new_entry_zone = max(0.05, current_entry_zone - 0.02)
                    
                    adjustment = {
                        'adjustment_id': f"auto_zone_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'timestamp': datetime.now().isoformat(),
                        'adjustment_type': 'entry_zone',
                        'parameter': 'entry_zone_default',
                        'old_value': current_entry_zone,
                        'new_value': new_entry_zone,
                        'reason': f"Timeframe accuracy degraded, tightening entry zones",
                        'expected_impact': 'More precise entry timing'
                    }
                    
                    current_thresholds['entry_zone_default'] = new_entry_zone
                    auto_adjustments.append(adjustment)
            
            # Record adjustments in meta config
            if auto_adjustments:
                meta_config['auto_adjustments_history'].extend(auto_adjustments)
                meta_config['last_updated'] = datetime.now().isoformat()
                self._save_json(self.meta_config_path, meta_config)
            
            return auto_adjustments
            
        except Exception as e:
            logger.error(f"Error making automatic adjustments: {str(e)}")
            return []

    def _generate_optimization_recommendations(self, degradation_analysis: Dict) -> List[Dict]:
        """Generate optimization recommendations for manual review"""
        try:
            recommendations = []
            
            # Recommend data quality improvements
            if degradation_analysis.get('overall_degradation'):
                recommendations.append({
                    'recommendation_id': f"data_quality_{datetime.now().strftime('%Y%m%d')}",
                    'type': 'data_quality_improvement',
                    'priority': 'high',
                    'title': 'Review Data Quality',
                    'description': 'Performance degradation detected. Consider reviewing data sources and quality.',
                    'suggested_actions': [
                        'Check for data source changes or outages',
                        'Validate technical indicator calculations',
                        'Review recent market regime changes',
                        'Consider expanding training dataset'
                    ],
                    'expected_effort': 'medium',
                    'expected_impact': 'high'
                })
            
            # Recommend model architecture changes for severely degraded models
            for degraded_model in degradation_analysis.get('degraded_models', []):
                if degraded_model['degradation'] > 0.15:  # Severe degradation
                    recommendations.append({
                        'recommendation_id': f"arch_change_{degraded_model['model']}_{datetime.now().strftime('%Y%m%d')}",
                        'type': 'model_architecture_change',
                        'priority': 'high',
                        'title': f"Consider Architecture Change for {degraded_model['model']}",
                        'description': f"{degraded_model['model']} showing severe degradation ({degraded_model['degradation']:.2%})",
                        'suggested_actions': [
                            f'Evaluate alternative architectures for {degraded_model["model"]}',
                            'Consider ensemble methods',
                            'Review feature engineering',
                            'Analyze model capacity vs complexity'
                        ],
                        'expected_effort': 'high',
                        'expected_impact': 'high'
                    })
            
            # Recommend strategy review for multiple degraded timeframes
            degraded_timeframes = degradation_analysis.get('degraded_timeframes', [])
            if len(degraded_timeframes) >= 2:
                recommendations.append({
                    'recommendation_id': f"strategy_review_{datetime.now().strftime('%Y%m%d')}",
                    'type': 'strategy_review',
                    'priority': 'medium',
                    'title': 'Review Trading Strategy',
                    'description': f'Multiple timeframes showing degradation: {[t["timeframe"] for t in degraded_timeframes]}',
                    'suggested_actions': [
                        'Review market regime detection',
                        'Evaluate timeframe-specific strategies',
                        'Consider adaptive timeframe selection',
                        'Review risk management parameters'
                    ],
                    'expected_effort': 'medium',
                    'expected_impact': 'medium'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {str(e)}")
            return []

    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        try:
            meta_config = self._load_json(self.meta_config_path)
            optimization_queue = self._load_json(self.optimization_queue_path)
            
            status = {
                'scheduler_running': self.scheduler_running,
                'last_optimization_cycle': None,
                'pending_jobs': len(optimization_queue.get('pending_jobs', [])),
                'active_jobs': len(optimization_queue.get('active_jobs', [])),
                'recent_auto_adjustments': len([
                    adj for adj in meta_config.get('auto_adjustments_history', [])
                    if (datetime.now() - datetime.fromisoformat(adj['timestamp'])).days <= 7
                ]),
                'current_model_versions': meta_config.get('current_model_versions', {}),
                'current_thresholds': meta_config.get('current_strategy_thresholds', {}),
                'system_health': self._get_system_health_summary()
            }
            
            # Find last optimization cycle
            log_files = [f for f in os.listdir(self.orchestration_logs_path) if f.startswith('optimization_cycle_')]
            if log_files:
                latest_log = sorted(log_files)[-1]
                status['last_optimization_cycle'] = latest_log.replace('optimization_cycle_', '').replace('.json', '')
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting orchestration status: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    # Helper methods
    def _load_recent_predictions(self, days: int = 7) -> List[Dict]:
        """Load recent prediction data for analysis"""
        try:
            history_path = "data/tracking/predictions_history.json"
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    data = json.load(f)
                    predictions = data.get('predictions', [])
                    
                    # Filter by date
                    cutoff_date = datetime.now() - timedelta(days=days)
                    recent_predictions = []
                    
                    for pred in predictions:
                        try:
                            pred_date = datetime.fromisoformat(pred.get('timestamp', ''))
                            if pred_date >= cutoff_date:
                                recent_predictions.append(pred)
                        except:
                            continue
                    
                    return recent_predictions
            return []
        except Exception as e:
            logger.error(f"Error loading recent predictions: {str(e)}")
            return []

    def _calculate_prediction_accuracy(self, prediction: Dict) -> float:
        """Calculate accuracy for a single prediction"""
        try:
            predicted_price = prediction.get('predicted_price', 0)
            actual_price = prediction.get('actual_price', predicted_price)
            
            if actual_price == 0:
                return 0.0
            
            accuracy = 1.0 - abs(predicted_price - actual_price) / actual_price
            return max(0.0, min(1.0, accuracy))
            
        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {str(e)}")
            return 0.0

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values"""
        try:
            if len(values) < 3:
                return 'insufficient_data'
            
            # Simple linear regression slope
            x = list(range(len(values)))
            slope = np.polyfit(x, values, 1)[0]
            
            if slope > 0.01:
                return 'improving'
            elif slope < -0.01:
                return 'degrading'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"Error calculating trend: {str(e)}")
            return 'unknown'

    def _check_recent_accuracy(self) -> float:
        """Check recent overall accuracy"""
        try:
            recent_predictions = self._load_recent_predictions(days=1)
            if not recent_predictions:
                return 0.75  # Default assumption
            
            accuracies = [self._calculate_prediction_accuracy(pred) for pred in recent_predictions]
            return np.mean(accuracies) if accuracies else 0.75
            
        except Exception as e:
            logger.error(f"Error checking recent accuracy: {str(e)}")
            return 0.75

    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource status (simplified)"""
        try:
            # Simplified resource check - in production, use proper system monitoring
            return {
                'status': 'healthy',
                'cpu_usage': 45,  # Placeholder
                'memory_usage': 60,  # Placeholder
                'disk_usage': 30   # Placeholder
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {str(e)}")
            return {'status': 'unknown'}

    def _check_optimization_queue_status(self) -> Dict[str, Any]:
        """Check optimization queue status"""
        try:
            optimization_queue = self._load_json(self.optimization_queue_path)
            return {
                'pending_jobs': len(optimization_queue.get('pending_jobs', [])),
                'active_jobs': len(optimization_queue.get('active_jobs', [])),
                'failed_jobs': len(optimization_queue.get('failed_jobs', []))
            }
        except Exception as e:
            logger.error(f"Error checking queue status: {str(e)}")
            return {'pending_jobs': 0, 'active_jobs': 0, 'failed_jobs': 0}

    def _get_system_health_summary(self) -> str:
        """Get overall system health summary"""
        try:
            recent_accuracy = self._check_recent_accuracy()
            queue_status = self._check_optimization_queue_status()
            
            if recent_accuracy < 0.60 or queue_status['failed_jobs'] > 5:
                return 'critical'
            elif recent_accuracy < 0.70 or queue_status['failed_jobs'] > 2:
                return 'warning'
            else:
                return 'healthy'
                
        except Exception as e:
            logger.error(f"Error getting system health summary: {str(e)}")
            return 'unknown'

    def _handle_critical_health_issues(self, issues: List[str]):
        """Handle critical health issues"""
        try:
            # Log critical issues
            critical_log = {
                'timestamp': datetime.now().isoformat(),
                'issues': issues,
                'action_taken': 'logged_for_manual_review'
            }
            
            critical_log_path = os.path.join(self.orchestration_logs_path, 'critical_issues.json')
            
            if os.path.exists(critical_log_path):
                with open(critical_log_path, 'r') as f:
                    logs = json.load(f)
            else:
                logs = {'critical_issues': []}
            
            logs['critical_issues'].append(critical_log)
            
            with open(critical_log_path, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error handling critical health issues: {str(e)}")

    def _update_version_control(self, cycle_results: Dict):
        """Update version control with cycle results"""
        try:
            version_control = self._load_json(self.version_control_path)
            
            # Create version entry for this cycle
            version_entry = {
                'version_id': cycle_results['cycle_id'],
                'timestamp': cycle_results['start_time'],
                'changes_made': cycle_results.get('auto_adjustments_made', []),
                'optimization_jobs': cycle_results.get('optimization_jobs_created', []),
                'performance_snapshot': cycle_results.get('analysis_results', {})
            }
            
            version_control['strategy_versions'][cycle_results['cycle_id']] = version_entry
            
            # Keep only last 50 versions
            if len(version_control['strategy_versions']) > 50:
                oldest_versions = sorted(version_control['strategy_versions'].keys())[:len(version_control['strategy_versions']) - 50]
                for old_version in oldest_versions:
                    del version_control['strategy_versions'][old_version]
            
            self._save_json(self.version_control_path, version_control)
            
        except Exception as e:
            logger.error(f"Error updating version control: {str(e)}")

    def _log_optimization_cycle(self, cycle_results: Dict):
        """Log optimization cycle results"""
        try:
            cycle_date = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.orchestration_logs_path, f"optimization_cycle_{cycle_date}.json")
            
            with open(log_file, 'w') as f:
                json.dump(cycle_results, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error logging optimization cycle: {str(e)}")

    def _log_health_check(self, health_check: Dict):
        """Log health check results"""
        try:
            health_date = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.orchestration_logs_path, f"health_check_{health_date}.json")
            
            # Append to daily health log
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = {'date': health_date, 'health_checks': []}
            
            logs['health_checks'].append(health_check)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error logging health check: {str(e)}")

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

    # Additional analysis methods (placeholder implementations)
    def _analyze_weekly_performance_trends(self) -> Dict:
        """Analyze weekly performance trends"""
        return {'status': 'placeholder', 'message': 'Weekly analysis not yet implemented'}

    def _compare_model_performances(self) -> Dict:
        """Compare model performances"""
        return {'status': 'placeholder', 'message': 'Model comparison not yet implemented'}

    def _analyze_strategy_effectiveness(self) -> Dict:
        """Analyze strategy effectiveness"""
        return {'status': 'placeholder', 'message': 'Strategy analysis not yet implemented'}

    def _generate_strategic_recommendations(self, deep_analysis: Dict) -> List[Dict]:
        """Generate strategic recommendations"""
        return [{'type': 'placeholder', 'message': 'Strategic recommendations not yet implemented'}]

    def _save_deep_analysis(self, deep_analysis: Dict):
        """Save deep analysis results"""
        try:
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            analysis_file = os.path.join(self.orchestration_logs_path, f"deep_analysis_{analysis_date}.json")
            
            with open(analysis_file, 'w') as f:
                json.dump(deep_analysis, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving deep analysis: {str(e)}")

def main():
    """Test Optimization Agent functionality"""
    agent = OptimizationAgent()
    
    print("=== Testing Optimization Agent ===")
    
    # Test analysis
    prediction_analysis = agent._analyze_prediction_performance()
    print(f"✅ Prediction analysis: {prediction_analysis.get('total_predictions', 0)} predictions analyzed")
    
    # Test degradation detection
    degradation_analysis = agent._detect_performance_degradation(prediction_analysis)
    print(f"✅ Degradation analysis: {degradation_analysis.get('severity', 'none')} severity")
    
    # Test status
    status = agent.get_orchestration_status()
    print(f"✅ Orchestration status: {status.get('system_health', 'unknown')} health")
    
    print("\n✅ Optimization Agent testing completed!")

if __name__ == "__main__":
    main()
