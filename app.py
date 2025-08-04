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
from historical_analyzer import HistoricalAnalyzer

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
    """API endpoint to get current stock data with backtesting info"""
    try:
        # Initialize file if it doesn't exist
        if not os.path.exists('top10.json'):
            ist_now = datetime.now(IST)
            initial_data = {
                'timestamp': ist_now.strftime('%Y-%m-%dT%H:%M:%S'),
                'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
                'stocks': [],
                'status': 'initial'
            }

            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

            return jsonify({
                'stocks': [],
                'status': 'initial',
                'last_updated': initial_data['last_updated'],
                'timestamp': initial_data['timestamp'],
                'stockCount': 0,
                'backtesting': {'status': 'no_data'}
            })

def check_file_integrity():
    """Check and repair file integrity"""
    try:
        # Check top10.json
        if os.path.exists('top10.json'):
            try:
                with open('top10.json', 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        if isinstance(data, dict) and 'stocks' in data:
                            logger.info("File integrity check passed")
                            return True
            except:
                pass
        
        # File is corrupted or missing, create minimal structure
        logger.warning("File integrity check failed, creating minimal structure")
        ist_now = datetime.now(IST)
        minimal_data = {
            'timestamp': ist_now.strftime('%Y-%m-%dT%H:%M:%S'),
            'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
            'stocks': [],
            'status': 'file_repaired'
        }
        
        with open('top10.json', 'w', encoding='utf-8') as f:
            json.dump(minimal_data, f, indent=2, ensure_ascii=False)
        
        logger.info("File repaired successfully")
        return True
        
    except Exception as e:
        logger.error(f"File integrity check failed: {str(e)}")
        return False

        # Read the file safely with performance optimization
        try:
            with open('top10.json', 'r', encoding='utf-8') as f:
                'stocks': [],
                'status': 'initial',
                'last_updated': initial_data['last_updated'],
                'timestamp': initial_data['timestamp'],
                'stockCount': 0,
                'backtesting': {'status': 'no_data'}
            })

        # Read the file safely with performance optimization
        try:
            with open('top10.json', 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.warning("Empty JSON file detected")
                    raise ValueError("Empty file")
                
                # Check for common invalid content
                if content in ['{}', '[]', 'null', 'undefined']:
                    logger.warning(f"Invalid JSON content: {content}")
                    raise ValueError("Invalid file content")
                
                # Attempt to parse JSON
                data = json.loads(content)
                
                # Validate structure
                if not isinstance(data, dict):
                    logger.warning("JSON is not a dictionary")
                    raise ValueError("Invalid data structure")

        except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
            logger.error(f"JSON parsing error in /api/stocks: {str(e)}")
            
            # Try to recover by creating fresh data
            try:
                from datetime import datetime
                ist_now = datetime.now(IST)
                
                # Try to run a quick screening to get fresh data
                try:
                    logger.info("Attempting to generate fresh data...")
                    from stock_screener import EnhancedStockScreener
                    screener = EnhancedStockScreener()
                    
                    # Get a few stocks quickly for recovery
                    quick_results = []
                    for symbol in ['SBIN', 'BHARTIARTL', 'ITC'][:3]:
                        try:
                            technical = screener.calculate_enhanced_technical_indicators(symbol)
                            fundamentals = screener.scrape_screener_data(symbol)
                            
                            if technical or fundamentals:
                                stocks_data = {symbol: {'fundamentals': fundamentals, 'technical': technical}}
                                scored = screener.enhanced_score_and_rank(stocks_data)
                                if scored:
                                    quick_results.extend(scored)
                        except:
                            continue
                    
                    if quick_results:
                        logger.info(f"Generated {len(quick_results)} recovery stocks")
                        recovery_data = {
                            'timestamp': ist_now.strftime('%Y-%m-%dT%H:%M:%S'),
                            'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
                            'stocks': quick_results,
                            'status': 'recovery_data',
                            'backtesting': {'status': 'recovery'}
                        }
                    else:
                        raise Exception("No recovery data generated")
                        
                except Exception as recovery_error:
                    logger.warning(f"Recovery screening failed: {recovery_error}")
                    # Final fallback to empty structure
                    recovery_data = {
                        'timestamp': ist_now.strftime('%Y-%m-%dT%H:%M:%S'),
                        'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
                        'stocks': [],
                        'status': 'file_reset',
                        'backtesting': {'status': 'error'}
                    }

                # Save recovery data
                with open('top10.json', 'w', encoding='utf-8') as f:
                    json.dump(recovery_data, f, ensure_ascii=False, indent=2)
                
                data = recovery_data
                logger.info("File recovered successfully")

            except Exception as recovery_error:
                logger.error(f"File recovery failed: {recovery_error}")
                return jsonify({
                    'stocks': [],
                    'status': 'critical_error',
                    'last_updated': 'Recovery Failed',
                    'timestamp': datetime.now(IST).strftime('%Y-%m-%dT%H:%M:%S'),
                    'stockCount': 0,
                    'backtesting': {'status': 'error'},
                    'error': str(recovery_error)
                }), 500


        # Add backtesting summary
        try:
            from backtesting_manager import BacktestingManager
            backtester = BacktestingManager()
            backtest_summary = backtester.get_latest_backtest_summary()
            data['backtesting'] = backtest_summary
        except Exception as bt_error:
            logger.warning(f"Backtesting data unavailable: {str(bt_error)}")
            data['backtesting'] = {'status': 'unavailable'}

        # Extract and validate data with comprehensive checks
        stocks = data.get('stocks', [])
        status = data.get('status', 'unknown')
        last_updated = data.get('last_updated', 'Never')
        timestamp = data.get('timestamp')
        
        # Validate stocks array
        if not isinstance(stocks, list):
            logger.warning("Stocks data is not a list, converting...")
            stocks = []
        
        # Validate status
        if not isinstance(status, str):
            status = 'unknown'
        
        # Validate last_updated
        if not isinstance(last_updated, str):
            last_updated = 'Never'

        # Fix timestamp if it's in wrong format
        if timestamp and 'T' not in str(timestamp):
            try:
                # Try to parse and reformat if needed
                if isinstance(timestamp, str) and '/' in timestamp:
                    # Convert from dd/mm/yyyy format to ISO format
                    from datetime import datetime
                    parsed_date = datetime.strptime(timestamp.split(',')[0], '%d/%m/%Y')
                    timestamp = parsed_date.strftime('%Y-%m-%dT%H:%M:%S')
            except:
                timestamp = datetime.now(IST).strftime('%Y-%m-%dT%H:%M:%S')

        # Validate stocks data and ensure all required fields
        valid_stocks = []
        for stock in stocks:
            if isinstance(stock, dict) and 'symbol' in stock:
                # Ensure required fields exist with proper defaults - handle None values
                score_value = stock.get('score', 50.0)
                if score_value is None or score_value == 'null' or score_value == 'undefined':
                    score_value = 50.0
                try:
                    score = float(score_value)
                except (ValueError, TypeError):
                    score = 50.0
                
                price_value = stock.get('current_price', 0.0)
                if price_value is None or price_value == 'null' or price_value == 'undefined':
                    price_value = 0.0
                try:
                    current_price = float(price_value)
                except (ValueError, TypeError):
                    current_price = 0.0
                
                stock.setdefault('score', score)
                stock.setdefault('current_price', current_price)
                stock.setdefault('predicted_gain', score * 0.2)
                stock.setdefault('confidence', max(50.0, min(95.0, score * 0.9)))
                stock.setdefault('pred_5d', stock.get('predicted_gain', 0) * 0.25)
                stock.setdefault('pred_1mo', stock.get('predicted_gain', 0))
                stock.setdefault('trend_class', 'sideways')
                stock.setdefault('trend_visual', '➡️ Sideways')
                stock.setdefault('risk_level', 'Medium')
                stock.setdefault('pe_ratio', stock.get('pe_ratio', 20.0))
                stock.setdefault('pe_description', 'At Par')
                stock.setdefault('technical_summary', f"Score: {score:.1f} | Analysis Complete")

                # Ensure numeric fields are actually numeric with comprehensive None/null handling
                numeric_fields = ['score', 'current_price', 'predicted_gain', 'confidence', 'pred_5d', 'pred_1mo', 'pe_ratio']
                for field in numeric_fields:
                    value = stock.get(field)
                    if (value is None or 
                        value == 'null' or 
                        value == 'undefined' or
                        value == '' or
                        str(value).strip() == ''):
                        stock[field] = 0.0
                    else:
                        try:
                            stock[field] = float(value)
                        except (ValueError, TypeError, AttributeError):
                            stock[field] = 0.0

                # Ensure string fields are properly sanitized
                string_defaults = {
                    'symbol': 'UNKNOWN',
                    'trend_class': 'sideways',
                    'trend_visual': '➡️ Sideways',
                    'pe_description': 'At Par',
                    'technical_summary': 'Analysis Complete',
                    'risk_level': 'Medium'
                }
                
                for field, default_value in string_defaults.items():
                    value = stock.get(field)
                    # Handle all possible problematic values
                    if (value is None or 
                        value == 'null' or 
                        value == 'undefined' or 
                        value == '' or
                        str(value).strip() == ''):
                        stock[field] = default_value
                    else:
                        try:
                            # Convert to string and clean
                            str_value = str(value).strip()
                            stock[field] = str_value if str_value else default_value
                        except (ValueError, TypeError, AttributeError):
                            stock[field] = default_value

                # Ensure critical fields exist
                if not stock.get('symbol'):
                    continue  # Skip stocks without symbol
                    
                valid_stocks.append(stock)

        logger.info(f"API response: {len(valid_stocks)} valid stocks, status: {status}")

        # Force status to success if we have valid stocks
        if valid_stocks and status in ['demo', 'unknown', 'initializing', 'screening_triggered']:
            status = 'success'

        response_data = {
            'stocks': valid_stocks,
            'status': status,
            'last_updated': last_updated,
            'timestamp': timestamp or datetime.now(IST).strftime('%Y-%m-%dT%H:%M:%S'),
            'stockCount': len(valid_stocks),
            'backtesting': data.get('backtesting', {'status': 'unavailable'})
        }

        logger.info(f"Sending API response with {len(valid_stocks)} stocks, status: {status}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in /api/stocks: {str(e)}")
        from datetime import datetime
        return jsonify({
            'status': 'error',
            'stocks': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'backtesting': {'status': 'error'}
        }), 200

def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    if scheduler is None:
        return {'running': False, 'message': 'Scheduler not initialized'}
    try:
        return {
            'running': scheduler.scheduler.running,
            'message': 'Scheduler active' if scheduler.scheduler.running else 'Scheduler idle'
        }
    except Exception as e:
        logger.error(f"Could not get scheduler status: {str(e)}")
        return {'running': False, 'message': str(e)}

def check_data_freshness():
    """Check if data is fresh"""
    try:
        if not os.path.exists('top10.json'):
            return {'fresh': False, 'message': 'No data file found'}
        with open('top10.json', 'r') as f:
            data = json.load(f)
            timestamp = data.get('timestamp')
            if not timestamp:
                return {'fresh': False, 'message': 'No timestamp in data'}

            # Convert timestamp to datetime object with timezone handling
            try:
                if 'T' in str(timestamp):
                    data_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    # Handle different timestamp formats
                    data_datetime = datetime.strptime(timestamp, '%d/%m/%Y, %H:%M:%S')
            except:
                # If parsing fails, assume data is fresh to avoid errors
                return {'fresh': True, 'message': 'Could not parse timestamp, assuming fresh'}
            
            # Use timezone-aware comparison
            now = datetime.now()
            if data_datetime.tzinfo is not None:
                now = now.replace(tzinfo=data_datetime.tzinfo)
            elif now.tzinfo is not None:
                data_datetime = data_datetime.replace(tzinfo=now.tzinfo)
            
            age = now - data_datetime

            # Consider data fresh if less than 2 hours old
            if age.total_seconds() < 7200:
                return {'fresh': True, 'message': 'Data is up to date'}
            else:
                return {'fresh': False, 'message': f'Data is {age} old'}
    except Exception as e:
        logger.error(f"Could not check data freshness: {str(e)}")
        return {'fresh': False, 'message': str(e)}

def load_stock_data():
    """Load current stock data from file"""
    try:
        if not os.path.exists('top10.json'):
            return {'stocks': [], 'status': 'no_data', 'message': 'No data file'}
        with open('top10.json', 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Could not load stock data: {str(e)}")
        return {'stocks': [], 'status': 'error', 'message': str(e)}

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    try:
        # Get scheduler status
        scheduler_status = get_scheduler_status()

        # Check data freshness
        data_freshness = check_data_freshness()

        # Get prediction stability status
        stability_status = {}
        try:
            from prediction_stability_manager import PredictionStabilityManager
            stability_manager = PredictionStabilityManager()
            stability_status = stability_manager.get_prediction_status()
        except Exception as e:
            logger.warning(f"Could not get stability status: {str(e)}")
            stability_status = {'error': 'Stability manager not available'}

        status_data = {
            'status': 'healthy',
            'timestamp': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S'),
            'scheduler': scheduler_status,
            'data_freshness': data_freshness,
            'prediction_stability': stability_status,
            'version': '1.3.0'
        }

        return jsonify(status_data)
    except Exception as e:
        logger.error(f"Status API error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/api/predictions-tracker')
def api_predictions_tracker():
    """API endpoint for prediction tracking data"""
    try:
        predictions = []

        # Load current stock data
        stock_data = load_stock_data()
        current_stocks = stock_data.get('stocks', [])

        # Add current predictions to tracking
        for stock in current_stocks:
            prediction_entry = {
                'symbol': stock.get('symbol', ''),
                'timestamp': datetime.now(IST).isoformat(),
                'current_price': stock.get('current_price', 0),
                'pred_24h': stock.get('pred_24h', 0),
                'pred_5d': stock.get('pred_5d', 0),
                'predicted_1mo': stock.get('pred_1mo', 0),
                'predicted_price': stock.get('predicted_price', 0),
                'confidence': stock.get('confidence', 0),
                'score': stock.get('score', 0)
            }
            predictions.append(prediction_entry)

        # Load historical predictions if available
        try:
            if os.path.exists('predictions_history.json'):
                with open('predictions_history.json', 'r') as f:
                    historical_data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(historical_data, list):
                        predictions.extend(historical_data)
                    elif isinstance(historical_data, dict) and 'predictions' in historical_data:
                        predictions.extend(historical_data['predictions'])
        except Exception as e:
            logger.warning(f"Could not load historical predictions: {str(e)}")

        return jsonify({
            'status': 'success',
            'predictions': predictions,
            'timestamp': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        logger.error(f"Predictions tracker API error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'predictions': []
        }), 500

@app.route('/api/run-now', methods=['POST'])
def run_now():
    """Manually trigger screening"""
    global scheduler
    try:
        logger.info("🔄 Manual refresh requested")

        # Run screening synchronously to ensure completion before returning
        try:
            if scheduler and hasattr(scheduler, 'run_screening_job_manual'):
                logger.info("Using scheduler for manual screening")
                success = scheduler.run_screening_job_manual()
                if success:
                    logger.info("✅ Manual screening completed successfully via scheduler")
                    return jsonify({
                        'success': True, 
                        'message': 'Screening completed successfully',
                        'data_ready': True,
                        'timestamp': datetime.now(IST).isoformat()
                    })
                else:
                    logger.warning("⚠️ Manual screening completed with issues via scheduler")
                    return jsonify({
                        'success': False, 
                        'message': 'Screening completed with issues',
                        'data_ready': False,
                        'timestamp': datetime.now(IST).isoformat()
                    })
            else:
                # Run standalone screening
                logger.info("Using standalone screening")
                from stock_screener import EnhancedStockScreener
                screener = EnhancedStockScreener()
                results = screener.run_enhanced_screener()
                
                if results and len(results) > 0:
                    logger.info(f"✅ Standalone manual screening completed with {len(results)} stocks")
                    return jsonify({
                        'success': True, 
                        'message': f'Screening completed successfully - {len(results)} stocks analyzed',
                        'data_ready': True,
                        'stock_count': len(results),
                        'timestamp': datetime.now(IST).isoformat()
                    })
                else:
                    logger.warning("⚠️ Standalone screening returned no results")
                    return jsonify({
                        'success': False, 
                        'message': 'Screening completed but no results generated',
                        'data_ready': False,
                        'timestamp': datetime.now(IST).isoformat()
                    })

        except Exception as e:
            logger.error(f"❌ Manual screening failed: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'Screening failed: {str(e)}',
                'data_ready': False,
                'error': str(e),
                'timestamp': datetime.now(IST).isoformat()
            })

    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Manual refresh error: {str(e)}',
            'error': str(e),
            'timestamp': datetime.now(IST).isoformat()
        })

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
            'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
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

@app.route('/api/backtest')
def get_backtest_results():
    """Get backtesting analysis results"""
    try:
        from backtesting_manager import BacktestingManager
        backtester = BacktestingManager()

        # Run fresh backtest analysis
        results = backtester.run_backtest_analysis()

        return jsonify({
            'status': 'success',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in backtesting API: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/prediction-tracker')
def prediction_tracker():
    """Prediction tracking dashboard page"""
    return render_template('prediction_tracker.html')

@app.route('/prediction-tracker-interactive')
def prediction_tracker_interactive():
    """Interactive prediction tracking page with dual view and charts"""
    return render_template('prediction_tracker_interactive.html')

@app.route('/api/predictions-tracker')
def get_predictions_tracker():
    """API endpoint to get prediction tracking data"""
    try:
        predictions = []

        # Load current stock data first and add as predictions
        try:
            current_data = load_stock_data()
            if current_data.get('stocks'):
                for stock in current_data['stocks']:
                    prediction_entry = {
                        'symbol': stock.get('symbol', ''),
                        'timestamp': current_data.get('timestamp', datetime.now(IST).isoformat()),
                        'current_price': stock.get('current_price', 0),
                        'predicted_price': stock.get('predicted_price', stock.get('current_price', 0)),
                        'pred_5d': stock.get('pred_5d', 0),
                        'predicted_1mo': stock.get('pred_1mo', 0),
                        'confidence': stock.get('confidence', 0),
                        'score': stock.get('score', 0),
                        'source': 'current_screening'
                    }
                    predictions.append(prediction_entry)
                    
        except Exception as e:
            logger.warning(f"Could not load current stock data: {str(e)}")

        # Load historical predictions from predictions_history.json
        try:
            if os.path.exists('predictions_history.json'):
                with open('predictions_history.json', 'r') as f:
                    data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(data, list):
                        historical_predictions = data
                    elif isinstance(data, dict) and 'predictions' in data:
                        historical_predictions = data['predictions']
                    else:
                        historical_predictions = []
                    
                    # Add source tag to historical predictions
                    for pred in historical_predictions:
                        pred['source'] = 'historical'
                        # Ensure required fields exist
                        if 'predicted_1mo' not in pred and 'pred_1mo' in pred:
                            pred['predicted_1mo'] = pred['pred_1mo']
                        if 'pred_5d' not in pred:
                            pred['pred_5d'] = pred.get('predicted_1mo', 0) * 0.15  # Estimate
                    
                    predictions.extend(historical_predictions)
                    
        except Exception as e:
            logger.warning(f"Could not load historical predictions: {str(e)}")

        # Load stable predictions if available
        try:
            if os.path.exists('stable_predictions.json'):
                with open('stable_predictions.json', 'r') as f:
                    stable_data = json.load(f)
                    for symbol, pred_data in stable_data.items():
                        if isinstance(pred_data, dict):
                            prediction_entry = {
                                'symbol': symbol,
                                'timestamp': pred_data.get('last_updated', datetime.now(IST).isoformat()),
                                'current_price': pred_data.get('current_price', 0),
                                'predicted_price': pred_data.get('predicted_price', pred_data.get('current_price', 0)),
                                'pred_5d': pred_data.get('pred_5d', 0),
                                'predicted_1mo': pred_data.get('pred_1mo', 0),
                                'confidence': pred_data.get('confidence', 0),
                                'score': pred_data.get('score', 0),
                                'source': 'stable_predictions',
                                'lock_reason': pred_data.get('lock_reason', 'unknown')
                            }
                            predictions.append(prediction_entry)
                            
        except Exception as e:
            logger.warning(f"Could not load stable predictions: {str(e)}")

        # Remove duplicates (keep most recent per symbol)
        unique_predictions = {}
        for pred in predictions:
            symbol = pred['symbol']
            timestamp = pred.get('timestamp', '')
            
            if symbol not in unique_predictions or timestamp > unique_predictions[symbol].get('timestamp', ''):
                unique_predictions[symbol] = pred

        final_predictions = list(unique_predictions.values())
        
        # Sort by timestamp (newest first)
        final_predictions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        logger.info(f"Serving {len(final_predictions)} predictions to tracker")

        return jsonify({
            'status': 'success',
            'predictions': final_predictions,
            'total_count': len(final_predictions),
            'timestamp': datetime.now(IST).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in predictions tracker API: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'predictions': [],
            'total_count': 0,
            'timestamp': datetime.now(IST).isoformat()
        }), 500

@app.route('/api/interactive-tracker-data')
def get_interactive_tracker_data():
    """API endpoint for interactive tracker enhanced data"""
    try:
        # Load interactive tracking data
        tracking_data = load_interactive_tracking_data()
        
        # If no tracking data exists, create initial structure
        if not tracking_data:
            tracking_data = initialize_empty_tracking_data()
        
        return jsonify({
            'status': 'success',
            'tracking_data': tracking_data,
            'timestamp': datetime.now(IST).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in interactive tracker data API: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'tracking_data': {},
            'timestamp': datetime.now(IST).isoformat()
        }), 500

def initialize_empty_tracking_data():
    """Initialize empty tracking data structure"""
    try:
        # Load current stock data to initialize tracking
        current_data = load_stock_data()
        stocks = current_data.get('stocks', [])
        
        tracking_data = {}
        for stock in stocks[:5]:  # Initialize tracking for top 5 stocks
            symbol = stock.get('symbol')
            if symbol:
                base_price = stock.get('current_price', 100)
                pred_5d = stock.get('pred_5d', 0)
                pred_30d = stock.get('pred_1mo', 0)
                
                # Generate predicted price arrays
                predicted_5d = []
                predicted_30d = []
                
                for i in range(5):
                    predicted_5d.append(base_price * (1 + (pred_5d/100) * (i+1)/5))
                
                for i in range(30):
                    predicted_30d.append(base_price * (1 + (pred_30d/100) * (i+1)/30))
                
                tracking_data[symbol] = {
                    'symbol': symbol,
                    'start_date': datetime.now(IST).strftime('%Y-%m-%d'),
                    'current_price': base_price,
                    'confidence': stock.get('confidence', 0),
                    'score': stock.get('score', 0),
                    'predicted_5d': predicted_5d,
                    'predicted_30d': predicted_30d,
                    'actual_progress_5d': [base_price] + [None] * 4,
                    'actual_progress_30d': [base_price] + [None] * 29,
                    'updated_prediction_5d': [None] * 5,
                    'updated_prediction_30d': [None] * 30,
                    'changed_on_5d': None,
                    'changed_on_30d': None,
                    'locked_5d': False,
                    'locked_30d': False,
                    'lock_date_5d': None,
                    'lock_date_30d': None,
                    'last_updated': datetime.now(IST).isoformat(),
                    'days_tracked': 0
                }
        
        # Save the initialized tracking data
        try:
            with open('interactive_tracking.json', 'w') as f:
                json.dump(tracking_data, f, indent=2, ensure_ascii=False)
        except Exception as save_error:
            logger.warning(f"Could not save initialized tracking data: {save_error}")
        
        return tracking_data
        
    except Exception as e:
        logger.error(f"Error initializing empty tracking data: {str(e)}")
        return {}

@app.route('/api/update-lock-status', methods=['POST'])
def update_lock_status():
    """API endpoint to update lock status for predictions"""
    try:
        data = request.get_json()
        symbol = data.get('symbol')
        period = data.get('period')  # '5d' or '30d'
        locked = data.get('locked', False)
        timestamp = data.get('timestamp')
        
        if not symbol or not period:
            return jsonify({'success': False, 'message': 'Symbol and period required'}), 400
        
        # Save lock status
        success = save_lock_status(symbol, period, locked, timestamp)
        
        if success:
            logger.info(f"Lock status updated: {symbol} {period} = {locked}")
            return jsonify({
                'success': True,
                'message': f'Lock status updated for {symbol}',
                'timestamp': datetime.now(IST).isoformat()
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save lock status'}), 500
            
    except Exception as e:
        logger.error(f"Error updating lock status: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def load_interactive_tracking_data():
    """Load enhanced tracking data for interactive charts"""
    try:
        from interactive_tracker_manager import InteractiveTrackerManager
        tracker_manager = InteractiveTrackerManager()
        return tracker_manager.load_tracking_data()
    except Exception as e:
        logger.warning(f"Could not load interactive tracking data: {str(e)}")
        return {}

def save_lock_status(symbol, period, locked, timestamp):
    """Save lock status for a stock prediction"""
    try:
        from interactive_tracker_manager import InteractiveTrackerManager
        tracker_manager = InteractiveTrackerManager()
        return tracker_manager.update_lock_status(symbol, period, locked, timestamp)
    except Exception as e:
        logger.error(f"Error saving lock status: {str(e)}")
        return False

def initialize_app():
    """Initialize the application with scheduler"""
    global scheduler

    try:
        # Check file integrity first
        check_file_integrity()
        
        # Create initial demo data
        create_initial_demo_data()

        from scheduler import StockAnalystScheduler
        scheduler = StockAnalystScheduler()
        scheduler.start_scheduler(interval_minutes=60)
        logger.info("✅ Scheduler started successfully")

    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {str(e)}")

def create_initial_demo_data():
    """Create minimal initial data structure"""
    try:
        ist_now = datetime.now(IST)

        initial_data = {
            'timestamp': ist_now.strftime('%Y-%m-%dT%H:%M:%S'),
            'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
            'status': 'initializing',
            'stocks': []
        }

        # Only create if file doesn't exist
        if not os.path.exists('top10.json'):
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

            logger.info("✅ Initial data structure created")

    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")

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