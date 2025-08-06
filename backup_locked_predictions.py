
#!/usr/bin/env python3
"""
Backup Locked Predictions
Creates a backup of today's predicted values for all locked graphs
"""

import json
import os
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')

def backup_locked_predictions():
    """Backup today's predicted values for all locked graphs"""
    try:
        # Load current tracking data
        tracking_file = 'data/tracking/interactive_tracking.json'
        if not os.path.exists(tracking_file):
            tracking_file = 'interactive_tracking.json'  # Fallback location
        
        if not os.path.exists(tracking_file):
            print("❌ No tracking data file found")
            return False
        
        with open(tracking_file, 'r') as f:
            tracking_data = json.load(f)
        
        # Create backup data structure
        current_time = datetime.now(IST)
        backup_data = {
            'backup_timestamp': current_time.isoformat(),
            'backup_date': current_time.strftime('%Y-%m-%d'),
            'locked_predictions': {}
        }
        
        locked_count = 0
        
        # Process each stock and extract locked prediction data
        for symbol, stock_data in tracking_data.items():
            if isinstance(stock_data, dict):
                stock_backup = {
                    'symbol': symbol,
                    'current_price': stock_data.get('current_price'),
                    'start_date': stock_data.get('start_date'),
                    'confidence': stock_data.get('confidence'),
                    'score': stock_data.get('score')
                }
                
                # Check for 5D lock
                if stock_data.get('locked_5d', False):
                    stock_backup['locked_5d'] = {
                        'locked': True,
                        'lock_start_date': stock_data.get('lock_start_date_5d'),
                        'persistent_lock': stock_data.get('persistent_lock_5d', False),
                        'predicted_values': stock_data.get('predicted_5d', []),
                        'actual_progress': stock_data.get('actual_progress_5d', []),
                        'updated_prediction': stock_data.get('updated_prediction_5d', []),
                        'changed_on': stock_data.get('changed_on_5d'),
                        'pred_percentage': stock_data.get('pred_5d')
                    }
                    locked_count += 1
                    print(f"✅ Backed up 5D lock for {symbol}")
                
                # Check for 30D lock
                if stock_data.get('locked_30d', False):
                    stock_backup['locked_30d'] = {
                        'locked': True,
                        'lock_start_date': stock_data.get('lock_start_date_30d'),
                        'persistent_lock': stock_data.get('persistent_lock_30d', False),
                        'predicted_values': stock_data.get('predicted_30d', []),
                        'actual_progress': stock_data.get('actual_progress_30d', []),
                        'updated_prediction': stock_data.get('updated_prediction_30d', []),
                        'changed_on': stock_data.get('changed_on_30d'),
                        'pred_percentage': stock_data.get('pred_1mo')
                    }
                    locked_count += 1
                    print(f"✅ Backed up 30D lock for {symbol}")
                
                # Only add to backup if there are locked predictions
                if 'locked_5d' in stock_backup or 'locked_30d' in stock_backup:
                    backup_data['locked_predictions'][symbol] = stock_backup
        
        # Create backup directory if it doesn't exist
        backup_dir = 'data/backup'
        os.makedirs(backup_dir, exist_ok=True)
        
        # Save backup file with timestamp
        backup_filename = f"locked_predictions_backup_{current_time.strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        with open(backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Also save as latest backup
        latest_backup_path = os.path.join(backup_dir, 'latest_locked_predictions_backup.json')
        with open(latest_backup_path, 'w') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 BACKUP COMPLETED SUCCESSFULLY!")
        print(f"📊 Backed up {locked_count} locked predictions")
        print(f"💾 Backup saved to: {backup_path}")
        print(f"📂 Latest backup: {latest_backup_path}")
        print(f"⏰ Backup timestamp: {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
        
        # Print summary
        if backup_data['locked_predictions']:
            print(f"\n📋 BACKUP SUMMARY:")
            for symbol, data in backup_data['locked_predictions'].items():
                locks = []
                if 'locked_5d' in data:
                    locks.append('5D')
                if 'locked_30d' in data:
                    locks.append('30D')
                print(f"  • {symbol}: {', '.join(locks)} locked")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        logger.error(f"Error creating locked predictions backup: {str(e)}")
        return False

def restore_locked_predictions(backup_file=None):
    """Restore locked predictions from backup file"""
    try:
        if not backup_file:
            backup_file = 'data/backup/latest_locked_predictions_backup.json'
        
        if not os.path.exists(backup_file):
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        print(f"🔄 RESTORE INSTRUCTIONS:")
        print(f"📁 Backup file: {backup_file}")
        print(f"📅 Backup date: {backup_data.get('backup_date')}")
        print(f"📊 Contains {len(backup_data['locked_predictions'])} stocks with locks")
        print(f"\n⚠️  To restore, manually copy the prediction data from this backup file")
        print(f"    into the interactive_tracking.json file for the affected stocks.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading backup: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backup or restore locked prediction data')
    parser.add_argument('--action', choices=['backup', 'restore'], default='backup',
                       help='Action to perform (default: backup)')
    parser.add_argument('--file', help='Backup file path for restore operation')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        print("🔄 Creating backup of locked predictions...")
        success = backup_locked_predictions()
        if success:
            print("\n✅ Backup completed successfully!")
        else:
            print("\n❌ Backup failed!")
    
    elif args.action == 'restore':
        print("🔄 Displaying restore information...")
        restore_locked_predictions(args.file)
