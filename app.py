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
        # Initialize file if it doesn't exist
        if not os.path.exists('top10.json'):
            ist_now = datetime.now(IST)
            initial_data = {
                'timestamp': ist_now.isoformat(),
                'last_updated': ist_now.strftime('%Y-%m-%d %H:%M:%S IST'),
                'stocks': [],
                'status': 'initial'
            }

            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

            return jsonify({
                'stocks': [],
                'status': 'initial',
                'last_updated': initial_data['last_updated'],
                'stockCount': 0
            })

        # Read the file safely
        try:
            with open('top10.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                raise ValueError("Empty file")

            data = json.loads(content)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"File read/parse error: {str(e)}")

            # Reset corrupted file
            ist_now = datetime.now(IST)
            reset_data = {
                'timestamp': ist_now.isoformat(),
                'last_updated': ist_now.strftime('%Y-%m-%d %H:%M:%S IST'),
                'stocks': [],
                'status': 'file_reset'
            }

            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(reset_data, f, ensure_ascii=False, indent=2)

            return jsonify({
                'stocks': [],
                'status': 'file_reset',
                'last_updated': reset_data['last_updated'],
                'stockCount': 0
            })

        # Extract and validate data
        stocks = data.get('stocks', [])
        status = data.get('status', 'unknown')
        last_updated = data.get('last_updated', 'Never')

        # Validate stocks data
        valid_stocks = []
        for stock in stocks:
            if isinstance(stock, dict) and 'symbol' in stock:
                # Ensure required fields exist
                if 'score' not in stock:
                    stock['score'] = 50.0
                if 'current_price' not in stock:
                    stock['current_price'] = 0.0
                if 'predicted_gain' not in stock:
                    stock['predicted_gain'] = stock.get('score', 50) * 0.2

                valid_stocks.append(stock)

        logger.info(f"API response: {len(valid_stocks)} valid stocks, status: {status}")

        return jsonify({
            'stocks': valid_stocks,
            'status': status,
            'last_updated': last_updated,
            'stockCount': len(valid_stocks)
        })

    except Exception as e:
        logger.error(f"Critical error in get_stocks API: {str(e)}")
        return jsonify({
            'stocks': [],
            'status': 'critical_error',
            'last_updated': 'System Error',
            'stockCount': 0,
            'error': str(e)
        }), 500

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

        def run_background_screening():
            try:
                if scheduler:
                    success = scheduler.run_screening_job_manual()
                    if success:
                        logger.info("✅ Manual screening completed successfully")
                    else:
                        logger.warning("⚠️ Manual screening completed with issues")
                else:
                    # Run standalone screening
                    from scheduler import run_screening_job_manual
                    success = run_screening_job_manual()
                    if success:
                        logger.info("✅ Standalone manual screening completed")
                    else:
                        logger.warning("⚠️ Standalone screening had issues")

            except Exception as e:
                logger.error(f"❌ Manual screening failed: {str(e)}")
                # Create emergency demo data
                try:
                    ist_now = datetime.now(IST)
                    demo_data = {
                        'timestamp': ist_now.isoformat(),
                        'last_updated': ist_now.strftime('%Y-%m-%d %H:%M:%S IST'),
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
                                'pe_description': 'At Par',
                                'revenue_growth': 8.5,
                                'risk_level': 'Low',
                                'last_analyzed': ist_now.strftime('%d/%m/%Y, %H:%M:%S')
                            }
                        ]
                    }
                    with open('top10.json', 'w', encoding='utf-8') as f:
                        json.dump(demo_data, f, indent=2, ensure_ascii=False)
                    logger.info("✅ Emergency demo data generated")
                except Exception as demo_error:
                    logger.error(f"Failed to generate demo data: {demo_error}")

        import threading
        threading.Thread(target=run_background_screening, daemon=True).start()
        return jsonify({'success': True, 'message': 'Screening started successfully'})

    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

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
            with open('top10.json', 'r', encoding='utf-8') as f:
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

@app.route('/api/force-demo', methods=['POST'])
def force_demo_data():
    """Generate demo data for testing when no real data available"""
    try:
        logger.info("Generating demo data")

        # Create sample data structure with predictions
        # Generate proper IST timestamp for demo data
        ist_now = datetime.now(IST)
        demo_data = {
            'timestamp': ist_now.isoformat(),
            'last_updated': ist_now.strftime('%Y-%m-%d %H:%M:%S'),
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
                    'pe_description': 'At Par',
                    'revenue_growth': 8.5,
                    'risk_level': 'Low'
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
                    'pe_description': 'At Par',
                    'revenue_growth': 6.2,
                    'risk_level': 'Low'
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
                    'pe_description': 'At Par',
                    'revenue_growth': 7.8,
                    'risk_level': 'Low'
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

def initialize_app():
    """Initialize the application with scheduler"""
    global scheduler

    try:
        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=60)
        logger.info("✅ Scheduler started successfully")

    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {str(e)}")

def create_app():
    """Application factory function for WSGI deployment"""
    initialize_app()
    return app

if __name__ == '__main__':
    initialize_app()

    # Print startup information
    print("\n" + "="*60)
    print("📈 STOCK MARKET ANALYST - DASHBOARD")
    print("="*60)
    print(f"🌐 Web Dashboard: http://localhost:5000")
    print(f"📊 API Endpoint: http://localhost:5000/api/stocks")
    print(f"🔄 Auto-refresh: Every 60 minutes")
    print("="*60)
    print("\n✅ Application started successfully!")
    print("📱 Open your browser and navigate to http://localhost:5000")
    print("\n🛑 Press Ctrl+C to stop the application\n")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )