
import json
import os
from datetime import datetime, timedelta
import random

def create_locked_predictions():
    """Create locked predictions for testing the dashboard"""
    
    # Sample stocks for testing
    stocks = [
        "RELIANCE", "TCS", "INFY", "HDFCBANK", "ITC", "HINDUNILVR", 
        "SBIN", "BHARTIARTL", "WIPRO", "MARUTI"
    ]
    
    # Create tracking directory if it doesn't exist
    tracking_dir = "data/tracking"
    os.makedirs(tracking_dir, exist_ok=True)
    
    tracking_data = []
    
    # Generate 3-5 locked trades with future expiry dates
    num_trades = random.randint(3, 5)
    
    for i in range(num_trades):
        stock = random.choice(stocks)
        
        # Future expiry date (3-30 days from now)
        expiry_date = datetime.now() + timedelta(days=random.randint(3, 30))
        
        # Generate realistic ROI values with more variation
        predicted_roi = round(random.uniform(18.0, 45.0), 1)
        
        # Simulate different scenarios for current ROI
        scenario = random.choice(['on_track', 'diverging', 'outperforming'])
        
        if scenario == 'on_track':
            # Within 10% of prediction (should be "On Track")
            variation = random.uniform(-0.08, 0.08)  # ±8%
            current_roi = round(predicted_roi * (1 + variation), 1)
            predicted_outcome = "On Track"
        elif scenario == 'diverging':
            # More than 10% below prediction (should be "Diverging")
            variation = random.uniform(-0.25, -0.12)  # -12% to -25%
            current_roi = round(predicted_roi * (1 + variation), 1)
            predicted_outcome = "Diverging"
        else:  # outperforming
            # More than 10% above prediction (should be "Outperforming")
            variation = random.uniform(0.12, 0.35)  # +12% to +35%
            current_roi = round(predicted_roi * (1 + variation), 1)
            predicted_outcome = "Outperforming"
        
        trade_entry = {
            "symbol": stock,
            "locked": True,
            "status": "in_progress",
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "predicted_roi": predicted_roi,
            "current_roi": current_roi,
            "predicted_outcome": predicted_outcome,
            "actual_outcome": None,
            "trade_type": "short_strangle",
            "timeframe": random.choice(["3D", "5D", "10D", "15D", "30D"]),
            "entry_date": (datetime.now() - timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d"),
            "reason": f"Technical analysis indicates {predicted_outcome.lower()} trend"
        }
        
        tracking_data.append(trade_entry)
    
    # Add some historical completed trades for accuracy stats
    for i in range(5):
        stock = random.choice(stocks)
        
        # Past expiry date
        expiry_date = datetime.now() - timedelta(days=random.randint(1, 10))
        
        predicted_roi = round(random.uniform(15.0, 35.0), 1)
        actual_roi = round(predicted_roi + random.uniform(-10.0, 10.0), 1)
        
        # Determine if successful (within 20% of prediction)
        was_successful = abs(actual_roi - predicted_roi) / predicted_roi <= 0.2 if predicted_roi != 0 else False
        
        historical_entry = {
            "symbol": stock,
            "locked": True,
            "status": "completed",
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "predicted_roi": predicted_roi,
            "current_roi": actual_roi,
            "predicted_outcome": "Completed",
            "actual_outcome": "successful" if was_successful else "failed",
            "trade_type": "short_strangle",
            "timeframe": random.choice(["3D", "5D", "10D", "15D", "30D"]),
            "entry_date": (expiry_date - timedelta(days=random.randint(3, 30))).strftime("%Y-%m-%d"),
            "reason": "Historical trade for stats"
        }
        
        tracking_data.append(historical_entry)
    
    # Write to file
    tracking_file = os.path.join(tracking_dir, "interactive_tracking.json")
    with open(tracking_file, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    
    print(f"✅ Created {len(tracking_data)} tracking entries:")
    print(f"   - {num_trades} active locked trades")
    print(f"   - 5 historical trades for accuracy stats")
    print(f"   - Saved to: {tracking_file}")
    
    # Display active trades
    active_trades = [t for t in tracking_data if t['status'] == 'in_progress']
    print(f"\n📊 Active Trades:")
    for trade in active_trades:
        print(f"   {trade['symbol']}: {trade['predicted_roi']}% → {trade['current_roi']}% ({trade['predicted_outcome']})")

if __name__ == "__main__":
    create_locked_predictions()
