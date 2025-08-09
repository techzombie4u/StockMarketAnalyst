"""
Backtesting Manager for Stock Market Analyst

Tracks prediction accuracy by comparing 1-month predictions with actual price movements
over the past 30 days to validate model performance.
"""

import json
import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class BacktestingManager:
    def __init__(self):
        self.backtest_file = 'backtesting_results.json'
        self.predictions_history_file = 'predictions_history.json'
        self.backtest_results = self.load_backtest_results()
        self.predictions_history = self.load_predictions_history()

    def load_backtest_results(self) -> Dict:
        """Load existing backtesting results"""
        try:
            if os.path.exists(self.backtest_file):
                with open(self.backtest_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading backtest results: {str(e)}")
            return {}

    def save_backtest_results(self):
        """Save backtesting results to file"""
        try:
            with open(self.backtest_file, 'w') as f:
                json.dump(self.backtest_results, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving backtest results: {str(e)}")

    def load_predictions_history(self) -> List[Dict]:
        """Load predictions history"""
        try:
            if os.path.exists(self.predictions_history_file):
                with open(self.predictions_history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading predictions history: {str(e)}")
            return []

    def save_predictions_history(self):
        """Save predictions history to file"""
        try:
            with open(self.predictions_history_file, 'w') as f:
                json.dump(self.predictions_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving predictions history: {str(e)}")

    def record_prediction(self, stock_data: Dict):
        """Record a prediction for future backtesting"""
        try:
            prediction_record = {
                'symbol': stock_data.get('symbol'),
                'timestamp': datetime.now().isoformat(),
                'current_price': stock_data.get('current_price', 0),
                'predicted_1mo': stock_data.get('pred_1mo', 0),
                'predicted_price': stock_data.get('predicted_price', 0),
                'score': stock_data.get('score', 0),
                'confidence': stock_data.get('confidence', 0),
                'trend_class': stock_data.get('trend_class', 'sideways')
            }

            # Record prediction (fix dict append error)
            if not hasattr(self, 'predictions'):
                self.predictions = []
            elif isinstance(self.predictions, dict):
                self.predictions = []  # Convert dict to list if needed

            self.predictions.append(prediction_record)

            # Keep only last 100 predictions to manage file size
            if len(self.predictions) > 100:
                self.predictions = self.predictions[-100:]

            self.save_predictions_history()

        except Exception as e:
            logger.error(f"Error recording prediction: {str(e)}")

    def get_actual_price_change(self, symbol: str, days_ago: int) -> Optional[float]:
        """Get actual price change for a symbol over specified days"""
        try:
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)

            # Get data for the period
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_ago + 5)  # Extra buffer

            hist_data = stock.history(start=start_date, end=end_date)

            if hist_data.empty or len(hist_data) < days_ago:
                return None

            # Calculate actual price change
            current_price = hist_data['Close'].iloc[-1]
            past_price = hist_data['Close'].iloc[-(days_ago + 1)] if len(hist_data) > days_ago else hist_data['Close'].iloc[0]

            actual_change_pct = ((current_price - past_price) / past_price) * 100
            return actual_change_pct

        except Exception as e:
            logger.error(f"Error getting actual price change for {symbol}: {str(e)}")
            return None

    def run_backtest_analysis(self) -> Dict:
        """Run backtesting analysis for predictions made 30 days ago"""
        try:
            backtest_date = datetime.now() - timedelta(days=30)
            backtest_results = {
                'analysis_date': datetime.now().isoformat(),
                'backtest_period': '30_days',
                'total_predictions': 0,
                'accurate_predictions': 0,
                'accuracy_rate': 0,
                'predictions_analyzed': [],
                'performance_by_score': {},
                'performance_by_trend': {}
            }

            # Filter predictions from ~30 days ago (±3 days window)
            target_predictions = []
            for prediction in self.predictions_history:
                pred_date = datetime.fromisoformat(prediction['timestamp'])
                days_diff = (datetime.now() - pred_date).days

                if 27 <= days_diff <= 33:  # 30 ± 3 days window
                    target_predictions.append(prediction)

            logger.info(f"Found {len(target_predictions)} predictions from ~30 days ago for backtesting")

            accurate_count = 0
            total_count = len(target_predictions)

            for prediction in target_predictions:
                symbol = prediction['symbol']
                predicted_change = prediction['predicted_1mo']
                pred_date = datetime.fromisoformat(prediction['timestamp'])
                days_ago = (datetime.now() - pred_date).days

                # Get actual price change
                actual_change = self.get_actual_price_change(symbol, days_ago)

                if actual_change is not None:
                    # Consider prediction accurate if direction matches and magnitude is reasonable
                    direction_match = (predicted_change > 0 and actual_change > 0) or (predicted_change < 0 and actual_change < 0)
                    magnitude_reasonable = abs(actual_change - predicted_change) < 20  # Within 20% tolerance

                    is_accurate = direction_match and magnitude_reasonable

                    if is_accurate:
                        accurate_count += 1

                    # Record individual analysis
                    analysis_record = {
                        'symbol': symbol,
                        'predicted_change': round(predicted_change, 2),
                        'actual_change': round(actual_change, 2),
                        'accuracy': is_accurate,
                        'direction_match': direction_match,
                        'magnitude_diff': round(abs(actual_change - predicted_change), 2),
                        'score': prediction.get('score', 0),
                        'confidence': prediction.get('confidence', 0),
                        'trend_class': prediction.get('trend_class', 'sideways')
                    }

                    backtest_results['predictions_analyzed'].append(analysis_record)

            # Calculate overall accuracy
            if total_count > 0:
                backtest_results['total_predictions'] = total_count
                backtest_results['accurate_predictions'] = accurate_count
                backtest_results['accuracy_rate'] = round((accurate_count / total_count) * 100, 2)

            # Performance by score ranges
            score_ranges = {'70-79': [], '80-89': [], '90-100': []}
            for analysis in backtest_results['predictions_analyzed']:
                score = analysis['score']
                if 70 <= score < 80:
                    score_ranges['70-79'].append(analysis['accuracy'])
                elif 80 <= score < 90:
                    score_ranges['80-89'].append(analysis['accuracy'])
                elif score >= 90:
                    score_ranges['90-100'].append(analysis['accuracy'])

            for range_name, accuracies in score_ranges.items():
                if accuracies:
                    backtest_results['performance_by_score'][range_name] = {
                        'count': len(accuracies),
                        'accuracy_rate': round((sum(accuracies) / len(accuracies)) * 100, 2)
                    }

            # Performance by trend
            trend_performance = {'uptrend': [], 'sideways': [], 'downtrend': []}
            for analysis in backtest_results['predictions_analyzed']:
                trend = analysis['trend_class']
                if trend in trend_performance:
                    trend_performance[trend].append(analysis['accuracy'])

            for trend, accuracies in trend_performance.items():
                if accuracies:
                    backtest_results['performance_by_trend'][trend] = {
                        'count': len(accuracies),
                        'accuracy_rate': round((sum(accuracies) / len(accuracies)) * 100, 2)
                    }

            # Save results
            self.backtest_results = backtest_results
            self.save_backtest_results()

            logger.info(f"Backtesting completed: {accurate_count}/{total_count} accurate predictions ({backtest_results['accuracy_rate']}%)")

            return backtest_results

        except Exception as e:
            logger.error(f"Error in backtesting analysis: {str(e)}")
            return {}

    def get_latest_backtest_summary(self) -> Dict:
        """Get summary of latest backtesting results"""
        try:
            if not self.backtest_results:
                return {'status': 'no_data', 'message': 'No backtesting data available'}

            summary = {
                'status': 'available',
                'last_analysis': self.backtest_results.get('analysis_date', 'Unknown'),
                'accuracy_rate': self.backtest_results.get('accuracy_rate', 0),
                'total_predictions': self.backtest_results.get('total_predictions', 0),
                'accurate_predictions': self.backtest_results.get('accurate_predictions', 0),
                'performance_by_score': self.backtest_results.get('performance_by_score', {}),
                'performance_by_trend': self.backtest_results.get('performance_by_trend', {})
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting backtest summary: {str(e)}")
            return {'status': 'error', 'message': str(e)}