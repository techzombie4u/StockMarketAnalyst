"""
Signal Management Module for Stock Market Analyst

Implements signal confirmation, minimum hold periods, and confidence-based filtering
to improve prediction stability for actual trading.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class SignalManager:
    def __init__(self):
        self.signals_file = 'active_signals.json'
        self.min_hold_period_hours = 24  # Minimum 24 hours between signal changes
        self.confirmation_threshold = 3   # Require 3 consecutive confirmations
        self.confidence_threshold = 80    # Only signals with >80% confidence
        self.active_signals = self.load_active_signals()

    def load_active_signals(self) -> Dict:
        """Load active signals from file"""
        try:
            if os.path.exists(self.signals_file):
                with open(self.signals_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading signals: {str(e)}")
            return {}

    def save_active_signals(self):
        """Save active signals to file"""
        try:
            with open(self.signals_file, 'w') as f:
                json.dump(self.active_signals, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving signals: {str(e)}")

    def should_update_signal(self, symbol: str, new_signal: Dict) -> bool:
        """Check if signal should be updated based on hold period and confirmation"""
        current_time = datetime.now()

        # Get existing signal
        existing_signal = self.active_signals.get(symbol)

        if not existing_signal:
            # No existing signal, check confidence threshold
            return new_signal.get('confidence', 0) >= self.confidence_threshold

        # Check minimum hold period
        last_update = datetime.fromisoformat(existing_signal['last_updated'])
        hours_since_update = (current_time - last_update).total_seconds() / 3600

        if hours_since_update < self.min_hold_period_hours:
            logger.info(f"Signal for {symbol} still in hold period ({hours_since_update:.1f}h < {self.min_hold_period_hours}h)")
            return False

        # Check if new signal differs significantly
        score_change = abs(new_signal.get('score', 0) - existing_signal.get('score', 0))
        prediction_change = abs(new_signal.get('predicted_gain', 0) - existing_signal.get('predicted_gain', 0))

        # Only update if significant change AND high confidence
        significant_change = score_change > 15 or prediction_change > 5
        high_confidence = new_signal.get('confidence', 0) >= self.confidence_threshold

        return significant_change and high_confidence

    def confirm_signal(self, symbol: str, signal_data: Dict) -> bool:
        """Add signal confirmation and check if enough confirmations exist"""
        current_time = datetime.now()

        # Initialize confirmation tracking if not exists
        if symbol not in self.active_signals:
            self.active_signals[symbol] = {
                'confirmations': [],
                'confirmed_signal': None,
                'last_updated': current_time.isoformat()
            }

        signal_info = self.active_signals[symbol]

        # Add new confirmation
        confirmation = {
            'timestamp': current_time.isoformat(),
            'score': signal_data.get('score', 0),
            'predicted_gain': signal_data.get('predicted_gain', 0),
            'confidence': signal_data.get('confidence', 0)
        }

        signal_info['confirmations'].append(confirmation)

        # Keep only recent confirmations (last 3 days)
        cutoff_time = current_time - timedelta(days=3)
        signal_info['confirmations'] = [
            conf for conf in signal_info['confirmations']
            if datetime.fromisoformat(conf['timestamp']) > cutoff_time
        ]

        # Check if we have enough confirmations
        recent_confirmations = [
            conf for conf in signal_info['confirmations']
            if datetime.fromisoformat(conf['timestamp']) > current_time - timedelta(hours=6)
        ]

        if len(recent_confirmations) >= self.confirmation_threshold:
            # Calculate average of confirmations
            avg_score = sum(conf['score'] for conf in recent_confirmations) / len(recent_confirmations)
            avg_prediction = sum(conf['predicted_gain'] for conf in recent_confirmations) / len(recent_confirmations)
            avg_confidence = sum(conf['confidence'] for conf in recent_confirmations) / len(recent_confirmations)

            # Update confirmed signal
            signal_info['confirmed_signal'] = {
                'symbol': symbol,
                'score': avg_score,
                'predicted_gain': avg_prediction,
                'confidence': avg_confidence,
                'confirmation_count': len(recent_confirmations),
                'confirmed_at': current_time.isoformat(),
                **signal_data  # Include other signal data
            }

            signal_info['last_updated'] = current_time.isoformat()
            self.save_active_signals()

            logger.info(f"Signal confirmed for {symbol} with {len(recent_confirmations)} confirmations")
            return True

        self.save_active_signals()
        logger.info(f"Signal for {symbol} needs more confirmations ({len(recent_confirmations)}/{self.confirmation_threshold})")
        return False

    def get_confirmed_signals(self) -> List[Dict]:
        """Get all confirmed signals that meet criteria"""
        confirmed_signals = []

        for symbol, signal_info in self.active_signals.items():
            confirmed_signal = signal_info.get('confirmed_signal')

            if confirmed_signal and confirmed_signal.get('confidence', 0) >= self.confidence_threshold:
                confirmed_signals.append(confirmed_signal)

        # Sort by confidence and score
        confirmed_signals.sort(
            key=lambda x: (x.get('confidence', 0), x.get('score', 0)),
            reverse=True
        )

        return confirmed_signals

    def filter_trading_signals(self, raw_signals: List[Dict]) -> List[Dict]:
        """Filter raw signals through confirmation and hold period logic"""
        trading_signals = []

        for signal in raw_signals:
            symbol = signal.get('symbol')
            if not symbol:
                continue

            # Check if signal should be updated
            if self.should_update_signal(symbol, signal):
                # Try to confirm signal
                if self.confirm_signal(symbol, signal):
                    trading_signals.append(signal)
                    logger.info(f"Trading signal confirmed for {symbol}")
                else:
                    logger.info(f"Signal for {symbol} awaiting confirmation")
            else:
                # Use existing confirmed signal if available
                existing_signal = self.active_signals.get(symbol, {}).get('confirmed_signal')
                if existing_signal:
                    trading_signals.append(existing_signal)

        return trading_signals

    def get_signal_status(self) -> Dict:
        """Get status of all signals for monitoring"""
        status = {
            'total_symbols': len(self.active_signals),
            'confirmed_signals': len([s for s in self.active_signals.values() if s.get('confirmed_signal')]),
            'pending_confirmations': len([s for s in self.active_signals.values() if not s.get('confirmed_signal')]),
            'high_confidence_signals': len([
                s for s in self.active_signals.values() 
                if s.get('confirmed_signal', {}).get('confidence', 0) >= self.confidence_threshold
            ])
        }
        return status
"""
Signal Management Module for Stock Market Analyst

