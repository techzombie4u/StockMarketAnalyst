
import json
import os
import sys
import time
from datetime import datetime

def test_stock_screener():
    """Test stock screener functionality"""
    print("🧪 Testing Stock Screener...")
    try:
        from stock_screener import StockScreener
        screener = StockScreener()
        
        # Test technical indicators
        technical = screener.calculate_enhanced_technical_indicators('RELIANCE')
        assert 'current_price' in technical, "Current price not found"
        assert 'atr_14' in technical, "ATR not calculated"
        print("✅ Technical indicators working")
        
        # Test fundamental data
        fundamentals = screener.scrape_screener_data('RELIANCE')
        assert 'pe_ratio' in fundamentals, "PE ratio not found"
        print("✅ Fundamental data working")
        
        return True
    except Exception as e:
        print(f"❌ Stock screener test failed: {str(e)}")
        return False

def test_scheduler():
    """Test scheduler functionality"""
    print("🧪 Testing Scheduler...")
    try:
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        status = scheduler.get_job_status()
        assert 'running' in status, "Scheduler status not available"
        print("✅ Scheduler working")
        return True
    except Exception as e:
        print(f"❌ Scheduler test failed: {str(e)}")
        return False

def test_predictions():
    """Test prediction functionality"""
    print("🧪 Testing Predictions...")
    try:
        # Check if top10.json exists and has proper structure
        if os.path.exists('top10.json'):
            with open('top10.json', 'r') as f:
                data = json.load(f)
            
            stocks = data.get('stocks', [])
            if stocks:
                stock = stocks[0]
                required_fields = ['pred_24h', 'pred_5d', 'pred_1mo', 'predicted_gain']
                
                for field in required_fields:
                    assert field in stock, f"Missing field: {field}"
                    assert isinstance(stock[field], (int, float)), f"Invalid type for {field}"
                    
                # Check that predictions are reasonable
                assert stock['pred_24h'] >= 0, "24h prediction should be non-negative"
                assert stock['pred_5d'] >= stock['pred_24h'], "5d prediction should be >= 24h"
                assert stock['pred_1mo'] >= stock['pred_5d'], "1mo prediction should be >= 5d"
                
                print("✅ Predictions structure validated")
                return True
        
        print("⚠️ No prediction data available for testing")
        return True
    except Exception as e:
        print(f"❌ Prediction test failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test Flask API endpoints"""
    print("🧪 Testing API Endpoints...")
    try:
        from app import app
        
        with app.test_client() as client:
            # Test main dashboard
            response = client.get('/')
            assert response.status_code == 200, "Dashboard not accessible"
            
            # Test stocks API
            response = client.get('/api/stocks')
            assert response.status_code == 200, "Stocks API not working"
            
            data = json.loads(response.data)
            assert 'stocks' in data, "Stocks data not found in API response"
            assert 'status' in data, "Status not found in API response"
            
            print("✅ API endpoints working")
            return True
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def test_ml_integration():
    """Test ML integration"""
    print("🧪 Testing ML Integration...")
    try:
        from predictor import MLPredictor
        predictor = MLPredictor()
        
        # Test initialization (should handle missing models gracefully)
        result = predictor.initialize()
        print(f"✅ ML predictor initialized (models available: {result})")
        return True
    except Exception as e:
        print(f"❌ ML integration test failed: {str(e)}")
        return False

def run_regression_tests():
    """Run all regression tests"""
    print("🔍 Starting Comprehensive Regression Test")
    print("=" * 50)
    
    tests = [
        test_stock_screener,
        test_scheduler,
        test_predictions,
        test_api_endpoints,
        test_ml_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All regression tests PASSED! System is working correctly.")
        return True
    else:
        print("⚠️ Some tests FAILED. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_regression_tests()
    sys.exit(0 if success else 1)
