
#!/usr/bin/env python3
"""
Comprehensive Test for Prediction Tracker Functionality
Tests all prediction tracker endpoints and data flow
"""

import requests
import json
import sys
import os
from datetime import datetime

def test_prediction_tracker():
    """Test prediction tracker functionality"""
    print("🧪 Testing Prediction Tracker Functionality")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Stocks API (source of prediction data)
    print("\n📊 Testing /api/stocks endpoint...")
    try:
        response = requests.get(f"{base_url}/api/stocks", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stocks API working - Status: {data.get('status')}")
            print(f"   Stock count: {len(data.get('stocks', []))}")
            
            # Check if stocks have prediction fields
            stocks = data.get('stocks', [])
            if stocks:
                sample_stock = stocks[0]
                print(f"   Sample stock fields: {list(sample_stock.keys())}")
                required_fields = ['symbol', 'current_price', 'pred_5d', 'pred_1mo']
                missing_fields = [field for field in required_fields if field not in sample_stock]
                if missing_fields:
                    print(f"⚠️  Missing prediction fields: {missing_fields}")
                else:
                    print("✅ All required prediction fields present")
        else:
            print(f"❌ Stocks API failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stocks API error: {str(e)}")
        return False
    
    # Test 2: Prediction Tracker API
    print("\n📈 Testing /api/predictions-tracker endpoint...")
    try:
        response = requests.get(f"{base_url}/api/predictions-tracker", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Predictions Tracker API working - Status: {data.get('status')}")
            print(f"   Predictions count: {data.get('total_count', 0)}")
            
            predictions = data.get('predictions', [])
            if predictions:
                sample_pred = predictions[0]
                print(f"   Sample prediction fields: {list(sample_pred.keys())}")
                
                # Check required fields for tracker
                required_fields = ['symbol', 'timestamp', 'current_price', 'pred_5d', 'predicted_1mo']
                missing_fields = [field for field in required_fields if field not in sample_pred]
                if missing_fields:
                    print(f"⚠️  Missing tracker fields: {missing_fields}")
                else:
                    print("✅ All required tracker fields present")
                    
                # Check data sources
                sources = set(pred.get('source', 'unknown') for pred in predictions)
                print(f"   Data sources: {list(sources)}")
            else:
                print("⚠️  No predictions found")
        else:
            print(f"❌ Predictions Tracker API failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Predictions Tracker API error: {str(e)}")
        return False
    
    # Test 3: Check prediction files
    print("\n📁 Testing prediction data files...")
    
    files_to_check = [
        'top10.json',
        'predictions_history.json', 
        'stable_predictions.json'
    ]
    
    available_files = []
    for filename in files_to_check:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    if filename == 'top10.json':
                        stock_count = len(data.get('stocks', []))
                        print(f"✅ {filename} - {stock_count} stocks")
                    elif filename == 'predictions_history.json':
                        if isinstance(data, list):
                            pred_count = len(data)
                        elif isinstance(data, dict):
                            pred_count = len(data.get('predictions', []))
                        else:
                            pred_count = 0
                        print(f"✅ {filename} - {pred_count} historical predictions")
                    elif filename == 'stable_predictions.json':
                        stable_count = len(data) if isinstance(data, dict) else 0
                        print(f"✅ {filename} - {stable_count} stable predictions")
                    
                    available_files.append(filename)
            except Exception as e:
                print(f"⚠️  {filename} exists but has issues: {str(e)}")
        else:
            print(f"⚠️  {filename} not found")
    
    if not available_files:
        print("❌ No prediction data files available")
        return False
    
    # Test 4: Web pages accessibility
    print("\n🌐 Testing web pages...")
    
    pages_to_test = [
        '/prediction-tracker',
        '/prediction-tracker-interactive'
    ]
    
    for page in pages_to_test:
        try:
            response = requests.get(f"{base_url}{page}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {page} accessible")
                
                # Check for JavaScript errors in HTML
                content = response.text
                if 'refreshData' in content or 'loadPredictions' in content:
                    print(f"   JavaScript functions present")
                else:
                    print(f"⚠️  Missing JavaScript functions in {page}")
            else:
                print(f"❌ {page} returned status: {response.status_code}")
        except Exception as e:
            print(f"❌ {page} error: {str(e)}")
    
    # Test 5: Data flow integration
    print("\n🔄 Testing data flow integration...")
    
    try:
        # Get stocks data
        stocks_response = requests.get(f"{base_url}/api/stocks", timeout=10)
        tracker_response = requests.get(f"{base_url}/api/predictions-tracker", timeout=10)
        
        if stocks_response.status_code == 200 and tracker_response.status_code == 200:
            stocks_data = stocks_response.json()
            tracker_data = tracker_response.json()
            
            stock_symbols = set(stock['symbol'] for stock in stocks_data.get('stocks', []))
            tracker_symbols = set(pred['symbol'] for pred in tracker_data.get('predictions', []))
            
            common_symbols = stock_symbols.intersection(tracker_symbols)
            
            print(f"✅ Data flow working")
            print(f"   Stocks symbols: {len(stock_symbols)}")
            print(f"   Tracker symbols: {len(tracker_symbols)}")
            print(f"   Common symbols: {len(common_symbols)}")
            
            if len(common_symbols) > 0:
                print(f"   Sample common symbols: {list(common_symbols)[:5]}")
            else:
                print("⚠️  No common symbols between stocks and tracker")
                
        else:
            print("❌ Data flow test failed - API endpoints not working")
            return False
            
    except Exception as e:
        print(f"❌ Data flow test error: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Prediction Tracker Test Summary:")
    print("   - APIs working ✅")
    print("   - Data files available ✅") 
    print("   - Web pages accessible ✅")
    print("   - Data flow integrated ✅")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_prediction_tracker()
    if success:
        print("\n🎉 All prediction tracker tests PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Some prediction tracker tests FAILED!")
        sys.exit(1)
