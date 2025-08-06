
#!/usr/bin/env python3
"""
Test Chart Data Fix - Verify Interactive Prediction Tracker Charts
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_chart_data_functionality():
    """Test chart data functionality end-to-end"""
    print("🧪 Testing Interactive Prediction Tracker Chart Data")
    print("=" * 60)
    
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
                    
                # Check data arrays
                pred_5d = sample_data.get('predicted_5d', [])
                pred_30d = sample_data.get('predicted_30d', [])
                actual_5d = sample_data.get('actual_progress_5d', [])
                actual_30d = sample_data.get('actual_progress_30d', [])
                
                print(f"   📊 Sample data for {sample_symbol}:")
                print(f"      5D Predicted: {len(pred_5d)} points - {pred_5d[:3] if pred_5d else 'None'}")
                print(f"      30D Predicted: {len(pred_30d)} points - {pred_30d[:3] if pred_30d else 'None'}")
                print(f"      5D Actual: {len(actual_5d)} points - {actual_5d[:3] if actual_5d else 'None'}")
                print(f"      30D Actual: {len(actual_30d)} points - {actual_30d[:3] if actual_30d else 'None'}")
                
                # Validate array lengths
                if len(pred_5d) != 5:
                    print(f"❌ 5D predicted array wrong length: {len(pred_5d)} (expected 5)")
                    return False
                if len(pred_30d) != 30:
                    print(f"❌ 30D predicted array wrong length: {len(pred_30d)} (expected 30)")
                    return False
                    
                # Check for numeric data
                valid_5d_data = [x for x in pred_5d if x is not None and not (isinstance(x, float) and x != x)]  # NaN check
                valid_30d_data = [x for x in pred_30d if x is not None and not (isinstance(x, float) and x != x)]
                
                if len(valid_5d_data) == 0:
                    print("❌ No valid 5D prediction data found")
                    return False
                if len(valid_30d_data) == 0:
                    print("❌ No valid 30D prediction data found")
                    return False
                    
                print(f"✅ Valid prediction data: {len(valid_5d_data)}/5 for 5D, {len(valid_30d_data)}/30 for 30D")
                
            else:
                print("❌ No tracking data found")
                return False
                
        else:
            print(f"❌ API failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API error: {str(e)}")
        return False
    
    # Test 2: Check predictions tracker API
    print("\n📋 Testing Predictions Tracker API...")
    
    try:
        response = requests.get(f"{base_url}/api/predictions-tracker", timeout=10)
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            print(f"✅ Predictions API working - {len(predictions)} predictions")
            
            if predictions:
                sample_pred = predictions[0]
                required_pred_fields = ['symbol', 'current_price', 'pred_5d']
                missing_pred_fields = [field for field in required_pred_fields if field not in sample_pred]
                
                if missing_pred_fields:
                    print(f"⚠️ Missing prediction fields: {missing_pred_fields}")
                else:
                    print("✅ Prediction data structure valid")
            else:
                print("⚠️ No predictions found")
        else:
            print(f"❌ Predictions API failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Predictions API error: {str(e)}")
    
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
    
    # Test 4: Test data generation manually
    print("\n🔧 Testing Data Generation Logic...")
    
    try:
        from src.managers.interactive_tracker_manager import InteractiveTrackerManager
        
        tracker = InteractiveTrackerManager()
        
        # Test initialization with sample data
        test_predictions = {
            'pred_5d': 5.0,
            'pred_1mo': 15.0,
            'confidence': 85,
            'score': 75
        }
        
        success = tracker.initialize_stock_tracking('TESTSTOCK', 100.0, test_predictions)
        if success:
            print("✅ Stock tracking initialization working")
            
            # Get the data back
            test_data = tracker.get_stock_data('TESTSTOCK')
            if test_data:
                pred_5d = test_data.get('predicted_5d', [])
                pred_30d = test_data.get('predicted_30d', [])
                
                print(f"   Generated 5D data: {len(pred_5d)} points")
                print(f"   Generated 30D data: {len(pred_30d)} points")
                
                if len(pred_5d) == 5 and len(pred_30d) == 30:
                    print("✅ Correct array lengths generated")
                    
                    # Check for numeric values
                    if all(isinstance(x, (int, float)) and not (isinstance(x, float) and x != x) for x in pred_5d):
                        print("✅ 5D data contains valid numbers")
                    else:
                        print("❌ 5D data contains invalid values")
                        return False
                        
                    if all(isinstance(x, (int, float)) and not (isinstance(x, float) and x != x) for x in pred_30d):
                        print("✅ 30D data contains valid numbers")
                    else:
                        print("❌ 30D data contains invalid values")
                        return False
                else:
                    print(f"❌ Wrong array lengths: 5D={len(pred_5d)}, 30D={len(pred_30d)}")
                    return False
            else:
                print("❌ Failed to retrieve test data")
                return False
        else:
            print("❌ Stock tracking initialization failed")
            return False
            
    except ImportError:
        print("❌ Interactive tracker manager not found")
        return False
    except Exception as e:
        print(f"❌ Data generation test error: {str(e)}")
        return False
    
    print(f"\n{'='*60}")
    print("🎉 ALL CHART DATA TESTS PASSED!")
    print("✅ Interactive prediction tracker charts should now display data properly")
    print("📊 Charts will show predicted lines, actual progress, and updated predictions")
    print(f"{'='*60}")
    
    return True

if __name__ == "__main__":
    success = test_chart_data_functionality()
    if not success:
        print("\n❌ CHART DATA TESTS FAILED!")
        print("📋 Check the errors above and fix the identified issues")
        sys.exit(1)
    else:
        print("\n✅ All tests passed - Charts should display data correctly!")
        sys.exit(0)
