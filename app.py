
"""
Stock Market Analyst - Flask Dashboard

Web interface for displaying stock screening results with auto-refresh.
"""

import json
import os
from datetime import datetime
from flask import Flask, render_template, jsonify
from scheduler import StockAnalystScheduler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global scheduler instance
scheduler = None

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
            return jsonify(data)
        else:
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'last_updated': 'No data available',
                'stocks': [],
                'message': 'Waiting for first screening run...'
            })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'stocks': []
        }), 500

@app.route('/api/status')
def get_status():
    """Get scheduler status"""
    global scheduler
    if scheduler:
        return jsonify(scheduler.get_job_status())
    else:
        return jsonify({'running': False, 'jobs': []})

@app.route('/api/run-now')
def run_now():
    """Manually trigger screening"""
    global scheduler
    try:
        if scheduler:
            scheduler.run_screening_job()
            return jsonify({'success': True, 'message': 'Screening triggered'})
        else:
            return jsonify({'success': False, 'message': 'Scheduler not running'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def initialize_app():
    """Initialize the application with scheduler"""
    global scheduler
    
    try:
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=30)
        print("✅ Scheduler started successfully")
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
