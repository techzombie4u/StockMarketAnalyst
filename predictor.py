
"""
Stock Market Analyst - ML Predictor Module

Handles real-time predictions using trained ML models.
Integrates with existing stock screening workflow.
"""

import logging
from typing import Dict, List, Optional
from data_loader import MLDataLoader
from models import MLModels

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self):
        self.data_loader = MLDataLoader()
        self.models = MLModels()
        self.models_loaded = False
    
    def initialize(self) -> bool:
        """Initialize predictor by loading trained models"""
        try:
            logger.info("Initializing ML Predictor...")
            self.models_loaded = self.models.load_models()
            
            if self.models_loaded:
                logger.info("✅ ML models loaded successfully")
            else:
                logger.warning("⚠️ ML models not found - predictions will be disabled")
            
            return self.models_loaded
            
        except Exception as e:
            logger.error(f"Error initializing ML Predictor: {str(e)}")
            return False
    
    def predict_stock(self, symbol: str, fundamentals: Dict) -> Optional[Dict]:
        """Generate ML predictions for a single stock"""
        try:
            if not self.models_loaded:
                return None
            
            # Prepare prediction data
            prediction_data = self.data_loader.prepare_prediction_data(symbol, fundamentals)
            if prediction_data is None:
                return None
            
            current_price = prediction_data['current_price']
            lstm_input = prediction_data['lstm_input']
            rf_input = prediction_data['rf_input']
            
            # Generate predictions
            predictions = {}
            
            # LSTM price prediction
            if lstm_input is not None:
                predicted_price = self.models.predict_price(lstm_input, current_price)
                if predicted_price is not None:
                    price_change = ((predicted_price - current_price) / current_price) * 100
                    predictions['predicted_price'] = round(predicted_price, 2)
                    predictions['predicted_change'] = round(price_change, 2)
            
            # Random Forest direction prediction
            if rf_input is not None:
                direction_pred = self.models.predict_direction(rf_input)
                if direction_pred is not None:
                    predictions.update(direction_pred)
            
            return predictions if predictions else None
            
        except Exception as e:
            logger.error(f"Error predicting for {symbol}: {str(e)}")
            return None
    
    def enrich_with_ml_predictions(self, stocks_data: List[Dict]) -> List[Dict]:
        """Enrich stock screening results with ML predictions"""
        try:
            if not self.models_loaded:
                logger.info("ML models not available - skipping predictions")
                return stocks_data
            
            logger.info(f"Adding ML predictions to {len(stocks_data)} stocks...")
            
            enriched_stocks = []
            
            for stock in stocks_data:
                try:
                    symbol = stock['symbol']
                    fundamentals = stock.get('fundamentals', {})
                    
                    # Get ML predictions
                    ml_predictions = self.predict_stock(symbol, fundamentals)
                    
                    # Add predictions to stock data
                    enhanced_stock = stock.copy()
                    
                    if ml_predictions:
                        # Add LSTM predictions
                        enhanced_stock['ml_predicted_price'] = ml_predictions.get('predicted_price', 0)
                        enhanced_stock['ml_predicted_change'] = ml_predictions.get('predicted_change', 0)
                        
                        # Add Random Forest predictions
                        enhanced_stock['ml_direction'] = ml_predictions.get('direction_label', 'UNKNOWN')
                        enhanced_stock['ml_confidence'] = round(ml_predictions.get('confidence', 0) * 100, 1)
                        enhanced_stock['ml_up_probability'] = round(ml_predictions.get('up_probability', 0.5) * 100, 1)
                        
                        # Calculate ML score boost
                        ml_score_boost = self.calculate_ml_score_boost(ml_predictions)
                        enhanced_stock['ml_score_boost'] = ml_score_boost
                        enhanced_stock['enhanced_score'] = round(stock['score'] + ml_score_boost, 1)
                    else:
                        # No ML predictions available
                        enhanced_stock['ml_predicted_price'] = 0
                        enhanced_stock['ml_predicted_change'] = 0
                        enhanced_stock['ml_direction'] = 'UNKNOWN'
                        enhanced_stock['ml_confidence'] = 0
                        enhanced_stock['ml_up_probability'] = 50.0
                        enhanced_stock['ml_score_boost'] = 0
                        enhanced_stock['enhanced_score'] = stock['score']
                    
                    enriched_stocks.append(enhanced_stock)
                    
                except Exception as e:
                    logger.error(f"Error enriching {stock.get('symbol', 'UNKNOWN')}: {str(e)}")
                    # Add stock without ML predictions
                    enhanced_stock = stock.copy()
                    enhanced_stock.update({
                        'ml_predicted_price': 0,
                        'ml_predicted_change': 0,
                        'ml_direction': 'ERROR',
                        'ml_confidence': 0,
                        'ml_up_probability': 50.0,
                        'ml_score_boost': 0,
                        'enhanced_score': stock['score']
                    })
                    enriched_stocks.append(enhanced_stock)
            
            # Re-sort by enhanced score
            enriched_stocks.sort(key=lambda x: x['enhanced_score'], reverse=True)
            
            logger.info("ML predictions added successfully")
            return enriched_stocks
            
        except Exception as e:
            logger.error(f"Error enriching stocks with ML predictions: {str(e)}")
            return stocks_data
    
    def calculate_ml_score_boost(self, ml_predictions: Dict) -> float:
        """Calculate score boost based on ML predictions"""
        try:
            boost = 0.0
            
            # Boost for positive price prediction
            predicted_change = ml_predictions.get('predicted_change', 0)
            if predicted_change > 2:
                boost += min(15, predicted_change * 2)  # Max 15 points
            elif predicted_change > 0:
                boost += predicted_change
            
            # Boost for UP direction with high confidence
            if ml_predictions.get('direction_label') == 'UP':
                confidence = ml_predictions.get('confidence', 0)
                boost += confidence * 10  # Max 10 points
            
            # Penalty for DOWN direction with high confidence
            if ml_predictions.get('direction_label') == 'DOWN':
                confidence = ml_predictions.get('confidence', 0)
                boost -= confidence * 10  # Max -10 points
            
            return round(boost, 1)
            
        except Exception as e:
            logger.error(f"Error calculating ML score boost: {str(e)}")
            return 0.0

def enrich_with_ml_predictions(stocks_data: List[Dict]) -> List[Dict]:
    """Standalone function for easy integration"""
    predictor = MLPredictor()
    predictor.initialize()
    return predictor.enrich_with_ml_predictions(stocks_data)

def main():
    """Test predictor"""
    # Test data
    test_stocks = [{
        'symbol': 'RELIANCE',
        'score': 75.0,
        'fundamentals': {
            'pe_ratio': 15.5,
            'revenue_growth': 12.0,
            'earnings_growth': 8.0,
            'promoter_buying': False
        }
    }]
    
    # Test enrichment
    enriched = enrich_with_ml_predictions(test_stocks)
    
    print("Enriched stock data:")
    for stock in enriched:
        print(f"Symbol: {stock['symbol']}")
        print(f"Original Score: {stock['score']}")
        print(f"Enhanced Score: {stock['enhanced_score']}")
        print(f"ML Predicted Price: {stock['ml_predicted_price']}")
        print(f"ML Direction: {stock['ml_direction']}")
        print(f"ML Confidence: {stock['ml_confidence']}%")

if __name__ == "__main__":
    main()
