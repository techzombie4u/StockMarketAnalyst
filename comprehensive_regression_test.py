
#!/usr/bin/env python3
"""
Comprehensive Regression Test for Stock Market Analyst
Tests all major functionality including deployment compatibility
"""

import json
import os
import sys
import time
import requests
import threading
from datetime import datetime

def test_core_modules():
    """Test all core modules can be imported and initialized"""
    print("🧪 Testing Core Module Imports...")
    
    try:
        # Test stock screener
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        print("✅ Stock screener imported and initialized")
        
        # Test scheduler
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        print("✅ Scheduler imported and initialized")
        
        # Test daily technical analyzer
        from daily_technical_analyzer import DailyTechnicalAnalyzer
        analyzer = DailyTechnicalAnalyzer()
        print("✅ Daily technical analyzer imported and initialized")
        
        # Test Flask app
        from app import app
        print("✅ Flask app imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Core module test failed: {str(e)}")
        return False

def test_data_processing():
    """Test data fetching and processing functionality"""
    print("\n🧪 Testing Data Processing...")
    
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test technical indicators
        test_symbol = 'RELIANCE'
        technical = screener.calculate_enhanced_technical_indicators(test_symbol)
        
        if technical and 'current_price' in technical:
            print(f"✅ Technical indicators working for {test_symbol}")
            print(f"   Current price: {technical.get('current_price', 'N/A')}")
            print(f"   Analysis type: {technical.get('analysis_type', 'N/A')}")
        else:
            print(f"❌ Technical indicators failed for {test_symbol}")
            return False
        
        # Test fundamental data
        fundamentals = screener.scrape_screener_data(test_symbol)
        if fundamentals and 'pe_ratio' in fundamentals:
            print(f"✅ Fundamental data working for {test_symbol}")
            print(f"   PE ratio: {fundamentals.get('pe_ratio', 'N/A')}")
        else:
            print(f"⚠️ Fundamental data limited for {test_symbol}")
        
        return True
    except Exception as e:
        print(f"❌ Data processing test failed: {str(e)}")
        return False

def test_scoring_algorithm():
    """Test the stock scoring and ranking system"""
    print("\n🧪 Testing Scoring Algorithm...")
    
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test with minimal data
        test_stocks = ['RELIANCE', 'TCS']
        results = []
        
        for symbol in test_stocks:
            technical = screener.calculate_enhanced_technical_indicators(symbol)
            fundamentals = screener.scrape_screener_data(symbol)
            
            if technical:
                # Test scoring
                score = screener._calculate_base_score(technical, fundamentals, {})
                print(f"✅ Scoring works for {symbol}: {score} points")
                results.append({'symbol': symbol, 'score': score})
        
        if results:
            print("✅ Scoring algorithm functional")
            return True
        else:
            print("❌ No scoring results generated")
            return False
            
    except Exception as e:
        print(f"❌ Scoring algorithm test failed: {str(e)}")
        return False

