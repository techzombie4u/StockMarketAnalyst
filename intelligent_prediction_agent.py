
"""
Intelligent Prediction Agent for Stock Market Analyst

Acts as an expert stock analyst that evaluates multiple prediction sources,
analyzes their reliability, and provides consolidated, unbiased recommendations.
"""

import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics

logger = logging.getLogger(__name__)

class IntelligentPredictionAgent:
    def __init__(self):
        self.agent_history_file = 'agent_decisions.json'
        self.confidence_weights = {
            'technical': 0.25,
            'ml_lstm': 0.20,
            'ml_rf': 0.20,
            'ensemble': 0.20,
            'sentiment': 0.15
        }
        
        # Agent personality traits
        self.risk_tolerance = 'moderate'  # conservative, moderate, aggressive
        self.market_experience = 'expert'
        self.analysis_style = 'comprehensive'
        
    def analyze_and_consolidate(self, symbol: str, all_predictions: Dict) -> Dict:
        """
        Main function: Analyze all prediction sources and provide expert recommendation
        """
        try:
            logger.info(f"🤖 AI Agent analyzing {symbol}...")
            
            # Extract individual predictions
            technical_pred = all_predictions.get('technical', {})
            ml_lstm_pred = all_predictions.get('ml_lstm', {})
            ml_rf_pred = all_predictions.get('ml_rf', {})
            ensemble_pred = all_predictions.get('ensemble', {})
            sentiment_data = all_predictions.get('sentiment', {})
            fundamentals = all_predictions.get('fundamentals', {})
            market_context = all_predictions.get('market_context', {})
            
            # Step 1: Evaluate prediction reliability
            reliability_scores = self._evaluate_prediction_reliability(
                technical_pred, ml_lstm_pred, ml_rf_pred, ensemble_pred
            )
            
            # Step 2: Analyze prediction consensus
            consensus_analysis = self._analyze_prediction_consensus(
                technical_pred, ml_lstm_pred, ml_rf_pred, ensemble_pred
            )
            
            # Step 3: Risk assessment
            risk_assessment = self._assess_investment_risk(
                symbol, fundamentals, technical_pred, market_context
            )
            
            # Step 4: Market timing analysis
            timing_analysis = self._analyze_market_timing(
                technical_pred, sentiment_data, market_context
            )
            
            # Step 5: Generate expert decision
            expert_decision = self._generate_expert_decision(
                symbol, reliability_scores, consensus_analysis, 
                risk_assessment, timing_analysis, all_predictions
            )
            
            # Step 6: Calculate final confidence
            final_confidence = self._calculate_agent_confidence(
                reliability_scores, consensus_analysis, risk_assessment
            )
            
            # Log decision for learning
            self._log_agent_decision(symbol, expert_decision, all_predictions)
            
            return {
                'agent_recommendation': expert_decision['action'],
                'agent_confidence': final_confidence,
                'target_price_24h': expert_decision.get('target_24h', 0),
                'target_price_5d': expert_decision.get('target_5d', 0),
                'target_price_1mo': expert_decision.get('target_1mo', 0),
                'reasoning': expert_decision['reasoning'],
                'risk_level': risk_assessment['level'],
                'timing_score': timing_analysis['score'],
                'prediction_consensus': consensus_analysis['consensus_level'],
                'reliability_breakdown': reliability_scores,
                'agent_notes': expert_decision.get('notes', []),
                'stop_loss_suggestion': expert_decision.get('stop_loss', 0),
                'take_profit_suggestion': expert_decision.get('take_profit', 0)
            }
            
        except Exception as e:
            logger.error(f"Error in AI agent analysis for {symbol}: {str(e)}")
            return self._get_fallback_decision()
    
    def _evaluate_prediction_reliability(self, technical: Dict, lstm: Dict, 
                                       rf: Dict, ensemble: Dict) -> Dict:
        """Evaluate how reliable each prediction source is"""
        reliability = {}
        
        # Technical analysis reliability
        tech_indicators_count = len([k for k in technical.keys() if k in 
                                   ['rsi_14', 'macd_signal', 'bb_position', 'trend_strength']])
        reliability['technical'] = min(100, (tech_indicators_count / 4) * 100)
        
        # LSTM reliability (based on confidence if available)
        lstm_confidence = lstm.get('confidence', 50)
        reliability['ml_lstm'] = lstm_confidence
        
        # Random Forest reliability
        rf_confidence = rf.get('confidence', 50) * 100 if rf.get('confidence') else 50
        reliability['ml_rf'] = rf_confidence
        
        # Ensemble reliability (average of components)
        ensemble_confidence = ensemble.get('confidence', 50)
        reliability['ensemble'] = ensemble_confidence
        
        return reliability
    
    def _analyze_prediction_consensus(self, technical: Dict, lstm: Dict, 
                                    rf: Dict, ensemble: Dict) -> Dict:
        """Analyze how much the predictions agree with each other"""
        
        # Collect directional predictions
        directions = []
        
        # Technical direction
        rsi = technical.get('rsi_14', 50)
        if rsi < 30:
            directions.append('bullish')
        elif rsi > 70:
            directions.append('bearish')
        else:
            directions.append('neutral')
        
        # LSTM direction
        lstm_change = lstm.get('predicted_change', 0)
        if lstm_change > 2:
            directions.append('bullish')
        elif lstm_change < -2:
            directions.append('bearish')
        else:
            directions.append('neutral')
        
        # Random Forest direction
        rf_direction = rf.get('direction_label', 'UNKNOWN')
        if rf_direction == 'UP':
            directions.append('bullish')
        elif rf_direction == 'DOWN':
            directions.append('bearish')
        else:
            directions.append('neutral')
        
        # Ensemble direction
        ensemble_1mo = ensemble.get('pred_1mo', 0)
        if ensemble_1mo > 3:
            directions.append('bullish')
        elif ensemble_1mo < -3:
            directions.append('bearish')
        else:
            directions.append('neutral')
        
        # Calculate consensus
        bullish_count = directions.count('bullish')
        bearish_count = directions.count('bearish')
        neutral_count = directions.count('neutral')
        total_predictions = len(directions)
        
        if bullish_count >= total_predictions * 0.7:
            consensus = 'strong_bullish'
            consensus_score = 90
        elif bearish_count >= total_predictions * 0.7:
            consensus = 'strong_bearish'
            consensus_score = 90
        elif bullish_count > bearish_count:
            consensus = 'weak_bullish'
            consensus_score = 60
        elif bearish_count > bullish_count:
            consensus = 'weak_bearish'
            consensus_score = 60
        else:
            consensus = 'mixed'
            consensus_score = 30
        
        return {
            'consensus_level': consensus,
            'consensus_score': consensus_score,
            'direction_breakdown': {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'neutral': neutral_count
            }
        }
    
    def _assess_investment_risk(self, symbol: str, fundamentals: Dict, 
                              technical: Dict, market_context: Dict) -> Dict:
        """Assess overall investment risk like an expert analyst"""
        
        risk_factors = []
        risk_score = 0
        
        # Fundamental risks
        pe_ratio = fundamentals.get('pe_ratio', 20)
        if pe_ratio > 30:
            risk_factors.append('High PE ratio indicates overvaluation')
            risk_score += 20
        elif pe_ratio < 8:
            risk_factors.append('Very low PE may indicate underlying issues')
            risk_score += 15
        
        debt_to_equity = fundamentals.get('debt_to_equity', 0.5)
        if debt_to_equity > 1.0:
            risk_factors.append('High debt levels')
            risk_score += 25
        
        # Technical risks
        volatility = technical.get('atr_volatility', 2)
        if volatility > 4:
            risk_factors.append('High volatility increases risk')
            risk_score += 20
        
        rsi = technical.get('rsi_14', 50)
        if rsi > 80:
            risk_factors.append('Extremely overbought conditions')
            risk_score += 15
        
        # Market context risks
        market_trend = market_context.get('trend', 'neutral')
        if market_trend == 'bearish':
            risk_factors.append('Overall market bearishness')
            risk_score += 20
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = 'HIGH'
        elif risk_score >= 30:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'level': risk_level,
            'score': risk_score,
            'factors': risk_factors,
            'recommendation': self._get_risk_recommendation(risk_level, risk_score)
        }
    
    def _analyze_market_timing(self, technical: Dict, sentiment: Dict, 
                             market_context: Dict) -> Dict:
        """Analyze if it's a good time to enter the market"""
        
        timing_score = 50  # Base score
        timing_notes = []
        
        # Technical timing indicators
        rsi = technical.get('rsi_14', 50)
        if 30 <= rsi <= 70:
            timing_score += 10
            timing_notes.append('RSI in healthy range')
        
        macd_histogram = technical.get('macd_histogram', 0)
        if macd_histogram > 0:
            timing_score += 15
            timing_notes.append('MACD showing positive momentum')
        
        bb_position = technical.get('bb_position', 50)
        if 20 <= bb_position <= 80:
            timing_score += 10
            timing_notes.append('Price in normal Bollinger Band range')
        
        # Volume analysis
        volume_ratio = technical.get('volume_sma_ratio', 1)
        if volume_ratio > 1.2:
            timing_score += 5
            timing_notes.append('Above average volume supports move')
        
        # Sentiment timing
        bulk_deal_bonus = sentiment.get('bulk_deal_bonus', 0)
        if bulk_deal_bonus > 0:
            timing_score += 10
            timing_notes.append('Recent bulk deal activity')
        
        # Market context
        market_volatility = market_context.get('volatility', 'normal')
        if market_volatility == 'low':
            timing_score += 10
            timing_notes.append('Low market volatility favorable')
        elif market_volatility == 'high':
            timing_score -= 15
            timing_notes.append('High market volatility increases risk')
        
        timing_score = max(0, min(100, timing_score))
        
        return {
            'score': timing_score,
            'notes': timing_notes,
            'recommendation': self._get_timing_recommendation(timing_score)
        }
    
    def _generate_expert_decision(self, symbol: str, reliability: Dict, 
                                consensus: Dict, risk: Dict, timing: Dict,
                                all_predictions: Dict) -> Dict:
        """Generate final expert decision like a seasoned stock analyst"""
        
        # Weighted decision matrix
        consensus_score = consensus['consensus_score']
        timing_score = timing['score']
        risk_score = 100 - risk['score']  # Invert risk (lower risk = higher score)
        avg_reliability = np.mean(list(reliability.values()))
        
        # Calculate decision score
        decision_score = (
            consensus_score * 0.35 +
            timing_score * 0.25 +
            risk_score * 0.25 +
            avg_reliability * 0.15
        )
        
        # Generate reasoning
        reasoning = []
        
        if consensus['consensus_level'] in ['strong_bullish', 'weak_bullish']:
            reasoning.append(f"Multiple prediction models show bullish consensus ({consensus['consensus_level']})")
        elif consensus['consensus_level'] in ['strong_bearish', 'weak_bearish']:
            reasoning.append(f"Multiple prediction models show bearish consensus ({consensus['consensus_level']})")
        else:
            reasoning.append("Mixed signals from prediction models require caution")
        
        reasoning.append(f"Market timing score: {timing_score}/100")
        reasoning.append(f"Risk assessment: {risk['level']} ({100-risk['score']}/100)")
        reasoning.append(f"Prediction reliability: {avg_reliability:.1f}/100")
        
        # Make decision
        if decision_score >= 75 and risk['level'] != 'HIGH':
            action = 'STRONG_BUY'
            notes = ['High confidence recommendation', 'Multiple positive signals align']
        elif decision_score >= 60 and risk['level'] in ['LOW', 'MEDIUM']:
            action = 'BUY'
            notes = ['Moderate confidence recommendation', 'Generally positive outlook']
        elif decision_score >= 45:
            action = 'HOLD'
            notes = ['Mixed signals suggest waiting', 'Monitor for clearer direction']
        elif decision_score >= 30:
            action = 'WEAK_SELL'
            notes = ['Some negative indicators present', 'Consider reducing position']
        else:
            action = 'STRONG_SELL'
            notes = ['Multiple negative signals', 'High risk of losses']
        
        # Generate target prices
        current_price = all_predictions.get('current_price', 0)
        
        if action in ['STRONG_BUY', 'BUY']:
            target_24h = current_price * (1 + (decision_score - 50) / 1000)
            target_5d = current_price * (1 + (decision_score - 50) / 500)
            target_1mo = current_price * (1 + (decision_score - 50) / 250)
            stop_loss = current_price * 0.92  # 8% stop loss
            take_profit = current_price * 1.15  # 15% take profit
        else:
            target_24h = current_price * (1 + (decision_score - 50) / 1000)
            target_5d = current_price * (1 + (decision_score - 50) / 500)
            target_1mo = current_price * (1 + (decision_score - 50) / 250)
            stop_loss = current_price * 1.05  # 5% stop for shorts
            take_profit = current_price * 0.90  # 10% profit for shorts
        
        return {
            'action': action,
            'reasoning': reasoning,
            'decision_score': round(decision_score, 1),
            'target_24h': round(target_24h, 2) if current_price > 0 else 0,
            'target_5d': round(target_5d, 2) if current_price > 0 else 0,
            'target_1mo': round(target_1mo, 2) if current_price > 0 else 0,
            'stop_loss': round(stop_loss, 2) if current_price > 0 else 0,
            'take_profit': round(take_profit, 2) if current_price > 0 else 0,
            'notes': notes
        }
    
    def _calculate_agent_confidence(self, reliability: Dict, consensus: Dict, risk: Dict) -> float:
        """Calculate agent's confidence in its decision"""
        
        avg_reliability = np.mean(list(reliability.values()))
        consensus_score = consensus['consensus_score']
        risk_factor = 100 - risk['score']
        
        confidence = (avg_reliability * 0.4 + consensus_score * 0.4 + risk_factor * 0.2)
        return round(confidence, 1)
    
    def _log_agent_decision(self, symbol: str, decision: Dict, predictions: Dict):
        """Log agent decisions for learning and improvement"""
        try:
            # Load existing decisions
            try:
                with open(self.agent_history_file, 'r') as f:
                    history = json.load(f)
            except FileNotFoundError:
                history = []
            
            # Add new decision
            decision_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'action': decision['action'],
                'confidence': decision.get('decision_score', 0),
                'reasoning_count': len(decision.get('reasoning', [])),
                'risk_level': decision.get('risk_level', 'UNKNOWN'),
                'current_price': predictions.get('current_price', 0)
            }
            
            history.append(decision_record)
            
            # Keep only last 1000 decisions
            history = history[-1000:]
            
            # Save history
            with open(self.agent_history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging agent decision: {str(e)}")
    
    def _get_risk_recommendation(self, risk_level: str, risk_score: int) -> str:
        """Get risk-based recommendation"""
        if risk_level == 'HIGH':
            return 'Avoid or use very small position sizes'
        elif risk_level == 'MEDIUM':
            return 'Use moderate position sizing with tight stops'
        else:
            return 'Standard position sizing acceptable'
    
    def _get_timing_recommendation(self, timing_score: float) -> str:
        """Get timing-based recommendation"""
        if timing_score >= 70:
            return 'Excellent entry timing'
        elif timing_score >= 50:
            return 'Good entry timing'
        else:
            return 'Poor timing - consider waiting'
    
    def _get_fallback_decision(self) -> Dict:
        """Fallback decision when analysis fails"""
        return {
            'agent_recommendation': 'HOLD',
            'agent_confidence': 30,
            'target_price_24h': 0,
            'target_price_5d': 0,
            'target_price_1mo': 0,
            'reasoning': ['Analysis failed - insufficient data'],
            'risk_level': 'HIGH',
            'timing_score': 30,
            'prediction_consensus': 'unknown',
            'agent_notes': ['Error in analysis - recommend manual review']
        }

# Integration function for stock screener
def get_agent_analysis(symbol: str, all_predictions: Dict) -> Dict:
    """Get AI agent analysis for a stock"""
    agent = IntelligentPredictionAgent()
    return agent.analyze_and_consolidate(symbol, all_predictions)

def main():
    """Test the agent"""
    # Sample prediction data
    test_predictions = {
        'technical': {'rsi_14': 45, 'macd_histogram': 0.5, 'bb_position': 60},
        'ml_lstm': {'predicted_change': 3.5, 'confidence': 75},
        'ml_rf': {'direction_label': 'UP', 'confidence': 0.8},
        'ensemble': {'pred_1mo': 5.2, 'confidence': 70},
        'fundamentals': {'pe_ratio': 18, 'debt_to_equity': 0.4},
        'sentiment': {'bulk_deal_bonus': 5},
        'market_context': {'trend': 'neutral', 'volatility': 'normal'},
        'current_price': 100
    }
    
    agent = IntelligentPredictionAgent()
    result = agent.analyze_and_consolidate('RELIANCE', test_predictions)
    
    print("AI Agent Analysis:")
    print(f"Recommendation: {result['agent_recommendation']}")
    print(f"Confidence: {result['agent_confidence']}%")
    print(f"Reasoning: {result['reasoning']}")

if __name__ == "__main__":
    main()
