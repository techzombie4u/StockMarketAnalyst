
#!/usr/bin/env python3
"""
AI Code Auditor & Suggestor

This module provides automated code auditing for model performance:
1. Weekly model performance analysis
2. Model suggestion generation (e.g., "Try XGBoost instead of RF")
3. Underperforming segment identification
4. Audit log generation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class AICodeAuditor:
    def __init__(self):
        self.audit_logs_path = "logs/goahead/audit"
        self.performance_data_path = "data/tracking/performance_history.json"
        self.suggestions_path = "data/tracking/audit_suggestions.json"
        
        # Ensure directories exist
        os.makedirs(self.audit_logs_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.performance_data_path), exist_ok=True)
        
        # Model performance thresholds
        self.performance_thresholds = {
            'poor': 60.0,
            'average': 75.0,
            'good': 85.0,
            'excellent': 90.0
        }
        
        # Model alternatives mapping
        self.model_alternatives = {
            'LSTM': ['XGBoost', 'GRU', 'LSTM_Enhanced'],
            'RandomForest': ['XGBoost', 'GradientBoosting', 'ExtraTrees'],
            'LinearRegression': ['Ridge', 'Lasso', 'ElasticNet'],
            'XGBoost': ['LightGBM', 'CatBoost', 'RandomForest']
        }
        
        # Initialize auditor
        self._initialize_auditor()

    def _initialize_auditor(self):
        """Initialize auditor data structures"""
        try:
            if not os.path.exists(self.performance_data_path):
                initial_data = {
                    'model_performance_history': {},
                    'stock_performance_history': {},
                    'timeframe_performance_history': {},
                    'last_audit': None,
                    'created_at': datetime.now().isoformat()
                }
                self._save_json(self.performance_data_path, initial_data)
                
            if not os.path.exists(self.suggestions_path):
                initial_suggestions = {
                    'active_suggestions': [],
                    'implemented_suggestions': [],
                    'dismissed_suggestions': [],
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.suggestions_path, initial_suggestions)
                
        except Exception as e:
            logger.error(f"Error initializing AI Code Auditor: {str(e)}")

    def run_weekly_audit(self) -> Dict[str, Any]:
        """Run comprehensive weekly performance audit"""
        try:
            logger.info("Starting weekly AI code audit...")
            
            audit_timestamp = datetime.now()
            audit_id = f"audit_{audit_timestamp.strftime('%Y%m%d_%H%M%S')}"
            
            # Collect performance data
            model_performance = self._analyze_model_performance()
            stock_performance = self._analyze_stock_performance()
            timeframe_performance = self._analyze_timeframe_performance()
            
            # Generate suggestions
            model_suggestions = self._generate_model_suggestions(model_performance)
            optimization_suggestions = self._generate_optimization_suggestions(
                model_performance, stock_performance, timeframe_performance
            )
            
            # Identify underperforming segments
            underperforming_segments = self._identify_underperforming_segments(
                model_performance, stock_performance, timeframe_performance
            )
            
            # Generate comprehensive audit report
            audit_report = {
                'audit_id': audit_id,
                'timestamp': audit_timestamp.isoformat(),
                'audit_period': f"{(audit_timestamp - timedelta(days=7)).strftime('%Y-%m-%d')} to {audit_timestamp.strftime('%Y-%m-%d')}",
                'overall_health': self._calculate_overall_health(model_performance),
                'model_performance_analysis': model_performance,
                'stock_performance_analysis': stock_performance,
                'timeframe_performance_analysis': timeframe_performance,
                'model_suggestions': model_suggestions,
                'optimization_suggestions': optimization_suggestions,
                'underperforming_segments': underperforming_segments,
                'action_items': self._generate_action_items(model_suggestions, optimization_suggestions),
                'risk_assessment': self._assess_risks(underperforming_segments)
            }
            
            # Save audit report
            self._save_audit_report(audit_report)
            
            # Update suggestions
            self._update_active_suggestions(model_suggestions + optimization_suggestions)
            
            logger.info(f"Weekly audit completed: {audit_id}")
            return audit_report
            
        except Exception as e:
            logger.error(f"Error in weekly audit: {str(e)}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def _analyze_model_performance(self) -> Dict[str, Any]:
        """Analyze performance of each model type"""
        try:
            performance_data = self._load_json(self.performance_data_path)
            model_history = performance_data.get('model_performance_history', {})
            
            model_analysis = {}
            
            # Analyze each model
            for model_name in ['LSTM', 'RandomForest', 'LinearRegression', 'XGBoost']:
                if model_name in model_history:
                    recent_performance = self._get_recent_performance(model_history[model_name])
                    
                    analysis = {
                        'average_accuracy': np.mean([p['accuracy'] for p in recent_performance]),
                        'accuracy_trend': self._calculate_trend([p['accuracy'] for p in recent_performance]),
                        'prediction_count': len(recent_performance),
                        'best_accuracy': max([p['accuracy'] for p in recent_performance]) if recent_performance else 0,
                        'worst_accuracy': min([p['accuracy'] for p in recent_performance]) if recent_performance else 0,
                        'consistency_score': self._calculate_consistency([p['accuracy'] for p in recent_performance]),
                        'performance_rating': self._rate_performance(np.mean([p['accuracy'] for p in recent_performance])),
                        'recent_failures': [p for p in recent_performance if p['accuracy'] < self.performance_thresholds['poor']]
                    }
                    
                    model_analysis[model_name] = analysis
                else:
                    # No data available
                    model_analysis[model_name] = {
                        'average_accuracy': 0,
                        'accuracy_trend': 'no_data',
                        'prediction_count': 0,
                        'performance_rating': 'no_data',
                        'status': 'insufficient_data'
                    }
            
            return model_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing model performance: {str(e)}")
            return {}

    def _analyze_stock_performance(self) -> Dict[str, Any]:
        """Analyze performance by stock"""
        try:
            performance_data = self._load_json(self.performance_data_path)
            stock_history = performance_data.get('stock_performance_history', {})
            
            stock_analysis = {}
            
            for stock, history in stock_history.items():
                recent_performance = self._get_recent_performance(history)
                
                if recent_performance:
                    analysis = {
                        'average_accuracy': np.mean([p['accuracy'] for p in recent_performance]),
                        'prediction_count': len(recent_performance),
                        'best_model': self._find_best_model_for_stock(recent_performance),
                        'worst_model': self._find_worst_model_for_stock(recent_performance),
                        'volatility_correlation': self._analyze_volatility_correlation(recent_performance),
                        'performance_rating': self._rate_performance(np.mean([p['accuracy'] for p in recent_performance]))
                    }
                    
                    stock_analysis[stock] = analysis
            
            return stock_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing stock performance: {str(e)}")
            return {}

    def _analyze_timeframe_performance(self) -> Dict[str, Any]:
        """Analyze performance by timeframe"""
        try:
            performance_data = self._load_json(self.performance_data_path)
            timeframe_history = performance_data.get('timeframe_performance_history', {})
            
            timeframe_analysis = {}
            
            for timeframe, history in timeframe_history.items():
                recent_performance = self._get_recent_performance(history)
                
                if recent_performance:
                    analysis = {
                        'average_accuracy': np.mean([p['accuracy'] for p in recent_performance]),
                        'prediction_count': len(recent_performance),
                        'best_performing_stocks': self._get_top_performers(recent_performance, 'stock'),
                        'worst_performing_stocks': self._get_bottom_performers(recent_performance, 'stock'),
                        'model_effectiveness': self._analyze_model_effectiveness_by_timeframe(recent_performance),
                        'performance_rating': self._rate_performance(np.mean([p['accuracy'] for p in recent_performance]))
                    }
                    
                    timeframe_analysis[timeframe] = analysis
            
            return timeframe_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing timeframe performance: {str(e)}")
            return {}

    def _generate_model_suggestions(self, model_performance: Dict) -> List[Dict]:
        """Generate model improvement suggestions"""
        try:
            suggestions = []
            
            for model_name, performance in model_performance.items():
                if performance.get('performance_rating') in ['poor', 'average']:
                    avg_accuracy = performance.get('average_accuracy', 0)
                    
                    # Suggest alternative models
                    if model_name in self.model_alternatives:
                        alternatives = self.model_alternatives[model_name]
                        
                        suggestion = {
                            'type': 'model_replacement',
                            'priority': 'high' if avg_accuracy < self.performance_thresholds['poor'] else 'medium',
                            'current_model': model_name,
                            'suggested_alternatives': alternatives,
                            'reason': f'{model_name} showing {performance.get("performance_rating", "poor")} performance ({avg_accuracy:.1f}% accuracy)',
                            'expected_improvement': self._estimate_improvement(model_name, alternatives),
                            'implementation_effort': self._estimate_effort(model_name, alternatives[0]),
                            'created_at': datetime.now().isoformat()
                        }
                        
                        suggestions.append(suggestion)
                
                # Check for declining trends
                if performance.get('accuracy_trend') == 'declining':
                    suggestion = {
                        'type': 'model_retraining',
                        'priority': 'medium',
                        'model': model_name,
                        'reason': f'{model_name} showing declining accuracy trend',
                        'suggested_action': 'Retrain model with recent data',
                        'implementation_effort': 'low',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    suggestions.append(suggestion)
                
                # Check for inconsistency
                consistency = performance.get('consistency_score', 1.0)
                if consistency < 0.7:
                    suggestion = {
                        'type': 'model_stabilization',
                        'priority': 'medium',
                        'model': model_name,
                        'reason': f'{model_name} showing inconsistent performance (consistency: {consistency:.2f})',
                        'suggested_action': 'Add regularization or ensemble methods',
                        'implementation_effort': 'medium',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating model suggestions: {str(e)}")
            return []

    def _generate_optimization_suggestions(self, model_performance: Dict, 
                                         stock_performance: Dict, 
                                         timeframe_performance: Dict) -> List[Dict]:
        """Generate optimization suggestions based on comprehensive analysis"""
        try:
            suggestions = []
            
            # Analyze cross-model opportunities
            best_models = {}
            for model, perf in model_performance.items():
                if perf.get('average_accuracy', 0) > 0:
                    best_models[model] = perf['average_accuracy']
            
            if best_models:
                best_model = max(best_models, key=best_models.get)
                worst_model = min(best_models, key=best_models.get)
                
                if best_models[best_model] - best_models[worst_model] > 10:
                    suggestion = {
                        'type': 'model_prioritization',
                        'priority': 'high',
                        'recommendation': f'Prioritize {best_model} over {worst_model}',
                        'reason': f'{best_model} outperforms {worst_model} by {best_models[best_model] - best_models[worst_model]:.1f}%',
                        'implementation_effort': 'low',
                        'created_at': datetime.now().isoformat()
                    }
                    suggestions.append(suggestion)
            
            # Stock-specific optimizations
            for stock, perf in stock_performance.items():
                if perf.get('performance_rating') == 'poor':
                    best_model = perf.get('best_model')
                    if best_model:
                        suggestion = {
                            'type': 'stock_model_assignment',
                            'priority': 'medium',
                            'stock': stock,
                            'recommended_model': best_model,
                            'reason': f'{stock} performs best with {best_model}',
                            'implementation_effort': 'low',
                            'created_at': datetime.now().isoformat()
                        }
                        suggestions.append(suggestion)
            
            # Timeframe optimizations
            for timeframe, perf in timeframe_performance.items():
                if perf.get('performance_rating') == 'poor':
                    model_effectiveness = perf.get('model_effectiveness', {})
                    if model_effectiveness:
                        best_tf_model = max(model_effectiveness, key=model_effectiveness.get)
                        suggestion = {
                            'type': 'timeframe_model_assignment',
                            'priority': 'medium',
                            'timeframe': timeframe,
                            'recommended_model': best_tf_model,
                            'reason': f'{timeframe} predictions work best with {best_tf_model}',
                            'implementation_effort': 'low',
                            'created_at': datetime.now().isoformat()
                        }
                        suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return []

    def _identify_underperforming_segments(self, model_performance: Dict,
                                         stock_performance: Dict,
                                         timeframe_performance: Dict) -> List[Dict]:
        """Identify specific underperforming segments"""
        try:
            underperforming = []
            
            # Model segments
            for model, perf in model_performance.items():
                if perf.get('performance_rating') in ['poor', 'average']:
                    segment = {
                        'type': 'model',
                        'segment_name': model,
                        'performance_rating': perf.get('performance_rating'),
                        'average_accuracy': perf.get('average_accuracy', 0),
                        'issues': self._identify_model_issues(perf),
                        'impact_level': self._calculate_impact_level(perf.get('prediction_count', 0))
                    }
                    underperforming.append(segment)
            
            # Stock segments
            for stock, perf in stock_performance.items():
                if perf.get('performance_rating') == 'poor':
                    segment = {
                        'type': 'stock',
                        'segment_name': stock,
                        'performance_rating': perf.get('performance_rating'),
                        'average_accuracy': perf.get('average_accuracy', 0),
                        'issues': ['Consistently poor predictions across models'],
                        'impact_level': self._calculate_impact_level(perf.get('prediction_count', 0))
                    }
                    underperforming.append(segment)
            
            # Timeframe segments
            for timeframe, perf in timeframe_performance.items():
                if perf.get('performance_rating') == 'poor':
                    segment = {
                        'type': 'timeframe',
                        'segment_name': timeframe,
                        'performance_rating': perf.get('performance_rating'),
                        'average_accuracy': perf.get('average_accuracy', 0),
                        'issues': ['Poor performance across multiple stocks'],
                        'impact_level': self._calculate_impact_level(perf.get('prediction_count', 0))
                    }
                    underperforming.append(segment)
            
            return underperforming
            
        except Exception as e:
            logger.error(f"Error identifying underperforming segments: {str(e)}")
            return []

    def record_model_performance(self, model_name: str, stock: str, timeframe: str, 
                               accuracy: float, additional_metrics: Dict = None):
        """Record model performance for audit analysis"""
        try:
            performance_data = self._load_json(self.performance_data_path)
            
            performance_entry = {
                'timestamp': datetime.now().isoformat(),
                'model': model_name,
                'stock': stock,
                'timeframe': timeframe,
                'accuracy': accuracy,
                'additional_metrics': additional_metrics or {}
            }
            
            # Update model performance history
            if model_name not in performance_data['model_performance_history']:
                performance_data['model_performance_history'][model_name] = []
            performance_data['model_performance_history'][model_name].append(performance_entry)
            
            # Update stock performance history
            if stock not in performance_data['stock_performance_history']:
                performance_data['stock_performance_history'][stock] = []
            performance_data['stock_performance_history'][stock].append(performance_entry)
            
            # Update timeframe performance history
            if timeframe not in performance_data['timeframe_performance_history']:
                performance_data['timeframe_performance_history'][timeframe] = []
            performance_data['timeframe_performance_history'][timeframe].append(performance_entry)
            
            self._save_json(self.performance_data_path, performance_data)
            
        except Exception as e:
            logger.error(f"Error recording model performance: {str(e)}")

    def get_audit_suggestions(self, active_only: bool = True) -> List[Dict]:
        """Get current audit suggestions"""
        try:
            suggestions_data = self._load_json(self.suggestions_path)
            
            if active_only:
                return suggestions_data.get('active_suggestions', [])
            else:
                return {
                    'active': suggestions_data.get('active_suggestions', []),
                    'implemented': suggestions_data.get('implemented_suggestions', []),
                    'dismissed': suggestions_data.get('dismissed_suggestions', [])
                }
                
        except Exception as e:
            logger.error(f"Error getting audit suggestions: {str(e)}")
            return []

    def implement_suggestion(self, suggestion_id: str) -> bool:
        """Mark suggestion as implemented"""
        try:
            suggestions_data = self._load_json(self.suggestions_path)
            
            # Find and move suggestion from active to implemented
            active_suggestions = suggestions_data.get('active_suggestions', [])
            implemented_suggestions = suggestions_data.get('implemented_suggestions', [])
            
            for i, suggestion in enumerate(active_suggestions):
                if suggestion.get('id') == suggestion_id:
                    suggestion['implemented_at'] = datetime.now().isoformat()
                    implemented_suggestions.append(suggestion)
                    active_suggestions.pop(i)
                    
                    suggestions_data['active_suggestions'] = active_suggestions
                    suggestions_data['implemented_suggestions'] = implemented_suggestions
                    suggestions_data['last_updated'] = datetime.now().isoformat()
                    
                    self._save_json(self.suggestions_path, suggestions_data)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error implementing suggestion: {str(e)}")
            return False

    # Helper methods
    def _get_recent_performance(self, history: List[Dict], days: int = 7) -> List[Dict]:
        """Get performance data from recent days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            return [p for p in history if datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00')) > cutoff_date]
        except Exception as e:
            logger.error(f"Error getting recent performance: {str(e)}")
            return []

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from values"""
        if len(values) < 2:
            return 'insufficient_data'
        
        # Simple linear trend
        x = list(range(len(values)))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 1:
            return 'improving'
        elif slope < -1:
            return 'declining'
        else:
            return 'stable'

    def _calculate_consistency(self, values: List[float]) -> float:
        """Calculate consistency score (1 - coefficient of variation)"""
        if len(values) < 2:
            return 1.0
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if mean_val == 0:
            return 0.0
        
        cv = std_val / mean_val
        return max(0.0, 1.0 - cv)

    def _rate_performance(self, accuracy: float) -> str:
        """Rate performance based on accuracy"""
        if accuracy >= self.performance_thresholds['excellent']:
            return 'excellent'
        elif accuracy >= self.performance_thresholds['good']:
            return 'good'
        elif accuracy >= self.performance_thresholds['average']:
            return 'average'
        elif accuracy >= self.performance_thresholds['poor']:
            return 'poor'
        else:
            return 'very_poor'

    def _calculate_overall_health(self, model_performance: Dict) -> Dict[str, Any]:
        """Calculate overall system health"""
        try:
            if not model_performance:
                return {'status': 'unknown', 'score': 0}
            
            accuracies = [p.get('average_accuracy', 0) for p in model_performance.values() 
                         if p.get('average_accuracy', 0) > 0]
            
            if not accuracies:
                return {'status': 'no_data', 'score': 0}
            
            overall_accuracy = np.mean(accuracies)
            health_score = overall_accuracy / 100
            
            if overall_accuracy >= self.performance_thresholds['excellent']:
                status = 'excellent'
            elif overall_accuracy >= self.performance_thresholds['good']:
                status = 'good'
            elif overall_accuracy >= self.performance_thresholds['average']:
                status = 'average'
            else:
                status = 'needs_attention'
            
            return {
                'status': status,
                'score': health_score,
                'overall_accuracy': overall_accuracy,
                'active_models': len([p for p in model_performance.values() if p.get('prediction_count', 0) > 0])
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall health: {str(e)}")
            return {'status': 'error', 'score': 0}

    def _save_audit_report(self, audit_report: Dict):
        """Save audit report to file"""
        try:
            timestamp = datetime.now()
            filename = f"{timestamp.strftime('%Y-%m-%d')}.json"
            filepath = os.path.join(self.audit_logs_path, filename)
            
            self._save_json(filepath, audit_report)
            
        except Exception as e:
            logger.error(f"Error saving audit report: {str(e)}")

    def _update_active_suggestions(self, new_suggestions: List[Dict]):
        """Update active suggestions list"""
        try:
            suggestions_data = self._load_json(self.suggestions_path)
            
            # Add IDs to new suggestions
            for i, suggestion in enumerate(new_suggestions):
                suggestion['id'] = f"suggestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}"
            
            suggestions_data['active_suggestions'] = new_suggestions
            suggestions_data['last_updated'] = datetime.now().isoformat()
            
            self._save_json(self.suggestions_path, suggestions_data)
            
        except Exception as e:
            logger.error(f"Error updating active suggestions: {str(e)}")

    def _estimate_improvement(self, current_model: str, alternatives: List[str]) -> str:
        """Estimate potential improvement from model change"""
        improvement_estimates = {
            ('LSTM', 'XGBoost'): '10-15%',
            ('RandomForest', 'XGBoost'): '5-10%',
            ('LinearRegression', 'Ridge'): '3-8%'
        }
        
        best_alternative = alternatives[0] if alternatives else 'Unknown'
        return improvement_estimates.get((current_model, best_alternative), '5-10%')

    def _estimate_effort(self, current_model: str, new_model: str) -> str:
        """Estimate implementation effort"""
        effort_matrix = {
            ('LSTM', 'XGBoost'): 'medium',
            ('RandomForest', 'XGBoost'): 'low',
            ('LinearRegression', 'Ridge'): 'low'
        }
        
        return effort_matrix.get((current_model, new_model), 'medium')

    def _generate_action_items(self, model_suggestions: List[Dict], 
                             optimization_suggestions: List[Dict]) -> List[Dict]:
        """Generate prioritized action items"""
        try:
            all_suggestions = model_suggestions + optimization_suggestions
            
            # Sort by priority
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            sorted_suggestions = sorted(all_suggestions, 
                                      key=lambda x: priority_order.get(x.get('priority', 'low'), 1), 
                                      reverse=True)
            
            action_items = []
            for suggestion in sorted_suggestions[:10]:  # Top 10 items
                action_item = {
                    'action': suggestion.get('suggested_action', suggestion.get('recommendation', 'Review suggestion')),
                    'priority': suggestion.get('priority', 'medium'),
                    'effort': suggestion.get('implementation_effort', 'medium'),
                    'expected_benefit': suggestion.get('expected_improvement', 'TBD'),
                    'type': suggestion.get('type', 'optimization')
                }
                action_items.append(action_item)
            
            return action_items
            
        except Exception as e:
            logger.error(f"Error generating action items: {str(e)}")
            return []

    def _assess_risks(self, underperforming_segments: List[Dict]) -> Dict[str, Any]:
        """Assess risks from underperforming segments"""
        try:
            high_impact_segments = [s for s in underperforming_segments if s.get('impact_level') == 'high']
            medium_impact_segments = [s for s in underperforming_segments if s.get('impact_level') == 'medium']
            
            risk_level = 'low'
            if len(high_impact_segments) > 2:
                risk_level = 'high'
            elif len(high_impact_segments) > 0 or len(medium_impact_segments) > 3:
                risk_level = 'medium'
            
            return {
                'overall_risk_level': risk_level,
                'high_impact_issues': len(high_impact_segments),
                'medium_impact_issues': len(medium_impact_segments),
                'primary_concerns': [s['segment_name'] for s in high_impact_segments],
                'recommendations': self._get_risk_recommendations(risk_level)
            }
            
        except Exception as e:
            logger.error(f"Error assessing risks: {str(e)}")
            return {'overall_risk_level': 'unknown'}

    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get recommendations based on risk level"""
        recommendations = {
            'high': [
                'Immediate attention required for underperforming models',
                'Consider emergency model retraining',
                'Implement fallback strategies'
            ],
            'medium': [
                'Schedule model performance review',
                'Gradually implement suggested improvements',
                'Monitor performance closely'
            ],
            'low': [
                'Continue regular monitoring',
                'Consider optimization suggestions when convenient'
            ]
        }
        
        return recommendations.get(risk_level, ['Review system performance'])

    # Additional helper methods...
    def _find_best_model_for_stock(self, performance_data: List[Dict]) -> str:
        """Find best performing model for a stock"""
        model_accuracy = defaultdict(list)
        for entry in performance_data:
            model_accuracy[entry['model']].append(entry['accuracy'])
        
        model_avg = {model: np.mean(accuracies) for model, accuracies in model_accuracy.items()}
        return max(model_avg, key=model_avg.get) if model_avg else 'Unknown'

    def _find_worst_model_for_stock(self, performance_data: List[Dict]) -> str:
        """Find worst performing model for a stock"""
        model_accuracy = defaultdict(list)
        for entry in performance_data:
            model_accuracy[entry['model']].append(entry['accuracy'])
        
        model_avg = {model: np.mean(accuracies) for model, accuracies in model_accuracy.items()}
        return min(model_avg, key=model_avg.get) if model_avg else 'Unknown'

    def _analyze_volatility_correlation(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """Analyze correlation between volatility and performance"""
        # Placeholder - would need actual volatility data
        return {
            'correlation': 'medium_negative',
            'note': 'Performance tends to decrease with higher volatility'
        }

    def _get_top_performers(self, performance_data: List[Dict], field: str) -> List[str]:
        """Get top performing items by field"""
        field_accuracy = defaultdict(list)
        for entry in performance_data:
            field_accuracy[entry[field]].append(entry['accuracy'])
        
        field_avg = {item: np.mean(accuracies) for item, accuracies in field_accuracy.items()}
        sorted_items = sorted(field_avg.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:3]]

    def _get_bottom_performers(self, performance_data: List[Dict], field: str) -> List[str]:
        """Get bottom performing items by field"""
        field_accuracy = defaultdict(list)
        for entry in performance_data:
            field_accuracy[entry[field]].append(entry['accuracy'])
        
        field_avg = {item: np.mean(accuracies) for item, accuracies in field_accuracy.items()}
        sorted_items = sorted(field_avg.items(), key=lambda x: x[1])
        return [item[0] for item in sorted_items[:3]]

    def _analyze_model_effectiveness_by_timeframe(self, performance_data: List[Dict]) -> Dict[str, float]:
        """Analyze which models work best for specific timeframe"""
        model_accuracy = defaultdict(list)
        for entry in performance_data:
            model_accuracy[entry['model']].append(entry['accuracy'])
        
        return {model: np.mean(accuracies) for model, accuracies in model_accuracy.items()}

    def _identify_model_issues(self, performance_data: Dict) -> List[str]:
        """Identify specific issues with model performance"""
        issues = []
        
        accuracy = performance_data.get('average_accuracy', 0)
        if accuracy < self.performance_thresholds['poor']:
            issues.append('Very low accuracy')
        
        trend = performance_data.get('accuracy_trend', 'stable')
        if trend == 'declining':
            issues.append('Declining performance trend')
        
        consistency = performance_data.get('consistency_score', 1.0)
        if consistency < 0.7:
            issues.append('Inconsistent predictions')
        
        return issues if issues else ['General underperformance']

    def _calculate_impact_level(self, prediction_count: int) -> str:
        """Calculate impact level based on prediction count"""
        if prediction_count > 50:
            return 'high'
        elif prediction_count > 20:
            return 'medium'
        else:
            return 'low'

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
    """Test AI Code Auditor functionality"""
    auditor = AICodeAuditor()
    
    # Test performance recording
    print("=== Testing AI Code Auditor ===")
    
    # Record some sample performance data
    auditor.record_model_performance('LSTM', 'SBIN', '5D', 78.5)
    auditor.record_model_performance('RandomForest', 'SBIN', '5D', 82.1)
    auditor.record_model_performance('LSTM', 'TCS', '10D', 65.3)
    
    # Run audit
    audit_report = auditor.run_weekly_audit()
    print(f"Audit completed: {audit_report.get('audit_id', 'unknown')}")
    print(f"Overall health: {audit_report.get('overall_health', {}).get('status', 'unknown')}")
    
    # Get suggestions
    suggestions = auditor.get_audit_suggestions()
    print(f"Active suggestions: {len(suggestions)}")
    
    print("\n✅ AI Code Auditor testing completed!")

if __name__ == "__main__":
    main()
