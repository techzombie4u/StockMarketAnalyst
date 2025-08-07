
#!/usr/bin/env python3
"""
Advanced Model Explainability Engine

This module provides SHAP-based feature importance and explainability for predictions:
1. SHAP integration for both LSTM & RF models
2. Top 3 contributing drivers per prediction
3. Cause → effect mapping for prediction explanations
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Try to import SHAP, fallback to custom implementation if not available
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("SHAP not available, using fallback explainability methods")

logger = logging.getLogger(__name__)

class ExplainabilityEngine:
    def __init__(self):
        self.explanations_path = "data/tracking/explanations.json"
        self.feature_importance_cache = "data/cache/feature_importance.json"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.explanations_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.feature_importance_cache), exist_ok=True)
        
        # Feature mapping for technical indicators
        self.feature_mapping = {
            'close': 'Closing Price',
            'volume': 'Trading Volume',
            'rsi': 'Relative Strength Index',
            'macd': 'MACD Signal',
            'macd_signal': 'MACD Signal Line',
            'macd_histogram': 'MACD Histogram',
            'bollinger_upper': 'Bollinger Upper Band',
            'bollinger_lower': 'Bollinger Lower Band',
            'bollinger_middle': 'Bollinger Middle Band',
            'sma_20': '20-day Simple Moving Average',
            'sma_50': '50-day Simple Moving Average',
            'ema_12': '12-day Exponential Moving Average',
            'ema_26': '26-day Exponential Moving Average',
            'stochastic_k': 'Stochastic %K',
            'stochastic_d': 'Stochastic %D',
            'williams_r': 'Williams %R',
            'momentum': 'Price Momentum',
            'roc': 'Rate of Change',
            'atr': 'Average True Range',
            'adx': 'Average Directional Index',
            'cci': 'Commodity Channel Index'
        }
        
        # Initialize explainability data
        self._initialize_explainability()

    def _initialize_explainability(self):
        """Initialize explainability data structures"""
        try:
            if not os.path.exists(self.explanations_path):
                initial_data = {
                    'prediction_explanations': {},
                    'feature_importance_history': {},
                    'explanation_patterns': {},
                    'last_updated': datetime.now().isoformat()
                }
                self._save_json(self.explanations_path, initial_data)
                
            if not os.path.exists(self.feature_importance_cache):
                initial_cache = {
                    'lstm_importance': {},
                    'rf_importance': {},
                    'cache_timestamp': datetime.now().isoformat()
                }
                self._save_json(self.feature_importance_cache, initial_cache)
                
        except Exception as e:
            logger.error(f"Error initializing explainability engine: {str(e)}")

    def explain_prediction(self, model_type: str, prediction_data: Dict, 
                         feature_data: Dict, model_object=None) -> Dict[str, Any]:
        """Generate comprehensive explanation for a prediction"""
        try:
            explanation_id = f"{prediction_data.get('symbol', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Get feature importance
            if SHAP_AVAILABLE and model_object is not None:
                shap_explanation = self._get_shap_explanation(model_type, feature_data, model_object)
            else:
                shap_explanation = self._get_fallback_explanation(model_type, feature_data, prediction_data)
            
            # Get top contributing features
            top_drivers = self._get_top_drivers(shap_explanation, n_top=3)
            
            # Generate cause-effect mapping
            cause_effect_mapping = self._generate_cause_effect_mapping(top_drivers, feature_data, prediction_data)
            
            # Create comprehensive explanation
            explanation = {
                'explanation_id': explanation_id,
                'timestamp': datetime.now().isoformat(),
                'model_type': model_type,
                'symbol': prediction_data.get('symbol', 'unknown'),
                'prediction_value': prediction_data.get('predicted_price', 0),
                'confidence': prediction_data.get('confidence', 0),
                'top_drivers': top_drivers,
                'cause_effect_mapping': cause_effect_mapping,
                'feature_importance': shap_explanation.get('feature_importance', {}),
                'shap_values': shap_explanation.get('shap_values', {}),
                'explanation_summary': self._generate_explanation_summary(top_drivers, cause_effect_mapping)
            }
            
            # Save explanation
            self._save_explanation(explanation)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining prediction: {str(e)}")
            return self._empty_explanation()

    def _get_shap_explanation(self, model_type: str, feature_data: Dict, model_object) -> Dict[str, Any]:
        """Get SHAP-based explanation"""
        try:
            if not SHAP_AVAILABLE:
                return self._get_fallback_explanation(model_type, feature_data, {})
            
            # Prepare feature array
            feature_array = self._prepare_feature_array(feature_data)
            
            if model_type.lower() == 'lstm':
                # For LSTM models, use DeepExplainer
                explainer = shap.DeepExplainer(model_object, feature_array[:10])  # Background sample
                shap_values = explainer.shap_values(feature_array[-1:])  # Latest prediction
            elif model_type.lower() in ['rf', 'randomforest']:
                # For tree-based models, use TreeExplainer
                explainer = shap.TreeExplainer(model_object)
                shap_values = explainer.shap_values(feature_array[-1:])
            else:
                # For other models, use KernelExplainer
                explainer = shap.KernelExplainer(model_object.predict, feature_array[:10])
                shap_values = explainer.shap_values(feature_array[-1:])
            
            # Convert to feature importance
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # For classification, take first class
            
            feature_names = list(feature_data.keys())
            importance_dict = {}
            
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]  # Take first sample
            
            for i, feature in enumerate(feature_names[:len(shap_values)]):
                importance_dict[feature] = float(shap_values[i])
            
            return {
                'feature_importance': importance_dict,
                'shap_values': importance_dict,
                'explanation_method': 'SHAP'
            }
            
        except Exception as e:
            logger.error(f"Error getting SHAP explanation: {str(e)}")
            return self._get_fallback_explanation(model_type, feature_data, {})

    def _get_fallback_explanation(self, model_type: str, feature_data: Dict, prediction_data: Dict) -> Dict[str, Any]:
        """Fallback explanation method when SHAP is not available"""
        try:
            # Load cached importance or calculate based on domain knowledge
            cached_importance = self._load_json(self.feature_importance_cache)
            
            if model_type.lower() in cached_importance:
                base_importance = cached_importance[model_type.lower()]
            else:
                base_importance = self._calculate_domain_importance(model_type)
            
            # Adjust importance based on current feature values
            adjusted_importance = {}
            for feature, value in feature_data.items():
                base_imp = base_importance.get(feature, 0.1)
                
                # Adjust based on feature value characteristics
                if feature == 'rsi':
                    if value > 70 or value < 30:  # Overbought/Oversold
                        adjusted_importance[feature] = base_imp * 1.5
                    else:
                        adjusted_importance[feature] = base_imp * 0.8
                elif feature == 'macd':
                    if abs(value) > 0.5:  # Strong signal
                        adjusted_importance[feature] = base_imp * 1.3
                    else:
                        adjusted_importance[feature] = base_imp
                elif feature == 'volume':
                    # Assume high volume is more important
                    adjusted_importance[feature] = base_imp * min(1.5, max(0.5, value / 1000000))
                else:
                    adjusted_importance[feature] = base_imp
            
            return {
                'feature_importance': adjusted_importance,
                'shap_values': adjusted_importance,
                'explanation_method': 'Domain Knowledge Fallback'
            }
            
        except Exception as e:
            logger.error(f"Error in fallback explanation: {str(e)}")
            return {'feature_importance': {}, 'shap_values': {}, 'explanation_method': 'Error'}

    def _calculate_domain_importance(self, model_type: str) -> Dict[str, float]:
        """Calculate feature importance based on domain knowledge"""
        
        if model_type.lower() == 'lstm':
            # LSTM models typically focus on sequential patterns
            importance = {
                'close': 0.25,
                'volume': 0.15,
                'rsi': 0.12,
                'macd': 0.12,
                'sma_20': 0.10,
                'sma_50': 0.08,
                'bollinger_upper': 0.06,
                'bollinger_lower': 0.06,
                'atr': 0.06
            }
        elif model_type.lower() in ['rf', 'randomforest']:
            # Random Forest typically values diverse indicators
            importance = {
                'rsi': 0.18,
                'macd': 0.16,
                'close': 0.15,
                'volume': 0.12,
                'bollinger_upper': 0.10,
                'bollinger_lower': 0.10,
                'sma_20': 0.08,
                'stochastic_k': 0.06,
                'atr': 0.05
            }
        else:
            # Default importance distribution
            importance = {
                'close': 0.20,
                'rsi': 0.15,
                'macd': 0.15,
                'volume': 0.12,
                'sma_20': 0.10,
                'sma_50': 0.08,
                'bollinger_upper': 0.08,
                'bollinger_lower': 0.08,
                'atr': 0.04
            }
        
        return importance

    def _get_top_drivers(self, explanation: Dict, n_top: int = 3) -> List[Dict]:
        """Get top N driving features for the prediction"""
        try:
            feature_importance = explanation.get('feature_importance', {})
            
            # Sort by absolute importance
            sorted_features = sorted(feature_importance.items(), 
                                   key=lambda x: abs(x[1]), reverse=True)
            
            top_drivers = []
            for i, (feature, importance) in enumerate(sorted_features[:n_top]):
                driver = {
                    'rank': i + 1,
                    'feature': feature,
                    'feature_name': self.feature_mapping.get(feature, feature.title()),
                    'importance': importance,
                    'impact': 'Positive' if importance > 0 else 'Negative',
                    'strength': 'Strong' if abs(importance) > 0.1 else 'Medium' if abs(importance) > 0.05 else 'Weak'
                }
                top_drivers.append(driver)
            
            return top_drivers
            
        except Exception as e:
            logger.error(f"Error getting top drivers: {str(e)}")
            return []

    def _generate_cause_effect_mapping(self, top_drivers: List[Dict], 
                                     feature_data: Dict, prediction_data: Dict) -> List[Dict]:
        """Generate cause-effect mapping for prediction explanation"""
        try:
            cause_effect_maps = []
            
            for driver in top_drivers:
                feature = driver['feature']
                feature_value = feature_data.get(feature, 0)
                importance = driver['importance']
                
                # Generate specific cause-effect explanation
                cause_effect = {
                    'cause': self._describe_feature_state(feature, feature_value),
                    'effect': self._describe_prediction_effect(feature, importance, prediction_data),
                    'mechanism': self._explain_mechanism(feature, feature_value, importance),
                    'confidence': self._calculate_explanation_confidence(driver['strength'])
                }
                
                cause_effect_maps.append(cause_effect)
            
            return cause_effect_maps
            
        except Exception as e:
            logger.error(f"Error generating cause-effect mapping: {str(e)}")
            return []

    def _describe_feature_state(self, feature: str, value: float) -> str:
        """Describe the current state of a feature"""
        feature_name = self.feature_mapping.get(feature, feature.title())
        
        if feature == 'rsi':
            if value > 70:
                return f"{feature_name} is in overbought territory at {value:.1f}"
            elif value < 30:
                return f"{feature_name} is in oversold territory at {value:.1f}"
            else:
                return f"{feature_name} is neutral at {value:.1f}"
        elif feature == 'macd':
            if value > 0:
                return f"{feature_name} shows bullish momentum at {value:.3f}"
            else:
                return f"{feature_name} shows bearish momentum at {value:.3f}"
        elif feature == 'volume':
            return f"{feature_name} is at {value:,.0f} shares"
        elif 'sma' in feature or 'ema' in feature:
            return f"{feature_name} is at ₹{value:.2f}"
        elif 'bollinger' in feature:
            return f"{feature_name} is at ₹{value:.2f}"
        else:
            return f"{feature_name} value is {value:.3f}"

    def _describe_prediction_effect(self, feature: str, importance: float, prediction_data: Dict) -> str:
        """Describe how the feature affects the prediction"""
        direction = "increases" if importance > 0 else "decreases"
        strength = "strongly" if abs(importance) > 0.1 else "moderately" if abs(importance) > 0.05 else "slightly"
        
        predicted_price = prediction_data.get('predicted_price', 0)
        
        return f"This {strength} {direction} the predicted price toward ₹{predicted_price:.2f}"

    def _explain_mechanism(self, feature: str, value: float, importance: float) -> str:
        """Explain the mechanism behind the feature's impact"""
        if feature == 'rsi':
            if value > 70:
                return "Overbought conditions typically lead to price corrections downward"
            elif value < 30:
                return "Oversold conditions often signal potential upward price movements"
            else:
                return "Neutral RSI suggests balanced buying and selling pressure"
        elif feature == 'macd':
            if value > 0:
                return "Positive MACD indicates upward momentum and potential price increase"
            else:
                return "Negative MACD suggests downward momentum and potential price decrease"
        elif feature == 'volume':
            return "High volume confirms price movement strength and trend validity"
        elif 'sma' in feature or 'ema' in feature:
            if importance > 0:
                return "Price above moving average indicates upward trend continuation"
            else:
                return "Price below moving average suggests downward pressure"
        elif 'bollinger' in feature:
            return "Bollinger band position indicates price volatility and potential reversal points"
        else:
            return "This indicator contributes to overall market sentiment analysis"

    def _calculate_explanation_confidence(self, strength: str) -> float:
        """Calculate confidence level for explanation"""
        strength_mapping = {
            'Strong': 0.9,
            'Medium': 0.7,
            'Weak': 0.5
        }
        return strength_mapping.get(strength, 0.5)

    def _generate_explanation_summary(self, top_drivers: List[Dict], 
                                    cause_effect_mapping: List[Dict]) -> str:
        """Generate human-readable explanation summary"""
        try:
            if not top_drivers:
                return "No significant drivers identified for this prediction."
            
            summary_parts = []
            
            # Main driving factor
            main_driver = top_drivers[0]
            main_cause = cause_effect_mapping[0] if cause_effect_mapping else {}
            
            summary_parts.append(f"The prediction is primarily driven by {main_driver['feature_name']} "
                                f"({main_driver['impact'].lower()} impact, {main_driver['strength'].lower()} strength).")
            
            if main_cause:
                summary_parts.append(f"{main_cause.get('cause', '')} - {main_cause.get('mechanism', '')}")
            
            # Supporting factors
            if len(top_drivers) > 1:
                supporting_factors = [d['feature_name'] for d in top_drivers[1:]]
                summary_parts.append(f"Supporting factors include {', '.join(supporting_factors)}.")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating explanation summary: {str(e)}")
            return "Unable to generate explanation summary."

    def _prepare_feature_array(self, feature_data: Dict) -> np.ndarray:
        """Prepare feature data as numpy array for SHAP"""
        try:
            # Convert feature dict to ordered array
            feature_values = []
            for feature in sorted(feature_data.keys()):
                value = feature_data[feature]
                if isinstance(value, (int, float)):
                    feature_values.append(float(value))
                else:
                    feature_values.append(0.0)  # Default for non-numeric
            
            return np.array(feature_values).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error preparing feature array: {str(e)}")
            return np.array([[]])

    def get_explanation_by_id(self, explanation_id: str) -> Optional[Dict]:
        """Retrieve explanation by ID"""
        try:
            explanations_data = self._load_json(self.explanations_path)
            return explanations_data.get('prediction_explanations', {}).get(explanation_id)
        except Exception as e:
            logger.error(f"Error retrieving explanation {explanation_id}: {str(e)}")
            return None

    def get_recent_explanations(self, limit: int = 10) -> List[Dict]:
        """Get recent explanations"""
        try:
            explanations_data = self._load_json(self.explanations_path)
            all_explanations = list(explanations_data.get('prediction_explanations', {}).values())
            
            # Sort by timestamp
            sorted_explanations = sorted(all_explanations, 
                                       key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return sorted_explanations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting recent explanations: {str(e)}")
            return []

    def _save_explanation(self, explanation: Dict):
        """Save explanation to storage"""
        try:
            explanations_data = self._load_json(self.explanations_path)
            
            explanation_id = explanation['explanation_id']
            explanations_data['prediction_explanations'][explanation_id] = explanation
            explanations_data['last_updated'] = datetime.now().isoformat()
            
            self._save_json(self.explanations_path, explanations_data)
            
        except Exception as e:
            logger.error(f"Error saving explanation: {str(e)}")

    def _empty_explanation(self) -> Dict:
        """Return empty explanation structure"""
        return {
            'explanation_id': 'error',
            'timestamp': datetime.now().isoformat(),
            'model_type': 'unknown',
            'symbol': 'unknown',
            'top_drivers': [],
            'cause_effect_mapping': [],
            'feature_importance': {},
            'explanation_summary': 'Unable to generate explanation due to error.'
        }

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
    """Test Explainability Engine functionality"""
    engine = ExplainabilityEngine()
    
    # Test explanation generation
    print("=== Testing Explainability Engine ===")
    
    sample_prediction = {
        'symbol': 'SBIN',
        'predicted_price': 652.50,
        'confidence': 85
    }
    
    sample_features = {
        'close': 640.0,
        'rsi': 75.2,
        'macd': 1.8,
        'volume': 2500000,
        'sma_20': 635.0,
        'bollinger_upper': 655.0,
        'bollinger_lower': 625.0
    }
    
    explanation = engine.explain_prediction('RF', sample_prediction, sample_features)
    print(f"Generated explanation: {explanation['explanation_summary']}")
    print(f"Top drivers: {[d['feature_name'] for d in explanation['top_drivers']]}")
    
    print("\n✅ Explainability Engine testing completed!")

if __name__ == "__main__":
    main()
