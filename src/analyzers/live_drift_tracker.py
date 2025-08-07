
#!/usr/bin/env python3
"""
Live Accuracy Drift Tracker

This module tracks rolling accuracy for each stock + timeframe combination:
1. Tracks rolling 15D and 30D prediction accuracy
2. Auto-flags accuracy drops > 10%
3. Suggests investigation via GoAhead
4. Provides UI panel with green/yellow/red bands per model
"""

import os
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

class LiveDriftTracker:
    def __init__(self):
        self.drift_data_path = "data/tracking/accuracy_drift.json"
        self.drift_alerts_path = "data/tracking/drift_alerts.json"
        self.drift_analysis_path = "logs/goahead/drift_analysis"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.drift_data_path), exist_ok=True)
        os.makedirs(self.drift_analysis_path, exist_ok=True)
        
        # Drift detection settings
        self.settings = {
            'drift_threshold': 0.10,  # 10% accuracy drop triggers alert
            'rolling_window_15d': 15,
            'rolling_window_30d': 30,
            'min_predictions_for_analysis': 5,
            'alert_cooldown_hours': 6,  # Don't spam alerts
            'green_threshold': 0.80,  # 80%+ accuracy = green
            'yellow_threshold': 0.70,  # 70-80% accuracy = yellow
            # Below 70% = red
        }
        
        # Model types to track
        self.tracked_models = ['LSTM', 'RandomForest', 'ensemble', 'technical']
        
        # Initialize tracker
        self._initialize_tracker()

    def _initialize_tracker(self):
        """Initialize drift tracker data structures"""
        try:
            if not os.path.exists(self.drift_data_path):
                initial_data = {
                    'stock_model_accuracy': {},  # stock -> model -> timeframe -> accuracy_history
                    'rolling_accuracy_15d': {},
                    'rolling_accuracy_30d': {},
                    'baseline_accuracy': {},
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.drift_data_path, initial_data)
                
            if not os.path.exists(self.drift_alerts_path):
                initial_alerts = {
                    'active_alerts': [],
                    'resolved_alerts': [],
                    'alert_history': [],
                    'last_alert_check': datetime.now().isoformat()
                }
                self._save_json(self.drift_alerts_path, initial_alerts)
                
        except Exception as e:
            logger.error(f"Error initializing Live Drift Tracker: {str(e)}")

    def record_prediction_accuracy(self, stock: str, model: str, timeframe: str, 
                                 predicted_price: float, actual_price: float, 
                                 accuracy_percentage: float):
        """Record a prediction accuracy for drift tracking"""
        try:
            drift_data = self._load_json(self.drift_data_path)
            
            # Initialize data structure if needed
            if stock not in drift_data['stock_model_accuracy']:
                drift_data['stock_model_accuracy'][stock] = {}
            if model not in drift_data['stock_model_accuracy'][stock]:
                drift_data['stock_model_accuracy'][stock][model] = {}
            if timeframe not in drift_data['stock_model_accuracy'][stock][model]:
                drift_data['stock_model_accuracy'][stock][model][timeframe] = []
            
            # Record accuracy entry
            accuracy_entry = {
                'timestamp': datetime.now().isoformat(),
                'predicted_price': predicted_price,
                'actual_price': actual_price,
                'accuracy_percentage': accuracy_percentage,
                'directional_accuracy': 1 if (predicted_price > actual_price) == (predicted_price > actual_price) else 0
            }
            
            drift_data['stock_model_accuracy'][stock][model][timeframe].append(accuracy_entry)
            
            # Keep only last 100 entries per combination
            drift_data['stock_model_accuracy'][stock][model][timeframe] = \
                drift_data['stock_model_accuracy'][stock][model][timeframe][-100:]
            
            # Update rolling accuracy calculations
            self._update_rolling_accuracy(drift_data, stock, model, timeframe)
            
            # Check for drift alerts
            self._check_drift_alert(stock, model, timeframe, drift_data)
            
            drift_data['last_updated'] = datetime.now().isoformat()
            self._save_json(self.drift_data_path, drift_data)
            
        except Exception as e:
            logger.error(f"Error recording prediction accuracy: {str(e)}")

    def _update_rolling_accuracy(self, drift_data: Dict, stock: str, model: str, timeframe: str):
        """Update rolling 15D and 30D accuracy calculations"""
        try:
            accuracy_history = drift_data['stock_model_accuracy'][stock][model][timeframe]
            
            if len(accuracy_history) < self.settings['min_predictions_for_analysis']:
                return
            
            # Calculate rolling accuracies
            cutoff_15d = datetime.now() - timedelta(days=self.settings['rolling_window_15d'])
            cutoff_30d = datetime.now() - timedelta(days=self.settings['rolling_window_30d'])
            
            recent_15d = []
            recent_30d = []
            
            for entry in accuracy_history:
                try:
                    entry_date = datetime.fromisoformat(entry['timestamp'])
                    if entry_date >= cutoff_15d:
                        recent_15d.append(entry['accuracy_percentage'])
                    if entry_date >= cutoff_30d:
                        recent_30d.append(entry['accuracy_percentage'])
                except:
                    continue
            
            # Calculate rolling averages
            key_15d = f"{stock}_{model}_{timeframe}"
            key_30d = f"{stock}_{model}_{timeframe}"
            
            if 'rolling_accuracy_15d' not in drift_data:
                drift_data['rolling_accuracy_15d'] = {}
            if 'rolling_accuracy_30d' not in drift_data:
                drift_data['rolling_accuracy_30d'] = {}
            
            if recent_15d:
                drift_data['rolling_accuracy_15d'][key_15d] = {
                    'current_accuracy': np.mean(recent_15d),
                    'sample_count': len(recent_15d),
                    'accuracy_std': np.std(recent_15d),
                    'last_updated': datetime.now().isoformat()
                }
            
            if recent_30d:
                drift_data['rolling_accuracy_30d'][key_30d] = {
                    'current_accuracy': np.mean(recent_30d),
                    'sample_count': len(recent_30d),
                    'accuracy_std': np.std(recent_30d),
                    'last_updated': datetime.now().isoformat()
                }
            
            # Update baseline if not exists
            if 'baseline_accuracy' not in drift_data:
                drift_data['baseline_accuracy'] = {}
            
            baseline_key = f"{stock}_{model}_{timeframe}"
            if baseline_key not in drift_data['baseline_accuracy'] and recent_30d:
                # Use first 30 days as baseline (or current if new)
                drift_data['baseline_accuracy'][baseline_key] = np.mean(recent_30d)
            
        except Exception as e:
            logger.error(f"Error updating rolling accuracy: {str(e)}")

    def _check_drift_alert(self, stock: str, model: str, timeframe: str, drift_data: Dict):
        """Check if accuracy drift warrants an alert"""
        try:
            alerts_data = self._load_json(self.drift_alerts_path)
            
            # Check if we recently alerted for this combination
            recent_alerts = [alert for alert in alerts_data.get('active_alerts', [])
                           if alert['stock'] == stock and alert['model'] == model 
                           and alert['timeframe'] == timeframe]
            
            if recent_alerts:
                last_alert_time = datetime.fromisoformat(recent_alerts[-1]['timestamp'])
                if (datetime.now() - last_alert_time).total_seconds() < self.settings['alert_cooldown_hours'] * 3600:
                    return  # Too soon to alert again
            
            # Get current and baseline accuracy
            key_15d = f"{stock}_{model}_{timeframe}"
            key_30d = f"{stock}_{model}_{timeframe}"
            baseline_key = f"{stock}_{model}_{timeframe}"
            
            current_15d = drift_data.get('rolling_accuracy_15d', {}).get(key_15d, {}).get('current_accuracy')
            current_30d = drift_data.get('rolling_accuracy_30d', {}).get(key_30d, {}).get('current_accuracy')
            baseline = drift_data.get('baseline_accuracy', {}).get(baseline_key)
            
            if current_15d is not None and baseline is not None:
                drift_15d = baseline - current_15d
                
                if drift_15d > self.settings['drift_threshold']:
                    # Create drift alert
                    alert = {
                        'alert_id': f"drift_{stock}_{model}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        'timestamp': datetime.now().isoformat(),
                        'stock': stock,
                        'model': model,
                        'timeframe': timeframe,
                        'alert_type': 'accuracy_drift',
                        'severity': 'high' if drift_15d > 0.15 else 'medium',
                        'baseline_accuracy': baseline,
                        'current_15d_accuracy': current_15d,
                        'current_30d_accuracy': current_30d,
                        'drift_amount': drift_15d,
                        'recommendation': 'investigate_via_goahead',
                        'status': 'active'
                    }
                    
                    alerts_data['active_alerts'].append(alert)
                    alerts_data['alert_history'].append(alert)
                    
                    # Log alert
                    logger.warning(f"Accuracy drift detected: {stock} {model} {timeframe} - "
                                 f"Baseline: {baseline:.1%}, Current: {current_15d:.1%}, "
                                 f"Drift: {drift_15d:.1%}")
                    
                    # Save alert
                    self._save_json(self.drift_alerts_path, alerts_data)
                    
                    # Create investigation suggestion
                    self._create_investigation_suggestion(alert)
            
        except Exception as e:
            logger.error(f"Error checking drift alert: {str(e)}")

    def _create_investigation_suggestion(self, alert: Dict):
        """Create investigation suggestion for GoAhead system"""
        try:
            suggestion = {
                'suggestion_id': f"investigate_{alert['alert_id']}",
                'timestamp': datetime.now().isoformat(),
                'type': 'accuracy_drift_investigation',
                'priority': 'high' if alert['severity'] == 'high' else 'medium',
                'source': 'live_drift_tracker',
                'stock': alert['stock'],
                'model': alert['model'],
                'timeframe': alert['timeframe'],
                'issue_description': f"Accuracy dropped {alert['drift_amount']:.1%} for {alert['stock']} {alert['model']} {alert['timeframe']} predictions",
                'investigation_steps': [
                    "Analyze recent prediction failures",
                    "Check for data quality issues",
                    "Review model parameters",
                    "Consider model retraining"
                ],
                'expected_outcome': 'Restore prediction accuracy to baseline levels'
            }
            
            # Save suggestion to investigation queue
            investigation_file = os.path.join(self.drift_analysis_path, 
                                            f"investigation_{datetime.now().strftime('%Y-%m-%d')}.json")
            
            if os.path.exists(investigation_file):
                with open(investigation_file, 'r') as f:
                    investigations = json.load(f)
            else:
                investigations = {'investigations': []}
            
            investigations['investigations'].append(suggestion)
            
            with open(investigation_file, 'w') as f:
                json.dump(investigations, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error creating investigation suggestion: {str(e)}")

    def get_drift_monitor_panel_data(self) -> Dict[str, Any]:
        """Get data for the live drift monitor UI panel"""
        try:
            drift_data = self._load_json(self.drift_data_path)
            alerts_data = self._load_json(self.drift_alerts_path)
            
            panel_data = {
                'last_updated': datetime.now().isoformat(),
                'model_status': {},
                'active_alerts': len(alerts_data.get('active_alerts', [])),
                'overall_health': 'unknown'
            }
            
            # Process each model's status
            for model in self.tracked_models:
                model_accuracy_data = []
                
                # Collect accuracy data for this model across all stocks/timeframes
                for stock, stock_data in drift_data.get('stock_model_accuracy', {}).items():
                    if model in stock_data:
                        for timeframe, accuracy_history in stock_data[model].items():
                            if len(accuracy_history) >= self.settings['min_predictions_for_analysis']:
                                key_15d = f"{stock}_{model}_{timeframe}"
                                current_accuracy = drift_data.get('rolling_accuracy_15d', {}).get(key_15d, {}).get('current_accuracy')
                                
                                if current_accuracy is not None:
                                    model_accuracy_data.append({
                                        'stock': stock,
                                        'timeframe': timeframe,
                                        'accuracy': current_accuracy,
                                        'band': self._get_accuracy_band(current_accuracy)
                                    })
                
                # Calculate model status
                if model_accuracy_data:
                    avg_accuracy = np.mean([d['accuracy'] for d in model_accuracy_data])
                    band_counts = defaultdict(int)
                    for d in model_accuracy_data:
                        band_counts[d['band']] += 1
                    
                    # Determine overall band for model
                    if band_counts['red'] > len(model_accuracy_data) * 0.3:
                        overall_band = 'red'
                    elif band_counts['yellow'] > len(model_accuracy_data) * 0.5:
                        overall_band = 'yellow'
                    else:
                        overall_band = 'green'
                    
                    panel_data['model_status'][model] = {
                        'overall_band': overall_band,
                        'average_accuracy': avg_accuracy,
                        'tracked_combinations': len(model_accuracy_data),
                        'band_distribution': dict(band_counts),
                        'details': model_accuracy_data[:10]  # Top 10 for UI
                    }
                else:
                    panel_data['model_status'][model] = {
                        'overall_band': 'grey',
                        'average_accuracy': 0,
                        'tracked_combinations': 0,
                        'band_distribution': {'grey': 1},
                        'details': []
                    }
            
            # Determine overall health
            model_bands = [status['overall_band'] for status in panel_data['model_status'].values()]
            if 'red' in model_bands:
                panel_data['overall_health'] = 'needs_attention'
            elif 'yellow' in model_bands:
                panel_data['overall_health'] = 'monitoring'
            else:
                panel_data['overall_health'] = 'healthy'
            
            return panel_data
            
        except Exception as e:
            logger.error(f"Error getting drift monitor panel data: {str(e)}")
            return {'error': str(e), 'last_updated': datetime.now().isoformat()}

    def _get_accuracy_band(self, accuracy: float) -> str:
        """Get color band for accuracy level"""
        if accuracy >= self.settings['green_threshold']:
            return 'green'
        elif accuracy >= self.settings['yellow_threshold']:
            return 'yellow'
        else:
            return 'red'

    def get_stock_model_drift_details(self, stock: str, model: str) -> Dict[str, Any]:
        """Get detailed drift information for specific stock-model combination"""
        try:
            drift_data = self._load_json(self.drift_data_path)
            
            if stock not in drift_data.get('stock_model_accuracy', {}) or \
               model not in drift_data['stock_model_accuracy'][stock]:
                return {'error': 'No data available for this combination'}
            
            model_data = drift_data['stock_model_accuracy'][stock][model]
            details = {}
            
            for timeframe, accuracy_history in model_data.items():
                if len(accuracy_history) >= self.settings['min_predictions_for_analysis']:
                    key_15d = f"{stock}_{model}_{timeframe}"
                    key_30d = f"{stock}_{model}_{timeframe}"
                    baseline_key = f"{stock}_{model}_{timeframe}"
                    
                    current_15d = drift_data.get('rolling_accuracy_15d', {}).get(key_15d, {})
                    current_30d = drift_data.get('rolling_accuracy_30d', {}).get(key_30d, {})
                    baseline = drift_data.get('baseline_accuracy', {}).get(baseline_key)
                    
                    details[timeframe] = {
                        'baseline_accuracy': baseline,
                        'rolling_15d_accuracy': current_15d.get('current_accuracy'),
                        'rolling_30d_accuracy': current_30d.get('current_accuracy'),
                        'prediction_count_15d': current_15d.get('sample_count', 0),
                        'prediction_count_30d': current_30d.get('sample_count', 0),
                        'accuracy_band': self._get_accuracy_band(current_15d.get('current_accuracy', 0)),
                        'drift_from_baseline': baseline - current_15d.get('current_accuracy', 0) if baseline else None,
                        'recent_accuracy_history': accuracy_history[-10:]  # Last 10 predictions
                    }
            
            return {
                'stock': stock,
                'model': model,
                'timeframe_details': details,
                'last_updated': drift_data.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"Error getting drift details for {stock} {model}: {str(e)}")
            return {'error': str(e)}

    def resolve_drift_alert(self, alert_id: str, resolution_notes: str = "") -> bool:
        """Mark a drift alert as resolved"""
        try:
            alerts_data = self._load_json(self.drift_alerts_path)
            
            # Find and resolve the alert
            for i, alert in enumerate(alerts_data.get('active_alerts', [])):
                if alert.get('alert_id') == alert_id:
                    alert['status'] = 'resolved'
                    alert['resolved_at'] = datetime.now().isoformat()
                    alert['resolution_notes'] = resolution_notes
                    
                    # Move to resolved alerts
                    alerts_data.setdefault('resolved_alerts', []).append(alert)
                    alerts_data['active_alerts'].pop(i)
                    
                    self._save_json(self.drift_alerts_path, alerts_data)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resolving drift alert {alert_id}: {str(e)}")
            return False

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
    """Test Live Drift Tracker functionality"""
    tracker = LiveDriftTracker()
    
    # Test accuracy recording
    print("=== Testing Live Drift Tracker ===")
    
    # Record some sample accuracy data
    tracker.record_prediction_accuracy('SBIN', 'LSTM', '5D', 650.0, 645.0, 85.2)
    tracker.record_prediction_accuracy('SBIN', 'LSTM', '5D', 655.0, 660.0, 78.5)
    tracker.record_prediction_accuracy('SBIN', 'RandomForest', '10D', 640.0, 635.0, 92.1)
    
    # Get panel data
    panel_data = tracker.get_drift_monitor_panel_data()
    print(f"Overall health: {panel_data.get('overall_health', 'unknown')}")
    print(f"Active alerts: {panel_data.get('active_alerts', 0)}")
    
    print("\n✅ Live Drift Tracker testing completed!")

if __name__ == "__main__":
    main()
"""
Live Drift Tracker - Real-time Model Performance Monitoring
Tracks accuracy degradation and alerts for model drift
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LiveDriftTracker:
    def __init__(self, drift_threshold: float = 0.15, alert_threshold: float = 0.10):
        """
        Initialize Live Drift Tracker
        
        Args:
            drift_threshold: Threshold for significant drift (15% default)
            alert_threshold: Threshold for alerts (10% default)
        """
        self.drift_threshold = drift_threshold
        self.alert_threshold = alert_threshold
        self.drift_log_path = "logs/goahead/drift"
        self.model_kpi_path = "logs/goahead/ModelKPI.json"
        
        # Ensure directories exist
        os.makedirs(self.drift_log_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.model_kpi_path), exist_ok=True)
        
    def track_prediction_accuracy(self, model_name: str, stock: str, 
                                predicted: float, actual: float, 
                                timeframe: str, confidence: float) -> Dict[str, Any]:
        """
        Track a single prediction's accuracy and update drift metrics
        
        Args:
            model_name: Name of the model (LSTM, RF, etc.)
            stock: Stock symbol
            predicted: Predicted value
            actual: Actual value
            timeframe: Prediction timeframe (3D, 5D, etc.)
            confidence: Model confidence
            
        Returns:
            Dict with drift status and alerts
        """
        try:
            # Calculate accuracy metrics
            accuracy = 1.0 - abs(predicted - actual) / abs(actual) if actual != 0 else 0.0
            direction_correct = (predicted > 0) == (actual > 0)
            
            # Create tracking entry
            tracking_entry = {
                'timestamp': datetime.now().isoformat(),
                'model': model_name,
                'stock': stock,
                'timeframe': timeframe,
                'predicted': predicted,
                'actual': actual,
                'accuracy': accuracy,
                'direction_correct': direction_correct,
                'confidence': confidence,
                'error_percentage': abs(predicted - actual) / abs(actual) * 100 if actual != 0 else 100
            }
            
            # Save to daily log
            self._save_drift_entry(tracking_entry)
            
            # Update model KPI
            self._update_model_kpi(model_name, tracking_entry)
            
            # Check for drift
            drift_status = self._check_drift(model_name, timeframe)
            
            return {
                'accuracy': accuracy,
                'direction_correct': direction_correct,
                'drift_status': drift_status,
                'alerts': self._generate_alerts(drift_status)
            }
            
        except Exception as e:
            logger.error(f"Error tracking prediction accuracy: {str(e)}")
            return {'error': str(e)}
    
    def get_drift_status(self, timeframe: str = "all") -> Dict[str, Any]:
        """
        Get current drift status for all models
        
        Args:
            timeframe: Specific timeframe or "all"
            
        Returns:
            Dict with drift status for each model
        """
        try:
            model_kpi = self._load_model_kpi()
            drift_status = {}
            
            for model_name, stats in model_kpi.get('models', {}).items():
                if timeframe == "all" or timeframe in stats.get('timeframes', {}):
                    recent_accuracy = stats.get('recent_accuracy', 0.0)
                    baseline_accuracy = stats.get('baseline_accuracy', 0.0)
                    
                    drift_amount = baseline_accuracy - recent_accuracy if baseline_accuracy > 0 else 0.0
                    
                    if drift_amount >= self.drift_threshold:
                        status = "RED"
                        alert_level = "HIGH"
                    elif drift_amount >= self.alert_threshold:
                        status = "YELLOW"
                        alert_level = "MEDIUM"
                    else:
                        status = "GREEN"
                        alert_level = "LOW"
                    
                    drift_status[model_name] = {
                        'status': status,
                        'alert_level': alert_level,
                        'drift_amount': drift_amount,
                        'recent_accuracy': recent_accuracy,
                        'baseline_accuracy': baseline_accuracy,
                        'prediction_count': stats.get('prediction_count', 0),
                        'last_updated': stats.get('last_updated', datetime.now().isoformat())
                    }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'drift_status': drift_status,
                'summary': self._generate_drift_summary(drift_status)
            }
            
        except Exception as e:
            logger.error(f"Error getting drift status: {str(e)}")
            return {'error': str(e)}
    
    def get_real_time_alerts(self) -> List[Dict[str, Any]]:
        """
        Get real-time drift alerts
        
        Returns:
            List of active alerts
        """
        try:
            drift_status = self.get_drift_status()
            alerts = []
            
            for model_name, status in drift_status.get('drift_status', {}).items():
                if status['alert_level'] in ['HIGH', 'MEDIUM']:
                    alerts.append({
                        'type': 'drift_alert',
                        'model': model_name,
                        'severity': status['alert_level'],
                        'message': f"Model {model_name} showing {status['drift_amount']:.1%} accuracy drift",
                        'recommendation': self._get_drift_recommendation(status),
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Add data quality alerts
            data_alerts = self._check_data_quality_alerts()
            alerts.extend(data_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting real-time alerts: {str(e)}")
            return [{'error': str(e)}]
    
    def _save_drift_entry(self, entry: Dict[str, Any]):
        """Save drift tracking entry to daily log"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.drift_log_path, f"{today}.json")
            
            # Load existing entries
            entries = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    entries = data.get('entries', [])
            
            # Add new entry
            entries.append(entry)
            
            # Save updated entries
            log_data = {
                'date': today,
                'entries': entries,
                'summary': self._calculate_daily_summary(entries)
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving drift entry: {str(e)}")
    
    def _update_model_kpi(self, model_name: str, entry: Dict[str, Any]):
        """Update model KPI with new prediction result"""
        try:
            # Load existing KPI
            model_kpi = self._load_model_kpi()
            
            if 'models' not in model_kpi:
                model_kpi['models'] = {}
            
            if model_name not in model_kpi['models']:
                model_kpi['models'][model_name] = {
                    'prediction_count': 0,
                    'total_accuracy': 0.0,
                    'recent_accuracy': 0.0,
                    'baseline_accuracy': 0.75,  # Default baseline
                    'timeframes': {},
                    'created': datetime.now().isoformat()
                }
            
            model_stats = model_kpi['models'][model_name]
            
            # Update overall stats
            model_stats['prediction_count'] += 1
            model_stats['total_accuracy'] += entry['accuracy']
            model_stats['average_accuracy'] = model_stats['total_accuracy'] / model_stats['prediction_count']
            
            # Calculate recent accuracy (last 10 predictions)
            if model_stats['prediction_count'] <= 10:
                model_stats['recent_accuracy'] = model_stats['average_accuracy']
            else:
                # For simplicity, use average accuracy as recent accuracy
                # In production, this would track last N predictions
                model_stats['recent_accuracy'] = model_stats['average_accuracy']
            
            # Update timeframe stats
            timeframe = entry['timeframe']
            if timeframe not in model_stats['timeframes']:
                model_stats['timeframes'][timeframe] = {
                    'count': 0,
                    'accuracy': 0.0,
                    'direction_accuracy': 0.0
                }
            
            tf_stats = model_stats['timeframes'][timeframe]
            tf_stats['count'] += 1
            tf_stats['accuracy'] = (tf_stats['accuracy'] * (tf_stats['count'] - 1) + entry['accuracy']) / tf_stats['count']
            tf_stats['direction_accuracy'] = (tf_stats['direction_accuracy'] * (tf_stats['count'] - 1) + 
                                           (1.0 if entry['direction_correct'] else 0.0)) / tf_stats['count']
            
            model_stats['last_updated'] = datetime.now().isoformat()
            model_kpi['last_updated'] = datetime.now().isoformat()
            
            # Save updated KPI
            with open(self.model_kpi_path, 'w') as f:
                json.dump(model_kpi, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating model KPI: {str(e)}")
    
    def _load_model_kpi(self) -> Dict[str, Any]:
        """Load model KPI data"""
        try:
            if os.path.exists(self.model_kpi_path):
                with open(self.model_kpi_path, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'created': datetime.now().isoformat(),
                    'models': {}
                }
        except Exception as e:
            logger.error(f"Error loading model KPI: {str(e)}")
            return {'models': {}}
    
    def _check_drift(self, model_name: str, timeframe: str) -> Dict[str, Any]:
        """Check if model is experiencing drift"""
        try:
            model_kpi = self._load_model_kpi()
            model_stats = model_kpi.get('models', {}).get(model_name, {})
            
            recent_accuracy = model_stats.get('recent_accuracy', 0.0)
            baseline_accuracy = model_stats.get('baseline_accuracy', 0.75)
            
            drift_amount = baseline_accuracy - recent_accuracy
            
            return {
                'model': model_name,
                'timeframe': timeframe,
                'drift_detected': drift_amount >= self.alert_threshold,
                'drift_amount': drift_amount,
                'severity': 'HIGH' if drift_amount >= self.drift_threshold else 'MEDIUM' if drift_amount >= self.alert_threshold else 'LOW'
            }
            
        except Exception as e:
            logger.error(f"Error checking drift: {str(e)}")
            return {'error': str(e)}
    
    def _generate_alerts(self, drift_status: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alerts based on drift status"""
        alerts = []
        
        if drift_status.get('drift_detected', False):
            alerts.append({
                'type': 'accuracy_drift',
                'severity': drift_status.get('severity', 'MEDIUM'),
                'message': f"Model {drift_status.get('model')} accuracy drift detected: {drift_status.get('drift_amount', 0):.1%}",
                'recommendation': self._get_drift_recommendation(drift_status)
            })
        
        return alerts
    
    def _get_drift_recommendation(self, status: Dict[str, Any]) -> str:
        """Get recommendation based on drift status"""
        drift_amount = status.get('drift_amount', 0)
        
        if drift_amount >= 0.20:
            return "URGENT: Consider immediate model retraining or switching to backup model"
        elif drift_amount >= 0.15:
            return "HIGH: Schedule model retraining within 24 hours"
        elif drift_amount >= 0.10:
            return "MEDIUM: Monitor closely and consider retraining within 48 hours"
        else:
            return "LOW: Continue monitoring"
    
    def _generate_drift_summary(self, drift_status: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of drift status"""
        total_models = len(drift_status)
        red_count = sum(1 for status in drift_status.values() if status['status'] == 'RED')
        yellow_count = sum(1 for status in drift_status.values() if status['status'] == 'YELLOW')
        green_count = sum(1 for status in drift_status.values() if status['status'] == 'GREEN')
        
        return {
            'total_models': total_models,
            'red_alerts': red_count,
            'yellow_alerts': yellow_count,
            'green_status': green_count,
            'overall_health': 'CRITICAL' if red_count > 0 else 'WARNING' if yellow_count > 0 else 'HEALTHY'
        }
    
    def _calculate_daily_summary(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate daily summary from entries"""
        if not entries:
            return {}
        
        total_predictions = len(entries)
        avg_accuracy = sum(e['accuracy'] for e in entries) / total_predictions
        direction_accuracy = sum(1 for e in entries if e['direction_correct']) / total_predictions
        
        model_stats = {}
        for entry in entries:
            model = entry['model']
            if model not in model_stats:
                model_stats[model] = {'count': 0, 'accuracy': 0.0}
            model_stats[model]['count'] += 1
            model_stats[model]['accuracy'] += entry['accuracy']
        
        for model in model_stats:
            model_stats[model]['accuracy'] /= model_stats[model]['count']
        
        return {
            'total_predictions': total_predictions,
            'average_accuracy': avg_accuracy,
            'direction_accuracy': direction_accuracy,
            'model_breakdown': model_stats
        }
    
    def _check_data_quality_alerts(self) -> List[Dict[str, Any]]:
        """Check for data quality issues that might affect predictions"""
        alerts = []
        
        # Check for missing data patterns
        try:
            # Check if we have recent drift data
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            recent_files = [
                os.path.join(self.drift_log_path, f"{today}.json"),
                os.path.join(self.drift_log_path, f"{yesterday}.json")
            ]
            
            recent_data_count = sum(1 for f in recent_files if os.path.exists(f))
            
            if recent_data_count == 0:
                alerts.append({
                    'type': 'data_quality',
                    'severity': 'HIGH',
                    'message': 'No recent drift tracking data available',
                    'recommendation': 'Check data collection system'
                })
            
        except Exception as e:
            logger.error(f"Error checking data quality: {str(e)}")
        
        return alerts
