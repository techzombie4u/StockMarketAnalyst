"""
Prediction Stability Manager

Ensures predictions remain stable for a minimum period to maintain reliability
for investment decisions.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class PredictionStabilityManager:
    def __init__(self):
        self.stable_predictions_file = 'stable_predictions.json'
        self.min_stability_hours = 24  # Minimum hours before prediction can change
        self.max_change_threshold = 5.0  # Maximum allowed % change in prediction
        self.history_file = 'predictions_history.json'

    def load_stable_predictions(self) -> Dict:
        """Load stable predictions from file"""
        try:
            with open(self.stable_predictions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            logger.error(f"Error loading stable predictions: {str(e)}")
            return {}

    def save_stable_predictions(self, predictions: Dict):
        """Save stable predictions to file"""
        try:
            with open(self.stable_predictions_file, 'w') as f:
                json.dump(predictions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stable predictions: {str(e)}")

    def should_update_prediction(self, symbol: str, new_prediction: Dict) -> bool:
        """Check if prediction should be updated based on stability rules"""
        stable_predictions = self.load_stable_predictions()
        current_time = datetime.now()

        if symbol not in stable_predictions:
            return True  # No previous prediction, allow new one

        existing = stable_predictions[symbol]
        last_update = datetime.fromisoformat(existing['last_updated'])
        hours_since = (current_time - last_update).total_seconds() / 3600

        # Check minimum stability period
        if hours_since < self.min_stability_hours:
            logger.info(f"Prediction for {symbol} is locked (stable for {hours_since:.1f}h)")
            return False

        # Check if change is significant enough to warrant update
        old_pred = existing.get('pred_1mo', 0)
        new_pred = new_prediction.get('pred_1mo', 0)

        if abs(new_pred - old_pred) < self.max_change_threshold:
            logger.info(f"Prediction change for {symbol} too small ({abs(new_pred - old_pred):.1f}%)")
            return False

        return True

    def stabilize_predictions(self, new_predictions: List[Dict]) -> List[Dict]:
        """Apply stability rules to new predictions"""
        stable_predictions = self.load_stable_predictions()
        stabilized = []
        current_time = datetime.now()
        updated_stable = stable_predictions.copy()

        # Track prediction history
        prediction_history = []

        for stock in new_predictions:
            symbol = stock.get('symbol', '')

            if self.should_update_prediction(symbol, stock):
                # Allow new prediction
                stabilized.append(stock)

                # Update stable predictions record
                updated_stable[symbol] = {
                    'symbol': symbol,
                    'pred_24h': stock.get('pred_24h', 0),
                    'pred_5d': stock.get('pred_5d', 0),
                    'pred_1mo': stock.get('pred_1mo', 0),
                    'predicted_price': stock.get('predicted_price', 0),
                    'current_price': stock.get('current_price', 0),
                    'confidence': stock.get('confidence', 0),
                    'score': stock.get('score', 0),
                    'last_updated': current_time.isoformat(),
                    'lock_reason': 'new_prediction'
                }

                # Add to prediction history
                prediction_history.append({
                    'symbol': symbol,
                    'timestamp': current_time.isoformat(),
                    'pred_24h': stock.get('pred_24h', 0),
                    'pred_5d': stock.get('pred_5d', 0),
                    'pred_1mo': stock.get('pred_1mo', 0),
                    'predicted_price': stock.get('predicted_price', 0),
                    'current_price': stock.get('current_price', 0),
                    'confidence': stock.get('confidence', 0),
                    'score': stock.get('score', 0),
                    'action': 'updated'
                })

                logger.info(f"✅ Updated prediction for {symbol}")
            else:
                # Use stable prediction
                stable_stock = updated_stable[symbol].copy()

                # Keep current technical data but use stable predictions
                stable_stock.update({
                    'score': stock.get('score', 0),  # Allow score to update
                    'current_price': stock.get('current_price', 0),  # Current price updates
                    'technical': stock.get('technical', {}),  # Technical data updates
                    'fundamentals': stock.get('fundamentals', {}),  # Fundamental data updates
                })

                stabilized.append(stable_stock)

                # Add to prediction history
                prediction_history.append({
                    'symbol': symbol,
                    'timestamp': current_time.isoformat(),
                    'pred_24h': stable_stock.get('pred_24h', 0),
                    'pred_5d': stable_stock.get('pred_5d', 0),
                    'pred_1mo': stable_stock.get('pred_1mo', 0),
                    'predicted_price': stable_stock.get('predicted_price', 0),
                    'current_price': stable_stock.get('current_price', 0),
                    'confidence': stable_stock.get('confidence', 0),
                    'score': stable_stock.get('score', 0),
                    'action': 'stable'
                })

                logger.info(f"🔒 Using stable prediction for {symbol}")

        # Save updated stable predictions
        self.save_stable_predictions(updated_stable)

        # Save prediction history
        self.save_prediction_history(prediction_history)

        return stabilized

    def save_prediction_history(self, predictions: List[Dict]):
        """Save prediction history with timestamp"""
        try:
            # Ensure predictions is a list of dictionaries
            if not isinstance(predictions, list):
                logger.warning(f"Expected list but got {type(predictions)}, converting...")
                predictions = []

            # Validate each prediction is a dictionary
            valid_predictions = []
            for pred in predictions:
                if isinstance(pred, dict) and pred.get('symbol'):
                    valid_predictions.append(pred)
                else:
                    logger.warning(f"Skipping invalid prediction: {type(pred)}")

            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'predictions': valid_predictions,
                'count': len(valid_predictions)
            }

            # Load existing history
            existing_history = []
            if os.path.exists(self.history_file):
                try:
                    with open(self.history_file, 'r') as f:
                        existing_history = json.load(f)
                    # Ensure existing_history is a list
                    if not isinstance(existing_history, list):
                        existing_history = []
                except (json.JSONDecodeError, TypeError):
                    existing_history = []

            # Add new entry
            existing_history.append(history_entry)

            # Keep only last 50 entries
            existing_history = existing_history[-50:]

            # Save updated history
            with open(self.history_file, 'w') as f:
                json.dump(existing_history, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving prediction history: {str(e)}")
            # Continue without failing the main process

    def get_prediction_status(self) -> Dict:
        """Get status of prediction stability"""
        stable_predictions = self.load_stable_predictions()
        current_time = datetime.now()

        status = {
            'total_stable_predictions': len(stable_predictions),
            'locked_predictions': 0,
            'updateable_predictions': 0,
            'predictions_by_age': {}
        }

        for symbol, pred in stable_predictions.items():
            last_update = datetime.fromisoformat(pred['last_updated'])
            hours_since = (current_time - last_update).total_seconds() / 3600

            if hours_since < self.min_stability_hours:
                status['locked_predictions'] += 1
            else:
                status['updateable_predictions'] += 1

            age_bucket = f"{int(hours_since//6)*6}-{int(hours_since//6)*6+6}h"
            status['predictions_by_age'][age_bucket] = status['predictions_by_age'].get(age_bucket, 0) + 1

        return status