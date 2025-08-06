
"""
Market Sentiment Analysis Module

Integrates market sentiment indicators to improve prediction accuracy.
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf

logger = logging.getLogger(__name__)

class MarketSentimentAnalyzer:
    def __init__(self):
        self.sentiment_cache = {}
        self.cache_expiry = timedelta(hours=1)
    
    def get_market_sentiment_score(self, symbol: str) -> Dict:
        """Calculate comprehensive market sentiment score"""
        try:
            sentiment_data = {}
            
            # 1. Options sentiment (Put/Call ratio approximation)
            sentiment_data.update(self._get_options_sentiment(symbol))
            
            # 2. Volume analysis sentiment
            sentiment_data.update(self._get_volume_sentiment(symbol))
            
            # 3. Price momentum sentiment
            sentiment_data.update(self._get_momentum_sentiment(symbol))
            
            # 4. Sector sentiment
            sentiment_data.update(self._get_sector_sentiment(symbol))
            
            # 5. Overall market sentiment
            sentiment_data.update(self._get_overall_market_sentiment())
            
            # Calculate composite sentiment score
            composite_score = self._calculate_composite_sentiment(sentiment_data)
            sentiment_data['composite_sentiment_score'] = composite_score
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Error calculating market sentiment for {symbol}: {str(e)}")
            return {'composite_sentiment_score': 0.5}  # Neutral
    
    def _get_options_sentiment(self, symbol: str) -> Dict:
        """Get options-based sentiment indicators"""
        try:
            # Simplified options sentiment using volume analysis
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")
            
            if hist.empty:
                return {'options_sentiment': 0.5}
            
            # Use volume patterns as proxy for options sentiment
            recent_volume = hist['Volume'].tail(3).mean()
            avg_volume = hist['Volume'].mean()
            
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # High volume with price increase = bullish sentiment
            price_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
            
            if volume_ratio > 1.2 and price_change > 0:
                sentiment_score = 0.7
            elif volume_ratio > 1.2 and price_change < 0:
                sentiment_score = 0.3
            else:
                sentiment_score = 0.5
            
            return {
                'options_sentiment': sentiment_score,
                'volume_ratio': round(volume_ratio, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting options sentiment: {str(e)}")
            return {'options_sentiment': 0.5}
    
    def _get_volume_sentiment(self, symbol: str) -> Dict:
        """Analyze volume patterns for sentiment"""
        try:
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="20d")
            
            if len(hist) < 10:
                return {'volume_sentiment': 0.5}
            
            # Calculate volume-price relationship
            hist['price_change'] = hist['Close'].pct_change()
            hist['volume_change'] = hist['Volume'].pct_change()
            
            # Positive correlation = healthy sentiment
            correlation = hist['price_change'].corr(hist['volume_change'])
            
            if pd.isna(correlation):
                sentiment_score = 0.5
            else:
                # Convert correlation to sentiment score (0-1)
                sentiment_score = max(0, min(1, (correlation + 1) / 2))
            
            return {
                'volume_sentiment': round(sentiment_score, 3),
                'volume_price_correlation': round(correlation, 3) if not pd.isna(correlation) else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting volume sentiment: {str(e)}")
            return {'volume_sentiment': 0.5}
    
    def _get_momentum_sentiment(self, symbol: str) -> Dict:
        """Calculate momentum-based sentiment"""
        try:
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="30d")
            
            if len(hist) < 20:
                return {'momentum_sentiment': 0.5}
            
            # Multiple timeframe momentum
            mom_5d = (hist['Close'].iloc[-1] - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]
            mom_10d = (hist['Close'].iloc[-1] - hist['Close'].iloc[-11]) / hist['Close'].iloc[-11]
            mom_20d = (hist['Close'].iloc[-1] - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]
            
            # Weight recent momentum more heavily
            weighted_momentum = (mom_5d * 0.5) + (mom_10d * 0.3) + (mom_20d * 0.2)
            
            # Convert to sentiment score
            sentiment_score = max(0, min(1, (weighted_momentum + 0.1) / 0.2))
            
            return {
                'momentum_sentiment': round(sentiment_score, 3),
                'momentum_5d': round(mom_5d * 100, 2),
                'momentum_10d': round(mom_10d * 100, 2),
                'momentum_20d': round(mom_20d * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting momentum sentiment: {str(e)}")
            return {'momentum_sentiment': 0.5}
    
    def _get_sector_sentiment(self, symbol: str) -> Dict:
        """Get sector-based sentiment (simplified)"""
        try:
            # Simplified sector classification
            sector_map = {
                'RELIANCE': 'Energy', 'TCS': 'IT', 'HDFC': 'Financial',
                'INFY': 'IT', 'ICICI': 'Financial', 'SBIN': 'Financial',
                'BHARTI': 'Telecom', 'ITC': 'FMCG', 'HDFCBANK': 'Financial'
            }
            
            sector = sector_map.get(symbol, 'Others')
            
            # Simplified sector sentiment (would be more sophisticated in production)
            sector_sentiment_map = {
                'IT': 0.65,
                'Financial': 0.60,
                'Energy': 0.55,
                'FMCG': 0.70,
                'Telecom': 0.50,
                'Others': 0.55
            }
            
            return {
                'sector_sentiment': sector_sentiment_map.get(sector, 0.55),
                'sector': sector
            }
            
        except Exception as e:
            logger.error(f"Error getting sector sentiment: {str(e)}")
            return {'sector_sentiment': 0.5}
    
    def _get_overall_market_sentiment(self) -> Dict:
        """Get overall market sentiment using NIFTY data"""
        try:
            # Use NIFTY 50 as market proxy
            nifty = yf.Ticker("^NSEI")
            hist = nifty.history(period="10d")
            
            if hist.empty:
                return {'market_sentiment': 0.5}
            
            # Calculate market momentum
            market_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
            
            # Calculate volatility
            returns = hist['Close'].pct_change().dropna()
            volatility = returns.std()
            
            # Market sentiment based on performance and volatility
            if market_change > 0.02 and volatility < 0.02:
                market_sentiment = 0.8  # Strong positive
            elif market_change > 0 and volatility < 0.03:
                market_sentiment = 0.65  # Moderate positive
            elif market_change < -0.02 or volatility > 0.04:
                market_sentiment = 0.3   # Negative
            else:
                market_sentiment = 0.5   # Neutral
            
            return {
                'market_sentiment': market_sentiment,
                'market_change_10d': round(market_change * 100, 2),
                'market_volatility': round(volatility * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting overall market sentiment: {str(e)}")
            return {'market_sentiment': 0.5}
    
    def _calculate_composite_sentiment(self, sentiment_data: Dict) -> float:
        """Calculate weighted composite sentiment score"""
        try:
            weights = {
                'options_sentiment': 0.25,
                'volume_sentiment': 0.20,
                'momentum_sentiment': 0.25,
                'sector_sentiment': 0.15,
                'market_sentiment': 0.15
            }
            
            composite_score = 0
            total_weight = 0
            
            for indicator, weight in weights.items():
                if indicator in sentiment_data:
                    composite_score += sentiment_data[indicator] * weight
                    total_weight += weight
            
            if total_weight > 0:
                composite_score = composite_score / total_weight
            else:
                composite_score = 0.5
            
            return round(composite_score, 3)
            
        except Exception as e:
            logger.error(f"Error calculating composite sentiment: {str(e)}")
            return 0.5

def get_market_sentiment(symbol: str) -> Dict:
    """Convenience function to get market sentiment"""
    analyzer = MarketSentimentAnalyzer()
    return analyzer.get_market_sentiment_score(symbol)
