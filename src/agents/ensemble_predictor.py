
"""
Enhanced Stock Market Analyst - Ensemble Prediction System

Combines multiple prediction methods for improved accuracy:
1. Technical Analysis Predictions
2. Fundamental Analysis Predictions  
3. Sentiment-based Predictions
4. Market Pattern Recognition
5. Volatility-adjusted Predictions
"""

import numpy as np
import pandas as pd
import logging
import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import yfinance as yf

logger = logging.getLogger(__name__)

class EnsemblePredictionSystem:
    def __init__(self):
        # Dynamic weights that adjust based on recent performance
        self.base_weights = {
            'technical': 0.35,
            'fundamental': 0.25, 
            'sentiment': 0.20,
            'pattern': 0.15,
            'volatility': 0.05
        }
        self.performance_history = self._load_performance_history()
        self.prediction_weights = self._calculate_dynamic_weights()
        
    def generate_ensemble_prediction(self, symbol: str, data: Dict) -> Dict:
        """Generate ensemble prediction combining multiple methods"""
        try:
            # Extract data components
            fundamentals = data.get('fundamentals', {})
            technical = data.get('technical', {})
            sentiment = data.get('sentiment', {})
            market_data = data.get('market_data', {})
            
            # Generate individual predictions
            tech_pred = self.technical_prediction(technical)
            fund_pred = self.fundamental_prediction(fundamentals)
            sent_pred = self.sentiment_prediction(sentiment)
            pattern_pred = self.pattern_prediction(symbol, technical)
            vol_pred = self.volatility_adjusted_prediction(technical)

    
    def _load_performance_history(self) -> Dict:
        """Load recent performance history of different prediction methods"""
        try:
            with open('ensemble_performance_history.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'technical': {'accuracy': 0.65, 'recent_predictions': 0},
                'fundamental': {'accuracy': 0.60, 'recent_predictions': 0},
                'sentiment': {'accuracy': 0.55, 'recent_predictions': 0},
                'pattern': {'accuracy': 0.58, 'recent_predictions': 0},
                'volatility': {'accuracy': 0.52, 'recent_predictions': 0}
            }
        except Exception as e:
            logger.error(f"Error loading performance history: {str(e)}")
            return {
                'technical': {'accuracy': 0.65, 'recent_predictions': 0},
                'fundamental': {'accuracy': 0.60, 'recent_predictions': 0},
                'sentiment': {'accuracy': 0.55, 'recent_predictions': 0},
                'pattern': {'accuracy': 0.58, 'recent_predictions': 0},
                'volatility': {'accuracy': 0.52, 'recent_predictions': 0}
            }
    
    def _calculate_dynamic_weights(self) -> Dict:
        """Calculate dynamic weights based on recent performance"""
        try:
            weights = self.base_weights.copy()
            
            # Adjust weights based on recent accuracy
            total_adjustment = 0
            for method in weights.keys():
                if method in self.performance_history:
                    accuracy = self.performance_history[method].get('accuracy', 0.5)
                    predictions_count = self.performance_history[method].get('recent_predictions', 0)
                    
                    # Only adjust if we have enough recent data
                    if predictions_count >= 10:
                        # Boost weight for high-performing methods
                        if accuracy > 0.7:
                            adjustment = 0.1 * (accuracy - 0.7)
                            weights[method] += adjustment
                            total_adjustment += adjustment
                        # Reduce weight for poor-performing methods
                        elif accuracy < 0.5:
                            adjustment = 0.1 * (0.5 - accuracy)
                            weights[method] = max(0.05, weights[method] - adjustment)
                            total_adjustment -= adjustment
            
            # Normalize weights to sum to 1
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v/total_weight for k, v in weights.items()}
            
            return weights
            
        except Exception as e:
            logger.error(f"Error calculating dynamic weights: {str(e)}")
            return self.base_weights
    
    def update_method_performance(self, method: str, was_correct: bool):
        """Update performance tracking for a prediction method"""
        try:
            if method not in self.performance_history:
                self.performance_history[method] = {'accuracy': 0.5, 'recent_predictions': 0, 'correct_predictions': 0}
            
            history = self.performance_history[method]
            history['recent_predictions'] += 1
            
            if was_correct:
                history['correct_predictions'] = history.get('correct_predictions', 0) + 1
            
            # Calculate rolling accuracy (last 50 predictions)
            if history['recent_predictions'] > 0:
                history['accuracy'] = history['correct_predictions'] / min(history['recent_predictions'], 50)
            
            # Reset counters if we have too many predictions
            if history['recent_predictions'] > 100:
                history['recent_predictions'] = 50
                history['correct_predictions'] = int(history['accuracy'] * 50)
            
            # Save updated history
            with open('ensemble_performance_history.json', 'w') as f:
                json.dump(self.performance_history, f, indent=2)
            
            # Recalculate weights
            self.prediction_weights = self._calculate_dynamic_weights()
            
        except Exception as e:
            logger.error(f"Error updating method performance: {str(e)}")

            
            # Calculate weighted ensemble prediction
            ensemble_pred = {
                '24h': (tech_pred['24h'] * self.prediction_weights['technical'] +
                       fund_pred['24h'] * self.prediction_weights['fundamental'] +
                       sent_pred['24h'] * self.prediction_weights['sentiment'] +
                       pattern_pred['24h'] * self.prediction_weights['pattern'] +
                       vol_pred['24h'] * self.prediction_weights['volatility']),
                
                '5d': (tech_pred['5d'] * self.prediction_weights['technical'] +
                      fund_pred['5d'] * self.prediction_weights['fundamental'] +
                      sent_pred['5d'] * self.prediction_weights['sentiment'] +
                      pattern_pred['5d'] * self.prediction_weights['pattern'] +
                      vol_pred['5d'] * self.prediction_weights['volatility']),
                
                '1mo': (tech_pred['1mo'] * self.prediction_weights['technical'] +
                       fund_pred['1mo'] * self.prediction_weights['fundamental'] +
                       sent_pred['1mo'] * self.prediction_weights['sentiment'] +
                       pattern_pred['1mo'] * self.prediction_weights['pattern'] +
                       vol_pred['1mo'] * self.prediction_weights['volatility'])
            }
            
            # Calculate prediction confidence
            confidence = self.calculate_prediction_confidence(
                tech_pred, fund_pred, sent_pred, pattern_pred, vol_pred
            )
            
            # Apply market regime adjustments
            ensemble_pred = self.apply_market_regime_adjustment(ensemble_pred, market_data)
            
            return {
                'pred_24h': round(ensemble_pred['24h'], 2),
                'pred_5d': round(ensemble_pred['5d'], 2), 
                'pred_1mo': round(ensemble_pred['1mo'], 2),
                'confidence': round(confidence, 1),
                'individual_predictions': {
                    'technical': tech_pred,
                    'fundamental': fund_pred,
                    'sentiment': sent_pred,
                    'pattern': pattern_pred,
                    'volatility': vol_pred
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble prediction for {symbol}: {str(e)}")
            return {
                'pred_24h': 0,
                'pred_5d': 0,
                'pred_1mo': 0,
                'confidence': 30,
                'individual_predictions': {}
            }
    
    def technical_prediction(self, technical: Dict) -> Dict:
        """Technical analysis based prediction"""
        try:
            prediction = {'24h': 0, '5d': 0, '1mo': 0}
            
            # RSI-based prediction
            rsi = technical.get('rsi_14', 50)
            if rsi < 30:
                prediction['24h'] += 2.0  # Oversold bounce
                prediction['5d'] += 4.0
                prediction['1mo'] += 6.0
            elif rsi > 70:
                prediction['24h'] -= 1.0  # Overbought correction
                prediction['5d'] -= 2.0
                prediction['1mo'] -= 3.0
            
            # MACD prediction
            macd_histogram = technical.get('macd_histogram', 0)
            if macd_histogram > 0:
                prediction['24h'] += 1.5
                prediction['5d'] += 3.0
                prediction['1mo'] += 4.5
            else:
                prediction['24h'] -= 1.0
                prediction['5d'] -= 2.0
                prediction['1mo'] -= 3.0
            
            # Bollinger Bands prediction
            bb_position = technical.get('bb_position', 50)
            if bb_position < 20:
                prediction['24h'] += 1.0  # Near lower band
                prediction['5d'] += 2.5
                prediction['1mo'] += 4.0
            elif bb_position > 80:
                prediction['24h'] -= 0.5  # Near upper band
                prediction['5d'] -= 1.5
                prediction['1mo'] -= 2.5
            
            # Trend strength
            trend_strength = technical.get('trend_strength', 0)
            trend_factor = trend_strength / 100 * 3  # Max 3% boost
            prediction['24h'] += trend_factor * 0.3
            prediction['5d'] += trend_factor * 0.7
            prediction['1mo'] += trend_factor * 1.0
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in technical prediction: {str(e)}")
            return {'24h': 0, '5d': 0, '1mo': 0}
    
    def fundamental_prediction(self, fundamentals: Dict) -> Dict:
        """Fundamental analysis based prediction"""
        try:
            prediction = {'24h': 0, '5d': 0, '1mo': 0}
            
            # PE ratio impact (stronger for longer timeframes)
            pe_ratio = fundamentals.get('pe_ratio', 20)
            if 0 < pe_ratio < 12:
                prediction['24h'] += 0.5
                prediction['5d'] += 2.0
                prediction['1mo'] += 5.0  # Undervalued stocks
            elif pe_ratio > 30:
                prediction['24h'] -= 0.3
                prediction['5d'] -= 1.0
                prediction['1mo'] -= 3.0  # Overvalued
            
            # Growth impact
            revenue_growth = fundamentals.get('revenue_growth', 0)
            earnings_growth = fundamentals.get('earnings_growth', 0)
            
            growth_factor = (revenue_growth + earnings_growth) / 40  # Normalize
            prediction['24h'] += growth_factor * 0.2
            prediction['5d'] += growth_factor * 0.8
            prediction['1mo'] += growth_factor * 2.0
            
            # Promoter buying (immediate positive signal)
            if fundamentals.get('promoter_buying', False):
                prediction['24h'] += 1.5
                prediction['5d'] += 3.0
                prediction['1mo'] += 5.0
            
            # Financial health ratios
            roe = fundamentals.get('roe', 0)
            if roe > 15:
                prediction['1mo'] += 2.0  # Good ROE impacts long-term
            
            debt_to_equity = fundamentals.get('debt_to_equity', 1)
            if debt_to_equity < 0.5:
                prediction['1mo'] += 1.0  # Low debt is good for long-term
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in fundamental prediction: {str(e)}")
            return {'24h': 0, '5d': 0, '1mo': 0}
    
    def sentiment_prediction(self, sentiment: Dict) -> Dict:
        """Sentiment analysis based prediction"""
        try:
            prediction = {'24h': 0, '5d': 0, '1mo': 0}
            
            # Bulk deal activity
            bulk_deal_bonus = sentiment.get('bulk_deal_bonus', 0)
            prediction['24h'] += bulk_deal_bonus * 0.1
            prediction['5d'] += bulk_deal_bonus * 0.3
            prediction['1mo'] += bulk_deal_bonus * 0.5
            
            # News sentiment (if available)
            news_sentiment = sentiment.get('news_sentiment', 0)  # -1 to 1
            prediction['24h'] += news_sentiment * 1.0
            prediction['5d'] += news_sentiment * 2.0
            prediction['1mo'] += news_sentiment * 3.0
            
            # Market sentiment indicators
            market_sentiment = sentiment.get('market_sentiment', 'neutral')
            if market_sentiment == 'bullish':
                prediction['24h'] += 0.5
                prediction['5d'] += 1.0
                prediction['1mo'] += 1.5
            elif market_sentiment == 'bearish':
                prediction['24h'] -= 0.5
                prediction['5d'] -= 1.0
                prediction['1mo'] -= 1.5
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in sentiment prediction: {str(e)}")
            return {'24h': 0, '5d': 0, '1mo': 0}
    
    def pattern_prediction(self, symbol: str, technical: Dict) -> Dict:
        """Pattern recognition based prediction"""
        try:
            prediction = {'24h': 0, '5d': 0, '1mo': 0}
            
            # Support/resistance levels
            price_position = technical.get('price_position', 50)
            
            # Near support (potential bounce)
            if price_position < 25:
                prediction['24h'] += 1.0
                prediction['5d'] += 2.0
                prediction['1mo'] += 2.5
            
            # Near resistance (potential rejection)
            elif price_position > 75:
                prediction['24h'] -= 0.5
                prediction['5d'] -= 1.0
                prediction['1mo'] -= 1.5
            
            # Volume pattern analysis
            volume_ratio = technical.get('volume_sma_ratio', 1)
            if volume_ratio > 1.5:  # High volume breakout
                prediction['24h'] += 0.8
                prediction['5d'] += 1.5
                prediction['1mo'] += 2.0
            
            # Volatility squeeze pattern
            bb_width = technical.get('bb_width', 5)
            if bb_width < 3:  # Low volatility (squeeze)
                prediction['5d'] += 1.0  # Expect breakout
                prediction['1mo'] += 2.0
            
            # Momentum divergence patterns
            rsi = technical.get('rsi_14', 50)
            price_momentum = technical.get('roc_10', 0)
            
            if rsi < 40 and price_momentum > 0:  # Bullish divergence
                prediction['5d'] += 1.5
                prediction['1mo'] += 2.5
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in pattern prediction: {str(e)}")
            return {'24h': 0, '5d': 0, '1mo': 0}
    
    def volatility_adjusted_prediction(self, technical: Dict) -> Dict:
        """Volatility-adjusted prediction"""
        try:
            prediction = {'24h': 0, '5d': 0, '1mo': 0}
            
            atr_volatility = technical.get('atr_volatility', 2)
            
            # Low volatility stocks tend to have mean reversion
            if atr_volatility < 1.5:
                prediction['24h'] += 0.3
                prediction['5d'] += 0.8
                prediction['1mo'] += 1.2
            
            # High volatility stocks are unpredictable
            elif atr_volatility > 4:
                prediction['24h'] -= 0.2
                prediction['5d'] -= 0.5
                prediction['1mo'] -= 0.8
            
            # Volatility mean reversion
            coeff_var_20 = technical.get('coeff_variation_20', 2)
            if coeff_var_20 > 3:  # High recent volatility
                prediction['5d'] += 0.5  # Expect calming down
                prediction['1mo'] += 1.0
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error in volatility prediction: {str(e)}")
            return {'24h': 0, '5d': 0, '1mo': 0}
    
    def calculate_prediction_confidence(self, tech_pred: Dict, fund_pred: Dict, 
                                      sent_pred: Dict, pattern_pred: Dict, vol_pred: Dict) -> float:
        """Calculate overall prediction confidence"""
        try:
            # Check agreement between different methods
            predictions_1mo = [
                tech_pred['1mo'], fund_pred['1mo'], sent_pred['1mo'],
                pattern_pred['1mo'], vol_pred['1mo']
            ]
            
            # Calculate standard deviation of predictions
            std_dev = np.std(predictions_1mo)
            
            # Lower std dev = higher confidence
            base_confidence = max(30, 90 - (std_dev * 10))
            
            # Boost confidence if most predictions agree on direction
            positive_count = sum(1 for p in predictions_1mo if p > 0)
            negative_count = sum(1 for p in predictions_1mo if p < 0)
            
            if positive_count >= 4 or negative_count >= 4:
                base_confidence += 15  # Strong agreement
            elif positive_count >= 3 or negative_count >= 3:
                base_confidence += 8   # Moderate agreement
            
            return min(100, base_confidence)
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 50
    
    def apply_market_regime_adjustment(self, prediction: Dict, market_data: Dict) -> Dict:
        """Adjust predictions based on overall market conditions"""
        try:
            # Market trend adjustment
            market_trend = market_data.get('market_trend', 'neutral')
            
            if market_trend == 'bullish':
                adjustment = 1.1  # 10% boost in bull market
            elif market_trend == 'bearish':
                adjustment = 0.9  # 10% reduction in bear market
            else:
                adjustment = 1.0
            
            # VIX-like volatility adjustment
            market_volatility = market_data.get('market_volatility', 'normal')
            
            if market_volatility == 'high':
                adjustment *= 0.95  # Reduce predictions in high vol environment
            elif market_volatility == 'low':
                adjustment *= 1.05  # Boost predictions in low vol environment
            
            # Apply adjustments
            prediction['24h'] *= adjustment
            prediction['5d'] *= adjustment  
            prediction['1mo'] *= adjustment
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error applying market regime adjustment: {str(e)}")
            return prediction

# Integration function for main stock screener
def get_ensemble_prediction(symbol: str, data: Dict) -> Dict:
    """Get ensemble prediction for a stock"""
    ensemble = EnsemblePredictionSystem()
    return ensemble.generate_ensemble_prediction(symbol, data)