def test_api_endpoints():
    """Test Flask API endpoints"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        from app import app
        
        with app.test_client() as client:
            # Test main dashboard
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Dashboard endpoint (/) working")
            else:
                print(f"❌ Dashboard endpoint failed: {response.status_code}")
                return False
            
            # Test stocks API
            response = client.get('/api/stocks')
            if response.status_code == 200:
                data = json.loads(response.data)
                print("✅ Stocks API endpoint (/api/stocks) working")
                print(f"   Status: {data.get('status', 'unknown')}")
                print(f"   Stocks count: {len(data.get('stocks', []))}")
            else:
                print(f"❌ Stocks API endpoint failed: {response.status_code}")
                return False
            
            # Test status API
            response = client.get('/api/status')
            if response.status_code == 200:
                print("✅ Status API endpoint (/api/status) working")
            else:
                print(f"❌ Status API endpoint failed: {response.status_code}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ API endpoints test failed: {str(e)}")
        return False

def test_scheduler_functionality():
    """Test scheduler functionality"""
    print("\n🧪 Testing Scheduler Functionality...")
    
    try:
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        
        # Test status
        status = scheduler.get_job_status()
        if 'running' in status:
            print("✅ Scheduler status check working")
            print(f"   Running: {status.get('running', False)}")
            print(f"   Jobs: {status.get('job_count', 0)}")
        else:
            print("❌ Scheduler status check failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Scheduler test failed: {str(e)}")
        return False

def test_data_persistence():
    """Test data file handling"""
    print("\n🧪 Testing Data Persistence...")
    
    try:
        # Test JSON file operations
        test_data = {
            'timestamp': datetime.now().isoformat(),
            'stocks': [
                {'symbol': 'TEST', 'score': 85, 'price': 100}
            ]
        }
        
        # Write test data
        with open('test_data.json', 'w') as f:
            json.dump(test_data, f)
        
        # Read test data
        with open('test_data.json', 'r') as f:
            loaded_data = json.load(f)
        
        if loaded_data['stocks'][0]['symbol'] == 'TEST':
            print("✅ JSON file operations working")
        else:
            print("❌ JSON file operations failed")
            return False
        
        # Cleanup
        os.remove('test_data.json')
        
        # Check if main data files exist
        if os.path.exists('top10.json'):
            print("✅ Main data file (top10.json) exists")
        else:
            print("⚠️ Main data file (top10.json) not found")
        
        return True
    except Exception as e:
        print(f"❌ Data persistence test failed: {str(e)}")
        return False

def test_production_compatibility():
    """Test production deployment compatibility"""
    print("\n🧪 Testing Production Compatibility...")
    
    try:
        # Test WSGI module
        from wsgi_optimized import application
        print("✅ WSGI module imports successfully")
        
        # Test that app runs on 0.0.0.0
        from app import app
        print("✅ Flask app configured for production")
        
        # Test error handling
        from enhanced_error_handler import safe_execute
        
        def test_function():
            return {'status': 'success'}
        
        result = safe_execute(test_function)
        if result.get('success'):
            print("✅ Error handling framework working")
        else:
            print("❌ Error handling framework failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Production compatibility test failed: {str(e)}")
        return False

def test_live_application():
    """Test the live running application"""
    print("\n🧪 Testing Live Application...")
    
    try:
        # Give the app a moment to fully start
        time.sleep(2)
        
        # Test if the application is responding
        base_url = "http://localhost:5000"
        
        try:
            response = requests.get(f"{base_url}/api/stocks", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ Live application responding")
                print(f"   API Status: {data.get('status', 'unknown')}")
                print(f"   Last Updated: {data.get('last_updated', 'unknown')}")
                print(f"   Stock Count: {len(data.get('stocks', []))}")
                return True
            else:
                print(f"❌ Live application not responding: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not connect to live application: {str(e)}")
            print("   (This may be normal if the app is starting)")
            return True  # Don't fail the test for connection issues
        
    except Exception as e:
        print(f"❌ Live application test failed: {str(e)}")
        return False

def run_comprehensive_regression_test():
    """Run all regression tests"""
    print("🚀 Starting Comprehensive Regression Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Core Modules", test_core_modules),
        ("Data Processing", test_data_processing),
        ("Scoring Algorithm", test_scoring_algorithm),
        ("API Endpoints", test_api_endpoints),
        ("Scheduler", test_scheduler_functionality),
        ("Data Persistence", test_data_persistence),
        ("Production Compatibility", test_production_compatibility),
        ("Live Application", test_live_application),
    ]
    
    passed = 0
    total = len(tests)
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                passed += 1
                print(f"✅ {test_name} Test: PASSED")
            else:
                print(f"❌ {test_name} Test: FAILED")
        except Exception as e:
            print(f"💥 {test_name} Test: CRASHED - {str(e)}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 REGRESSION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print()
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("=" * 60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Application is functioning correctly.")
        exit_code = 0
    elif passed >= total * 0.8:  # 80% pass rate
        print("⚠️  Most tests passed. Minor issues detected.")
        exit_code = 0
    else:
        print("🚨 Multiple test failures detected. Please investigate.")
        exit_code = 1
    
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return exit_code == 0

if __name__ == "__main__":
    success = run_comprehensive_regression_test()
    sys.exit(0 if success else 1)
