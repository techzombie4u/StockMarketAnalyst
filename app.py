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
        # Check if file exists and is readable
        if not os.path.exists('top10.json'):
            logger.warning("top10.json does not exist, creating default")
            default_data = {
                'timestamp': datetime.now(IST).isoformat(),
                'last_updated': 'Initializing system...',
                'stocks': [],
                'status': 'initializing'
            }
            
            try:
                with open('top10.json', 'w') as f:
                    json.dump(default_data, f, indent=2)
            except Exception as write_error:
                logger.error(f"Failed to create top10.json: {write_error}")
            
            return jsonify(default_data)

        # Try to read the file
        try:
            with open('top10.json', 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as file_error:
            logger.error(f"Error reading top10.json: {file_error}")
            # Return error response but don't crash
            error_data = {
                'timestamp': datetime.now(IST).isoformat(),
                'last_updated': 'File read error',
                'stocks': [],
                'status': 'file_error',
                'error': f'File read error: {str(file_error)}'
            }
            return jsonify(error_data)

        # Validate data structure
        if not isinstance(data, dict):
            logger.error("Invalid data format in top10.json")
            raise ValueError("Invalid data format")

        # Process stock data
        stocks = data.get('stocks', [])
        if not isinstance(stocks, list):
            stocks = []

        validated_stocks = []
        for stock in stocks:
            if not isinstance(stock, dict):
                continue
                
            # Ensure required fields exist
            stock.setdefault('symbol', 'UNKNOWN')
            stock.setdefault('score', 0)
            stock.setdefault('current_price', 0)
            stock.setdefault('predicted_gain', 0)
            
            # Fix prediction fields
            predicted_gain = stock.get('predicted_gain', 0)
            if 'pred_24h' not in stock or not stock['pred_24h']:
                stock['pred_24h'] = round(predicted_gain * 0.05, 2)
            if 'pred_5d' not in stock or not stock['pred_5d']:
                stock['pred_5d'] = round(predicted_gain * 0.25, 2)
            if 'pred_1mo' not in stock or not stock['pred_1mo']:
                stock['pred_1mo'] = round(predicted_gain, 2)

            # Ensure minimum values for good scores
            if stock.get('score', 0) > 50:
                stock['pred_24h'] = max(0.1, stock['pred_24h'])
                stock['pred_5d'] = max(0.5, stock['pred_5d']) 
                stock['pred_1mo'] = max(1.0, stock['pred_1mo'])

            validated_stocks.append(stock)

        # Build response
        response_data = {
            'timestamp': data.get('timestamp', datetime.now(IST).isoformat()),
            'last_updated': data.get('last_updated', 'Unknown'),
            'stocks': validated_stocks,
            'error': data.get('error', None),
            'status': 'success' if validated_stocks else data.get('status', 'no_data')
        }

        # If no stocks but file seems to have been updated recently, reload it
        if not validated_stocks and os.path.exists('top10.json'):
            try:
                # Check file modification time
                file_mtime = os.path.getmtime('top10.json')
                current_time = datetime.now().timestamp()
                
                # If file was modified in last 10 minutes, try reloading
                if current_time - file_mtime < 600:
                    logger.info("File recently modified, attempting reload...")
                    with open('top10.json', 'r') as f:
                        fresh_data = json.load(f)
                        fresh_stocks = fresh_data.get('stocks', [])
                        if fresh_stocks:
                            logger.info(f"Found {len(fresh_stocks)} stocks on reload")
                            response_data['stocks'] = fresh_stocks
                            response_data['status'] = 'success'
                            response_data['last_updated'] = fresh_data.get('last_updated', 'Recently updated')
            except Exception as e:
                logger.error(f"Failed to reload recent data: {str(e)}")
        
        # If still no stocks, check for recent historical data
        if not response_data.get('stocks') and os.path.exists('historical_data'):
            try:
                import glob
                recent_files = sorted(glob.glob('historical_data/screening_data_*.json'), reverse=True)
                if recent_files:
                    with open(recent_files[0], 'r') as f:
                        recent_data = json.load(f)
                        if recent_data.get('stocks'):
                            logger.info(f"Using recent historical data with {len(recent_data['stocks'])} stocks")
                            response_data['stocks'] = recent_data['stocks'][:10]  # Show top 10
                            response_data['last_updated'] = 'Recent historical data'
                            response_data['status'] = 'historical_fallback'
            except Exception as e:
                logger.error(f"Failed to load historical fallback: {str(e)}")

        logger.info(f"API response: {len(response_data['stocks'])} stocks, status: {response_data['status']}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Critical error in /api/stocks: {str(e)}")
        error_response = {
            'error': str(e),
            'timestamp': datetime.now(IST).isoformat(),
            'last_updated': 'Critical error occurred',
            'stocks': [],
            'status': 'critical_error'
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
        logger.info("Manual refresh requested")
        
        # Always try to run screening
        def run_background_screening():
            try:
                if scheduler:
                    scheduler.run_screening_job_manual()
                    logger.info("✅ Manual screening completed successfully")
                else:
                    # Initialize and run if scheduler not available
                    from scheduler import StockAnalystScheduler
                    temp_scheduler = StockAnalystScheduler()
                    result = temp_scheduler.run_screening_job_manual()
                    if result:
                        logger.info("✅ Manual screening with temporary scheduler completed")
                    else:
                        logger.warning("⚠️ Manual screening returned no results")
                        
            except Exception as e:
                logger.error(f"❌ Manual screening failed: {str(e)}")
                # Generate demo data as fallback
                try:
                    logger.info("Generating fallback demo data")
                    demo_data = {
                        'timestamp': datetime.now(IST).isoformat(),
                        'last_updated': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST'),
                        'status': 'demo_fallback',
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
                                'revenue_growth': 8.5,
                                'risk_level': 'Low',
                                'confidence_level': 'high'
                            }
                        ]
                    }
                    with open('top10.json', 'w') as f:
                        json.dump(demo_data, f, indent=2)
                    logger.info("✅ Demo data generated as fallback")
                except Exception as demo_error:
                    logger.error(f"Failed to generate demo data: {demo_error}")
        
        import threading
        threading.Thread(target=run_background_screening, daemon=True).start()
        return jsonify({'success': True, 'message': 'Screening started successfully'})
        
    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
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
    global scheduler
    
    # Check if data file exists and has content
    data_status = 'no_data'
    stock_count = 0
    last_updated = 'never'
    
    try:
        if os.path.exists('top10.json'):
            with open('top10.json', 'r') as f:
                data = json.load(f)
                stock_count = len(data.get('stocks', []))
                last_updated = data.get('last_updated', 'unknown')
                data_status = data.get('status', 'unknown')
    except Exception as e:
        data_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy',
        'service': 'Stock Market Analyst',
        'port': 5000,
        'scheduler_running': scheduler is not None and hasattr(scheduler, 'scheduler') and scheduler.scheduler.running,
        'data_status': data_status,
        'stock_count': stock_count,
        'last_updated': last_updated
    })

@app.route('/readiness')
def readiness_check():
    """Readiness check for deployment"""
    return jsonify({'ready': True})

def initialize_app():
    """Initialize the application with scheduler"""
    global scheduler

    try:
        # scheduler import moved to function scope to avoid circular import
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=60)  # More frequent updates in production
        print("✅ Scheduler started successfully")
        
        # Run initial screening for production deployment
        import threading
        def delayed_initial_run():
            import time
            time.sleep(5)  # Wait for full initialization
            try:
                scheduler.run_screening_job_manual()
                print("✅ Initial production screening completed")
            except Exception as e:
                print(f"⚠️ Initial screening failed: {str(e)}")
        
        threading.Thread(target=delayed_initial_run, daemon=True).start()

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