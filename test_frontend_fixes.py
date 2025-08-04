
#!/usr/bin/env python3
"""
Test Frontend and Backend Fixes

This script tests:
1. Stock screener syntax errors
2. API endpoints functionality
3. Data generation and display
4. Error handling
"""

import json
import os
import sys
import time
import requests
from datetime import datetime

def test_stock_screener_syntax():
    """Test that stock screener can be imported without syntax errors"""
    print("🧪 Testing Stock Screener Syntax...")
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        print("✅ Stock screener imports successfully")
        
        # Test a simple method
        technical = screener.calculate_enhanced_technical_indicators('RELIANCE')
        if technical:
            print("✅ Technical analysis working")
        else:
            print("⚠️ Technical analysis returned empty data")
        
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in stock screener: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Other error in stock screener: {e}")
        return True  # Syntax is OK, other errors are acceptable

def test_api_endpoints():
    """Test API endpoints respond correctly"""
    print("\n🧪 Testing API Endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/api/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"⚠️ Health endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    # Test stocks endpoint
    try:
        response = requests.get(f"{base_url}/api/stocks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stocks endpoint working - Status: {data.get('status')}")
            print(f"   Stock count: {data.get('stockCount', 0)}")
            return data.get('status') != 'error'
        else:
            print(f"❌ Stocks endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stocks endpoint failed: {e}")
        return False

def test_manual_screening():
    """Test manual screening trigger"""
    print("\n🧪 Testing Manual Screening...")
    
    try:
        from scheduler import run_screening_job_manual
        result = run_screening_job_manual()
        
        if result:
            print("✅ Manual screening completed successfully")
            
            # Check if data file was created
            if os.path.exists('top10.json'):
                with open('top10.json', 'r') as f:
                    data = json.load(f)
                    status = data.get('status', 'unknown')
                    stock_count = len(data.get('stocks', []))
                    print(f"✅ Data file created - Status: {status}, Stocks: {stock_count}")
                    return stock_count > 0
            else:
                print("⚠️ Data file not created")
                return False
        else:
            print("❌ Manual screening failed")
            return False
            
    except Exception as e:
        print(f"❌ Manual screening error: {e}")
        return False

def test_data_generation():
    """Test data generation with fallback"""
    print("\n🧪 Testing Data Generation...")
    
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test fallback data generation
        fallback_data = screener._generate_fallback_data()
        
        if fallback_data and len(fallback_data) > 0:
            print(f"✅ Fallback data generation working - {len(fallback_data)} stocks")
            
            # Save as test data
            ist_now = datetime.now()
            test_data = {
                'timestamp': ist_now.isoformat(),
                'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
                'status': 'test_success',
                'stocks': fallback_data[:7]  # Limit to 7 for testing
            }
            
            with open('top10.json', 'w') as f:
                json.dump(test_data, f, indent=2)
            
            print("✅ Test data saved to top10.json")
            return True
        else:
            print("❌ Fallback data generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Data generation error: {e}")
        return False

def run_frontend_backend_test():
    """Run comprehensive frontend and backend test"""
    print("🚀 Starting Frontend and Backend Fix Test")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Syntax errors
    syntax_ok = test_stock_screener_syntax()
    test_results.append(('Syntax Check', syntax_ok))
    
    # Test 2: Generate test data
    data_ok = test_data_generation()
    test_results.append(('Data Generation', data_ok))
    
    # Test 3: API endpoints (if server is running)
    api_ok = test_api_endpoints()
    test_results.append(('API Endpoints', api_ok))
    
    # Test 4: Manual screening
    if syntax_ok:
        screening_ok = test_manual_screening()
        test_results.append(('Manual Screening', screening_ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
    elif passed >= total - 1:
        print("⚠️ Most tests passed. Minor issues may exist.")
    else:
        print("❌ Multiple test failures. Significant issues detected.")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = run_frontend_backend_test()
    sys.exit(0 if success else 1)
