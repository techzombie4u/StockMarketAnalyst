
"""
Stock Market Analyst - Prediction Accuracy Monitor

Tracks prediction accuracy and automatically adjusts models for better performance.
"""

import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import yfinance as yf

logger = logging.getLogger(__name__)

class PredictionAccuracyMonitor:
    def __init__(self):
        self.predictions_file = 'prediction_tracking.json'
        self.accuracy_threshold = 70  # Minimum acceptable accuracy
        
    def track_prediction(self, symbol: str, prediction_data: Dict, actual_price: float = None):
        """Track a prediction for later accuracy assessment"""
        try:
            # Load existing predictions
            predictions = self.load_predictions()
            
            # Create prediction record
            prediction_record = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'predicted_24h': prediction_data.get('pred_24h', 0),
                'predicted_5d': prediction_data.get('pred_5d', 0),
                'predicted_1mo': prediction_data.get('pred_1mo', 0),
                'current_price': prediction_data.get('current_price', 0),
                'confidence': prediction_data.get('confidence', 50),
                'method': prediction_data.get('method', 'ensemble'),
                'actual_price': actual_price,
                'accuracy_checked': False
            }
            
            predictions.append(prediction_record)
            
            # Keep only last 1000 predictions
            predictions = predictions[-1000:]
            
            # Save predictions
            with open(self.predictions_file, 'w') as f:
                json.dump(predictions, f, indent=2)
                
            logger.info(f"Tracked prediction for {symbol}")
            
        except Exception as e:
            logger.error(f"Error tracking prediction: {str(e)}")
    
    def check_prediction_accuracy(self) -> Dict:
        """Check accuracy of past predictions and update models"""
        try:
            predictions = self.load_predictions()
            updated_predictions = []
            accuracy_stats = {
                '24h': {'correct': 0, 'total': 0, 'accuracy': 0},
                '5d': {'correct': 0, 'total': 0, 'accuracy': 0},
                '1mo': {'correct': 0, 'total': 0, 'accuracy': 0},
                'overall_accuracy': 0,
                'recommendations': []
            }
            
            now = datetime.now()
            
            for pred in predictions:
                try:
                    pred_time = datetime.fromisoformat(pred['timestamp'])
                    symbol = pred['symbol']
                    
                    # Check 24h predictions (after 1 day)
                    if not pred.get('accuracy_checked_24h', False) and now - pred_time >= timedelta(days=1):
                        actual_24h = self.get_actual_price_change(symbol, pred_time, timedelta(days=1))
                        if actual_24h is not None:
                            pred['actual_24h'] = actual_24h
                            pred['accuracy_24h'] = self.calculate_accuracy(pred['predicted_24h'], actual_24h)
                            pred['accuracy_checked_24h'] = True
                            
                            accuracy_stats['24h']['total'] += 1
                            if pred['accuracy_24h'] > 70:  # Consider >70% as correct
                                accuracy_stats['24h']['correct'] += 1
                    
                    # Check 5d predictions (after 5 days)
                    if not pred.get('accuracy_checked_5d', False) and now - pred_time >= timedelta(days=5):
                        actual_5d = self.get_actual_price_change(symbol, pred_time, timedelta(days=5))
                        if actual_5d is not None:
                            pred['actual_5d'] = actual_5d
                            pred['accuracy_5d'] = self.calculate_accuracy(pred['predicted_5d'], actual_5d)
                            pred['accuracy_checked_5d'] = True
                            
                            accuracy_stats['5d']['total'] += 1
                            if pred['accuracy_5d'] > 70:
                                accuracy_stats['5d']['correct'] += 1
                    
                    # Check 1mo predictions (after 30 days)
                    if not pred.get('accuracy_checked_1mo', False) and now - pred_time >= timedelta(days=30):
                        actual_1mo = self.get_actual_price_change(symbol, pred_time, timedelta(days=30))
                        if actual_1mo is not None:
                            pred['actual_1mo'] = actual_1mo
                            pred['accuracy_1mo'] = self.calculate_accuracy(pred['predicted_1mo'], actual_1mo)
                            pred['accuracy_checked_1mo'] = True
                            
                            accuracy_stats['1mo']['total'] += 1
                            if pred['accuracy_1mo'] > 70:
                                accuracy_stats['1mo']['correct'] += 1
                    
                    updated_predictions.append(pred)
                    
                except Exception as e:
                    logger.warning(f"Error checking prediction accuracy: {str(e)}")
                    updated_predictions.append(pred)
            
            # Calculate accuracy percentages
            for timeframe in ['24h', '5d', '1mo']:
                if accuracy_stats[timeframe]['total'] > 0:
                    accuracy_stats[timeframe]['accuracy'] = (
                        accuracy_stats[timeframe]['correct'] / accuracy_stats[timeframe]['total'] * 100
                    )
            
            # Calculate overall accuracy
            total_correct = sum(accuracy_stats[tf]['correct'] for tf in ['24h', '5d', '1mo'])
            total_predictions = sum(accuracy_stats[tf]['total'] for tf in ['24h', '5d', '1mo'])
            
            if total_predictions > 0:
                accuracy_stats['overall_accuracy'] = total_correct / total_predictions * 100
            
            # Generate improvement recommendations
            accuracy_stats['recommendations'] = self.generate_improvement_recommendations(accuracy_stats)
            
            # Save updated predictions
            with open(self.predictions_file, 'w') as f:
                json.dump(updated_predictions, f, indent=2)
            
            logger.info(f"Accuracy check complete. Overall accuracy: {accuracy_stats['overall_accuracy']:.1f}%")
            
            return accuracy_stats
            
        except Exception as e:
            logger.error(f"Error checking prediction accuracy: {str(e)}")
            return {}
    
    def get_actual_price_change(self, symbol: str, start_time: datetime, duration: timedelta) -> float:
        """Get actual price change over specified duration"""
        try:
            end_time = start_time + duration
            
            # Get price data
            ticker = yf.Ticker(f"{symbol}.NS")
            hist_data = ticker.history(start=start_time.date(), end=end_time.date() + timedelta(days=2))
            
            if len(hist_data) < 2:
                return None
            
            start_price = hist_data['Close'].iloc[0]
            end_price = hist_data['Close'].iloc[-1]
            
            price_change_pct = ((end_price - start_price) / start_price) * 100
            return round(price_change_pct, 2)
            
        except Exception as e:
            logger.warning(f"Could not get actual price change for {symbol}: {str(e)}")
            return None
    
    def calculate_accuracy(self, predicted: float, actual: float) -> float:
        """Calculate prediction accuracy percentage"""
        try:
            if abs(predicted) < 0.1 and abs(actual) < 0.1:
                return 100  # Both predictions near zero
            
            # Calculate percentage error
            error = abs(predicted - actual)
            magnitude = max(abs(predicted), abs(actual))
            
            accuracy = max(0, 100 - (error / magnitude * 100))
            return round(accuracy, 1)
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {str(e)}")
            return 0
    
    def generate_improvement_recommendations(self, accuracy_stats: Dict) -> List[str]:
        """Generate recommendations for improving prediction accuracy"""
        recommendations = []
        
        try:
            overall_accuracy = accuracy_stats.get('overall_accuracy', 0)
            
            if overall_accuracy < 60:
                recommendations.append("Consider adjusting prediction weights in ensemble model")
                recommendations.append("Increase focus on fundamental analysis for better long-term predictions")
            
            # Check individual timeframe performance
            if accuracy_stats['24h']['accuracy'] < 50:
                recommendations.append("Improve short-term technical indicators (RSI, MACD tuning)")
                recommendations.append("Add more real-time sentiment analysis")
            
            if accuracy_stats['5d']['accuracy'] < 60:
                recommendations.append("Enhance pattern recognition algorithms")
                recommendations.append("Consider market regime detection")
            
            if accuracy_stats['1mo']['accuracy'] < 70:
                recommendations.append("Strengthen fundamental analysis weightings")
                recommendations.append("Add sector rotation analysis")
            
            # Data quality recommendations
            recommendations.append("Regularly validate data sources for accuracy")
            recommendations.append("Consider adding alternative data sources (news sentiment, insider trading)")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Monitor prediction accuracy regularly"]
    
    def load_predictions(self) -> List[Dict]:
        """Load prediction history"""
        try:
            with open(self.predictions_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            logger.error(f"Error loading predictions: {str(e)}")
            return []
    
    def get_accuracy_report(self) -> str:
        """Generate a formatted accuracy report"""
        try:
            accuracy_stats = self.check_prediction_accuracy()
            
            report = []
            report.append("=== PREDICTION ACCURACY REPORT ===")
            report.append(f"Overall Accuracy: {accuracy_stats.get('overall_accuracy', 0):.1f}%")
            report.append("")
            
            for timeframe in ['24h', '5d', '1mo']:
                stats = accuracy_stats.get(timeframe, {})
                report.append(f"{timeframe.upper()} Predictions:")
                report.append(f"  Accuracy: {stats.get('accuracy', 0):.1f}%")
                report.append(f"  Correct: {stats.get('correct', 0)}")
                report.append(f"  Total: {stats.get('total', 0)}")
                report.append("")
            
            report.append("IMPROVEMENT RECOMMENDATIONS:")
            for rec in accuracy_stats.get('recommendations', []):
                report.append(f"• {rec}")
            
            return "\n".join(report)
            
        except Exception as e:
            logger.error(f"Error generating accuracy report: {str(e)}")
            return "Error generating report"

def monitor_predictions():
    """Standalone function to monitor predictions"""
    monitor = PredictionAccuracyMonitor()
    return monitor.check_prediction_accuracy()
