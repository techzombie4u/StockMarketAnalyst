
#!/usr/bin/env python3
"""
Comprehensive Chart Regression Test
Tests all aspects of the interactive prediction tracker charts
"""

import requests
import json
import time
import sys
from datetime import datetime

def run_comprehensive_chart_test():
    """Run comprehensive chart regression test"""
    print("🧪 COMPREHENSIVE CHART REGRESSION TEST")
    print("=" * 70)
    
    base_url = "http://localhost:5000"
    test_results = []
    
    # Test 1: Backend Data APIs
    print("\n📊 Testing Backend Data APIs...")
    
    try:
        # Test interactive tracker data
        response = requests.get(f"{base_url}/api/interactive-tracker-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tracking_data = data.get('tracking_data', {})
            
            if tracking_data:
                test_results.append(("✅", "Interactive tracker data API", f"{len(tracking_data)} stocks"))
                
                # Test sample stock data structure
                sample_symbol = list(tracking_data.keys())[0]
                sample_data = tracking_data[sample_symbol]
                
                required_fields = ['predicted_5d', 'predicted_30d', 'current_price']
                if all(field in sample_data for field in required_fields):
                    test_results.append(("✅", "Data structure validation", "All required fields present"))
                else:
                    test_results.append(("❌", "Data structure validation", "Missing required fields"))
                    
                # Test array lengths
                pred_5d = sample_data.get('predicted_5d', [])
                pred_30d = sample_data.get('predicted_30d', [])
                
                if len(pred_5d) == 5 and len(pred_30d) == 30:
                    test_results.append(("✅", "Array length validation", "Correct lengths"))
                else:
                    test_results.append(("❌", "Array length validation", f"Wrong lengths: 5D={len(pred_5d)}, 30D={len(pred_30d)}"))
                    
                # Test data validity
                valid_5d = [x for x in pred_5d if x is not None and isinstance(x, (int, float)) and not (isinstance(x, float) and x != x)]
                valid_30d = [x for x in pred_30d if x is not None and isinstance(x, (int, float)) and not (isinstance(x, float) and x != x)]
                
                if len(valid_5d) > 0 and len(valid_30d) > 0:
                    test_results.append(("✅", "Data validity check", f"Valid data: 5D={len(valid_5d)}/5, 30D={len(valid_30d)}/30"))
                else:
                    test_results.append(("❌", "Data validity check", "No valid numeric data found"))
                    
            else:
                test_results.append(("❌", "Interactive tracker data API", "No tracking data"))
        else:
            test_results.append(("❌", "Interactive tracker data API", f"HTTP {response.status_code}"))
            
    except Exception as e:
        test_results.append(("❌", "Interactive tracker data API", f"Error: {str(e)}"))
    
    # Test 2: Predictions Tracker API
    try:
        response = requests.get(f"{base_url}/api/predictions-tracker", timeout=10)
        if response.status_code == 200:
            data = response.json()
            predictions = data.get('predictions', [])
            test_results.append(("✅", "Predictions tracker API", f"{len(predictions)} predictions"))
        else:
            test_results.append(("❌", "Predictions tracker API", f"HTTP {response.status_code}"))
    except Exception as e:
        test_results.append(("❌", "Predictions tracker API", f"Error: {str(e)}"))
    
    # Test 3: Frontend Page Loading
    print("\n🌐 Testing Frontend Components...")
    
    try:
        response = requests.get(f"{base_url}/prediction-tracker-interactive", timeout=10)
        if response.status_code == 200:
            content = response.text
            test_results.append(("✅", "Interactive tracker page", "Page loads successfully"))
            
            # Check Chart.js
            if 'chart.js' in content.lower():
                test_results.append(("✅", "Chart.js library", "Included"))
            else:
                test_results.append(("❌", "Chart.js library", "Missing"))
                
            # Check key functions
            key_functions = ['updateChart', 'loadPredictionData', 'selectStock', 'switchView']
            missing_functions = [func for func in key_functions if func not in content]
            
            if not missing_functions:
                test_results.append(("✅", "JavaScript functions", "All key functions present"))
            else:
                test_results.append(("❌", "JavaScript functions", f"Missing: {missing_functions}"))
                
        else:
            test_results.append(("❌", "Interactive tracker page", f"HTTP {response.status_code}"))
            
    except Exception as e:
        test_results.append(("❌", "Interactive tracker page", f"Error: {str(e)}"))
    
    # Test 4: Lock Status API
    print("\n🔐 Testing Lock Status Management...")
    
    try:
        test_payload = {
            'symbol': 'TESTSTOCK',
            'period': '5d',
            'locked': True,
            'persistent': True,
            'timestamp': datetime.now().isoformat()
        }
        
        response = requests.post(f"{base_url}/api/update-lock-status", json=test_payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                test_results.append(("✅", "Lock status update", "Working"))
            else:
                test_results.append(("❌", "Lock status update", f"Failed: {data.get('message')}"))
        else:
            test_results.append(("❌", "Lock status update", f"HTTP {response.status_code}"))
            
    except Exception as e:
        test_results.append(("❌", "Lock status update", f"Error: {str(e)}"))
    
    # Test 5: Debug Endpoint (if available)
    print("\n🔧 Testing Debug Endpoints...")
    
    try:
        # Get first available stock for testing
        response = requests.get(f"{base_url}/api/interactive-tracker-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tracking_data = data.get('tracking_data', {})
            
            if tracking_data:
                test_symbol = list(tracking_data.keys())[0]
                
                # Test debug endpoint
                debug_response = requests.get(f"{base_url}/api/debug-chart-data/{test_symbol}", timeout=10)
                if debug_response.status_code == 200:
                    debug_data = debug_response.json()
                    validation = debug_data.get('data_validation', {})
                    
                    if validation.get('predicted_5d_valid_count', 0) > 0:
                        test_results.append(("✅", "Debug endpoint validation", f"Valid 5D data: {validation.get('predicted_5d_valid_count')}"))
                    else:
                        test_results.append(("❌", "Debug endpoint validation", "No valid 5D data"))
                        
                else:
                    test_results.append(("⚠️", "Debug endpoint", "Not available or failed"))
            else:
                test_results.append(("⚠️", "Debug endpoint test", "No stocks available"))
                
    except Exception as e:
        test_results.append(("⚠️", "Debug endpoint test", f"Error: {str(e)}"))
    
    # Test 6: Data Generation Logic
    print("\n🔧 Testing Data Generation...")
    
    try:
        from src.managers.interactive_tracker_manager import InteractiveTrackerManager
        
        tracker = InteractiveTrackerManager()
        
        # Test with realistic data
        test_predictions = {
            'pred_5d': 3.5,
            'pred_1mo': 12.0,
            'confidence': 80,
            'score': 72
        }
        
        success = tracker.initialize_stock_tracking('REGRESSION_TEST', 150.0, test_predictions)
        if success:
            test_data = tracker.get_stock_data('REGRESSION_TEST')
            
            if test_data:
                pred_5d = test_data.get('predicted_5d', [])
                pred_30d = test_data.get('predicted_30d', [])
                
                # Validate data
                if len(pred_5d) == 5 and len(pred_30d) == 30:
                    test_results.append(("✅", "Data generation", "Correct array lengths"))
                    
                    # Check numeric validity
                    if all(isinstance(x, (int, float)) for x in pred_5d) and all(isinstance(x, (int, float)) for x in pred_30d):
                        test_results.append(("✅", "Data numeric validity", "All values are numeric"))
                        
                        # Check progression (should be increasing for positive prediction)
                        if pred_5d[0] < pred_5d[-1] and pred_30d[0] < pred_30d[-1]:
                            test_results.append(("✅", "Data progression", "Prediction shows expected growth"))
                        else:
                            test_results.append(("❌", "Data progression", "Unexpected progression pattern"))
                    else:
                        test_results.append(("❌", "Data numeric validity", "Non-numeric values found"))
                else:
                    test_results.append(("❌", "Data generation", f"Wrong lengths: 5D={len(pred_5d)}, 30D={len(pred_30d)}"))
            else:
                test_results.append(("❌", "Data generation", "Failed to retrieve generated data"))
        else:
            test_results.append(("❌", "Data generation", "Initialization failed"))
            
    except Exception as e:
        test_results.append(("❌", "Data generation", f"Error: {str(e)}"))
    
    # Print Results
    print(f"\n{'='*70}")
    print("📊 REGRESSION TEST RESULTS")
    print(f"{'='*70}")
    
    passed = 0
    failed = 0
    warnings = 0
    
    for status, test_name, details in test_results:
        print(f"{status} {test_name}: {details}")
        if status == "✅":
            passed += 1
        elif status == "❌":
            failed += 1
        else:
            warnings += 1
    
    print(f"\n{'='*70}")
    print(f"📈 SUMMARY: {passed} passed, {failed} failed, {warnings} warnings")
    
    if failed == 0:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print("✅ Interactive prediction tracker charts should display data correctly")
        print("📊 Charts will show predicted lines, actual progress, and lock functionality")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Review the failed tests above and fix the issues")
        return False

if __name__ == "__main__":
    success = run_comprehensive_chart_test()
    sys.exit(0 if success else 1)
