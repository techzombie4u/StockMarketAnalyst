
#!/usr/bin/env python3
"""
Training Results Validation Script
Validates that new stock training completed successfully and models are ready
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_training_results():
    """Comprehensive validation of training results"""
    
    print("🔍 TRAINING RESULTS VALIDATION")
    print("=" * 50)
    
    validation_results = {
        'timestamp': datetime.now().isoformat(),
        'models_found': 0,
        'kpi_stocks': 0,
        'validation_errors': [],
        'successful_stocks': [],
        'missing_models': []
    }
    
    # 1. Check models directory
    models_dir = "models_trained"
    if os.path.exists(models_dir):
        model_files = [f for f in os.listdir(models_dir) if f.endswith(('.h5', '.pkl', '.keras'))]
        validation_results['models_found'] = len(model_files)
        
        # Group by stock symbol
        stock_models = {}
        for model_file in model_files:
            stock_symbol = model_file.split('_')[0]
            if stock_symbol not in stock_models:
                stock_models[stock_symbol] = []
            stock_models[stock_symbol].append(model_file)
        
        print(f"📁 Models Directory: {len(model_files)} total model files")
        print(f"📊 Unique Stocks with Models: {len(stock_models)}")
        
        # Check for complete model pairs (LSTM + RF)
        complete_models = 0
        for stock, models in stock_models.items():
            has_lstm = any('lstm' in m for m in models)
            has_rf = any('rf' in m for m in models)
            
            if has_lstm and has_rf:
                complete_models += 1
                validation_results['successful_stocks'].append(stock)
            else:
                validation_results['missing_models'].append({
                    'stock': stock,
                    'has_lstm': has_lstm,
                    'has_rf': has_rf,
                    'files': models
                })
        
        print(f"✅ Complete Model Pairs: {complete_models}")
        print(f"⚠️  Incomplete Models: {len(stock_models) - complete_models}")
        
    else:
        validation_results['validation_errors'].append("Models directory not found")
        print("❌ Models directory not found")
    
    # 2. Check KPI registry
    kpi_file = "data/tracking/model_kpi.json"
    if os.path.exists(kpi_file):
        try:
            with open(kpi_file, 'r') as f:
                kpi_data = json.load(f)
            
            stock_kpis = [k for k in kpi_data.keys() if k != 'last_training']
            validation_results['kpi_stocks'] = len(stock_kpis)
            
            print(f"📈 KPI Registry: {len(stock_kpis)} stocks tracked")
            
            if 'last_training' in kpi_data:
                last_training = kpi_data['last_training']
                print(f"🕐 Last Training: {last_training.get('date', 'Unknown')}")
                print(f"📊 Training Stats: {last_training.get('successful', 0)} successful, {last_training.get('failed', 0)} failed")
            
        except Exception as e:
            validation_results['validation_errors'].append(f"KPI file error: {str(e)}")
            print(f"❌ KPI file error: {str(e)}")
    else:
        validation_results['validation_errors'].append("KPI file not found")
        print("❌ KPI file not found")
    
    # 3. Check training log files
    log_files = [f for f in os.listdir('.') if f.startswith('new_stock_training_results_')]
    if log_files:
        latest_log = sorted(log_files)[-1]
        print(f"📝 Latest Training Log: {latest_log}")
        
        try:
            with open(latest_log, 'r') as f:
                log_data = json.load(f)
            
            print(f"🎯 Log Summary:")
            print(f"   Total Planned: {log_data.get('total_planned', 0)}")
            print(f"   Successful: {log_data.get('successful', 0)}")
            print(f"   Failed: {log_data.get('failed', 0)}")
            
            if log_data.get('errors'):
                print(f"⚠️  Top Errors:")
                for error in log_data['errors'][:3]:
                    print(f"   • {error}")
                    
        except Exception as e:
            validation_results['validation_errors'].append(f"Log file error: {str(e)}")
            print(f"❌ Log file error: {str(e)}")
    
    # 4. Historical data validation
    data_dir = "data/historical/downloaded_historical_data"
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        print(f"📊 Historical Data: {len(csv_files)} CSV files")
        
        # Validate a few sample files
        sample_validation = []
        for csv_file in csv_files[:5]:  # Check first 5 files
            try:
                import pandas as pd
                df = pd.read_csv(os.path.join(data_dir, csv_file))
                sample_validation.append({
                    'file': csv_file,
                    'rows': len(df),
                    'valid': len(df) >= 1000  # 5-year data requirement
                })
            except Exception as e:
                sample_validation.append({
                    'file': csv_file,
                    'error': str(e),
                    'valid': False
                })
        
        valid_samples = sum(1 for s in sample_validation if s.get('valid', False))
        print(f"✅ Sample Data Quality: {valid_samples}/{len(sample_validation)} files have 1000+ rows")
    
    # 5. Overall validation status
    print("\n" + "=" * 50)
    print("🏆 VALIDATION SUMMARY")
    print("=" * 50)
    
    if validation_results['models_found'] > 0 and validation_results['kpi_stocks'] > 0:
        print("✅ TRAINING VALIDATION: PASSED")
        print(f"   • {validation_results['models_found']} model files found")
        print(f"   • {len(validation_results['successful_stocks'])} stocks with complete models")
        print(f"   • {validation_results['kpi_stocks']} stocks in KPI registry")
    else:
        print("❌ TRAINING VALIDATION: FAILED")
        if validation_results['validation_errors']:
            print("   Errors:")
            for error in validation_results['validation_errors']:
                print(f"   • {error}")
    
    # Save validation results
    validation_file = f"training_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(validation_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n💾 Validation results saved to: {validation_file}")
    
    return validation_results

if __name__ == "__main__":
    validate_training_results()
