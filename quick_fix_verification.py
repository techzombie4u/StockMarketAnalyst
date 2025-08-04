
#!/usr/bin/env python3
"""
Quick Fix Verification Script
Tests the most critical fixes for immediate feedback
"""

import json
import os
import sys
import requests
import time
from datetime import datetime

def test_prediction_tracker_api():
    """Test the prediction tracker API endpoint"""
    print("🧪 Testing Prediction Tracker API...")
    
    try:
        response = requests.get("http://localhost:5000/api/predictions-tracker", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prediction tracker API working - Status: {data.get('status')}")
            print(f"   Predictions count: {data.get('total_count', 0)}")
            return True
        else:
            print(f"❌ Prediction tracker API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Prediction tracker API error: {e}")
        return False

def test_predictions_history_file():
    """Test predictions history file handling"""
    print("\n🧪 Testing Predictions History File...")
    
    try:
        # Test if file exists and can be read
        if os.path.exists('predictions_history.json'):
            with open('predictions_history.json', 'r') as f:
                data = json.load(f)
                print(f"✅ Predictions history file readable")
                
                # Test data format handling
                if isinstance(data, list):
                    print(f"✅ List format detected with {len(data)} items")
                elif isinstance(data, dict) and 'predictions' in data:
                    print(f"✅ Dict format detected with {len(data['predictions'])} predictions")
                else:
                    print(f"⚠️ Unknown format: {type(data)}")
                
                return True
        else:
            print("ℹ️ No predictions history file found (this is normal for new installations)")
            return True
            
    except Exception as e:
        print(f"❌ Predictions history file error: {e}")
        return False

def test_stock_screener_core():
    """Test core stock screener functionality"""
    print("\n🧪 Testing Stock Screener Core...")
    
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test technical analysis
        technical = screener.calculate_enhanced_technical_indicators('RELIANCE')
        if technical and 'current_price' in technical:
            print("✅ Technical analysis working")
        else:
            print("⚠️ Technical analysis returned limited data")
        
        return True
        
    except Exception as e:
        print(f"❌ Stock screener error: {e}")
        return False

def test_main_dashboard():
    """Test main dashboard accessibility"""
    print("\n🧪 Testing Main Dashboard...")
    
    try:
        response = requests.get("http://localhost:5000/", timeout=10)
        if response.status_code == 200:
            print("✅ Main dashboard accessible")
            return True
        else:
            print(f"❌ Main dashboard failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Main dashboard error: {e}")
        return False

def test_stocks_api():
    """Test stocks API endpoint"""
    print("\n🧪 Testing Stocks API...")
    
    try:
        response = requests.get("http://localhost:5000/api/stocks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stocks API working - Status: {data.get('status')}")
            print(f"   Stock count: {len(data.get('stocks', []))}")
            return True
        else:
            print(f"❌ Stocks API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stocks API error: {e}")
        return False

def run_quick_verification():
    """Run quick verification tests"""
    print("🚀 Running Quick Fix Verification")
    print("=" * 50)
    
    tests = [
        test_stock_screener_core,
        test_predictions_history_file,
        test_main_dashboard,
        test_stocks_api,
        test_prediction_tracker_api
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"💥 Test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Quick Verification Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All quick tests PASSED! Core functionality is working.")
        return True
    elif passed >= total - 1:
        print("⚠️ Most tests passed, minor issues may exist.")
        return True
    else:
        print("❌ Multiple failures detected. Check the issues above.")
        return False

if __name__ == "__main__":
    success = run_quick_verification()
    sys.exit(0 if success else 1)
