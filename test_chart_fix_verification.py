
#!/usr/bin/env python3
"""
Chart Fix Verification Test
Tests to ensure the interactive prediction tracker charts display data properly
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_chart_data_fix():
    """Test that chart data is properly structured and displays"""
    print("🔧 Testing Chart Data Fix Verification")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Check interactive tracker data API
    print("\n📊 Testing Interactive Tracker Data API...")
    
    try:
        response = requests.get(f"{base_url}/api/interactive-tracker-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working - Status: {data.get('status')}")
            
            tracking_data = data.get('tracking_data', {})
            if tracking_data:
                print(f"   📈 Found {len(tracking_data)} tracked stocks")
                
                # Check first stock data structure
                sample_symbol = list(tracking_data.keys())[0]
                sample_data = tracking_data[sample_symbol]
                
                print(f"   📊 Sample data for {sample_symbol}:")
                
                # Validate 5D data
                predicted_5d = sample_data.get('predicted_5d', [])
                actual_5d = sample_data.get('actual_progress_5d', [])
                
                print(f"      5D Predicted: {len(predicted_5d)} points - {predicted_5d[:3] if predicted_5d else 'None'}")
                print(f"      5D Actual: {len(actual_5d)} points - {actual_5d[:3] if actual_5d else 'None'}")
                
                # Validate 30D data
                predicted_30d = sample_data.get('predicted_30d', [])
                actual_30d = sample_data.get('actual_progress_30d', [])
                
                print(f"      30D Predicted: {len(predicted_30d)} points - {predicted_30d[:3] if predicted_30d else 'None'}")
                print(f"      30D Actual: {len(actual_30d)} points - {actual_30d[:3] if actual_30d else 'None'}")
                
                # Check data validation
                valid_5d = len([x for x in predicted_5d if x is not None and not (isinstance(x, float) and x != x)])
                valid_30d = len([x for x in predicted_30d if x is not None and not (isinstance(x, float) and x != x)])
                
                print(f"✅ Valid prediction data: {valid_5d}/5 for 5D, {valid_30d}/30 for 30D")
                
                if len(predicted_5d) == 5 and len(predicted_30d) == 30 and valid_5d >= 5 and valid_30d >= 30:
                    print("✅ Chart data structure is correct")
                    return True
                else:
                    print("❌ Chart data structure has issues")
                    return False
            else:
                print("❌ No tracking data found")
                return False
        else:
            print(f"❌ API failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        return False

def test_predictions_tracker_api():
    """Test predictions tracker API"""
    print("\n📋 Testing Predictions Tracker API...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/api/predictions-tracker", timeout=10)
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"✅ Predictions API working - {len(predictions)} predictions")
            
            if predictions:
                sample_pred = predictions[0]
                required_fields = ['symbol', 'current_price', 'pred_5d', 'predicted_1mo']
                missing_fields = [field for field in required_fields if field not in sample_pred]
                
                if not missing_fields:
                    print("✅ Prediction data structure valid")
                    return True
                else:
                    print(f"❌ Missing fields: {missing_fields}")
                    return False
            else:
                print("⚠️ No predictions found")
                return True
        else:
            print(f"❌ Predictions API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Predictions API error: {str(e)}")
        return False

def test_interactive_page():
    """Test that interactive tracker page loads"""
    print("\n🌐 Testing Interactive Tracker Page...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/prediction-tracker-interactive", timeout=10)
        if response.status_code == 200:
            print("✅ Interactive tracker page accessible")
            
            content = response.text
            
            # Check for Chart.js
            if 'chart.js' in content.lower():
                print("✅ Chart.js library included")
            else:
                print("❌ Chart.js library not found")
                return False
                
            # Check for key functions
            key_functions = ['updateChart', 'switchView', 'selectStock', 'loadPredictionData']
            missing_functions = []
            
            for func in key_functions:
                if func not in content:
                    missing_functions.append(func)
                    
            if missing_functions:
                print(f"❌ Missing JavaScript functions: {missing_functions}")
                return False
            else:
                print("✅ All key JavaScript functions present")
                return True
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Page error: {str(e)}")
        return False

def main():
    """Run all chart fix verification tests"""
    print("🧪 Chart Fix Verification Test Suite")
    print("=" * 60)
    
    tests = [
        ("Interactive Tracker Data API", test_chart_data_fix),
        ("Predictions Tracker API", test_predictions_tracker_api),
        ("Interactive Tracker Page", test_interactive_page)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL CHART FIX VERIFICATION TESTS PASSED!")
        print("✅ Interactive prediction tracker charts should now display data properly")
        print("📊 Charts will show:")
        print("   • Green line: Original predictions (straight line)")
        print("   • Blue line: Actual market progress (progressive)")
        print("   • Red line: Updated predictions (incremental changes)")
        return True
    else:
        print("❌ SOME CHART FIX VERIFICATION TESTS FAILED!")
        print("📋 Check the errors above and fix the identified issues")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    else:
        print("\n✅ All tests passed - Charts should display data correctly!")
