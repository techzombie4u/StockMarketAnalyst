
#!/usr/bin/env python3
"""
Enhanced Test Chart Data Fix - Verify Interactive Prediction Tracker Charts
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_chart_data_functionality():
    """Test chart data functionality end-to-end with enhanced validation"""
    print("🧪 Enhanced Testing Interactive Prediction Tracker Chart Data")
    print("=" * 70)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Check if interactive tracker data API is working
    print("\n📊 Testing Interactive Tracker Data API...")
    
    try:
        response = requests.get(f"{base_url}/api/interactive-tracker-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working - Status: {data.get('status')}")
            
            tracking_data = data.get('tracking_data', {})
            if tracking_data:
                print(f"   📈 Found {len(tracking_data)} tracked stocks")
                
                # Check data structure for first stock
                sample_symbol = list(tracking_data.keys())[0]
                sample_data = tracking_data[sample_symbol]
                
                # Validate required fields
                required_fields = ['predicted_5d', 'predicted_30d', 'actual_progress_5d', 'actual_progress_30d']
                missing_fields = [field for field in required_fields if field not in sample_data]
                
                if missing_fields:
                    print(f"❌ Missing fields in sample data: {missing_fields}")
                    return False
                else:
                    print("✅ All required data fields present")
                    
                # Check data arrays with enhanced validation
                pred_5d = sample_data.get('predicted_5d', [])
                pred_30d = sample_data.get('predicted_30d', [])
                actual_5d = sample_data.get('actual_progress_5d', [])
                actual_30d = sample_data.get('actual_progress_30d', [])
                
                print(f"   📊 Sample data for {sample_symbol}:")
                print(f"      5D Predicted: {len(pred_5d)} points - {pred_5d[:3] if pred_5d else 'None'}")
                print(f"      30D Predicted: {len(pred_30d)} points - {pred_30d[:3] if pred_30d else 'None'}")
                print(f"      5D Actual: {len(actual_5d)} points - {actual_5d[:3] if actual_5d else 'None'}")
                print(f"      30D Actual: {len(actual_30d)} points - {actual_30d[:3] if actual_30d else 'None'}")
                
                # Enhanced validation
                if len(pred_5d) != 5:
                    print(f"❌ 5D predicted array wrong length: {len(pred_5d)} (expected 5)")
                    return False
                if len(pred_30d) != 30:
                    print(f"❌ 30D predicted array wrong length: {len(pred_30d)} (expected 30)")
                    return False
                    
                # Check for numeric data and validate all values
                valid_5d_data = [x for x in pred_5d if x is not None and not (isinstance(x, float) and x != x) and isinstance(x, (int, float))]
                valid_30d_data = [x for x in pred_30d if x is not None and not (isinstance(x, float) and x != x) and isinstance(x, (int, float))]
                
                print(f"      Valid 5D values: {len(valid_5d_data)}/5")
                print(f"      Valid 30D values: {len(valid_30d_data)}/30")
                
                if len(valid_5d_data) == 0:
                    print("❌ No valid 5D prediction data found")
                    return False
                if len(valid_30d_data) == 0:
                    print("❌ No valid 30D prediction data found")
                    return False
                    
                # Check if values are realistic (not all zeros)
                if all(x == 0 for x in valid_5d_data):
                    print("❌ All 5D prediction values are zero")
                    return False
                if all(x == 0 for x in valid_30d_data):
                    print("❌ All 30D prediction values are zero")
                    return False
                    
                print(f"✅ Valid prediction data: {len(valid_5d_data)}/5 for 5D, {len(valid_30d_data)}/30 for 30D")
                
                # Test actual price data
                valid_actual_5d = [x for x in actual_5d if x is not None and isinstance(x, (int, float))]
                valid_actual_30d = [x for x in actual_30d if x is not None and isinstance(x, (int, float))]
                
                print(f"      Valid actual 5D: {len(valid_actual_5d)}")
                print(f"      Valid actual 30D: {len(valid_actual_30d)}")
                
                if len(valid_actual_5d) == 0:
                    print("⚠️ No actual 5D data - this is expected for new predictions")
                if len(valid_actual_30d) == 0:
                    print("⚠️ No actual 30D data - this is expected for new predictions")
                
            else:
                print("❌ No tracking data found")
                return False
                
        else:
            print(f"❌ API failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API error: {str(e)}")
        return False
    
    # Test 2: Validate individual stock data
    print(f"\n🔍 Testing individual stock data for {sample_symbol}...")
    
    try:
        response = requests.get(f"{base_url}/api/debug-chart-data/{sample_symbol}", timeout=10)
        if response.status_code == 200:
            debug_data = response.json()
            print("✅ Debug API working")
            
            validation = debug_data.get('data_validation', {})
            print(f"   📊 Data validation results:")
            print(f"      Predicted 5D length: {validation.get('predicted_5d_length')}")
            print(f"      Predicted 30D length: {validation.get('predicted_30d_length')}")
            print(f"      Valid 5D count: {validation.get('predicted_5d_valid_count')}")
            print(f"      Valid 30D count: {validation.get('predicted_30d_valid_count')}")
            
            if validation.get('predicted_5d_valid_count', 0) == 0:
                print("❌ No valid 5D prediction data in debug response")
                return False
            if validation.get('predicted_30d_valid_count', 0) == 0:
                print("❌ No valid 30D prediction data in debug response")
                return False
                
            print("✅ Individual stock data validation passed")
        else:
            print(f"⚠️ Debug API returned status: {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Debug API error: {str(e)}")
    
    # Test 3: Check page accessibility
    print("\n🌐 Testing Interactive Tracker Page...")
    
    try:
        response = requests.get(f"{base_url}/prediction-tracker-interactive", timeout=10)
        if response.status_code == 200:
            content = response.text
            print("✅ Interactive tracker page accessible")
            
            # Check for Chart.js
            if 'chart.js' in content.lower():
                print("✅ Chart.js library included")
            else:
                print("❌ Chart.js library missing")
                return False
                
            # Check for key JavaScript functions
            key_functions = ['updateChart', 'loadPredictionData', 'generateSampleTrackingData']
            missing_functions = []
            
            for func in key_functions:
                if func not in content:
                    missing_functions.append(func)
                    
            if missing_functions:
                print(f"❌ Missing JavaScript functions: {missing_functions}")
                return False
            else:
                print("✅ All key JavaScript functions present")
                
        else:
            print(f"❌ Page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Page error: {str(e)}")
        return False
    
    print(f"\n{'='*70}")
    print("🎉 ALL ENHANCED CHART DATA TESTS PASSED!")
    print("✅ Interactive prediction tracker charts should now display data properly")
    print("📊 Charts will show:")
    print("   • Green line: Original predictions (straight line)")
    print("   • Blue line: Actual market progress (progressive)")
    print("   • Red line: Updated predictions (incremental changes)")
    print(f"{'='*70}")
    
    return True

if __name__ == "__main__":
    success = test_chart_data_functionality()
    if not success:
        print("\n❌ ENHANCED CHART DATA TESTS FAILED!")
        print("📋 Check the errors above and fix the identified issues")
        sys.exit(1)
    else:
        print("\n✅ All enhanced tests passed - Charts should display data correctly!")
        sys.exit(0)
