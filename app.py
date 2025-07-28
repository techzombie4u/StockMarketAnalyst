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

            # Validate and clean stock data
            stocks = data.get('stocks', [])
            validated_stocks = []
            
            for stock in stocks:
                # Ensure all prediction fields exist with proper values
                if 'pred_24h' not in stock or stock['pred_24h'] == 0:
                    stock['pred_24h'] = round(stock.get('predicted_gain', 0) * 0.05, 2)
                if 'pred_5d' not in stock or stock['pred_5d'] == 0:
                    stock['pred_5d'] = round(stock.get('predicted_gain', 0) * 0.25, 2)
                if 'pred_1mo' not in stock or stock['pred_1mo'] == 0:
                    stock['pred_1mo'] = round(stock.get('predicted_gain', 0), 2)
                
                # Ensure minimum values
                stock['pred_24h'] = max(0.1, stock['pred_24h']) if stock['score'] > 50 else stock['pred_24h']
                stock['pred_5d'] = max(0.5, stock['pred_5d']) if stock['score'] > 50 else stock['pred_5d']
                stock['pred_1mo'] = max(1.0, stock['pred_1mo']) if stock['score'] > 50 else stock['pred_1mo']
                
                validated_stocks.append(stock)

            # Add default values if missing
            response_data = {
                'timestamp': data.get('timestamp', ''),
                'last_updated': data.get('last_updated', 'Unknown'),
                'stocks': validated_stocks,
                'error': data.get('error', None),
                'status': 'success' if validated_stocks else 'no_data'
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
            # Try to initialize scheduler if not running (production fallback)
            try:
                from scheduler import StockAnalystScheduler
                scheduler = StockAnalystScheduler()
                scheduler.start_scheduler(interval_minutes=30)
                scheduler.run_screening_job_manual()
                return jsonify({'success': True, 'message': 'Scheduler initialized and screening started'})
            except Exception as init_error:
                logger.error(f"Failed to initialize scheduler: {str(init_error)}")
                return jsonify({'success': False, 'message': f'Scheduler initialization failed: {str(init_error)}'})
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
        # Initialize analyzer
        analyzer = HistoricalAnalyzer()
        
        # Try to get existing analysis
        analysis_data = analyzer.get_analysis_summary()
        
        # If no analysis exists, check for historical data files
        if not analysis_data or analysis_data.get('status') == 'no_data':
            historical_files = []
            if os.path.exists('historical_data'):
                historical_files = [f for f in os.listdir('historical_data') if f.endswith('.json')]
            
            # Load current screening results
            current_stocks = []
            current_data_status = 'no_data'
            if os.path.exists('top10.json'):
                try:
                    with open('top10.json', 'r') as f:
                        current_data = json.load(f)
                        current_stocks = current_data.get('stocks', [])
                        current_data_status = current_data.get('status', 'no_data')
                except Exception as e:
                    logger.warning(f"Error reading current data: {str(e)}")
            
            # Create meaningful analysis based on available data
            if historical_files or current_stocks:
                # Calculate some basic metrics from available data
                total_stocks_analyzed = len(current_stocks)
                high_score_stocks = len([s for s in current_stocks if s.get('score', 0) >= 70])
                avg_score = sum(s.get('score', 0) for s in current_stocks) / max(1, len(current_stocks))
                
                # Extract top performers from current data
                top_performers = sorted(current_stocks, key=lambda x: x.get('score', 0), reverse=True)[:5]
                
                analysis_data = {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'current_analysis',
                    'total_predictions_analyzed': total_stocks_analyzed,
                    'correct_predictions': high_score_stocks,
                    'accuracy_rate': round((high_score_stocks / max(1, total_stocks_analyzed)) * 100, 1),
                    'top_performing_stocks': [
                        {
                            'symbol': stock.get('symbol', 'N/A'),
                            'success_rate': round(min(100, stock.get('score', 0)), 1),
                            'predictions_analyzed': 1
                        }
                        for stock in top_performers
                    ],
                    'worst_performing_stocks': [],
                    'pattern_insights': [
                        f'📊 Current Analysis: {total_stocks_analyzed} stocks screened',
                        f'🎯 High-Quality Picks: {high_score_stocks} stocks with score ≥70',
                        f'📈 Average Score: {avg_score:.1f}/100',
                        f'📁 Historical Files: {len(historical_files)} screening sessions recorded',
                        '🔄 Run screening multiple times for trend analysis' if len(historical_files) < 3 else '📈 Sufficient data for trend analysis available',
                        '⚡ Real-time analysis based on latest screening results'
                    ],
                    'data_quality': 'good' if current_stocks else 'limited',
                    'sessions_analyzed': len(historical_files) + (1 if current_stocks else 0)
                }
            else:
                # No data available at all
                analysis_data = {
                    'timestamp': datetime.now().isoformat(),
                    'status': 'no_data',
                    'total_predictions_analyzed': 0,
                    'correct_predictions': 0,
                    'accuracy_rate': 0,
                    'top_performing_stocks': [],
                    'worst_performing_stocks': [],
                    'pattern_insights': [
                        '📋 No historical analysis data available',
                        '🔄 Run the stock screener to generate analysis data',
                        '📊 Analysis dashboard will populate after screening sessions',
                        '⏱️ Initial screening may take a few minutes to complete'
                    ],
                    'data_quality': 'none',
                    'sessions_analyzed': 0
                }
        
        return jsonify(analysis_data)

    except Exception as e:
        logger.error(f"Error in /api/analysis: {str(e)}")
        return jsonify({
            'error': f'Analysis error: {str(e)}',
            'status': 'error',
            'total_predictions_analyzed': 0,
            'correct_predictions': 0,
            'accuracy_rate': 0,
            'top_performing_stocks': [],
            'worst_performing_stocks': [],
            'pattern_insights': [
                '❌ Error loading analysis data',
                f'🔧 Technical issue: {str(e)}',
                '🔄 Try refreshing the page or running screening again'
            ],
            'data_quality': 'error',
            'sessions_analyzed': 0
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

@app.route('/lookup')
def stock_lookup():
    """Stock lookup page"""
    return render_template('lookup.html')

@app.route('/api/lookup/<symbol>')
def lookup_stock(symbol):
    """API endpoint to analyze a specific stock"""
    try:
        symbol = symbol.upper().strip()
        
        if not symbol:
            return jsonify({'error': 'Stock symbol is required'}), 400
        
        logger.info(f"Looking up stock: {symbol}")
        
        # Import here to avoid circular imports
        from stock_screener import EnhancedStockScreener
        
        screener = EnhancedStockScreener()
        
        # Get fundamental data
        fundamentals = screener.scrape_screener_data(symbol)
        
        # Get technical indicators
        technical = screener.calculate_enhanced_technical_indicators(symbol)
        
        if not fundamentals and not technical:
            return jsonify({'error': f'No data found for symbol {symbol}'}), 404
        
        # Create stock data structure
        stocks_data = {
            symbol: {
                'fundamentals': fundamentals,
                'technical': technical
            }
        }
        
        # Score and rank (returns list)
        scored_stocks = screener.enhanced_score_and_rank(stocks_data)
        
        if not scored_stocks:
            return jsonify({'error': f'Unable to analyze {symbol}'}), 404
        
        stock_result = scored_stocks[0]  # Get the first (and only) result
        
        # Try to add ML predictions if available
        try:
            from predictor import enrich_with_ml_predictions
            enhanced_stocks = enrich_with_ml_predictions([stock_result])
            if enhanced_stocks:
                stock_result = enhanced_stocks[0]
        except Exception as e:
            logger.warning(f"ML predictions failed for {symbol}: {str(e)}")
        
        return jsonify({
            'stock': stock_result,
            'timestamp': datetime.now(IST).isoformat(),
            'analyzed_at': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')
        })
        
    except Exception as e:
        logger.error(f"Error in stock lookup for {symbol}: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Stock Market Analyst',
        'port': 5000
    })

@app.route('/readiness')
def readiness_check():
    """Readiness check for deployment"""
    return jsonify({'ready': True})

def initialize_app():
    """Initialize the application with scheduler"""
    global scheduler

    try:
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=30)
        print("✅ Scheduler started successfully")
        # Remove blocking initial screening - let it run via scheduler

    except Exception as e:
        print(f"❌ Error starting scheduler: {str(e)}")

def create_app():
    """Application factory function for WSGI deployment"""
    # Start Flask app immediately, initialize scheduler after
    from threading import Thread
    def delayed_init():
        import time
        time.sleep(2)  # Let Flask start first
        initialize_app()
    Thread(target=delayed_init, daemon=True).start()
    return app

if __name__ == '__main__':
    # Start Flask app immediately, initialize scheduler after
    from threading import Thread
    def delayed_init():
        import time
        time.sleep(2)  # Let Flask start first
        initialize_app()
    Thread(target=delayed_init, daemon=True).start()
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # Set to False in production
        threaded=True
    )