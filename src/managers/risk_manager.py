
"""
Risk Management Module for Stock Market Analyst

Implements position sizing, stop-loss/take-profit calculations,
and portfolio correlation analysis without external dependencies.
"""

import json
import logging
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self):
        self.portfolio_file = 'portfolio_risk.json'
        self.risk_settings = {
            'max_position_size': 0.05,  # 5% max per position
            'max_portfolio_risk': 0.20,  # 20% max portfolio risk
            'stop_loss_pct': 0.08,      # 8% stop loss
            'take_profit_pct': 0.15,    # 15% take profit
            'correlation_threshold': 0.7, # High correlation limit
            'volatility_adjustment': True
        }
        
    def calculate_position_size(self, stock_data: Dict, portfolio_value: float) -> Dict:
        """Calculate optimal position size based on risk parameters"""
        try:
            symbol = stock_data.get('symbol', 'UNKNOWN')
            current_price = stock_data.get('current_price', 0)
            volatility = stock_data.get('technical', {}).get('atr_volatility', 2.0)
            confidence = stock_data.get('confidence', 50) / 100
            
            if current_price <= 0:
                return self._get_zero_position()
            
            # Base position size (Kelly Criterion inspired)
            win_probability = confidence
            win_loss_ratio = stock_data.get('predicted_gain', 10) / 100 / self.risk_settings['stop_loss_pct']
            
            # Kelly percentage
            kelly_pct = (win_probability * win_loss_ratio - (1 - win_probability)) / win_loss_ratio
            kelly_pct = max(0, min(kelly_pct, self.risk_settings['max_position_size']))
            
            # Volatility adjustment
            if self.risk_settings['volatility_adjustment']:
                volatility_factor = min(1.0, 2.0 / volatility)  # Reduce size for high volatility
                kelly_pct *= volatility_factor
            
            # Calculate actual position
            position_value = portfolio_value * kelly_pct
            shares = int(position_value / current_price)
            actual_position_value = shares * current_price
            actual_position_pct = actual_position_value / portfolio_value if portfolio_value > 0 else 0
            
            return {
                'symbol': symbol,
                'recommended_shares': shares,
                'position_value': round(actual_position_value, 2),
                'position_percentage': round(actual_position_pct * 100, 2),
                'kelly_percentage': round(kelly_pct * 100, 2),
                'volatility_adjustment': round(volatility_factor if self.risk_settings['volatility_adjustment'] else 1.0, 3),
                'risk_score': self._calculate_position_risk_score(stock_data, actual_position_pct),
                'recommendation': self._get_position_recommendation(actual_position_pct, volatility)
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size for {symbol}: {str(e)}")
            return self._get_zero_position()
    
    def calculate_stop_loss_take_profit(self, stock_data: Dict) -> Dict:
        """Calculate stop-loss and take-profit levels"""
        try:
            symbol = stock_data.get('symbol', 'UNKNOWN')
            current_price = stock_data.get('current_price', 0)
            atr = stock_data.get('technical', {}).get('atr_14', current_price * 0.02)
            volatility = stock_data.get('technical', {}).get('atr_volatility', 2.0)
            predicted_gain = stock_data.get('predicted_gain', 10) / 100
            
            if current_price <= 0:
                return {'symbol': symbol, 'error': 'Invalid price data'}
            
            # Dynamic stop-loss based on volatility
            dynamic_stop_pct = max(self.risk_settings['stop_loss_pct'], atr / current_price * 2)
            stop_loss_price = current_price * (1 - dynamic_stop_pct)
            
            # Dynamic take-profit based on predicted gain
            take_profit_pct = max(self.risk_settings['take_profit_pct'], predicted_gain * 1.2)
            take_profit_price = current_price * (1 + take_profit_pct)
            
            # Support and resistance levels
            technical = stock_data.get('technical', {})
            bb_lower = technical.get('bb_lower', current_price * 0.95)
            bb_upper = technical.get('bb_upper', current_price * 1.05)
            
            # Adjust levels based on technical indicators
            support_stop_loss = max(stop_loss_price, bb_lower * 0.98)
            resistance_take_profit = min(take_profit_price, bb_upper * 1.02)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'stop_loss_price': round(support_stop_loss, 2),
                'stop_loss_pct': round((current_price - support_stop_loss) / current_price * 100, 2),
                'take_profit_price': round(resistance_take_profit, 2),
                'take_profit_pct': round((resistance_take_profit - current_price) / current_price * 100, 2),
                'risk_reward_ratio': round((resistance_take_profit - current_price) / (current_price - support_stop_loss), 2),
                'atr_based_stop': round(current_price - atr * 2, 2),
                'support_level': round(bb_lower, 2),
                'resistance_level': round(bb_upper, 2),
                'volatility_adjusted': volatility > 3.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating stop-loss/take-profit for {symbol}: {str(e)}")
            return {'symbol': symbol, 'error': str(e)}
    
    def analyze_portfolio_correlation(self, stocks_data: List[Dict]) -> Dict:
        """Analyze correlation between selected stocks"""
        try:
            if len(stocks_data) < 2:
                return {'correlation_analysis': 'Insufficient data for correlation analysis'}
            
            # Create correlation matrix based on technical indicators
            correlation_matrix = {}
            high_correlations = []
            
            for i, stock1 in enumerate(stocks_data):
                symbol1 = stock1.get('symbol', f'Stock{i}')
                correlation_matrix[symbol1] = {}
                
                for j, stock2 in enumerate(stocks_data):
                    symbol2 = stock2.get('symbol', f'Stock{j}')
                    
                    if i == j:
                        correlation_matrix[symbol1][symbol2] = 1.0
                    else:
                        # Calculate correlation based on multiple factors
                        correlation = self._calculate_stock_correlation(stock1, stock2)
                        correlation_matrix[symbol1][symbol2] = correlation
                        
                        if correlation > self.risk_settings['correlation_threshold'] and i < j:
                            high_correlations.append({
                                'stock1': symbol1,
                                'stock2': symbol2,
                                'correlation': round(correlation, 3),
                                'risk_level': 'High' if correlation > 0.8 else 'Medium'
                            })
            
            # Portfolio diversification score
            avg_correlation = self._calculate_average_correlation(correlation_matrix)
            diversification_score = max(0, 100 - (avg_correlation * 100))
            
            return {
                'correlation_matrix': correlation_matrix,
                'high_correlations': high_correlations,
                'average_correlation': round(avg_correlation, 3),
                'diversification_score': round(diversification_score, 1),
                'portfolio_risk_level': self._get_portfolio_risk_level(avg_correlation),
                'recommendations': self._get_diversification_recommendations(high_correlations, avg_correlation)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio correlation: {str(e)}")
            return {'error': str(e)}
    
    def assess_portfolio_risk(self, positions: List[Dict], market_conditions: Dict = None) -> Dict:
        """Comprehensive portfolio risk assessment"""
        try:
            total_portfolio_value = sum(pos.get('position_value', 0) for pos in positions)
            total_risk_exposure = 0
            concentration_risk = 0
            sector_exposure = {}
            
            # Calculate various risk metrics
            for position in positions:
                position_pct = position.get('position_percentage', 0) / 100
                risk_score = position.get('risk_score', 0)
                
                # Position risk contribution
                position_risk = position_pct * risk_score
                total_risk_exposure += position_risk
                
                # Concentration risk
                if position_pct > self.risk_settings['max_position_size']:
                    concentration_risk += position_pct - self.risk_settings['max_position_size']
                
                # Sector exposure (simplified)
                market_cap = position.get('market_cap', 'Unknown')
                sector_exposure[market_cap] = sector_exposure.get(market_cap, 0) + position_pct
            
            # Market condition adjustments
            market_risk_multiplier = 1.0
            if market_conditions:
                market_volatility = market_conditions.get('market_volatility', 'normal')
                if market_volatility == 'high':
                    market_risk_multiplier = 1.3
                elif market_volatility == 'low':
                    market_risk_multiplier = 0.8
            
            adjusted_risk = total_risk_exposure * market_risk_multiplier
            
            return {
                'total_portfolio_value': round(total_portfolio_value, 2),
                'total_risk_exposure': round(adjusted_risk, 3),
                'concentration_risk': round(concentration_risk * 100, 2),
                'sector_exposure': {k: round(v * 100, 2) for k, v in sector_exposure.items()},
                'risk_level': self._get_risk_level(adjusted_risk),
                'market_risk_multiplier': market_risk_multiplier,
                'risk_recommendations': self._get_risk_recommendations(adjusted_risk, concentration_risk),
                'max_drawdown_estimate': round(adjusted_risk * 100, 1),
                'risk_score': min(100, round(adjusted_risk * 100, 1))
            }
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_stock_correlation(self, stock1: Dict, stock2: Dict) -> float:
        """Calculate correlation between two stocks based on available data"""
        try:
            # Factors to compare
            factors = [
                ('pe_ratio', 'fundamentals'),
                ('revenue_growth', 'fundamentals'),
                ('rsi_14', 'technical'),
                ('atr_volatility', 'technical'),
                ('trend_strength', 'technical')
            ]
            
            correlations = []
            
            for factor, data_type in factors:
                val1 = stock1.get(data_type, {}).get(factor)
                val2 = stock2.get(data_type, {}).get(factor)
                
                if val1 is not None and val2 is not None:
                    # Normalize and calculate similarity
                    max_val = max(abs(val1), abs(val2))
                    if max_val > 0:
                        similarity = 1 - abs(val1 - val2) / max_val
                        correlations.append(similarity)
            
            # Market cap similarity
            market_cap1 = stock1.get('market_cap', 'Unknown')
            market_cap2 = stock2.get('market_cap', 'Unknown')
            if market_cap1 != 'Unknown' and market_cap2 != 'Unknown':
                cap_correlation = 0.8 if market_cap1 == market_cap2 else 0.3
                correlations.append(cap_correlation)
            
            return sum(correlations) / len(correlations) if correlations else 0.5
            
        except Exception as e:
            logger.error(f"Error calculating stock correlation: {str(e)}")
            return 0.5
    
    def _calculate_average_correlation(self, correlation_matrix: Dict) -> float:
        """Calculate average correlation across portfolio"""
        correlations = []
        symbols = list(correlation_matrix.keys())
        
        for i, symbol1 in enumerate(symbols):
            for j, symbol2 in enumerate(symbols):
                if i < j:  # Avoid duplicates and self-correlation
                    correlations.append(correlation_matrix[symbol1][symbol2])
        
        return sum(correlations) / len(correlations) if correlations else 0.0
    
    def _calculate_position_risk_score(self, stock_data: Dict, position_pct: float) -> float:
        """Calculate risk score for a position"""
        try:
            volatility = stock_data.get('technical', {}).get('atr_volatility', 2.0)
            confidence = stock_data.get('confidence', 50) / 100
            
            # Base risk from volatility and position size
            volatility_risk = min(1.0, volatility / 5.0)  # Normalize volatility
            size_risk = min(1.0, position_pct / self.risk_settings['max_position_size'])
            confidence_risk = 1 - confidence
            
            # Combined risk score
            risk_score = (volatility_risk * 0.4 + size_risk * 0.3 + confidence_risk * 0.3)
            return min(1.0, risk_score)
            
        except Exception as e:
            logger.error(f"Error calculating position risk score: {str(e)}")
            return 0.5
    
    def _get_zero_position(self) -> Dict:
        """Return zero position structure"""
        return {
            'recommended_shares': 0,
            'position_value': 0,
            'position_percentage': 0,
            'kelly_percentage': 0,
            'risk_score': 0,
            'recommendation': 'SKIP - Insufficient data'
        }
    
    def _get_position_recommendation(self, position_pct: float, volatility: float) -> str:
        """Get position sizing recommendation"""
        if position_pct == 0:
            return 'SKIP - No position recommended'
        elif position_pct > self.risk_settings['max_position_size']:
            return 'REDUCE - Position too large'
        elif volatility > 4.0:
            return 'CAUTION - High volatility'
        elif position_pct < 0.01:
            return 'SMALL - Conservative position'
        else:
            return 'NORMAL - Good position size'
    
    def _get_portfolio_risk_level(self, avg_correlation: float) -> str:
        """Determine portfolio risk level based on correlation"""
        if avg_correlation > 0.7:
            return 'High - Poor diversification'
        elif avg_correlation > 0.5:
            return 'Medium - Moderate diversification'
        else:
            return 'Low - Well diversified'
    
    def _get_risk_level(self, risk_exposure: float) -> str:
        """Get overall risk level"""
        if risk_exposure > 0.3:
            return 'High Risk'
        elif risk_exposure > 0.15:
            return 'Medium Risk'
        else:
            return 'Low Risk'
    
    def _get_diversification_recommendations(self, high_correlations: List[Dict], avg_correlation: float) -> List[str]:
        """Generate diversification recommendations"""
        recommendations = []
        
        if avg_correlation > 0.7:
            recommendations.append("Portfolio is poorly diversified - consider different sectors")
        
        if len(high_correlations) > 3:
            recommendations.append("Too many correlated positions - reduce overlapping stocks")
        
        for corr in high_correlations[:3]:  # Top 3 high correlations
            recommendations.append(f"Consider reducing correlation between {corr['stock1']} and {corr['stock2']}")
        
        if not recommendations:
            recommendations.append("Portfolio diversification looks good")
        
        return recommendations
    
    def _get_risk_recommendations(self, risk_exposure: float, concentration_risk: float) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if risk_exposure > self.risk_settings['max_portfolio_risk']:
            recommendations.append("Portfolio risk exceeds maximum threshold - reduce position sizes")
        
        if concentration_risk > 0.05:
            recommendations.append("High concentration risk - diversify positions")
        
        if risk_exposure < 0.05:
            recommendations.append("Portfolio may be too conservative - consider increasing allocation")
        
        recommendations.append("Regularly review and rebalance positions")
        recommendations.append("Monitor stop-loss levels closely")
        
        return recommendations

# Integration functions for main application
def calculate_position_sizes(stocks_data: List[Dict], portfolio_value: float = 100000) -> List[Dict]:
    """Calculate position sizes for a list of stocks"""
    risk_manager = RiskManager()
    
    enhanced_stocks = []
    for stock in stocks_data:
        position_info = risk_manager.calculate_position_size(stock, portfolio_value)
        stop_loss_info = risk_manager.calculate_stop_loss_take_profit(stock)
        
        enhanced_stock = stock.copy()
        enhanced_stock['position_sizing'] = position_info
        enhanced_stock['risk_levels'] = stop_loss_info
        enhanced_stocks.append(enhanced_stock)
    
    return enhanced_stocks

def analyze_portfolio_risk(stocks_data: List[Dict]) -> Dict:
    """Analyze overall portfolio risk"""
    risk_manager = RiskManager()
    
    # Calculate position sizes first
    enhanced_stocks = calculate_position_sizes(stocks_data)
    positions = [stock['position_sizing'] for stock in enhanced_stocks]
    
    # Perform risk analysis
    correlation_analysis = risk_manager.analyze_portfolio_correlation(stocks_data)
    portfolio_risk = risk_manager.assess_portfolio_risk(positions)
    
    return {
        'correlation_analysis': correlation_analysis,
        'portfolio_risk': portfolio_risk,
        'enhanced_stocks': enhanced_stocks
    }
