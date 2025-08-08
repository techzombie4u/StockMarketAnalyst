
import json
import os
from datetime import datetime, timedelta

def create_sample_tracking_data():
    """Create sample tracking data for testing the prediction dashboard"""
    
    # Sample tracking data with active and completed predictions
    sample_data = {
        "RELIANCE": {
            "locked_5d": True,
            "locked_30d": True,
            "expiry_date_5d": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            "expiry_date_30d": (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'),
            "predicted_roi_5d": 12.5,
            "predicted_roi_30d": 28.0,
            "actual_roi_5d": None,  # Still in progress
            "actual_roi_30d": None,  # Still in progress
            "predicted_outcome": "On Track"
        },
        "TCS": {
            "locked_5d": True,
            "locked_30d": True,
            "expiry_date_5d": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            "expiry_date_30d": (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),
            "predicted_roi_5d": 15.0,
            "predicted_roi_30d": 32.0,
            "actual_roi_5d": 16.2,  # Completed - successful
            "actual_roi_30d": None,  # Still in progress
            "predicted_outcome": "On Track"
        },
        "HDFCBANK": {
            "locked_5d": True,
            "locked_30d": True,
            "expiry_date_5d": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            "expiry_date_30d": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            "predicted_roi_5d": 18.0,
            "predicted_roi_30d": 35.0,
            "actual_roi_5d": 12.3,  # Completed - failed
            "actual_roi_30d": 28.5,  # Completed - failed
            "predicted_outcome": "On Track"
        }
    }
    
    # Ensure tracking directory exists
    os.makedirs('data/tracking', exist_ok=True)
    
    # Save sample data
    with open('data/tracking/interactive_tracking.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("✅ Sample tracking data created for testing")
    print("📁 Saved to: data/tracking/interactive_tracking.json")
    
    # Also create backup in root for compatibility
    with open('interactive_tracking.json', 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print("📁 Backup saved to: interactive_tracking.json")

if __name__ == "__main__":
    create_sample_tracking_data()
