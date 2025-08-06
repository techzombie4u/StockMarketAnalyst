
"""
SmartStockAgent: Enhanced Intelligent Prediction Agent
Implements all requirements from the SmartStockAgent specification including:
- Input aggregation from multiple sources
- Signal evaluation & conflict resolution
- Scoring & final decision making
- Explainable AI (XAI)
- Prediction stability monitoring
- Time-based decision management
- Historical performance awareness
- Risk & signal quality assessment
- Intelligent filtering & signal confirmation
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import hashlib

logger = logging.getLogger(__name__)

class SmartStockAgent:
    def __init__(self):
        self.agent_history_file = 'agent_decisions.json'
        self.performance_history_file = 'agent_performance.json'
        self.locked_predictions_file = 'locked_predictions.json'
        
        # Dynamic weights for different prediction sources
        self.base_weights = {
            'technical': 0.25,
            'ml_lstm': 0.20,
            'ml_rf': 0.20,
            'ensemble': 0.15,
            'sentiment': 0.10,
            'fundamentals': 0.10
        }
        
        # Agent configuration
        self.confidence_threshold = 70.0  # Minimum confidence for recommendations
        self.stability_threshold = 5.0    # % change threshold for prediction updates
        self.lock_duration_hours = {
            '24h': 24,
            '5d': 120,   # 5 days
            '30d': 720   # 30 days
        }
        
        # Performance tracking
        self.model_performance = {}
        self.load_performance_history()
        
    def analyze_and_consolidate(self, symbol: str, all_predictions: Dict) -> Dict:
        """
        🔍 1. INPUT AGGREGATION - Main analysis function
        """
        try:
            logger.info(f"🤖 SmartStockAgent analyzing {symbol}...")
            
            # Step 1: Input Aggregation
            aggregated_data = self._aggregate_inputs(symbol, all_predictions)
            
            # Step 2: Signal Evaluation & Conflict Resolution
            signal_analysis = self._evaluate_signals_and_resolve_conflicts(aggregated_data)
            
            # Step 3: Risk & Signal Quality Assessment
            quality_assessment = self._assess_signal_quality_and_risk(aggregated_data, signal_analysis)
            
            # Step 4: Scoring & Final Decision Making
            final_decision = self._make_final_decision(symbol, aggregated_data, signal_analysis, quality_assessment)
            
            # Step 5: Explainable AI (XAI)
            explanation = self._generate_explanation(symbol, final_decision, signal_analysis, quality_assessment)
            
            # Step 6: Time-Based Decision Management
            time_managed_decision = self._apply_time_based_management(symbol, final_decision)
            
            # Step 7: Historical Performance Awareness
            performance_adjusted = self._apply_performance_awareness(time_managed_decision, signal_analysis)
            
            # Step 8: Prediction Stability Monitoring
            stability_result = self._monitor_prediction_stability(symbol, performance_adjusted)
            
            # Combine all results
            final_result = {
                **stability_result,
                'explanation': explanation,
                'signal_analysis': signal_analysis,
                'quality_assessment': quality_assessment,
                'timestamp': datetime.now().isoformat(),
                'agent_version': '2.0'
            }
            
            # Log decision for learning
            self._log_agent_decision(symbol, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error in SmartStockAgent analysis for {symbol}: {str(e)}")
            return self._get_fallback_decision(symbol)
    
    def _aggregate_inputs(self, symbol: str, all_predictions: Dict) -> Dict:
        """
        🔍 1. INPUT AGGREGATION - Collect predictions from multiple sources
        """
        aggregated = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'sources': {}
        }
        
        # Technical Indicators (RSI, MACD, Bollinger Bands)
        technical = all_predictions.get('technical', {})
        if technical:
            aggregated['sources']['technical'] = {
                'rsi_14': technical.get('rsi_14', 50),
                'macd_signal': technical.get('macd_bullish', False),
                'bb_position': technical.get('bb_position', 50),
                'trend_strength': technical.get('trend_strength', 50),
                'volume_ratio': technical.get('volume_ratio_10', 1.0),
                'atr_volatility': technical.get('atr_volatility', 2.0),
                'current_price': technical.get('current_price', 0),
                'confidence': min(100, len([k for k, v in technical.items() if v is not None]) * 5)
            }
        
        # Machine Learning Models (LSTM, Random Forest, etc.)
        ml_lstm = all_predictions.get('ml_lstm', {})
        if ml_lstm:
            aggregated['sources']['ml_lstm'] = {
                'predicted_change': ml_lstm.get('predicted_change', 0),
                'direction': ml_lstm.get('direction', 'UNKNOWN'),
                'confidence': ml_lstm.get('confidence', 50),
                'horizon': ml_lstm.get('horizon_days', 30)
            }
        
        ml_rf = all_predictions.get('ml_rf', {})
        if ml_rf:
            aggregated['sources']['ml_rf'] = {
                'direction_label': ml_rf.get('direction_label', 'UNKNOWN'),
                'confidence': ml_rf.get('confidence', 0.5) * 100,
                'feature_importance': ml_rf.get('feature_importance', {})
            }
        
        # Ensemble Predictor
        ensemble = all_predictions.get('ensemble', {})
        if ensemble:
            aggregated['sources']['ensemble'] = {
                'pred_24h': ensemble.get('pred_24h', 0),
                'pred_5d': ensemble.get('pred_5d', 0),
                'pred_1mo': ensemble.get('pred_1mo', 0),
                'confidence': ensemble.get('confidence', 50)
            }
        
        # Pattern Recognition (candlestick patterns, breakouts)
        patterns = technical.get('patterns', {}) if technical else {}
        aggregated['sources']['patterns'] = {
            'bullish_patterns': patterns.get('bullish', []),
            'bearish_patterns': patterns.get('bearish', []),
            'breakout_signals': patterns.get('breakouts', [])
        }
        
        # Sentiment/News-Based Scores
        sentiment = all_predictions.get('sentiment', {})
        aggregated['sources']['sentiment'] = {
            'bulk_deal_bonus': sentiment.get('bulk_deal_bonus', 0),
            'news_sentiment': sentiment.get('news_score', 0),
            'social_sentiment': sentiment.get('social_score', 0)
        }
        
        # Recent Price/Volume Behavior
        if technical:
            aggregated['sources']['price_volume'] = {
                'momentum_5d': technical.get('momentum_5d_pct', 0),
                'volume_spike': technical.get('volume_ratio_10', 1) > 1.5,
                'price_trend': 'up' if technical.get('momentum_5d_pct', 0) > 2 else 'down' if technical.get('momentum_5d_pct', 0) < -2 else 'sideways'
            }
        
        # Supplementary data (volatility, earnings, FII/DII activity)
        fundamentals = all_predictions.get('fundamentals', {})
        aggregated['sources']['fundamentals'] = {
            'pe_ratio': fundamentals.get('pe_ratio', 20),
            'revenue_growth': fundamentals.get('revenue_growth', 0),
            'earnings_growth': fundamentals.get('earnings_growth', 0),
            'debt_to_equity': fundamentals.get('debt_to_equity', 0.5),
            'promoter_buying': fundamentals.get('promoter_buying', False)
        }
        
        return aggregated
    
    def _evaluate_signals_and_resolve_conflicts(self, aggregated_data: Dict) -> Dict:
        """
        ⚖️ 2. SIGNAL EVALUATION & CONFLICT RESOLUTION
        """
        sources = aggregated_data.get('sources', {})
        conflicts = []
        consensus_signals = {'bullish': 0, 'bearish': 0, 'neutral': 0}
        
        # Collect directional signals from each source
        directional_signals = {}
        
        # Technical signals
        technical = sources.get('technical', {})
        if technical:
            rsi = technical.get('rsi_14', 50)
            if rsi < 30:
                tech_signal = 'bullish'
            elif rsi > 70:
                tech_signal = 'bearish'
            else:
                tech_signal = 'neutral'
            
            directional_signals['technical'] = {
                'direction': tech_signal,
                'confidence': technical.get('confidence', 50),
                'weight': self._get_dynamic_weight('technical', technical)
            }
            consensus_signals[tech_signal] += directional_signals['technical']['weight']
        
        # ML LSTM signals
        ml_lstm = sources.get('ml_lstm', {})
        if ml_lstm:
            predicted_change = ml_lstm.get('predicted_change', 0)
            if predicted_change > 2:
                lstm_signal = 'bullish'
            elif predicted_change < -2:
                lstm_signal = 'bearish'
            else:
                lstm_signal = 'neutral'
            
            directional_signals['ml_lstm'] = {
                'direction': lstm_signal,
                'confidence': ml_lstm.get('confidence', 50),
                'weight': self._get_dynamic_weight('ml_lstm', ml_lstm)
            }
            consensus_signals[lstm_signal] += directional_signals['ml_lstm']['weight']
        
        # ML Random Forest signals
        ml_rf = sources.get('ml_rf', {})
        if ml_rf:
            rf_direction = ml_rf.get('direction_label', 'UNKNOWN')
            if rf_direction == 'UP':
                rf_signal = 'bullish'
            elif rf_direction == 'DOWN':
                rf_signal = 'bearish'
            else:
                rf_signal = 'neutral'
            
            directional_signals['ml_rf'] = {
                'direction': rf_signal,
                'confidence': ml_rf.get('confidence', 50),
                'weight': self._get_dynamic_weight('ml_rf', ml_rf)
            }
            consensus_signals[rf_signal] += directional_signals['ml_rf']['weight']
        
        # Ensemble signals
        ensemble = sources.get('ensemble', {})
        if ensemble:
            pred_1mo = ensemble.get('pred_1mo', 0)
            if pred_1mo > 3:
                ensemble_signal = 'bullish'
            elif pred_1mo < -3:
                ensemble_signal = 'bearish'
            else:
                ensemble_signal = 'neutral'
            
            directional_signals['ensemble'] = {
                'direction': ensemble_signal,
                'confidence': ensemble.get('confidence', 50),
                'weight': self._get_dynamic_weight('ensemble', ensemble)
            }
            consensus_signals[ensemble_signal] += directional_signals['ensemble']['weight']
        
        # Detect conflicts
        unique_directions = set(sig['direction'] for sig in directional_signals.values())
        if len(unique_directions) > 2 or ('bullish' in unique_directions and 'bearish' in unique_directions):
            conflicts.append("Conflicting directional signals detected")
        
        # Determine consensus
        total_weight = sum(consensus_signals.values())
        if total_weight > 0:
            consensus_percentages = {k: (v/total_weight)*100 for k, v in consensus_signals.items()}
        else:
            consensus_percentages = {'bullish': 33, 'bearish': 33, 'neutral': 34}
        
        # Determine dominant consensus
        dominant_signal = max(consensus_percentages.items(), key=lambda x: x[1])
        consensus_strength = dominant_signal[1]
        
        if consensus_strength > 60:
            consensus_level = f"strong_{dominant_signal[0]}"
        elif consensus_strength > 45:
            consensus_level = f"weak_{dominant_signal[0]}"
        else:
            consensus_level = "mixed"
        
        return {
            'directional_signals': directional_signals,
            'conflicts': conflicts,
            'consensus_signals': consensus_signals,
            'consensus_percentages': consensus_percentages,
            'consensus_level': consensus_level,
            'consensus_strength': consensus_strength,
            'has_conflicts': len(conflicts) > 0
        }
    
    def _get_dynamic_weight(self, source_type: str, source_data: Dict) -> float:
        """
        Assign dynamic weights based on model confidence, historical accuracy, market context
        """
        base_weight = self.base_weights.get(source_type, 0.1)
        
        # Adjust based on confidence
        confidence = source_data.get('confidence', 50) / 100.0
        confidence_multiplier = 0.5 + (confidence * 1.0)  # 0.5 to 1.5 range
        
        # Adjust based on historical accuracy
        historical_accuracy = self.model_performance.get(source_type, {}).get('accuracy', 0.7)
        accuracy_multiplier = 0.5 + (historical_accuracy * 1.0)  # 0.5 to 1.5 range
        
        # Market context adjustments
        market_context_multiplier = self._get_market_context_multiplier(source_type)
        
        final_weight = base_weight * confidence_multiplier * accuracy_multiplier * market_context_multiplier
        return max(0.01, min(0.5, final_weight))  # Clamp between 1% and 50%
    
    def _get_market_context_multiplier(self, source_type: str) -> float:
        """
        Adjust weights based on market context (volatile/stable)
        """
        # For now, return 1.0 (neutral)
        # In a full implementation, this would analyze current market volatility
        # and adjust weights accordingly (e.g., technical analysis more reliable in stable markets)
        return 1.0
    
    def _assess_signal_quality_and_risk(self, aggregated_data: Dict, signal_analysis: Dict) -> Dict:
        """
        🧪 8. RISK & SIGNAL QUALITY ASSESSMENT
        """
        sources = aggregated_data.get('sources', {})
        
        # Assess volatility
        technical = sources.get('technical', {})
        volatility = technical.get('atr_volatility', 2.0)
        
        if volatility > 5:
            volatility_risk = 'high'
        elif volatility > 3:
            volatility_risk = 'medium'
        else:
            volatility_risk = 'low'
        
        # Assess momentum
        price_volume = sources.get('price_volume', {})
        momentum_5d = price_volume.get('momentum_5d', 0)
        
        if abs(momentum_5d) > 10:
            momentum_strength = 'strong'
        elif abs(momentum_5d) > 5:
            momentum_strength = 'medium'
        else:
            momentum_strength = 'weak'
        
        # Assess trend strength
        trend_strength = technical.get('trend_strength', 50)
        if trend_strength > 75:
            trend_quality = 'strong'
        elif trend_strength > 50:
            trend_quality = 'medium'
        else:
            trend_quality = 'weak'
        
        # Volume spikes
        volume_spike = price_volume.get('volume_spike', False)
        
        # Overall signal quality
        quality_factors = []
        quality_score = 0
        
        # Check for sufficient data
        source_count = len([s for s in sources.values() if s])
        if source_count >= 4:
            quality_score += 25
            quality_factors.append("Multiple data sources available")
        elif source_count >= 2:
            quality_score += 15
            quality_factors.append("Limited data sources")
        else:
            quality_factors.append("Insufficient data sources")
        
        # Check for consensus
        if signal_analysis.get('consensus_strength', 0) > 60:
            quality_score += 30
            quality_factors.append("Strong signal consensus")
        elif signal_analysis.get('consensus_strength', 0) > 45:
            quality_score += 20
            quality_factors.append("Moderate signal consensus")
        else:
            quality_factors.append("Weak signal consensus")
        
        # Check for conflicts
        if not signal_analysis.get('has_conflicts', True):
            quality_score += 20
            quality_factors.append("No conflicting signals")
        else:
            quality_factors.append("Conflicting signals present")
        
        # Volume confirmation
        if volume_spike:
            quality_score += 15
            quality_factors.append("Volume spike confirms move")
        
        # Technical confirmation
        if trend_quality == 'strong':
            quality_score += 10
            quality_factors.append("Strong trend confirmation")
        
        # Risk assessment
        risk_factors = []
        risk_score = 0
        
        if volatility_risk == 'high':
            risk_score += 30
            risk_factors.append("High volatility increases risk")
        elif volatility_risk == 'medium':
            risk_score += 15
            risk_factors.append("Moderate volatility")
        
        # Fundamental risks
        fundamentals = sources.get('fundamentals', {})
        pe_ratio = fundamentals.get('pe_ratio', 20)
        if pe_ratio > 30:
            risk_score += 20
            risk_factors.append("High valuation (PE > 30)")
        elif pe_ratio < 8:
            risk_score += 15
            risk_factors.append("Very low PE may indicate issues")
        
        debt_equity = fundamentals.get('debt_to_equity', 0.5)
        if debt_equity > 1.0:
            risk_score += 15
            risk_factors.append("High debt levels")
        
        # Overall assessments
        if quality_score >= 70:
            overall_quality = 'high'
        elif quality_score >= 40:
            overall_quality = 'medium'
        else:
            overall_quality = 'low'
        
        if risk_score >= 50:
            overall_risk = 'high'
        elif risk_score >= 25:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        return {
            'signal_quality': {
                'score': quality_score,
                'level': overall_quality,
                'factors': quality_factors
            },
            'risk_assessment': {
                'score': risk_score,
                'level': overall_risk,
                'factors': risk_factors,
                'volatility': volatility_risk,
                'momentum_strength': momentum_strength,
                'trend_quality': trend_quality
            },
            'filter_recommendation': overall_quality != 'low' and overall_risk != 'high'
        }
    
    def _make_final_decision(self, symbol: str, aggregated_data: Dict, 
                           signal_analysis: Dict, quality_assessment: Dict) -> Dict:
        """
        🎯 3. SCORING & FINAL DECISION MAKING
        """
        # Calculate weighted score
        consensus_strength = signal_analysis.get('consensus_strength', 50)
        quality_score = quality_assessment.get('signal_quality', {}).get('score', 50)
        risk_score = quality_assessment.get('risk_assessment', {}).get('score', 25)
        
        # Weighted decision score
        decision_score = (
            consensus_strength * 0.4 +
            quality_score * 0.3 +
            (100 - risk_score) * 0.3  # Invert risk score
        )
        
        # Generate final recommendation
        consensus_level = signal_analysis.get('consensus_level', 'mixed')
        risk_level = quality_assessment.get('risk_assessment', {}).get('level', 'medium')
        
        if decision_score >= 75 and risk_level != 'high':
            if 'strong_bullish' in consensus_level:
                action = '🔼 STRONG_BUY'
                confidence = min(95, decision_score)
            else:
                action = '🔼 BUY'
                confidence = min(85, decision_score)
        elif decision_score >= 60 and risk_level in ['low', 'medium']:
            action = '🔼 BUY'
            confidence = min(80, decision_score)
        elif decision_score >= 45:
            action = '⏸️ HOLD'
            confidence = min(70, decision_score)
        elif decision_score >= 30:
            action = '🔽 WEAK_SELL'
            confidence = min(65, decision_score)
        else:
            action = '🔽 STRONG_SELL'
            confidence = min(60, decision_score)
        
        # Generate target prices
        current_price = aggregated_data.get('sources', {}).get('technical', {}).get('current_price', 0)
        
        if current_price > 0:
            expected_return = (decision_score - 50) / 200  # -25% to +25% range
            target_price = current_price * (1 + expected_return)
            
            # Time-based predictions
            pred_24h = expected_return * 0.05 * 100  # 5% of expected return in 24h
            pred_5d = expected_return * 0.25 * 100   # 25% of expected return in 5d
            pred_1mo = expected_return * 100         # Full expected return in 1mo
        else:
            target_price = 0
            pred_24h = pred_5d = pred_1mo = 0
        
        return {
            'action': action,
            'confidence': round(confidence, 1),
            'decision_score': round(decision_score, 1),
            'target_price': round(target_price, 2) if target_price > 0 else 0,
            'predictions': {
                'pred_24h': round(pred_24h, 2),
                'pred_5d': round(pred_5d, 2),
                'pred_1mo': round(pred_1mo, 2)
            },
            'risk_level': risk_level,
            'consensus_level': consensus_level
        }
    
    def _generate_explanation(self, symbol: str, decision: Dict, 
                            signal_analysis: Dict, quality_assessment: Dict) -> Dict:
        """
        💡 4. EXPLAINABLE AI (XAI)
        """
        explanation = {
            'decision_reasoning': [],
            'top_3_drivers': [],
            'contradictory_signals': [],
            'human_readable_summary': ""
        }
        
        # Main reasoning
        consensus_level = decision.get('consensus_level', 'mixed')
        confidence = decision.get('confidence', 50)
        risk_level = decision.get('risk_level', 'medium')
        
        if 'bullish' in consensus_level:
            explanation['decision_reasoning'].append(
                f"Multiple prediction models show {consensus_level.replace('_', ' ')} consensus"
            )
        elif 'bearish' in consensus_level:
            explanation['decision_reasoning'].append(
                f"Multiple prediction models show {consensus_level.replace('_', ' ')} consensus"
            )
        else:
            explanation['decision_reasoning'].append(
                "Mixed signals from prediction models require caution"
            )
        
        explanation['decision_reasoning'].append(f"Signal quality: {quality_assessment.get('signal_quality', {}).get('level', 'medium')}")
        explanation['decision_reasoning'].append(f"Risk assessment: {risk_level}")
        explanation['decision_reasoning'].append(f"Overall confidence: {confidence}%")
        
        # Top 3 drivers
        directional_signals = signal_analysis.get('directional_signals', {})
        
        # Sort signals by weight
        sorted_signals = sorted(
            directional_signals.items(),
            key=lambda x: x[1].get('weight', 0),
            reverse=True
        )[:3]
        
        for source, signal_data in sorted_signals:
            driver_text = f"{source.upper()}: {signal_data.get('direction', 'unknown')} signal (confidence: {signal_data.get('confidence', 0):.1f}%)"
            explanation['top_3_drivers'].append(driver_text)
        
        # Contradictory signals
        conflicts = signal_analysis.get('conflicts', [])
        if conflicts:
            explanation['contradictory_signals'] = conflicts
            
            # Find specific contradictions
            bullish_sources = []
            bearish_sources = []
            
            for source, signal_data in directional_signals.items():
                direction = signal_data.get('direction', 'neutral')
                if direction == 'bullish':
                    bullish_sources.append(source)
                elif direction == 'bearish':
                    bearish_sources.append(source)
            
            if bullish_sources and bearish_sources:
                explanation['contradictory_signals'].append(
                    f"Bullish signals from: {', '.join(bullish_sources)}"
                )
                explanation['contradictory_signals'].append(
                    f"Bearish signals from: {', '.join(bearish_sources)}"
                )
        
        # Human-readable summary
        action = decision.get('action', 'HOLD').replace('🔼 ', '').replace('🔽 ', '').replace('⏸️ ', '')
        
        if 'STRONG_BUY' in action:
            summary = f"Strong buy recommendation for {symbol}. "
        elif 'BUY' in action:
            summary = f"Buy recommendation for {symbol}. "
        elif 'HOLD' in action:
            summary = f"Hold recommendation for {symbol}. "
        elif 'SELL' in action:
            summary = f"Sell recommendation for {symbol}. "
        else:
            summary = f"Neutral stance on {symbol}. "
        
        if explanation['contradictory_signals']:
            summary += "Despite some conflicting indicators, "
        
        if len(explanation['top_3_drivers']) > 0:
            primary_driver = explanation['top_3_drivers'][0].split(':')[0]
            summary += f"the {primary_driver} analysis provides the strongest signal. "
        
        summary += f"Confidence level is {confidence}% with {risk_level} risk."
        
        explanation['human_readable_summary'] = summary
        
        return explanation
    
    def _apply_time_based_management(self, symbol: str, decision: Dict) -> Dict:
        """
        ⌛ 6. TIME-BASED DECISION MANAGEMENT
        """
        try:
            # Load locked predictions
            locked_predictions = self._load_locked_predictions()
            
            current_time = datetime.now()
            decision_copy = decision.copy()
            
            # Check if prediction is locked
            if symbol in locked_predictions:
                locked_data = locked_predictions[symbol]
                lock_time = datetime.fromisoformat(locked_data['lock_time'])
                lock_duration = locked_data.get('lock_duration_hours', 24)
                
                # Check if lock is still valid
                if (current_time - lock_time).total_seconds() < lock_duration * 3600:
                    # Use locked prediction
                    decision_copy.update(locked_data['decision'])
                    decision_copy['is_locked'] = True
                    decision_copy['lock_expires'] = (lock_time + timedelta(hours=lock_duration)).isoformat()
                    return decision_copy
                else:
                    # Lock expired, remove from locked predictions
                    del locked_predictions[symbol]
                    self._save_locked_predictions(locked_predictions)
            
            # Check if new prediction differs significantly from previous
            previous_decision = self._get_previous_decision(symbol)
            if previous_decision:
                current_confidence = decision.get('confidence', 0)
                previous_confidence = previous_decision.get('confidence', 0)
                
                confidence_change = abs(current_confidence - previous_confidence)
                
                # If change is significant, lock the new prediction
                if confidence_change > self.stability_threshold:
                    # Determine lock duration based on confidence
                    if current_confidence >= 80:
                        lock_hours = self.lock_duration_hours['30d']  # 30 days for high confidence
                    elif current_confidence >= 65:
                        lock_hours = self.lock_duration_hours['5d']   # 5 days for medium confidence
                    else:
                        lock_hours = self.lock_duration_hours['24h']  # 24 hours for low confidence
                    
                    # Lock the prediction
                    locked_predictions[symbol] = {
                        'decision': decision_copy,
                        'lock_time': current_time.isoformat(),
                        'lock_duration_hours': lock_hours,
                        'reason': f'Significant change detected: {confidence_change:.1f}% confidence change'
                    }
                    
                    self._save_locked_predictions(locked_predictions)
                    
                    decision_copy['is_locked'] = True
                    decision_copy['lock_expires'] = (current_time + timedelta(hours=lock_hours)).isoformat()
                    decision_copy['lock_reason'] = locked_predictions[symbol]['reason']
            
            return decision_copy
            
        except Exception as e:
            logger.error(f"Error in time-based decision management: {str(e)}")
            decision['is_locked'] = False
            return decision
    
    def _apply_performance_awareness(self, decision: Dict, signal_analysis: Dict) -> Dict:
        """
        📊 7. HISTORICAL PERFORMANCE AWARENESS
        """
        try:
            # Evaluate recent performance of each model
            directional_signals = signal_analysis.get('directional_signals', {})
            
            performance_adjustments = {}
            for source, signal_data in directional_signals.items():
                performance = self.model_performance.get(source, {})
                
                win_rate = performance.get('win_rate', 0.5)
                recent_accuracy = performance.get('recent_accuracy', 0.5)
                
                # Adjust weight based on performance
                if win_rate > 0.7 and recent_accuracy > 0.7:
                    adjustment = 1.2  # Boost performing models
                    performance_adjustments[source] = 'boosted'
                elif win_rate < 0.4 or recent_accuracy < 0.4:
                    adjustment = 0.8  # Reduce underperforming models
                    performance_adjustments[source] = 'reduced'
                else:
                    adjustment = 1.0  # No change
                    performance_adjustments[source] = 'neutral'
                
                # Apply adjustment to signal weight
                original_weight = signal_data.get('weight', 0.1)
                signal_data['adjusted_weight'] = original_weight * adjustment
                signal_data['performance_adjustment'] = adjustment
            
            # Recalculate confidence based on performance adjustments
            original_confidence = decision.get('confidence', 50)
            
            # Calculate weighted average of adjustments
            total_weight = sum(sig.get('weight', 0.1) for sig in directional_signals.values())
            if total_weight > 0:
                weighted_adjustment = sum(
                    sig.get('performance_adjustment', 1.0) * sig.get('weight', 0.1)
                    for sig in directional_signals.values()
                ) / total_weight
                
                adjusted_confidence = original_confidence * weighted_adjustment
                decision['confidence'] = round(max(30, min(95, adjusted_confidence)), 1)
                decision['performance_adjustment'] = round(weighted_adjustment, 2)
                decision['performance_adjustments'] = performance_adjustments
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in performance awareness: {str(e)}")
            return decision
    
    def _monitor_prediction_stability(self, symbol: str, decision: Dict) -> Dict:
        """
        📈 5. PREDICTION STABILITY MONITORING
        """
        try:
            # Get previous predictions for this symbol
            history = self._get_prediction_history(symbol, days=7)  # Last 7 days
            
            if len(history) < 2:
                decision['stability'] = {
                    'is_stable': True,
                    'stability_score': 100,
                    'reason': 'Insufficient history for stability analysis'
                }
                return decision
            
            # Calculate stability metrics
            confidences = [h.get('confidence', 50) for h in history]
            recent_confidence = decision.get('confidence', 50)
            
            # Add current to history for analysis
            confidences.append(recent_confidence)
            
            # Calculate confidence stability
            confidence_std = np.std(confidences)
            confidence_mean = np.mean(confidences)
            
            # Calculate CV (coefficient of variation)
            cv = (confidence_std / confidence_mean) * 100 if confidence_mean > 0 else 100
            
            # Determine stability
            if cv < 10:  # Less than 10% variation
                stability_level = 'very_stable'
                stability_score = 95
            elif cv < 20:  # Less than 20% variation
                stability_level = 'stable'
                stability_score = 80
            elif cv < 30:  # Less than 30% variation
                stability_level = 'moderately_stable'
                stability_score = 65
            else:
                stability_level = 'unstable'
                stability_score = 40
            
            # Check for significant change from last prediction
            if len(history) > 0:
                last_confidence = history[-1].get('confidence', 50)
                confidence_change = abs(recent_confidence - last_confidence)
                
                if confidence_change > 15:  # More than 15% change
                    stability_level = 'significant_change'
                    stability_score = max(30, stability_score - 20)
            
            decision['stability'] = {
                'is_stable': stability_score >= 60,
                'stability_score': stability_score,
                'stability_level': stability_level,
                'confidence_cv': round(cv, 2),
                'confidence_std': round(confidence_std, 2),
                'history_count': len(history)
            }
            
            # If unstable, flag for review
            if stability_score < 60:
                decision['requires_review'] = True
                decision['review_reason'] = f'Unstable predictions: {stability_level}'
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in stability monitoring: {str(e)}")
            decision['stability'] = {
                'is_stable': False,
                'stability_score': 50,
                'reason': f'Error in stability analysis: {str(e)}'
            }
            return decision
    
    def _intelligent_signal_confirmation(self, aggregated_data: Dict, signal_analysis: Dict) -> bool:
        """
        🧠 9. INTELLIGENT FILTERING & SIGNAL CONFIRMATION
        """
        # Confirm buy/sell signals only if multiple criteria are met
        consensus_strength = signal_analysis.get('consensus_strength', 0)
        has_conflicts = signal_analysis.get('has_conflicts', True)
        
        sources = aggregated_data.get('sources', {})
        technical = sources.get('technical', {})
        
        # Basic confirmation criteria
        criteria_met = 0
        total_criteria = 5
        
        # 1. Strong consensus (>60%)
        if consensus_strength > 60:
            criteria_met += 1
        
        # 2. No major conflicts
        if not has_conflicts:
            criteria_met += 1
        
        # 3. Volume confirmation
        volume_ratio = technical.get('volume_ratio', 1.0)
        if volume_ratio > 1.2:  # Above average volume
            criteria_met += 1
        
        # 4. Technical trend confirmation
        trend_strength = technical.get('trend_strength', 50)
        if trend_strength > 60:
            criteria_met += 1
        
        # 5. Reasonable volatility
        volatility = technical.get('atr_volatility', 2.0)
        if volatility < 4.0:  # Not too volatile
            criteria_met += 1
        
        # Require at least 3 out of 5 criteria
        confirmation_score = (criteria_met / total_criteria) * 100
        return confirmation_score >= 60
    
    def _load_locked_predictions(self) -> Dict:
        """Load locked predictions from file"""
        try:
            with open(self.locked_predictions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Error loading locked predictions: {str(e)}")
            return {}
    
    def _save_locked_predictions(self, locked_predictions: Dict):
        """Save locked predictions to file"""
        try:
            with open(self.locked_predictions_file, 'w') as f:
                json.dump(locked_predictions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving locked predictions: {str(e)}")
    
    def _get_previous_decision(self, symbol: str) -> Optional[Dict]:
        """Get the most recent decision for a symbol"""
        try:
            with open(self.agent_history_file, 'r') as f:
                history = json.load(f)
            
            # Find most recent decision for this symbol
            symbol_decisions = [d for d in history if d.get('symbol') == symbol]
            if symbol_decisions:
                return symbol_decisions[-1]
            return None
        except:
            return None
    
    def _get_prediction_history(self, symbol: str, days: int = 7) -> List[Dict]:
        """Get prediction history for a symbol over specified days"""
        try:
            with open(self.agent_history_file, 'r') as f:
                history = json.load(f)
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter for symbol and recent history
            recent_history = []
            for decision in history:
                if decision.get('symbol') == symbol:
                    try:
                        decision_time = datetime.fromisoformat(decision.get('timestamp', ''))
                        if decision_time >= cutoff_date:
                            recent_history.append(decision)
                    except:
                        continue
            
            return recent_history
        except:
            return []
    
    def load_performance_history(self):
        """Load model performance history"""
        try:
            with open(self.performance_history_file, 'r') as f:
                self.model_performance = json.load(f)
        except FileNotFoundError:
            # Initialize with default performance metrics
            self.model_performance = {
                'technical': {'win_rate': 0.6, 'recent_accuracy': 0.65, 'total_predictions': 0},
                'ml_lstm': {'win_rate': 0.55, 'recent_accuracy': 0.58, 'total_predictions': 0},
                'ml_rf': {'win_rate': 0.52, 'recent_accuracy': 0.55, 'total_predictions': 0},
                'ensemble': {'win_rate': 0.58, 'recent_accuracy': 0.62, 'total_predictions': 0}
            }
        except Exception as e:
            logger.error(f"Error loading performance history: {str(e)}")
            self.model_performance = {}
    
    def update_performance_metrics(self, symbol: str, prediction_results: Dict):
        """Update performance metrics based on actual outcomes"""
        try:
            # This would be called when we have actual price data to compare against predictions
            # For now, simulate performance updates
            for source in ['technical', 'ml_lstm', 'ml_rf', 'ensemble']:
                if source in self.model_performance:
                    current_total = self.model_performance[source]['total_predictions']
                    self.model_performance[source]['total_predictions'] = current_total + 1
            
            # Save updated performance
            with open(self.performance_history_file, 'w') as f:
                json.dump(self.model_performance, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")
    
    def _log_agent_decision(self, symbol: str, decision: Dict):
        """Log agent decisions for learning and audit trail"""
        try:
            # Load existing history
            try:
                with open(self.agent_history_file, 'r') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []
            
            # Create decision record
            decision_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': decision.get('action', 'HOLD'),
                'confidence': decision.get('confidence', 50),
                'decision_score': decision.get('decision_score', 50),
                'risk_level': decision.get('risk_level', 'medium'),
                'consensus_level': decision.get('consensus_level', 'mixed'),
                'is_locked': decision.get('is_locked', False),
                'stability_score': decision.get('stability', {}).get('stability_score', 50),
                'explanation_summary': decision.get('explanation', {}).get('human_readable_summary', ''),
                'agent_version': decision.get('agent_version', '2.0')
            }
            
            history.append(decision_record)
            
            # Keep only last 2000 decisions (manage file size)
            history = history[-2000:]
            
            # Save updated history
            with open(self.agent_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging agent decision: {str(e)}")
    
    def _get_fallback_decision(self, symbol: str) -> Dict:
        """Fallback decision when analysis fails"""
        return {
            'action': '⏸️ HOLD',
            'confidence': 30,
            'decision_score': 30,
            'target_price': 0,
            'predictions': {'pred_24h': 0, 'pred_5d': 0, 'pred_1mo': 0},
            'risk_level': 'HIGH',
            'consensus_level': 'unknown',
            'explanation': {
                'decision_reasoning': ['Analysis failed - insufficient data'],
                'top_3_drivers': ['Error in data processing'],
                'contradictory_signals': [],
                'human_readable_summary': f'Unable to analyze {symbol} due to technical issues. Recommend manual review.'
            },
            'is_locked': False,
            'stability': {'is_stable': False, 'stability_score': 0, 'reason': 'Analysis failed'},
            'requires_review': True,
            'review_reason': 'Analysis system error',
            'agent_version': '2.0'
        }

# Integration function for stock screener
def get_enhanced_agent_analysis(symbol: str, all_predictions: Dict) -> Dict:
    """Get enhanced AI agent analysis for a stock"""
    agent = SmartStockAgent()
    return agent.analyze_and_consolidate(symbol, all_predictions)

# Backward compatibility
def get_agent_analysis(symbol: str, all_predictions: Dict) -> Dict:
    """Backward compatibility function"""
    return get_enhanced_agent_analysis(symbol, all_predictions)

if __name__ == "__main__":
    # Test the enhanced agent
    test_predictions = {
        'technical': {'rsi_14': 45, 'macd_bullish': True, 'bb_position': 60, 'current_price': 100, 'trend_strength': 70, 'volume_ratio_10': 1.3, 'atr_volatility': 2.1},
        'ml_lstm': {'predicted_change': 3.5, 'confidence': 75, 'direction': 'UP'},
        'ml_rf': {'direction_label': 'UP', 'confidence': 0.8},
        'ensemble': {'pred_1mo': 5.2, 'confidence': 70, 'pred_24h': 0.5, 'pred_5d': 2.1},
        'fundamentals': {'pe_ratio': 18, 'debt_to_equity': 0.4, 'revenue_growth': 8.5, 'earnings_growth': 6.2},
        'sentiment': {'bulk_deal_bonus': 5, 'news_score': 2, 'social_score': 1}
    }
    
    agent = SmartStockAgent()
    result = agent.analyze_and_consolidate('RELIANCE', test_predictions)
    
    print("🤖 SmartStockAgent Analysis:")
    print(f"Recommendation: {result.get('action', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 'N/A')}%")
    print(f"Explanation: {result.get('explanation', {}).get('human_readable_summary', 'N/A')}")
    print(f"Risk Level: {result.get('risk_level', 'N/A')}")
    print(f"Stability Score: {result.get('stability', {}).get('stability_score', 'N/A')}")
