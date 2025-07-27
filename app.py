"""
Stock Market Analyst - Flask Dashboard

Web interface for displaying stock screening results with auto-refresh.
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from scheduler import StockAnalystScheduler
from historical_analyzer import HistoricalAnalyzer
import pytz

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global scheduler instance
scheduler = None

# Timezone for India
IST = pytz.timezone('Asia/Kolkata')

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/stocks')
def get_stocks():
    """API endpoint to get current stock data"""
    try:
        if os.path.exists('top10.json'):
            with open('top10.json', 'r') as f:
                data = json.load(f)

            # Ensure data has required structure
            if not isinstance(data, dict):
                raise ValueError("Invalid data format")

            # Add default values if missing
            response_data = {
                'timestamp': data.get('timestamp', ''),
                'last_updated': data.get('last_updated', 'Unknown'),
                'stocks': data.get('stocks', []),
                'error': data.get('error', None),
                'status': 'success' if data.get('stocks') else 'no_data'
            }

            return jsonify(response_data)
        else:
            # Create default empty file if it doesn't exist
            default_data = {
                'timestamp': '',
                'last_updated': 'Initializing...',
                'stocks': [],
                'status': 'initializing'
            }

            with open('top10.json', 'w') as f:
                json.dump(default_data, f, indent=2)

            return jsonify(default_data)

    except Exception as e:
        logger.error(f"Error in /api/stocks: {str(e)}")
        error_response = {
            'error': str(e),
            'timestamp': '',
            'last_updated': 'Error loading data',
            'stocks': [],
            'status': 'error'
        }
        return jsonify(error_response), 500

@app.route('/api/status')
def get_status():
    """Get scheduler status"""
    global scheduler
    if scheduler:
        return jsonify(scheduler.get_job_status())
    else:
        return jsonify({'running': False, 'jobs': []})

@app.route('/api/run-now', methods=['POST'])
def run_now():
    """Manually trigger screening"""
    global scheduler
    try:
        if scheduler:
            scheduler.run_screening_job_manual()
            return jsonify({'success': True, 'message': 'Screening started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Scheduler not running'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/force-demo', methods=['POST'])
def force_demo_data():
    """Generate demo data for testing when no real data available"""
    try:
        logger.info("Generating demo data")

        # Create sample data structure with predictions
        demo_data = {
            'timestamp': datetime.now(IST).isoformat(),
            'last_updated': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST'),
            'status': 'demo',
            'stocks': [
                {
                    'symbol': 'RELIANCE',
                    'score': 85.0,
                    'adjusted_score': 82.5,
                    'confidence': 90,
                    'current_price': 1400.0,
                    'predicted_price': 1680.0,
                    'predicted_gain': 20.0,
                    'pred_24h': 1.2,
                    'pred_5d': 4.8,
                    'pred_1mo': 18.5,
                    'volatility': 1.5,
                    'time_horizon': 12,
                    'pe_ratio': 25.0,
                    'revenue_growth': 8.5
                },
                {
                    'symbol': 'TCS',
                    'score': 82.0,
                    'adjusted_score': 80.1,
                    'confidence': 88,
                    'current_price': 3150.0,
                    'predicted_price': 3780.0,
                    'predicted_gain': 20.0,
                    'pred_24h': 0.9,
                    'pred_5d': 3.6,
                    'pred_1mo': 15.2,
                    'volatility': 1.4,
                    'time_horizon': 12,
                    'pe_ratio': 23.0,
                    'revenue_growth': 6.2
                },
                {
                    'symbol': 'INFY',
                    'score': 78.0,
                    'adjusted_score': 75.5,
                    'confidence': 85,
                    'current_price': 1450.0,
                    'predicted_price': 1668.0,
                    'predicted_gain': 15.0,
                    'pred_24h': 0.8,
                    'pred_5d': 3.2,
                    'pred_1mo': 12.8,
                    'volatility': 1.3,
                    'time_horizon': 15,
                    'pe_ratio': 22.0,
                    'revenue_growth': 7.8
                }
            ]
        }

        # Save demo data
        with open('top10.json', 'w') as f:
            json.dump(demo_data, f, indent=2)

        logger.info("Demo data generated successfully")
        return jsonify({
            'success': True,
            'message': 'Demo data generated successfully',
            'data': demo_data
        })

    except Exception as e:
        logger.error(f"Demo data generation failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Demo data error: {str(e)}'
        }), 500

@app.route('/analysis')
def analysis_dashboard():
    """Analysis dashboard page"""
    return render_template('analysis.html')

@app.route('/api/analysis')
def get_analysis():
    """API endpoint to get historical analysis data"""
    try:
        analyzer = HistoricalAnalyzer()
        analysis_data = analyzer.get_analysis_summary()

        # If no analysis data exists, try to generate from existing historical data
        if not analysis_data:
            historical_data = analyzer._load_historical_data()
            if len(historical_data) >= 1:
                # Force analysis generation
                analysis_data = analyzer._analyze_predictions()
                if analysis_data:
                    logger.info("Generated analysis from existing historical data")
                else:
                    # Create minimal sample data for demonstration
                    analysis_data = {
                        'timestamp': datetime.now().isoformat(),
                        'total_predictions_analyzed': 0,
                        'correct_predictions': 0,
                        'accuracy_rate': 0,
                        'top_performing_stocks': [],
                        'worst_performing_stocks': [],
                        'pattern_insights': ['📋 Insufficient data for analysis. Run more screening sessions to generate insights.'],
                        'status': 'insufficient_data'
                    }
            else:
                return jsonify({
                    'message': 'No analysis data available yet. Run the stock screener multiple times to generate analysis.',
                    'status': 'no_data'
                })

        return jsonify(analysis_data)

    except Exception as e:
        logger.error(f"Error in /api/analysis: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/historical-trends')
def get_historical_trends():
    """API endpoint to get historical trends"""
    try:
        analyzer = HistoricalAnalyzer()
        trends_data = analyzer.get_historical_trends()
        return jsonify(trends_data)

    except Exception as e:
        logger.error(f"Error in /api/historical-trends: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Stock Market Analyst'
    })

def initialize_app():
    """Initialize the application with scheduler"""
    global scheduler

    try:
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=60)
        print("✅ Scheduler started successfully")

        # Run initial screening to populate data
        scheduler.run_screening_job_manual()
        print("✅ Initial screening triggered")

    except Exception as e:
        print(f"❌ Error starting scheduler: {str(e)}")

if __name__ == '__main__':
    initialize_app()

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Set to False in production
        threaded=True
    )