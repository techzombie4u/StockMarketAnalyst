
#!/usr/bin/env python3
"""
Prediction Tracker Verification Script
Verifies that the prediction tracker is working with real data
"""

import json
import os
import sys
from datetime import datetime, timedelta
import requests

def verify_prediction_data():
    """Verify prediction data files and structure"""
    print("🔍 Verifying Prediction Data Structure")
    print("=" * 50)
    
    # Check main data file
    if os.path.exists('top10.json'):
        with open('top10.json', 'r') as f:
            data = json.load(f)
            stocks = data.get('stocks', [])
            print(f"✅ Main data file: {len(stocks)} stocks")
            
            if stocks:
                sample = stocks[0]
                print(f"   Sample stock: {sample.get('symbol', 'N/A')}")
                print(f"   Has pred_5d: {'pred_5d' in sample}")
                print(f"   Has pred_1mo: {'pred_1mo' in sample}")
                print(f"   Has predicted_price: {'predicted_price' in sample}")
                return True
    else:
        print("❌ No main data file found")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    try:
        # Test stocks API
        response = requests.get(f"{base_url}/api/stocks", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /api/stocks: {len(data.get('stocks', []))} stocks")
        else:
            print(f"❌ /api/stocks failed: {response.status_code}")
            return False
            
        # Test prediction tracker API  
        response = requests.get(f"{base_url}/api/predictions-tracker", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ /api/predictions-tracker: {data.get('total_count', 0)} predictions")
            
            predictions = data.get('predictions', [])
            if predictions:
                sources = {}
                for pred in predictions:
                    source = pred.get('source', 'unknown')
                    sources[source] = sources.get(source, 0) + 1
                
                print("   Data sources:")
                for source, count in sources.items():
                    print(f"     {source}: {count}")
            
            return True
        else:
            print(f"❌ /api/predictions-tracker failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        return False

def create_demo_predictions():
    """Create demo prediction data for testing"""
    print("\n🛠️  Creating Demo Prediction Data")
    print("=" * 50)
    
    try:
        # Load current stocks if available
        current_stocks = []
        if os.path.exists('top10.json'):
            with open('top10.json', 'r') as f:
                data = json.load(f)
                current_stocks = data.get('stocks', [])
        
        if not current_stocks:
            print("❌ No current stocks found - cannot create demo data")
            return False
        
        # Create historical predictions based on current stocks
        historical_predictions = []
        
        for i, stock in enumerate(current_stocks[:5]):  # Take first 5 stocks
            for days_ago in [1, 2, 3]:  # Create 3 days of historical data
                timestamp = datetime.now() - timedelta(days=days_ago)
                
                prediction = {
                    'symbol': stock['symbol'],
                    'timestamp': timestamp.isoformat(),
                    'current_price': stock.get('current_price', 100) * (1 + (days_ago * 0.01)),
                    'predicted_price': stock.get('predicted_price', stock.get('current_price', 100)),
                    'pred_5d': stock.get('pred_5d', 2.5),
                    'predicted_1mo': stock.get('pred_1mo', 10.0),
                    'confidence': stock.get('confidence', 85),
                    'score': stock.get('score', 70),
                    'source': 'demo_historical'
                }
                historical_predictions.append(prediction)
        
        # Save historical predictions
        with open('predictions_history.json', 'w') as f:
            json.dump(historical_predictions, f, indent=2)
        
        print(f"✅ Created {len(historical_predictions)} demo predictions")
        return True
        
    except Exception as e:
        print(f"❌ Demo data creation failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("📊 Prediction Tracker Verification")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Verify data files
    data_ok = verify_prediction_data()
    
    # Step 2: Test API endpoints
    api_ok = test_api_endpoints()
    
    # Step 3: Create demo data if needed
    if data_ok and api_ok:
        demo_ok = create_demo_predictions()
    else:
        demo_ok = False
    
    # Final summary
    print("\n" + "=" * 50)
    print("📋 Verification Summary:")
    print(f"   Data Files: {'✅' if data_ok else '❌'}")
    print(f"   API Endpoints: {'✅' if api_ok else '❌'}")
    print(f"   Demo Data: {'✅' if demo_ok else '❌'}")
    
    if data_ok and api_ok:
        print("\n🎉 Prediction Tracker is ready!")
        print("   Visit: http://localhost:5000/prediction-tracker")
        print("   Interactive: http://localhost:5000/prediction-tracker-interactive")
        return True
    else:
        print("\n❌ Prediction Tracker needs attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