Implements signal confirmation, minimum hold periods, and confidence-based filtering
to improve prediction stability for actual trading.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class SignalManager:
    def __init__(self):
        self.signals_file = 'active_signals.json'
        self.min_hold_period_hours = 24  # Minimum 24 hours between signal changes
        self.confirmation_threshold = 3   # Require 3 consecutive confirmations
        self.confidence_threshold = 80    # Only signals with >80% confidence
        self.active_signals = self.load_active_signals()
        self.signal_history_file = 'signal_history.json'
        self.signal_history = self.load_signal_history()
        self.score_consistency_threshold = 25
        self.max_volatility_threshold = 5

    def load_signal_history(self) -> Dict:
        """Load signal history from file"""
        try:
            if os.path.exists(self.signal_history_file):
                with open(self.signal_history_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading signal history: {str(e)}")
            return {}

    def save_signal_history(self):
        """Save signal history to file"""
        try:
            with open(self.signal_history_file, 'w') as f:
                json.dump(self.signal_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving signal history: {str(e)}")

    def load_active_signals(self) -> Dict:
        """Load active signals from file"""
        try:
            if os.path.exists(self.signals_file):
                with open(self.signals_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading signals: {str(e)}")
            return {}

    def save_active_signals(self):
        """Save active signals to file"""
        try:
            with open(self.signals_file, 'w') as f:
                json.dump(self.active_signals, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving signals: {str(e)}")

    def should_update_signal(self, symbol: str, new_signal: Dict) -> bool:
        """Check if signal should be updated based on hold period and confirmation"""
        current_time = datetime.now()

        # Get existing signal
        existing_signal = self.active_signals.get(symbol)

        if not existing_signal:
            # No existing signal, check confidence threshold
            return new_signal.get('confidence', 0) >= self.confidence_threshold

        # Check minimum hold period
        last_update = datetime.fromisoformat(existing_signal['last_updated'])
        hours_since_update = (current_time - last_update).total_seconds() / 3600

        if hours_since_update < self.min_hold_period_hours:
            logger.info(f"Signal for {symbol} still in hold period ({hours_since_update:.1f}h < {self.min_hold_period_hours}h)")
            return False

        # Check if new signal differs significantly
        score_change = abs(new_signal.get('score', 0) - existing_signal.get('score', 0))
        prediction_change = abs(new_signal.get('predicted_gain', 0) - existing_signal.get('predicted_gain', 0))

        # Only update if significant change AND high confidence
        significant_change = score_change > 15 or prediction_change > 5
        high_confidence = new_signal.get('confidence', 0) >= self.confidence_threshold

        return significant_change and high_confidence

    def confirm_signal(self, symbol: str, signal_data: Dict) -> bool:
        """Add signal confirmation and check if enough confirmations exist"""
        current_time = datetime.now()

        # Initialize confirmation tracking if not exists
        if symbol not in self.active_signals:
            self.active_signals[symbol] = {
                'confirmations': [],
                'confirmed_signal': None,
                'last_updated': current_time.isoformat()
            }

        signal_info = self.active_signals[symbol]

        # Add new confirmation
        confirmation = {
            'timestamp': current_time.isoformat(),
            'score': signal_data.get('score', 0),
            'predicted_gain': signal_data.get('predicted_gain', 0),
            'confidence': signal_data.get('confidence', 0)
        }

        signal_info['confirmations'].append(confirmation)

        # Keep only recent confirmations (last 3 days)
        cutoff_time = current_time - timedelta(days=3)
        signal_info['confirmations'] = [
            conf for conf in signal_info['confirmations']
            if datetime.fromisoformat(conf['timestamp']) > cutoff_time
        ]

        # Check if we have enough confirmations
        recent_confirmations = [
            conf for conf in signal_info['confirmations']
            if datetime.fromisoformat(conf['timestamp']) > current_time - timedelta(hours=6)
        ]

        if len(recent_confirmations) >= self.confirmation_threshold:
            # Calculate average of confirmations
            avg_score = sum(conf['score'] for conf in recent_confirmations) / len(recent_confirmations)
            avg_prediction = sum(conf['predicted_gain'] for conf in recent_confirmations) / len(recent_confirmations)
            avg_confidence = sum(conf['confidence'] for conf in recent_confirmations) / len(recent_confirmations)

            # Update confirmed signal
            signal_info['confirmed_signal'] = {
                'symbol': symbol,
                'score': avg_score,
                'predicted_gain': avg_prediction,
                'confidence': avg_confidence,
                'confirmation_count': len(recent_confirmations),
                'confirmed_at': current_time.isoformat(),
                **signal_data  # Include other signal data
            }

            signal_info['last_updated'] = current_time.isoformat()
            self.save_active_signals()

            logger.info(f"Signal confirmed for {symbol} with {len(recent_confirmations)} confirmations")
            return True

        self.save_active_signals()
        logger.info(f"Signal for {symbol} needs more confirmations ({len(recent_confirmations)}/{self.confirmation_threshold})")
        return False

    def get_confirmed_signals(self) -> List[Dict]:
        """Get all confirmed signals that meet criteria"""
        confirmed_signals = []

        for symbol, signal_info in self.active_signals.items():
            confirmed_signal = signal_info.get('confirmed_signal')

            if confirmed_signal and confirmed_signal.get('confidence', 0) >= self.confidence_threshold:
                confirmed_signals.append(confirmed_signal)

        # Sort by confidence and score
        confirmed_signals.sort(
            key=lambda x: (x.get('confidence', 0), x.get('score', 0)),
            reverse=True
        )

        return confirmed_signals

    def filter_trading_signals(self, stocks: List[Dict]) -> List[Dict]:
        """
        Filter trading signals based on:
        1. Minimum hold period (reduced to 1 hour for better responsiveness)
        2. Signal strength consistency
        3. Volatility thresholds
        """
        if not stocks:
            return []

        try:
            filtered_signals = []
            current_time = datetime.now()

            for stock in stocks:
                symbol = stock.get('symbol', '')
                score = stock.get('score', 0)

                # More lenient filtering for better user experience
                should_include = True

                # Check if signal exists in history
                if symbol in self.signal_history:
                    last_signal = self.signal_history[symbol]
                    last_time = datetime.fromisoformat(last_signal['timestamp'])
                    hours_since = (current_time - last_time).total_seconds() / 3600

                    # Reduced hold period to 1 hour for better responsiveness
                    if hours_since < 1.0:
                        logger.info(f"Signal for {symbol} still in hold period ({hours_since:.1f}h < 1h)")
                        should_include = False

                    # More lenient consistency check - only filter if score drops significantly
                    score_change = score - last_signal['score']
                    if score_change < -20:  # Only filter if score drops by more than 20 points
                        logger.info(f"Signal for {symbol} score dropped significantly: {score_change}")
                        should_include = False

                # More lenient volatility filter
                volatility = stock.get('technical', {}).get('atr_volatility_pct', 0)
                if volatility > 8.0:  # Increased threshold from 5% to 8%
                    logger.info(f"Signal for {symbol} too volatile: {volatility}% > 8%")
                    should_include = False

                # Include high-score stocks regardless of other filters
                if score >= 80:
                    should_include = True
                    logger.info(f"Including high-score stock {symbol} (score: {score})")

                if should_include:
                    filtered_signals.append(stock)

                    # Update signal history
                    self.signal_history[symbol] = {
                        'timestamp': current_time.isoformat(),
                        'score': score,
                        'volatility': volatility
                    }

            # If no signals pass filtering, return top 3 stocks to ensure data is shown
            if not filtered_signals and stocks:
                logger.warning("No signals passed filtering, returning top 3 stocks")
                top_stocks = sorted(stocks, key=lambda x: x.get('score', 0), reverse=True)[:3]
                for stock in top_stocks:
                    symbol = stock.get('symbol', '')
                    self.signal_history[symbol] = {
                        'timestamp': current_time.isoformat(),
                        'score': stock.get('score', 0),
                        'volatility': stock.get('technical', {}).get('atr_volatility_pct', 0)
                    }
                filtered_signals = top_stocks

            # Save updated history
            self.save_signal_history()

            logger.info(f"Signal filtering: {len(stocks)} input → {len(filtered_signals)} filtered")
            return filtered_signals

        except Exception as e:
            logger.error(f"Error in signal filtering: {str(e)}")
            # Return top 5 stocks if filtering fails
            if stocks:
                top_stocks = sorted(stocks, key=lambda x: x.get('score', 0), reverse=True)[:5]
                return top_stocks
            return stocks

    def get_signal_status(self) -> Dict:
        """Get status of all signals for monitoring"""
        status = {
            'total_symbols': len(self.active_signals),
            'confirmed_signals': len([s for s in self.active_signals.values() if s.get('confirmed_signal')]),
            'pending_confirmations': len([s for s in self.active_signals.values() if not s.get('confirmed_signal')]),
            'high_confidence_signals': len([
                s for s in self.active_signals.values() 
                if s.get('confirmed_signal', {}).get('confidence', 0) >= self.confidence_threshold
            ])
        }
        return status