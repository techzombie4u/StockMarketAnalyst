
#!/usr/bin/env python3
"""
Smart Data Validation & Gap Filling

This module validates data integrity before predictions and handles:
1. Missing OHLC values detection
2. Unusual spike identification
3. Incomplete technical indicator validation
4. Auto-marking questionable predictions with warnings
5. Skipping lock if major data integrity issues exist
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

class SmartDataValidator:
    def __init__(self):
        self.validation_logs_path = "logs/goahead/validation"
        self.validation_rules_path = "data/tracking/validation_rules.json"
        self.data_quality_cache = "data/cache/data_quality.json"
        
        # Ensure directories exist
        os.makedirs(self.validation_logs_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.validation_rules_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.data_quality_cache), exist_ok=True)
        
        # Validation thresholds
        self.thresholds = {
            'missing_data_limit': 0.1,  # 10% missing data tolerance
            'price_spike_factor': 3.0,  # 3x standard deviation for spike detection
            'volume_spike_factor': 5.0,  # 5x average volume for spike detection
            'indicator_completeness': 0.8,  # 80% indicator completeness required
            'data_freshness_hours': 24,  # Data must be within 24 hours
            'min_data_points': 20  # Minimum data points for validation
        }
        
        # Required indicators for prediction
        self.required_indicators = [
            'rsi', 'macd', 'sma_20', 'sma_50', 'bollinger_upper', 
            'bollinger_lower', 'volume', 'close', 'high', 'low', 'open'
        ]
        
        # Initialize validator
        self._initialize_validator()

    def _initialize_validator(self):
        """Initialize data validator components"""
        try:
            if not os.path.exists(self.validation_rules_path):
                initial_rules = {
                    'spike_detection_rules': {
                        'price_deviation_threshold': 3.0,
                        'volume_deviation_threshold': 5.0,
                        'consecutive_spike_limit': 2
                    },
                    'completeness_rules': {
                        'required_indicators': self.required_indicators,
                        'min_completeness_ratio': 0.8,
                        'critical_indicators': ['close', 'volume', 'rsi', 'macd']
                    },
                    'data_freshness_rules': {
                        'max_age_hours': 24,
                        'market_hours_only': True,
                        'weekend_tolerance': True
                    },
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.validation_rules_path, initial_rules)
                
            if not os.path.exists(self.data_quality_cache):
                initial_cache = {
                    'stock_quality_scores': {},
                    'validation_history': {},
                    'quality_trends': {},
                    'last_validation': datetime.now().isoformat()
                }
                self._save_json(self.data_quality_cache, initial_cache)
                
        except Exception as e:
            logger.error(f"Error initializing Smart Data Validator: {str(e)}")

    def validate_prediction_data(self, stock: str, prediction_data: Dict, 
                               market_data: Dict) -> Dict[str, Any]:
        """Comprehensive data validation before prediction locking"""
        try:
            validation_id = f"{stock}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            validation_result = {
                'validation_id': validation_id,
                'timestamp': datetime.now().isoformat(),
                'stock': stock,
                'overall_quality': 'unknown',
                'data_integrity_score': 0.0,
                'validation_checks': {},
                'issues_found': [],
                'warnings': [],
                'recommendation': 'unknown',
                'lock_decision': 'pending'
            }
            
            # Perform validation checks
            ohlc_validation = self._validate_ohlc_data(market_data)
            spike_validation = self._detect_unusual_spikes(market_data)
            indicator_validation = self._validate_technical_indicators(prediction_data)
            freshness_validation = self._validate_data_freshness(market_data)
            completeness_validation = self._validate_data_completeness(market_data, prediction_data)
            
            # Aggregate validation results
            validation_result['validation_checks'] = {
                'ohlc_validation': ohlc_validation,
                'spike_detection': spike_validation,
                'indicator_validation': indicator_validation,
                'freshness_validation': freshness_validation,
                'completeness_validation': completeness_validation
            }
            
            # Calculate overall data integrity score
            integrity_score = self._calculate_integrity_score(validation_result['validation_checks'])
            validation_result['data_integrity_score'] = integrity_score
            
            # Determine overall quality and recommendation
            quality_assessment = self._assess_overall_quality(integrity_score, validation_result['validation_checks'])
            validation_result.update(quality_assessment)
            
            # Save validation log
            self._save_validation_log(validation_result)
            
            # Update quality cache
            self._update_quality_cache(stock, validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating prediction data for {stock}: {str(e)}")
            return self._error_validation_result(stock, str(e))

    def _validate_ohlc_data(self, market_data: Dict) -> Dict[str, Any]:
        """Validate OHLC data integrity"""
        try:
            ohlc_fields = ['open', 'high', 'low', 'close']
            missing_fields = []
            invalid_values = []
            logical_errors = []
            
            # Check for missing fields
            for field in ohlc_fields:
                if field not in market_data or market_data[field] is None:
                    missing_fields.append(field)
                elif not isinstance(market_data[field], (int, float)) or market_data[field] <= 0:
                    invalid_values.append(field)
            
            # Check logical consistency (if all fields present and valid)
            if not missing_fields and not invalid_values:
                open_price = float(market_data['open'])
                high_price = float(market_data['high'])
                low_price = float(market_data['low'])
                close_price = float(market_data['close'])
                
                if high_price < max(open_price, close_price):
                    logical_errors.append('High price lower than open/close')
                if low_price > min(open_price, close_price):
                    logical_errors.append('Low price higher than open/close')
                if high_price < low_price:
                    logical_errors.append('High price lower than low price')
            
            # Calculate validation score
            total_checks = len(ohlc_fields) + 3  # 4 fields + 3 logical checks
            passed_checks = len(ohlc_fields) - len(missing_fields) - len(invalid_values)
            if not logical_errors:
                passed_checks += 3
            
            validation_score = passed_checks / total_checks
            
            return {
                'status': 'pass' if validation_score >= 0.9 else 'warning' if validation_score >= 0.7 else 'fail',
                'score': validation_score,
                'missing_fields': missing_fields,
                'invalid_values': invalid_values,
                'logical_errors': logical_errors,
                'issues_count': len(missing_fields) + len(invalid_values) + len(logical_errors)
            }
            
        except Exception as e:
            logger.error(f"Error validating OHLC data: {str(e)}")
            return {'status': 'error', 'score': 0.0, 'error': str(e)}

    def _detect_unusual_spikes(self, market_data: Dict) -> Dict[str, Any]:
        """Detect unusual price and volume spikes"""
        try:
            # Get historical data for comparison (would need actual implementation)
            # For now, using simplified spike detection
            
            current_price = market_data.get('close', 0)
            current_volume = market_data.get('volume', 0)
            
            # Get recent averages (simplified - would use actual historical data)
            price_history = market_data.get('price_history', [current_price])
            volume_history = market_data.get('volume_history', [current_volume])
            
            price_spikes = []
            volume_spikes = []
            
            if len(price_history) > 1:
                recent_prices = price_history[-10:]  # Last 10 data points
                price_mean = np.mean(recent_prices)
                price_std = np.std(recent_prices)
                
                if price_std > 0:
                    price_z_score = abs(current_price - price_mean) / price_std
                    if price_z_score > self.thresholds['price_spike_factor']:
                        price_spikes.append({
                            'type': 'price_spike',
                            'current_value': current_price,
                            'mean_value': price_mean,
                            'z_score': price_z_score,
                            'severity': 'high' if price_z_score > 5 else 'medium'
                        })
            
            if len(volume_history) > 1:
                recent_volumes = volume_history[-10:]
                volume_mean = np.mean(recent_volumes)
                volume_std = np.std(recent_volumes)
                
                if volume_std > 0:
                    volume_z_score = abs(current_volume - volume_mean) / volume_std
                    if volume_z_score > self.thresholds['volume_spike_factor']:
                        volume_spikes.append({
                            'type': 'volume_spike',
                            'current_value': current_volume,
                            'mean_value': volume_mean,
                            'z_score': volume_z_score,
                            'severity': 'high' if volume_z_score > 10 else 'medium'
                        })
            
            # Calculate spike score
            total_spikes = len(price_spikes) + len(volume_spikes)
            spike_score = max(0.0, 1.0 - (total_spikes * 0.3))  # Penalty for spikes
            
            return {
                'status': 'pass' if total_spikes == 0 else 'warning' if total_spikes <= 1 else 'fail',
                'score': spike_score,
                'price_spikes': price_spikes,
                'volume_spikes': volume_spikes,
                'total_spikes': total_spikes
            }
            
        except Exception as e:
            logger.error(f"Error detecting spikes: {str(e)}")
            return {'status': 'error', 'score': 0.0, 'error': str(e)}

    def _validate_technical_indicators(self, prediction_data: Dict) -> Dict[str, Any]:
        """Validate technical indicators completeness and values"""
        try:
            indicators = prediction_data.get('indicators', {})
            missing_indicators = []
            invalid_indicators = []
            range_violations = []
            
            # Check for required indicators
            for indicator in self.required_indicators:
                if indicator not in indicators:
                    missing_indicators.append(indicator)
                else:
                    value = indicators[indicator]
                    
                    # Validate indicator values
                    if not isinstance(value, (int, float)) or np.isnan(value) or np.isinf(value):
                        invalid_indicators.append(indicator)
                    else:
                        # Check indicator-specific ranges
                        range_violation = self._check_indicator_range(indicator, value)
                        if range_violation:
                            range_violations.append(range_violation)
            
            # Calculate completeness score
            total_required = len(self.required_indicators)
            available_valid = total_required - len(missing_indicators) - len(invalid_indicators)
            completeness_score = available_valid / total_required
            
            # Adjust score for range violations
            range_penalty = len(range_violations) * 0.1
            final_score = max(0.0, completeness_score - range_penalty)
            
            return {
                'status': 'pass' if final_score >= 0.8 else 'warning' if final_score >= 0.6 else 'fail',
                'score': final_score,
                'completeness_ratio': completeness_score,
                'missing_indicators': missing_indicators,
                'invalid_indicators': invalid_indicators,
                'range_violations': range_violations,
                'total_indicators': len(indicators)
            }
            
        except Exception as e:
            logger.error(f"Error validating technical indicators: {str(e)}")
            return {'status': 'error', 'score': 0.0, 'error': str(e)}

    def _check_indicator_range(self, indicator: str, value: float) -> Optional[Dict]:
        """Check if indicator value is within expected range"""
        try:
            # Define expected ranges for common indicators
            indicator_ranges = {
                'rsi': (0, 100),
                'stochastic_k': (0, 100),
                'stochastic_d': (0, 100),
                'williams_r': (-100, 0),
                'cci': (-300, 300),
                'adx': (0, 100)
            }
            
            if indicator in indicator_ranges:
                min_val, max_val = indicator_ranges[indicator]
                if not (min_val <= value <= max_val):
                    return {
                        'indicator': indicator,
                        'value': value,
                        'expected_range': f"{min_val} to {max_val}",
                        'violation_type': 'range_exceeded'
                    }
            
            # Check for reasonable price-based indicators
            if any(x in indicator.lower() for x in ['price', 'sma', 'ema', 'bollinger']):
                if value <= 0 or value > 100000:  # Unreasonable price values
                    return {
                        'indicator': indicator,
                        'value': value,
                        'violation_type': 'unreasonable_price'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking indicator range for {indicator}: {str(e)}")
            return None

    def _validate_data_freshness(self, market_data: Dict) -> Dict[str, Any]:
        """Validate data freshness and timeliness"""
        try:
            timestamp_str = market_data.get('timestamp', datetime.now().isoformat())
            
            try:
                data_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                # Fallback parsing
                data_timestamp = datetime.now() - timedelta(hours=25)  # Force stale
            
            current_time = datetime.now()
            age_hours = (current_time - data_timestamp).total_seconds() / 3600
            
            # Check if data is within acceptable freshness window
            max_age = self.thresholds['data_freshness_hours']
            
            # Weekend adjustment
            if current_time.weekday() >= 5:  # Saturday or Sunday
                max_age = 72  # Allow 3 days for weekend
            
            freshness_score = max(0.0, 1.0 - (age_hours / max_age))
            
            return {
                'status': 'pass' if age_hours <= max_age else 'warning' if age_hours <= max_age * 2 else 'fail',
                'score': freshness_score,
                'data_age_hours': age_hours,
                'max_allowed_age': max_age,
                'data_timestamp': timestamp_str,
                'is_stale': age_hours > max_age
            }
            
        except Exception as e:
            logger.error(f"Error validating data freshness: {str(e)}")
            return {'status': 'error', 'score': 0.0, 'error': str(e)}

    def _validate_data_completeness(self, market_data: Dict, prediction_data: Dict) -> Dict[str, Any]:
        """Validate overall data completeness"""
        try:
            total_expected_fields = 0
            present_fields = 0
            critical_missing = []
            
            # Check market data completeness
            expected_market_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
            for field in expected_market_fields:
                total_expected_fields += 1
                if field in market_data and market_data[field] is not None:
                    present_fields += 1
                else:
                    if field in ['close', 'volume']:  # Critical fields
                        critical_missing.append(field)
            
            # Check prediction data completeness
            expected_prediction_fields = ['predicted_price', 'confidence', 'indicators']
            for field in expected_prediction_fields:
                total_expected_fields += 1
                if field in prediction_data and prediction_data[field] is not None:
                    present_fields += 1
                else:
                    if field in ['predicted_price', 'confidence']:  # Critical fields
                        critical_missing.append(field)
            
            # Calculate completeness score
            completeness_ratio = present_fields / total_expected_fields if total_expected_fields > 0 else 0
            
            # Heavy penalty for critical missing fields
            critical_penalty = len(critical_missing) * 0.3
            final_score = max(0.0, completeness_ratio - critical_penalty)
            
            return {
                'status': 'pass' if final_score >= 0.9 and not critical_missing else 'warning' if final_score >= 0.7 else 'fail',
                'score': final_score,
                'completeness_ratio': completeness_ratio,
                'present_fields': present_fields,
                'total_expected': total_expected_fields,
                'critical_missing': critical_missing
            }
            
        except Exception as e:
            logger.error(f"Error validating data completeness: {str(e)}")
            return {'status': 'error', 'score': 0.0, 'error': str(e)}

    def _calculate_integrity_score(self, validation_checks: Dict) -> float:
        """Calculate overall data integrity score"""
        try:
            scores = []
            weights = {
                'ohlc_validation': 0.25,
                'spike_detection': 0.20,
                'indicator_validation': 0.25,
                'freshness_validation': 0.15,
                'completeness_validation': 0.15
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for check_name, check_result in validation_checks.items():
                if check_name in weights and 'score' in check_result:
                    weight = weights[check_name]
                    score = check_result['score']
                    weighted_score += score * weight
                    total_weight += weight
            
            return weighted_score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating integrity score: {str(e)}")
            return 0.0

    def _assess_overall_quality(self, integrity_score: float, validation_checks: Dict) -> Dict[str, Any]:
        """Assess overall data quality and make recommendation"""
        try:
            issues_found = []
            warnings = []
            
            # Collect issues from validation checks
            for check_name, check_result in validation_checks.items():
                if check_result.get('status') == 'fail':
                    issues_found.append(f"{check_name}: {check_result.get('error', 'Failed validation')}")
                elif check_result.get('status') == 'warning':
                    warnings.append(f"{check_name}: Quality concerns detected")
            
            # Determine overall quality
            if integrity_score >= 0.9:
                overall_quality = 'excellent'
                recommendation = 'safe_to_lock'
                lock_decision = 'approve'
            elif integrity_score >= 0.8:
                overall_quality = 'good'
                recommendation = 'safe_to_lock'
                lock_decision = 'approve'
            elif integrity_score >= 0.7:
                overall_quality = 'acceptable'
                recommendation = 'lock_with_warning'
                lock_decision = 'approve_with_warning'
            elif integrity_score >= 0.5:
                overall_quality = 'questionable'
                recommendation = 'manual_review_required'
                lock_decision = 'hold_for_review'
            else:
                overall_quality = 'poor'
                recommendation = 'skip_lock'
                lock_decision = 'reject'
            
            return {
                'overall_quality': overall_quality,
                'recommendation': recommendation,
                'lock_decision': lock_decision,
                'issues_found': issues_found,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Error assessing overall quality: {str(e)}")
            return {
                'overall_quality': 'error',
                'recommendation': 'skip_lock',
                'lock_decision': 'reject',
                'issues_found': [f"Assessment error: {str(e)}"],
                'warnings': []
            }

    def get_stock_quality_history(self, stock: str, days: int = 30) -> Dict[str, Any]:
        """Get data quality history for a stock"""
        try:
            quality_cache = self._load_json(self.data_quality_cache)
            stock_history = quality_cache.get('validation_history', {}).get(stock, [])
            
            # Filter recent history
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_history = []
            
            for entry in stock_history:
                try:
                    entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                    if entry_date >= cutoff_date:
                        recent_history.append(entry)
                except:
                    continue
            
            # Calculate quality trends
            if recent_history:
                scores = [entry.get('data_integrity_score', 0) for entry in recent_history]
                avg_score = np.mean(scores)
                score_trend = 'improving' if len(scores) > 1 and scores[-1] > scores[0] else 'stable'
                
                # Count issues
                total_issues = sum(len(entry.get('issues_found', [])) for entry in recent_history)
                avg_issues_per_validation = total_issues / len(recent_history)
            else:
                avg_score = 0.0
                score_trend = 'unknown'
                avg_issues_per_validation = 0
            
            return {
                'stock': stock,
                'validation_count': len(recent_history),
                'average_quality_score': avg_score,
                'quality_trend': score_trend,
                'average_issues_per_validation': avg_issues_per_validation,
                'recent_validations': recent_history[-5:]  # Last 5 validations
            }
            
        except Exception as e:
            logger.error(f"Error getting quality history for {stock}: {str(e)}")
            return {'stock': stock, 'error': str(e)}

    # Helper methods
    def _save_validation_log(self, validation_result: Dict):
        """Save validation log to file"""
        try:
            timestamp = datetime.now()
            date_str = timestamp.strftime('%Y-%m-%d')
            time_str = timestamp.strftime('%H%M%S')
            
            log_file = os.path.join(self.validation_logs_path, f"validation_{date_str}.json")
            
            # Load existing logs or create new
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = {'date': date_str, 'validations': []}
            
            logs['validations'].append(validation_result)
            
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving validation log: {str(e)}")

    def _update_quality_cache(self, stock: str, validation_result: Dict):
        """Update quality cache with validation result"""
        try:
            quality_cache = self._load_json(self.data_quality_cache)
            
            # Update stock quality score
            quality_cache['stock_quality_scores'][stock] = validation_result.get('data_integrity_score', 0)
            
            # Add to validation history
            if 'validation_history' not in quality_cache:
                quality_cache['validation_history'] = {}
            if stock not in quality_cache['validation_history']:
                quality_cache['validation_history'][stock] = []
            
            # Keep only last 50 validations per stock
            quality_cache['validation_history'][stock].append(validation_result)
            quality_cache['validation_history'][stock] = quality_cache['validation_history'][stock][-50:]
            
            quality_cache['last_validation'] = datetime.now().isoformat()
            
            self._save_json(self.data_quality_cache, quality_cache)
            
        except Exception as e:
            logger.error(f"Error updating quality cache: {str(e)}")

    def _error_validation_result(self, stock: str, error_msg: str) -> Dict[str, Any]:
        """Return error validation result"""
        return {
            'validation_id': f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'stock': stock,
            'overall_quality': 'error',
            'data_integrity_score': 0.0,
            'recommendation': 'skip_lock',
            'lock_decision': 'reject',
            'issues_found': [f"Validation error: {error_msg}"],
            'warnings': [],
            'validation_checks': {}
        }

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
    """Test Smart Data Validator functionality"""
    validator = SmartDataValidator()
    
    # Test validation
    print("=== Testing Smart Data Validator ===")
    
    sample_market_data = {
        'open': 640.0,
        'high': 655.0,
        'low': 635.0,
        'close': 650.0,
        'volume': 2500000,
        'timestamp': datetime.now().isoformat()
    }
    
    sample_prediction_data = {
        'predicted_price': 665.0,
        'confidence': 82,
        'indicators': {
            'rsi': 68.5,
            'macd': 1.2,
            'sma_20': 645.0,
            'sma_50': 640.0,
            'bollinger_upper': 660.0,
            'bollinger_lower': 630.0
        }
    }
    
    validation_result = validator.validate_prediction_data('SBIN', sample_prediction_data, sample_market_data)
    print(f"Validation result: {validation_result['overall_quality']}")
    print(f"Data integrity score: {validation_result['data_integrity_score']:.2f}")
    print(f"Lock decision: {validation_result['lock_decision']}")
    
    print("\n✅ Smart Data Validator testing completed!")

if __name__ == "__main__":
    main()
"""
Smart Data Validator - Intelligent Data Quality Monitoring
Detects OHLC gaps, validates data integrity, and marks questionable predictions
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class SmartDataValidator:
    def __init__(self, gap_threshold: float = 0.05, quality_threshold: float = 0.8):
        """
        Initialize Smart Data Validator
        
        Args:
            gap_threshold: Threshold for detecting significant gaps (5% default)
            quality_threshold: Minimum data quality score (80% default)
        """
        self.gap_threshold = gap_threshold
        self.quality_threshold = quality_threshold
        self.validation_log_path = "logs/goahead/validation"
        
        # Ensure directories exist
        os.makedirs(self.validation_log_path, exist_ok=True)
        
    def validate_ohlc_data(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate OHLC data for gaps and anomalies
        
        Args:
            stock_data: Dictionary containing OHLC data for a stock
            
        Returns:
            Dict with validation results and quality score
        """
        try:
            symbol = stock_data.get('symbol', 'UNKNOWN')
            ohlc = stock_data.get('ohlc', {})
            
            validation_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'quality_score': 1.0,
                'issues': [],
                'gaps_detected': [],
                'recommendations': [],
                'should_skip_prediction': False
            }
            
            # Check for missing OHLC values
            required_fields = ['open', 'high', 'low', 'close', 'volume']
            missing_fields = [field for field in required_fields if field not in ohlc or ohlc[field] is None]
            
            if missing_fields:
                validation_result['issues'].append({
                    'type': 'missing_data',
                    'severity': 'HIGH',
                    'fields': missing_fields,
                    'message': f"Missing OHLC fields: {', '.join(missing_fields)}"
                })
                validation_result['quality_score'] *= 0.5
                validation_result['should_skip_prediction'] = True
            
            if not missing_fields:
                # Check for logical inconsistencies
                open_price = float(ohlc.get('open', 0))
                high_price = float(ohlc.get('high', 0))
                low_price = float(ohlc.get('low', 0))
                close_price = float(ohlc.get('close', 0))
                volume = float(ohlc.get('volume', 0))
                
                # Validate OHLC relationships
                ohlc_issues = self._validate_ohlc_relationships(open_price, high_price, low_price, close_price)
                validation_result['issues'].extend(ohlc_issues)
                
                # Check for price gaps
                gaps = self._detect_price_gaps(stock_data)
                validation_result['gaps_detected'] = gaps
                
                # Check for volume anomalies
                volume_issues = self._validate_volume(volume, stock_data.get('avg_volume', volume))
                validation_result['issues'].extend(volume_issues)
                
                # Calculate overall quality score
                validation_result['quality_score'] = self._calculate_quality_score(validation_result)
                
                # Determine if prediction should be skipped
                validation_result['should_skip_prediction'] = (
                    validation_result['quality_score'] < self.quality_threshold or
                    any(issue['severity'] == 'HIGH' for issue in validation_result['issues']) or
                    len(validation_result['gaps_detected']) > 0
                )
                
                # Generate recommendations
                validation_result['recommendations'] = self._generate_recommendations(validation_result)
            
            # Log validation result
            self._log_validation_result(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating OHLC data for {stock_data.get('symbol', 'UNKNOWN')}: {str(e)}")
            return {
                'symbol': stock_data.get('symbol', 'UNKNOWN'),
                'error': str(e),
                'should_skip_prediction': True,
                'quality_score': 0.0
            }
    
    def validate_historical_data(self, symbol: str, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate historical data series for continuity and quality
        
        Args:
            symbol: Stock symbol
            data_points: List of historical data points
            
        Returns:
            Dict with historical validation results
        """
        try:
            if not data_points:
                return {
                    'symbol': symbol,
                    'error': 'No historical data available',
                    'should_skip_prediction': True
                }
            
            validation_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'data_points': len(data_points),
                'continuity_score': 1.0,
                'quality_score': 1.0,
                'gaps': [],
                'anomalies': [],
                'recommendations': []
            }
            
            # Check for date gaps
            date_gaps = self._detect_date_gaps(data_points)
            validation_result['gaps'] = date_gaps
            
            # Check for price anomalies
            price_anomalies = self._detect_price_anomalies(data_points)
            validation_result['anomalies'] = price_anomalies
            
            # Calculate continuity score
            validation_result['continuity_score'] = self._calculate_continuity_score(date_gaps, len(data_points))
            
            # Calculate quality score
            validation_result['quality_score'] = self._calculate_historical_quality_score(
                validation_result['continuity_score'], 
                price_anomalies
            )
            
            # Generate recommendations
            validation_result['recommendations'] = self._generate_historical_recommendations(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating historical data for {symbol}: {str(e)}")
            return {
                'symbol': symbol,
                'error': str(e),
                'should_skip_prediction': True
            }
    
    def get_data_quality_report(self, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Get comprehensive data quality report
        
        Args:
            timeframe: Report timeframe (24h, 7d, 30d)
            
        Returns:
            Dict with quality metrics and recommendations
        """
        try:
            # Load recent validation logs
            validation_files = self._get_validation_files(timeframe)
            all_validations = []
            
            for file_path in validation_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        all_validations.extend(data.get('validations', []))
                except Exception as e:
                    logger.warning(f"Could not load validation file {file_path}: {str(e)}")
            
            if not all_validations:
                return {
                    'timeframe': timeframe,
                    'message': 'No validation data available for the specified timeframe'
                }
            
            # Calculate aggregate metrics
            total_validations = len(all_validations)
            avg_quality_score = np.mean([v.get('quality_score', 0) for v in all_validations])
            skip_rate = np.mean([1 if v.get('should_skip_prediction', False) else 0 for v in all_validations])
            
            # Count issues by type
            issue_counts = {}
            gap_counts = 0
            
            for validation in all_validations:
                for issue in validation.get('issues', []):
                    issue_type = issue.get('type', 'unknown')
                    issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                
                gap_counts += len(validation.get('gaps_detected', []))
            
            # Generate quality summary by stock
            stock_quality = {}
            for validation in all_validations:
                symbol = validation.get('symbol', 'UNKNOWN')
                if symbol not in stock_quality:
                    stock_quality[symbol] = {
                        'validations': 0,
                        'total_quality': 0,
                        'skip_count': 0
                    }
                
                stock_quality[symbol]['validations'] += 1
                stock_quality[symbol]['total_quality'] += validation.get('quality_score', 0)
                if validation.get('should_skip_prediction', False):
                    stock_quality[symbol]['skip_count'] += 1
            
            # Calculate averages for each stock
            for symbol in stock_quality:
                stock_quality[symbol]['avg_quality'] = (
                    stock_quality[symbol]['total_quality'] / stock_quality[symbol]['validations']
                )
                stock_quality[symbol]['skip_rate'] = (
                    stock_quality[symbol]['skip_count'] / stock_quality[symbol]['validations']
                )
            
            return {
                'timeframe': timeframe,
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_validations': total_validations,
                    'average_quality_score': avg_quality_score,
                    'prediction_skip_rate': skip_rate,
                    'total_gaps_detected': gap_counts
                },
                'issue_breakdown': issue_counts,
                'stock_quality': stock_quality,
                'recommendations': self._generate_system_recommendations(
                    avg_quality_score, skip_rate, issue_counts
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating data quality report: {str(e)}")
            return {'error': str(e)}
    
    def _validate_ohlc_relationships(self, open_price: float, high_price: float, 
                                   low_price: float, close_price: float) -> List[Dict[str, Any]]:
        """Validate logical relationships between OHLC values"""
        issues = []
        
        # High should be >= max(open, close)
        if high_price < max(open_price, close_price):
            issues.append({
                'type': 'ohlc_logic_error',
                'severity': 'HIGH',
                'message': f"High price ({high_price}) is less than max(open, close) ({max(open_price, close_price)})"
            })
        
        # Low should be <= min(open, close)
        if low_price > min(open_price, close_price):
            issues.append({
                'type': 'ohlc_logic_error',
                'severity': 'HIGH',
                'message': f"Low price ({low_price}) is greater than min(open, close) ({min(open_price, close_price)})"
            })
        
        # Check for zero or negative prices
        if any(price <= 0 for price in [open_price, high_price, low_price, close_price]):
            issues.append({
                'type': 'invalid_price',
                'severity': 'HIGH',
                'message': "Zero or negative prices detected"
            })
        
        return issues
    
    def _detect_price_gaps(self, stock_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect significant price gaps"""
        gaps = []
        
        try:
            current_price = float(stock_data.get('ohlc', {}).get('close', 0))
            previous_close = float(stock_data.get('previous_close', current_price))
            
            if previous_close > 0:
                gap_percentage = abs(current_price - previous_close) / previous_close
                
                if gap_percentage >= self.gap_threshold:
                    gaps.append({
                        'type': 'price_gap',
                        'gap_percentage': gap_percentage,
                        'current_price': current_price,
                        'previous_close': previous_close,
                        'severity': 'HIGH' if gap_percentage >= 0.10 else 'MEDIUM'
                    })
        
        except (ValueError, TypeError) as e:
            logger.warning(f"Error detecting price gaps: {str(e)}")
        
        return gaps
    
    def _validate_volume(self, current_volume: float, avg_volume: float) -> List[Dict[str, Any]]:
        """Validate volume data for anomalies"""
        issues = []
        
        try:
            if current_volume <= 0:
                issues.append({
                    'type': 'invalid_volume',
                    'severity': 'MEDIUM',
                    'message': "Zero or negative volume detected"
                })
            elif avg_volume > 0:
                volume_ratio = current_volume / avg_volume
                
                if volume_ratio > 5.0:  # Volume spike
                    issues.append({
                        'type': 'volume_anomaly',
                        'severity': 'MEDIUM',
                        'message': f"Unusual volume spike: {volume_ratio:.1f}x average"
                    })
                elif volume_ratio < 0.1:  # Very low volume
                    issues.append({
                        'type': 'volume_anomaly',
                        'severity': 'LOW',
                        'message': f"Unusually low volume: {volume_ratio:.1%} of average"
                    })
        
        except (ValueError, TypeError) as e:
            logger.warning(f"Error validating volume: {str(e)}")
        
        return issues
    
    def _calculate_quality_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        base_score = 1.0
        
        # Reduce score based on issues
        for issue in validation_result.get('issues', []):
            if issue['severity'] == 'HIGH':
                base_score *= 0.6
            elif issue['severity'] == 'MEDIUM':
                base_score *= 0.8
            elif issue['severity'] == 'LOW':
                base_score *= 0.9
        
        # Reduce score for gaps
        gap_count = len(validation_result.get('gaps_detected', []))
        if gap_count > 0:
            base_score *= (0.8 ** gap_count)
        
        return max(0.0, base_score)
    
    def _detect_date_gaps(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect gaps in historical data dates"""
        gaps = []
        
        try:
            # Sort by date
            sorted_points = sorted(data_points, key=lambda x: x.get('date', ''))
            
            for i in range(1, len(sorted_points)):
                current_date = datetime.fromisoformat(sorted_points[i]['date'].replace('Z', '+00:00'))
                previous_date = datetime.fromisoformat(sorted_points[i-1]['date'].replace('Z', '+00:00'))
                
                # Check for weekend gaps (acceptable)
                days_diff = (current_date - previous_date).days
                
                # Flag gaps longer than 3 days (excluding weekends)
                if days_diff > 3:
                    gaps.append({
                        'type': 'date_gap',
                        'start_date': previous_date.isoformat(),
                        'end_date': current_date.isoformat(),
                        'days_missing': days_diff
                    })
        
        except Exception as e:
            logger.warning(f"Error detecting date gaps: {str(e)}")
        
        return gaps
    
    def _detect_price_anomalies(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect price anomalies in historical data"""
        anomalies = []
        
        try:
            if len(data_points) < 5:
                return anomalies
            
            # Extract close prices
            prices = [float(point.get('close', 0)) for point in data_points if point.get('close')]
            
            if len(prices) < 5:
                return anomalies
            
            # Calculate moving average and standard deviation
            window_size = min(10, len(prices) // 2)
            
            for i in range(window_size, len(prices)):
                window_prices = prices[i-window_size:i]
                mean_price = np.mean(window_prices)
                std_price = np.std(window_prices)
                
                current_price = prices[i]
                
                # Flag prices that are more than 3 standard deviations away
                if std_price > 0:
                    z_score = abs(current_price - mean_price) / std_price
                    
                    if z_score > 3:
                        anomalies.append({
                            'type': 'price_anomaly',
                            'date': data_points[i].get('date', ''),
                            'price': current_price,
                            'expected_range': f"{mean_price - 2*std_price:.2f} - {mean_price + 2*std_price:.2f}",
                            'z_score': z_score
                        })
        
        except Exception as e:
            logger.warning(f"Error detecting price anomalies: {str(e)}")
        
        return anomalies
    
    def _calculate_continuity_score(self, gaps: List[Dict[str, Any]], total_points: int) -> float:
        """Calculate data continuity score"""
        if total_points == 0:
            return 0.0
        
        # Base score
        continuity_score = 1.0
        
        # Reduce score for each gap
        for gap in gaps:
            days_missing = gap.get('days_missing', 1)
            # Reduce score based on gap size
            continuity_score *= max(0.1, 1.0 - (days_missing / 30.0))
        
        return max(0.0, continuity_score)
    
    def _calculate_historical_quality_score(self, continuity_score: float, 
                                          anomalies: List[Dict[str, Any]]) -> float:
        """Calculate overall historical data quality score"""
        base_score = continuity_score
        
        # Reduce score for anomalies
        anomaly_count = len(anomalies)
        if anomaly_count > 0:
            base_score *= max(0.5, 1.0 - (anomaly_count / 100.0))
        
        return max(0.0, base_score)
    
    def _generate_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if validation_result['should_skip_prediction']:
            recommendations.append("SKIP prediction due to poor data quality")
        
        if validation_result['quality_score'] < 0.8:
            recommendations.append("Consider using alternative data sources")
        
        for issue in validation_result.get('issues', []):
            if issue['type'] == 'ohlc_logic_error':
                recommendations.append("Verify OHLC data source and collection process")
            elif issue['type'] == 'volume_anomaly':
                recommendations.append("Investigate volume spike - possible news event")
        
        if validation_result.get('gaps_detected'):
            recommendations.append("Check for market halts or data feed issues")
        
        return recommendations
    
    def _generate_historical_recommendations(self, validation_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations for historical data issues"""
        recommendations = []
        
        if validation_result.get('continuity_score', 1.0) < 0.8:
            recommendations.append("Fill historical data gaps before training models")
        
        anomaly_count = len(validation_result.get('anomalies', []))
        if anomaly_count > 5:
            recommendations.append(f"Review {anomaly_count} price anomalies - may need data cleaning")
        
        return recommendations
    
    def _generate_system_recommendations(self, avg_quality: float, skip_rate: float, 
                                       issue_counts: Dict[str, int]) -> List[str]:
        """Generate system-level recommendations"""
        recommendations = []
        
        if avg_quality < 0.7:
            recommendations.append("URGENT: Review data collection processes - quality below acceptable threshold")
        
        if skip_rate > 0.2:
            recommendations.append(f"HIGH: {skip_rate:.1%} of predictions being skipped due to data quality")
        
        if issue_counts.get('ohlc_logic_error', 0) > 0:
            recommendations.append("Review OHLC data validation logic - logic errors detected")
        
        if issue_counts.get('price_gap', 0) > 10:
            recommendations.append("Investigate frequent price gaps - may indicate feed issues")
        
        return recommendations
    
    def _log_validation_result(self, validation_result: Dict[str, Any]):
        """Log validation result to daily file"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = os.path.join(self.validation_log_path, f"{today}.json")
            
            # Load existing validations
            validations = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    data = json.load(f)
                    validations = data.get('validations', [])
            
            # Add new validation
            validations.append(validation_result)
            
            # Save updated validations
            log_data = {
                'date': today,
                'validations': validations,
                'summary': {
                    'total_validations': len(validations),
                    'avg_quality': np.mean([v.get('quality_score', 0) for v in validations]),
                    'skip_rate': np.mean([1 if v.get('should_skip_prediction', False) else 0 for v in validations])
                }
            }
            
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging validation result: {str(e)}")
    
    def _get_validation_files(self, timeframe: str) -> List[str]:
        """Get validation log files for specified timeframe"""
        files = []
        
        try:
            if timeframe == "24h":
                days = 1
            elif timeframe == "7d":
                days = 7
            elif timeframe == "30d":
                days = 30
            else:
                days = 1
            
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                file_path = os.path.join(self.validation_log_path, f"{date}.json")
                if os.path.exists(file_path):
                    files.append(file_path)
        
        except Exception as e:
            logger.error(f"Error getting validation files: {str(e)}")
        
        return files
