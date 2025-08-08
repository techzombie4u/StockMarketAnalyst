
import json
import os
from datetime import datetime, timedelta

def create_locked_predictions_file():
    """Create a proper locked predictions file for testing"""
    
    # Ensure tracking directory exists
    os.makedirs('data/tracking', exist_ok=True)
    
    # Sample locked predictions data
    locked_predictions = {
        "RELIANCE": {
            "locked_5d": True,
            "locked_30d": True,
            "expiry_date_5d": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
            "expiry_date_30d": (datetime.now() + timedelta(days=25)).strftime('%Y-%m-%d'),
            "predicted_roi_5d": 12.5,
            "predicted_roi_30d": 28.0,
            "actual_roi_5d": None,  # Still in progress
            "actual_roi_30d": None,  # Still in progress
            "predicted_outcome": "On Track",
            "lock_start_date_5d": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
            "lock_start_date_30d": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
            "status": "in_progress"
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
            "predicted_outcome": "On Track",
            "lock_start_date_5d": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            "lock_start_date_30d": (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            "status": "partial_complete"
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
            "predicted_outcome": "On Track",
            "lock_start_date_5d": (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            "lock_start_date_30d": (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d'),
            "status": "completed"
        },
        "INFY": {
            "locked_5d": True,
            "locked_30d": False,
            "expiry_date_5d": (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "predicted_roi_5d": 22.0,
            "actual_roi_5d": None,  # Still in progress
            "predicted_outcome": "On Track",
            "lock_start_date_5d": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
            "status": "in_progress"
        },
        "ITC": {
            "locked_5d": False,
            "locked_30d": True,
            "expiry_date_30d": (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),
            "predicted_roi_30d": 45.0,
            "actual_roi_30d": None,  # Still in progress
            "predicted_outcome": "On Track",
            "lock_start_date_30d": (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            "status": "in_progress"
        }
    }
    
    # Save to multiple locations for compatibility
    files_to_create = [
        'data/tracking/locked_predictions.json',
        'data/tracking/interactive_tracking.json'
    ]
    
    for file_path in files_to_create:
        try:
            with open(file_path, 'w') as f:
                json.dump(locked_predictions, f, indent=2)
            print(f"✅ Created locked predictions file: {file_path}")
        except Exception as e:
            print(f"❌ Error creating {file_path}: {e}")
    
    print(f"📊 Created {len(locked_predictions)} locked prediction entries")
    return locked_predictions

if __name__ == "__main__":
    create_locked_predictions_file()
