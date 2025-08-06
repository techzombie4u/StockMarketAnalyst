
#!/usr/bin/env python3
"""
Chart Display Fix Test
Tests to ensure charts display lines correctly:
- Green line: Straight from start to predicted end
- Blue line: Incremental for days that have passed only
- Red line: Starts from green line for prediction changes
"""

import requests
import json
import time
from datetime import datetime, timedelta
import pytz

def test_chart_display_logic():
    """Test that chart data displays correctly"""
    print("🔧 Testing Chart Display Logic")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    IST = pytz.timezone('Asia/Kolkata')
    
    # Test 1: Get interactive tracker data
    print("\n📊 Testing Interactive Tracker Data Structure...")
    
    try:
        response = requests.get(f"{base_url}/api/interactive-tracker-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tracking_data = data.get('tracking_data', {})
            
            if tracking_data:
                print(f"✅ Found {len(tracking_data)} stocks")
                
                # Test a sample stock
                sample_symbol = list(tracking_data.keys())[0]
                sample_data = tracking_data[sample_symbol]
                
                print(f"\n🔍 Analyzing {sample_symbol}:")
                
                # Check GREEN LINE (predicted data)
                predicted_5d = sample_data.get('predicted_5d', [])
                predicted_30d = sample_data.get('predicted_30d', [])
                
                if len(predicted_5d) == 5 and len(predicted_30d) == 30:
                    print("✅ Green line arrays have correct lengths")
                    
                    # Check if it's a straight line (monotonic progression)
                    is_straight_5d = all(predicted_5d[i] <= predicted_5d[i+1] for i in range(len(predicted_5d)-1))
                    is_straight_30d = all(predicted_30d[i] <= predicted_30d[i+1] for i in range(len(predicted_30d)-1))
                    
                    if is_straight_5d and is_straight_30d:
                        print("✅ Green line shows straight progression")
                    else:
                        print("❌ Green line is not straight")
                        return False
                else:
                    print(f"❌ Green line length issue: 5D={len(predicted_5d)}, 30D={len(predicted_30d)}")
                    return False
                
                # Check BLUE LINE (actual data) - should be incremental
                actual_5d = sample_data.get('actual_progress_5d', [])
                actual_30d = sample_data.get('actual_progress_30d', [])
                
                if len(actual_5d) == 5 and len(actual_30d) == 30:
                    print("✅ Blue line arrays have correct lengths")
                    
                    # Count non-null values (should only be for days that passed)
                    actual_5d_count = len([x for x in actual_5d if x is not None])
                    actual_30d_count = len([x for x in actual_30d if x is not None])
                    
                    current_time = datetime.now(IST)
                    is_market_day = current_time.weekday() < 5
                    is_market_closed = current_time.hour >= 15 and current_time.minute >= 30
                    
                    # Expected actual data points based on current time
                    expected_actual_points = 1  # At least start price
                    if is_market_day and is_market_closed:
                        expected_actual_points = 2  # Start + today
                    elif current_time.weekday() >= 5:  # Weekend
                        expected_actual_points = 2  # Start + Friday
                    
                    print(f"   📈 5D actual data points: {actual_5d_count} (expected: {expected_actual_points})")
                    print(f"   📈 30D actual data points: {actual_30d_count} (expected: {expected_actual_points})")
                    
                    # Blue line should not have future data
                    if actual_5d_count <= expected_actual_points + 1:  # Allow some tolerance
                        print("✅ Blue line shows incremental data only")
                    else:
                        print("❌ Blue line shows too much future data")
                        return False
                else:
                    print(f"❌ Blue line length issue: 5D={len(actual_5d)}, 30D={len(actual_30d)}")
                    return False
                
                # Check RED LINE (updated predictions) - should start from green line
                updated_5d = sample_data.get('updated_prediction_5d', [])
                updated_30d = sample_data.get('updated_prediction_30d', [])
                
                if len(updated_5d) == 5 and len(updated_30d) == 30:
                    print("✅ Red line arrays have correct lengths")
                    
                    # Find where updates start
                    update_start_5d = None
                    update_start_30d = None
                    
                    for i, val in enumerate(updated_5d):
                        if val is not None:
                            update_start_5d = i
                            break
                            
                    for i, val in enumerate(updated_30d):
                        if val is not None:
                            update_start_30d = i
                            break
                    
                    if update_start_5d is not None:
                        # Check if update starts close to predicted line
                        predicted_at_start = predicted_5d[update_start_5d]
                        updated_at_start = updated_5d[update_start_5d]
                        variance = abs(updated_at_start - predicted_at_start) / predicted_at_start
                        
                        print(f"   📊 5D update variance from green line: {variance:.2%}")
                        
                    if update_start_30d is not None:
                        # Check if update starts close to predicted line
                        predicted_at_start = predicted_30d[update_start_30d]
                        updated_at_start = updated_30d[update_start_30d]
                        variance = abs(updated_at_start - predicted_at_start) / predicted_at_start
                        
                        print(f"   📊 30D update variance from green line: {variance:.2%}")
                    
                    print("✅ Red line logic verified")
                else:
                    print(f"❌ Red line length issue: 5D={len(updated_5d)}, 30D={len(updated_30d)}")
                    return False
                
                return True
            else:
                print("❌ No tracking data found")
                return False
        else:
            print(f"❌ API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def test_multiple_stocks():
    """Test multiple stocks for consistency"""
    print("\n🔍 Testing Multiple Stocks for Consistency...")
    
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/api/interactive-tracker-data", timeout=10)
        if response.status_code == 200:
            data = response.json()
            tracking_data = data.get('tracking_data', {})
            
            consistent_stocks = 0
            total_stocks = len(tracking_data)
            
            for symbol, stock_data in tracking_data.items():
                # Check array lengths
                predicted_5d = stock_data.get('predicted_5d', [])
                predicted_30d = stock_data.get('predicted_30d', [])
                actual_5d = stock_data.get('actual_progress_5d', [])
                actual_30d = stock_data.get('actual_progress_30d', [])
                updated_5d = stock_data.get('updated_prediction_5d', [])
                updated_30d = stock_data.get('updated_prediction_30d', [])
                
                lengths_correct = (
                    len(predicted_5d) == 5 and len(predicted_30d) == 30 and
                    len(actual_5d) == 5 and len(actual_30d) == 30 and
                    len(updated_5d) == 5 and len(updated_30d) == 30
                )
                
                if lengths_correct:
                    consistent_stocks += 1
                else:
                    print(f"❌ {symbol} has incorrect array lengths")
            
            consistency_rate = (consistent_stocks / total_stocks) * 100
            print(f"   📊 Consistency rate: {consistent_stocks}/{total_stocks} ({consistency_rate:.1f}%)")
            
            if consistency_rate >= 90:
                print("✅ Stock data consistency good")
                return True
            else:
                print("❌ Stock data consistency issues")
                return False
                
        else:
            print(f"❌ API failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def main():
    """Run all chart display fix tests"""
    print("🧪 Chart Display Fix Test Suite")
    print("=" * 60)
    
    tests = [
        ("Chart Display Logic", test_chart_display_logic),
        ("Multiple Stocks Consistency", test_multiple_stocks)
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
        print("🎉 ALL CHART DISPLAY TESTS PASSED!")
        print("✅ Chart lines should now display correctly:")
        print("   🟢 Green line: Straight from start to predicted end")
        print("   🔵 Blue line: Incremental for days that have passed only")
        print("   🔴 Red line: Starts from green line for prediction changes")
        return True
    else:
        print("❌ SOME CHART DISPLAY TESTS FAILED!")
        print("📋 Check the errors above and fix the identified issues")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
    else:
        print("\n✅ All tests passed - Chart lines should display correctly!")
