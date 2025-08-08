
#!/usr/bin/env python3
"""
GoAhead Post-Training Analysis
Automatically validates model performance after training completion
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_post_training(training_date: str = None) -> Dict[str, Any]:
    """Analyze models after training completion"""
    try:
        from src.analyzers.smart_go_agent import SmartGoAgent
        
        logger.info("🧠 Starting GoAhead post-training analysis")
        
        # Initialize SmartGoAgent
        agent = SmartGoAgent()
        
        # Get model performance validation
        validation_results = agent.validate_predictions('5D')
        
        # Get model KPI data
        kpi_data = agent.get_model_kpi()
        
        # Analyze training success rate
        models_dir = "models_trained"
        model_files = []
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) if f.endswith(('.h5', '.pkl', '.keras'))]
        
        # Compile comprehensive analysis
        analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'training_date': training_date or datetime.now().strftime('%Y-%m-%d'),
            'model_inventory': {
                'total_model_files': len(model_files),
                'lstm_models': len([f for f in model_files if 'lstm' in f]),
                'rf_models': len([f for f in model_files if 'rf' in f])
            },
            'validation_results': validation_results,
            'kpi_summary': kpi_data,
            'recommendations': [],
            'flags': []
        }
        
        # Generate recommendations based on analysis
        total_models = analysis['model_inventory']['total_model_files']
        if total_models > 0:
            analysis['recommendations'].append({
                'priority': 'HIGH',
                'action': 'Model Validation Complete',
                'description': f'{total_models} models ready for prediction use',
                'expected_impact': 'Full prediction capability restored'
            })
        
        # Flag low-performing models for retraining
        if 'models' in kpi_data:
            for model, stats in kpi_data['models'].items():
                accuracy = stats.get('accuracy', 0)
                if accuracy < 60:
                    analysis['flags'].append({
                        'model': model,
                        'issue': 'Low accuracy',
                        'accuracy': accuracy,
                        'recommendation': 'Schedule for retraining'
                    })
        
        # Save analysis results
        analysis_file = f"goahead_post_training_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Print summary
        print("\n🧠 GOAHEAD POST-TRAINING ANALYSIS")
        print("=" * 50)
        print(f"📊 Total Model Files: {analysis['model_inventory']['total_model_files']}")
        print(f"🧠 LSTM Models: {analysis['model_inventory']['lstm_models']}")
        print(f"🌲 RF Models: {analysis['model_inventory']['rf_models']}")
        print(f"🎯 Recommendations: {len(analysis['recommendations'])}")
        print(f"⚠️  Flags: {len(analysis['flags'])}")
        print(f"💾 Analysis saved to: {analysis_file}")
        
        if analysis['flags']:
            print("\n⚠️ FLAGGED MODELS:")
            for flag in analysis['flags'][:5]:
                print(f"   • {flag['model']}: {flag['issue']} ({flag.get('accuracy', 'N/A')}% accuracy)")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in post-training analysis: {str(e)}")
        return {'error': str(e), 'analysis_timestamp': datetime.now().isoformat()}

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GoAhead Post-Training Analysis')
    parser.add_argument('--mode', default='post_training', help='Analysis mode')
    parser.add_argument('--date', help='Training date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.mode == 'post_training':
        results = analyze_post_training(args.date)
        if 'error' not in results:
            print("✅ GoAhead analysis completed successfully")
        else:
            print(f"❌ Analysis failed: {results['error']}")

if __name__ == "__main__":
    main()
