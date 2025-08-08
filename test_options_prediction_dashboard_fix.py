
#!/usr/bin/env python3
"""
Test Options Prediction Dashboard Fixes
Validates all the fixes applied to resolve 404 and 500 errors
"""

import os
import json
import requests
import time
from datetime import datetime

def test_file_existence():
    """Test that required files exist"""
    print("🔍 Testing File Existence...")
    
    required_files = [
        'data/tracking/options_tracking.json',
        'data/tracking/interactive_tracking.json'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    print(f"   📊 Contains {len(data) if isinstance(data, (list, dict)) else 'unknown'} entries")
            except json.JSONDecodeError:
                print(f"   ❌ Invalid JSON in {file_path}")
                return False
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_smartgoagent_methods():
    """Test SmartGoAgent methods directly"""
    print("\n🧪 Testing SmartGoAgent Methods...")
    
    try:
        from src.analyzers.smart_go_agent import SmartGoAgent
        agent = SmartGoAgent()
        
        # Test get_active_options_predictions
        print("   Testing get_active_options_predictions...")
        active_predictions = agent.get_active_options_predictions()
        if isinstance(active_predictions, list):
            print(f"   ✅ Returns list with {len(active_predictions)} predictions")
        else:
            print(f"   ❌ Expected list, got {type(active_predictions)}")
            return False
        
        # Test get_prediction_accuracy_summary
        print("   Testing get_prediction_accuracy_summary...")
        summary = agent.get_prediction_accuracy_summary()
        if isinstance(summary, dict):
            print(f"   ✅ Returns dict with {len(summary)} timeframes")
            for timeframe, data in summary.items():
                if not isinstance(data, dict) or 'accuracy' not in data:
                    print(f"   ❌ Invalid structure for {timeframe}")
                    return False
        else:
            print(f"   ❌ Expected dict, got {type(summary)}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ SmartGoAgent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Test API endpoint"""
    print("\n📡 Testing API Endpoint...")
    
    try:
        response = requests.get('http://localhost:5000/api/options-prediction-dashboard', timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ API returns 200 OK")
            
            # Validate response structure
            required_keys = ['live_trades', 'summary_stats', 'timestamp']
            for key in required_keys:
                if key in data:
                    print(f"   ✅ Contains '{key}'")
                else:
                    print(f"   ❌ Missing '{key}'")
                    return False
            
            # Validate data types
            if isinstance(data.get('live_trades'), list):
                print(f"   ✅ live_trades is list with {len(data['live_trades'])} entries")
            else:
                print(f"   ❌ live_trades should be list, got {type(data.get('live_trades'))}")
                return False
            
            if isinstance(data.get('summary_stats'), dict):
                print(f"   ✅ summary_stats is dict with {len(data['summary_stats'])} entries")
            else:
                print(f"   ❌ summary_stats should be dict, got {type(data.get('summary_stats'))}")
                return False
            
            return True
            
        else:
            print(f"   ❌ API returned {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Could not connect to server (is it running?)")
        return False
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False

def test_options_tracking_file():
    """Test the options_tracking.json file specifically"""
    print("\n📋 Testing options_tracking.json...")
    
    tracking_file = '/options_tracking.json'
    try:
        response = requests.get(f'http://localhost:5000{tracking_file}', timeout=10)
        if response.status_code == 200:
            print("   ✅ options_tracking.json is accessible")
            return True
        elif response.status_code == 404:
            print("   ❌ options_tracking.json returns 404 (should be fixed)")
            return False
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing options_tracking.json: {e}")
        return False

def main():
    """Run all tests"""
    print("🔧 OPTIONS PREDICTION DASHBOARD FIX TEST")
    print("=" * 50)
    
    tests = [
        ("File Existence", test_file_existence),
        ("SmartGoAgent Methods", test_smartgoagent_methods),
        ("API Endpoint", test_api_endpoint),
        ("Options Tracking File", test_options_tracking_file)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FIXES SUCCESSFUL - DASHBOARD SHOULD WORK!")
        return True
    else:
        print("⚠️ Some issues remain - check individual test results")
        return False

if __name__ == "__main__":
    main()
