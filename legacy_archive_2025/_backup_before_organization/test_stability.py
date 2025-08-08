
"""
Testing Framework for Stock Market Analyst
Focus on prediction stability and signal confirmation
"""

import unittest
import json
import os
from datetime import datetime, timedelta
from src.managers.signal_manager import SignalManager
from src.analyzers.stock_screener import StockScreener

class TestPredictionStability(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.signal_manager = SignalManager()
        self.test_signals_file = 'test_signals.json'
        
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_signals_file):
            os.remove(self.test_signals_file)
    
    def test_signal_confirmation_threshold(self):
        """Test that signals require proper confirmation"""
        test_signal = {
            'symbol': 'TEST',
            'score': 85,
            'confidence': 90,
            'predicted_gain': 15
        }
        
        # First signal should not be confirmed immediately
        confirmed = self.signal_manager.confirm_signal('TEST', test_signal)
        self.assertFalse(confirmed, "Signal should not be confirmed on first attempt")
        
        # Add more confirmations
        for i in range(3):
            confirmed = self.signal_manager.confirm_signal('TEST', test_signal)
        
        self.assertTrue(confirmed, "Signal should be confirmed after multiple attempts")
    
    def test_minimum_hold_period(self):
        """Test minimum hold period enforcement"""
        test_signal = {
            'symbol': 'HOLD_TEST',
            'score': 85,
            'confidence': 90,
            'predicted_gain': 15
        }
        
        # Confirm initial signal
        for i in range(3):
            self.signal_manager.confirm_signal('HOLD_TEST', test_signal)
        
        # Try to update immediately - should be blocked
        new_signal = {
            'symbol': 'HOLD_TEST',
            'score': 70,
            'confidence': 85,
            'predicted_gain': 10
        }
        
        should_update = self.signal_manager.should_update_signal('HOLD_TEST', new_signal)
        self.assertFalse(should_update, "Signal should not update during hold period")
    
    def test_confidence_filtering(self):
        """Test confidence-based filtering"""
        low_confidence_signal = {
            'symbol': 'LOW_CONF',
            'score': 85,
            'confidence': 60,  # Below threshold
            'predicted_gain': 15
        }
        
        high_confidence_signal = {
            'symbol': 'HIGH_CONF',
            'score': 85,
            'confidence': 90,  # Above threshold
            'predicted_gain': 15
        }
        
        # Low confidence should be rejected
        should_update_low = self.signal_manager.should_update_signal('LOW_CONF', low_confidence_signal)
        self.assertFalse(should_update_low, "Low confidence signal should be rejected")
        
        # High confidence should be accepted
        should_update_high = self.signal_manager.should_update_signal('HIGH_CONF', high_confidence_signal)
        self.assertTrue(should_update_high, "High confidence signal should be accepted")
    
    def test_signal_stability_over_time(self):
        """Test that signals remain stable over time"""
        # This test would be expanded with historical data
        pass

class TestDataQuality(unittest.TestCase):
    
    def setUp(self):
        self.screener = StockScreener()
    
    def test_basic_screener_functionality(self):
        """Test basic screener functionality"""
        # Test with a known stock
        technical = self.screener.calculate_enhanced_technical_indicators('RELIANCE')
        self.assertIsInstance(technical, dict, "Technical indicators should return dict")
        
        fundamentals = self.screener.scrape_screener_data('RELIANCE')
        self.assertIsInstance(fundamentals, dict, "Fundamentals should return dict")
    
    def test_confidence_calculation(self):
        """Test confidence calculation logic"""
        # This would test the confidence scoring mechanism
        pass

def run_stability_tests():
    """Run all stability tests"""
    print("🧪 Running Prediction Stability Tests...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTest(unittest.makeSuite(TestPredictionStability))
    suite.addTest(unittest.makeSuite(TestDataQuality))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Report results
    if result.wasSuccessful():
        print("✅ All stability tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False

if __name__ == "__main__":
    run_stability_tests()
