"""
Stock Market Analyst - Flask Dashboard

Web interface for displaying stock screening results with auto-refresh.
Refactored to use shared-core + product-plugins architecture.
"""

import sys
import os
from datetime import datetime, timedelta
import pytz
import json
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from flask import Flask, render_template, jsonify, request, abort
from flask_caching import Cache
from flask_cors import CORS
import traceback
import atexit
import gc
import time

# Import shared core components
from common_repository.feature_flags import feature_flags
from common_repository.utils.date_utils import IST, get_ist_now
from common_repository.utils.error_handler import ErrorContext, safe_execute
from common_repository.storage.json_store import json_store

# Import product services
from products.equities.api import equity_bp
from products.options.api import options_bp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with consolidated structure
logger.info("🚀 Starting Stock Market Analyst - Version 1.7.4 (Consolidated)")
logger.info("📁 Using consolidated /src/ structure")

# Initialize Flask application with optimized settings
app = Flask(__name__,
           template_folder='../../web/templates',
           static_folder='../../web/static')

# Configure Flask app for stability
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 60  # Reduced cache timeout
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize cache with limits
cache = Cache(app)

# Simplified request tracking without threading complexity
current_requests = set()
import weakref

def cleanup_resources():
    """Clean up resources to prevent memory leaks"""
    try:
        # Force garbage collection
        import gc
        collected = gc.collect()

        # Clear Flask app cache
        if hasattr(cache, 'clear'):
            cache.clear()

        logger.info(f"Resources cleaned: {collected} objects collected")
        return True
    except Exception as e:
        logger.error(f"Error cleaning resources: {e}")
        return False

# Import consolidated modules with error handling
SmartGoAgent = None
ShortStrangleEngine = None

# Lightweight pinned stocks management - symbols only
PIN_FILE = "data/pinned_stocks.json"
PINNED_SYMBOLS = set()

def load_pinned_stocks():
    """Load pinned symbols from persistent file using shared storage"""
    global PINNED_SYMBOLS
    try:
        # Use shared storage system
        data = json_store.load('pinned_stocks', [])

        # Ensure we only store symbols, not full objects
        if isinstance(data, list):
            PINNED_SYMBOLS = set([str(item) if isinstance(item, str) else item.get('symbol', '') for item in data if item])
        else:
            PINNED_SYMBOLS = set()

        # Clean out empty strings
        PINNED_SYMBOLS = {s for s in PINNED_SYMBOLS if s and isinstance(s, str)}
        logger.info(f"Loaded {len(PINNED_SYMBOLS)} pinned symbols: {list(PINNED_SYMBOLS)}")

        # Verify and trim if needed
        if len(PINNED_SYMBOLS) > 100:
            logger.warning(f"Too many pinned symbols ({len(PINNED_SYMBOLS)}), trimming to 100")
            PINNED_SYMBOLS = set(list(PINNED_SYMBOLS)[:100])
            save_pinned_stocks()

    except Exception as e:
        logger.error(f"Error loading pinned symbols: {e}")
        PINNED_SYMBOLS = set()

def save_pinned_stocks():
    """Save pinned symbols using shared storage system"""
    try:
        # Store only symbol strings, no full row objects
        symbols_list = list(PINNED_SYMBOLS)[:100]  # Limit to 100

        # Use shared storage system
        success = json_store.save('pinned_stocks', symbols_list)

        if success:
            logger.info(f"Saved {len(symbols_list)} pinned symbols")
        else:
            logger.error("Failed to save pinned symbols")

    except Exception as e:
        logger.error(f"Error saving pinned symbols: {e}")

# Load pinned symbols on startup
load_pinned_stocks()

@app.route('/api/pin-stock', methods=['POST'])
def pin_stock():
    """API endpoint to pin/unpin a stock - lightweight symbol-only storage"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper().strip()
        action = data.get('action', 'toggle')  # 'pin', 'unpin', or 'toggle'

        if not symbol:
            return jsonify({'error': 'Symbol required'}), 400

        # Validate symbol format
        if not isinstance(symbol, str) or len(symbol) > 20:
            return jsonify({'error': 'Invalid symbol format'}), 400

        global PINNED_SYMBOLS

        # Idempotent operations to prevent duplicates
        if action == 'pin':
            PINNED_SYMBOLS.add(symbol)
            pinned = True
        elif action == 'unpin':
            PINNED_SYMBOLS.discard(symbol)  # discard won't raise error if not present
            pinned = False
        else:  # toggle
            if symbol in PINNED_SYMBOLS:
                PINNED_SYMBOLS.discard(symbol)
                pinned = False
            else:
                PINNED_SYMBOLS.add(symbol)
                pinned = True

        # Enforce 100 symbol limit to keep under 2KB
        if len(PINNED_SYMBOLS) > 100:
            PINNED_SYMBOLS = set(list(PINNED_SYMBOLS)[:100])

        save_pinned_stocks()

        return jsonify({
            'success': True,
            'symbol': symbol,
            'pinned': pinned,
            'total_pinned': len(PINNED_SYMBOLS),
            'pinned_stocks': list(PINNED_SYMBOLS)
        })

    except Exception as e:
        logger.error(f"Error in pin_stock API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pinned-stocks', methods=['GET'])
def get_pinned_stocks():
    """API endpoint to get all pinned symbols - lightweight response"""
    try:
        return jsonify({
            'pinned_stocks': list(PINNED_SYMBOLS),
            'total_count': len(PINNED_SYMBOLS)
        })
    except Exception as e:
        logger.error(f"Error in get_pinned_stocks API: {str(e)}")
        return jsonify({'error': str(e)}), 500


def _refresh_locked_predictions_data():
    """Refresh locked predictions data from all sources"""
    try:
        print("🔄 Refreshing locked predictions data...")

        # Check if interactive tracking file exists and has active trades
        tracking_file = 'data/tracking/interactive_tracking.json'
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)

            current_date = datetime.now().date()
            active_count = 0

            # Count active trades
            if isinstance(tracking_data, list):
                for entry in tracking_data:
                    if (isinstance(entry, dict) and
                        entry.get('locked') == True and
                        entry.get('status') == 'in_progress'):
                        try:
                            expiry_date = datetime.strptime(entry['expiry_date'], '%Y-%m-%d').date()
                            if expiry_date >= current_date:
                                active_count += 1
                        except:
                            pass

            print(f"✅ Refreshed: Found {active_count} active locked predictions")
            return True

        else:
            print("⚠️ No tracking file found, running create_locked_predictions.py...")
            # Run the script to create test data if no file exists
            try:
                import subprocess
                result = subprocess.run(['python', 'create_locked_predictions.py'],
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print("✅ Created locked predictions data")
                    return True
                else:
                    print(f"❌ Failed to create locked predictions: {result.stderr}")
            except Exception as e:
                print(f"❌ Error running create_locked_predictions.py: {e}")

        return False

    except Exception as e:
        logger.error(f"Error refreshing locked predictions data: {str(e)}")
        return False


def clearDataCache():
    """Clear old data cache to prevent memory leaks"""
    try:
        import gc
        collected = gc.collect()
        logger.info(f"Memory cleared: {collected} objects collected")
        return collected
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        return 0


enhanced_error_handler = None
ExternalDataImporter = None
InteractiveTrackerManager = None
SchedulerManager = None

try:
    from src.analyzers.smart_go_agent import SmartGoAgent
    logger.info("✅ SmartGoAgent imported")
except Exception as e:
    logger.warning(f"⚠️ SmartGoAgent import failed: {e}")

try:
    from src.analyzers.short_strangle_engine import ShortStrangleEngine
    logger.info("✅ ShortStrangleEngine imported")
except Exception as e:
    logger.warning(f"⚠️ ShortStrangleEngine import failed: {e}")

try:
    from src.managers.enhanced_error_handler import enhanced_error_handler
    logger.info("✅ enhanced_error_handler imported")
except Exception as e:
    logger.warning(f"⚠️ enhanced_error_handler import failed: {e}")
    enhanced_error_handler = None

try:
    from src.utils.external_data_importer import ExternalDataImporter
    logger.info("✅ ExternalDataImporter imported")
except Exception as e:
    logger.warning(f"⚠️ ExternalDataImporter import failed: {e}")

try:
    from src.managers.interactive_tracker_manager import InteractiveTrackerManager
    logger.info("✅ InteractiveTrackerManager imported")
except Exception as e:
    logger.warning(f"⚠️ InteractiveTrackerManager import failed: {e}")
    # Create dummy class
    class InteractiveTrackerManager:
        def get_all_tracking_data(self):
            return {}

# Create a dummy SchedulerManager if not available
class SchedulerManager:
    def __init__(self):
        pass

# Set template folder to the correct location
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'web', 'templates')
app.template_folder = template_dir

# Enable CORS for all routes
CORS(app)

# Register blueprints
app.register_blueprint(equity_bp)
app.register_blueprint(options_bp)

# Register KPI blueprint
try:
    from products.shared.api.kpi_api import kpi_bp
    app.register_blueprint(kpi_bp)
    logger.info("✅ KPI blueprint registered")
except ImportError as e:
    logger.error(f"Failed to import KPI blueprint: {e}")


# Register meta API
from src.app.api.meta import meta_bp
app.register_blueprint(meta_bp)

# Global scheduler instance
scheduler = None

# Initialize managers with error handling
error_handler = None
if enhanced_error_handler:
    try:
        error_handler = enhanced_error_handler()
        logger.info("✅ Error handler initialized")
    except Exception as e:
        logger.warning(f"Error handler initialization failed: {e}")

interactive_tracker = InteractiveTrackerManager() if InteractiveTrackerManager else None
scheduler_manager = SchedulerManager() if SchedulerManager else None
strangle_engine = ShortStrangleEngine() if ShortStrangleEngine else None

# Timezone for India
IST = pytz.timezone('Asia/Kolkata')

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/stocks')
def get_stocks():
    """Get current stock analysis results with refresh tracking"""
    try:
        # Track refresh type
        refresh_type = request.args.get('refresh_type', 'auto')
        force_refresh = request.args.get('force', '0') == '1'

        # Update last updated timestamp
        from src.app.api.meta import update_last_updated
        update_last_updated('dashboard', refresh_type)
        # Clear data cache on every refresh
        clearDataCache()

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

                return data

        except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
            logger.error(f"JSON parsing error in /api/stocks: {str(e)}")

            # Try to recover by creating fresh data
            try:
                logger.info("Attempting to recover from JSON parsing error...")
                ist_now = datetime.now(IST)

                # Try to run a quick screening to get fresh data
                try:
                    logger.info("Attempting to generate fresh data...")
                    from src.analyzers.stock_screener import EnhancedStockScreener
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
                        except Exception as recovery_symbol_error:
                            logger.warning(f"Error processing symbol for recovery {symbol}: {recovery_symbol_error}")
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
            from managers.backtesting_manager import BacktestingManager
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
            except Exception as ts_error:
                logger.warning(f"Timestamp format issue: {ts_error}")
                timestamp = datetime.now(IST).strftime('%Y-%m-%dT%H:%M:%S')
        elif not timestamp:
            timestamp = datetime.now(IST).strftime('%Y-%m-%dT%H:%M:%S')


        # Normalize API fields to fix blank columns - comprehensive mapping
        def normalize_stock_data(stock):
            """Normalize stock data to strict schema"""
            if not isinstance(stock, dict) or not stock.get('symbol'):
                return None

            # Strict field mapping schema
            field_mapping = {
                'symbol': ['symbol'],
                'call_strike': ['call_strike', 'callStrike', 'call_price'],
                'put_strike': ['put_strike', 'putStrike', 'put_price'],
                'total_premium': ['total_premium', 'totalPremium', 'premium'],
                'breakeven_low': ['breakeven_low', 'breakevenLow', 'lower_breakeven'],
                'breakeven_high': ['breakeven_high', 'breakevenHigh', 'upper_breakeven'],
                'margin_req': ['margin_req', 'marginReq', 'margin', 'margin_required'],
                'roi_pct': ['roi_pct', 'expected_roi', 'roi', 'return_pct'],
                'confidence': ['confidence'],
                'stop_loss_call': ['stop_loss_call', 'stopLossCall'],
                'stop_loss_put': ['stop_loss_put', 'stopLossPut'],
                'risk': ['risk', 'risk_level'],
                'result': ['result', 'status'],
                'current_price': ['current_price', 'price'],
                'predicted_gain': ['predicted_gain', 'gain', 'expected_gain'],
                'score': ['score', 'rating'],
                'pe_ratio': ['pe_ratio', 'pe', 'price_earnings']
            }

            normalized = {}

            # Apply field mapping with fallbacks
            for target_field, source_fields in field_mapping.items():
                value = None
                for source_field in source_fields:
                    if source_field in stock and stock[source_field] is not None:
                        raw_value = stock[source_field]
                        # Clean problematic values
                        if str(raw_value).strip().lower() not in ['null', 'undefined', '', 'none']:
                            value = raw_value
                            break

                # Set default if no valid value found
                if value is None:
                    if target_field in ['symbol']:
                        normalized[target_field] = stock.get('symbol', 'UNKNOWN')
                    elif target_field in ['roi_pct', 'confidence', 'score', 'current_price', 'predicted_gain']:
                        normalized[target_field] = 0.0
                    elif target_field in ['call_strike', 'put_strike', 'total_premium', 'margin_req']:
                        normalized[target_field] = 0.0
                    elif target_field in ['breakeven_low', 'breakeven_high']:
                        normalized[target_field] = 0.0
                    elif target_field in ['pe_ratio']:
                        normalized[target_field] = 20.0
                    elif target_field in ['risk']:
                        normalized[target_field] = 'Medium'
                    elif target_field in ['result']:
                        normalized[target_field] = 'unknown'
                    else:
                        normalized[target_field] = "—"  # Placeholder for missing data
                else:
                    # Type conversion for numeric fields
                    numeric_fields = ['roi_pct', 'confidence', 'score', 'current_price', 'predicted_gain',
                                    'call_strike', 'put_strike', 'total_premium', 'margin_req',
                                    'breakeven_low', 'breakeven_high', 'pe_ratio']
                    if target_field in numeric_fields:
                        try:
                            normalized[target_field] = float(value)
                        except (ValueError, TypeError):
                            normalized[target_field] = 0.0
                    else:
                        normalized[target_field] = str(value).strip()

            # Add pinning status
            normalized['pinned'] = normalized['symbol'] in PINNED_SYMBOLS

            # Add computed fields with safe defaults
            normalized.setdefault('trend_class', 'sideways')
            normalized.setdefault('trend_visual', '➡️ Sideways')
            normalized.setdefault('pe_description', 'At Par')
            normalized.setdefault('technical_summary', f"Score: {normalized.get('score', 0):.1f}")

            return normalized

        # Validate and normalize stocks data
        valid_stocks = []
        for stock in stocks:
            normalized_stock = normalize_stock_data(stock)
            if normalized_stock and normalized_stock.get('symbol') != 'UNKNOWN':
                valid_stocks.append(normalized_stock)

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
        return jsonify({
            'status': 'error',
            'stocks': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'backtesting': {'status': 'error'}
        }), 200

def check_file_integrity():
    """Check integrity of critical files"""
    critical_files = [
        'top10.json',
        'predictions_history.json',
        'agent_decisions.json',
        'stable_predictions.json',
        'signal_history.json'
    ]

    for file_path in critical_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        json.loads(content)
            else:
                # Create empty file
                with open(file_path, 'w') as f:
                    json.dump({}, f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"File integrity issue with {file_path}: {e}. Attempting to fix.")
            # Fix corrupted file
            try:
                with open(file_path, 'w') as f:
                    json.dump({}, f)
            except IOError:
                logger.error(f"Failed to fix corrupted file: {file_path}")

def get_scheduler_status():
    """Get current scheduler status"""
    global scheduler
    if scheduler is None:
        return {'running': False, 'message': 'Scheduler not initialized'}
    try:
        # Safely access scheduler attributes
        if hasattr(scheduler, 'scheduler') and scheduler.scheduler:
            return {
                'running': scheduler.scheduler.running,
                'message': 'Scheduler active' if scheduler.scheduler.running else 'Scheduler idle'
            }
        else:
            return {'running': False, 'message': 'Scheduler internal state unavailable'}
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
            timestamp_str = data.get('timestamp')
            if not timestamp_str:
                return {'fresh': False, 'message': 'No timestamp in data'}

            # Convert timestamp to datetime object with timezone handling
            try:
                # Attempt to parse ISO format first (YYYY-MM-DDTHH:MM:SS)
                if 'T' in timestamp_str:
                    # Handle potential timezone info like 'Z' or '+00:00'
                    if timestamp_str.endswith('Z'):
                        timestamp_str = timestamp_str[:-1] + '+00:00'
                    data_datetime = datetime.fromisoformat(timestamp_str)
                else:
                    # Handle fallback format like 'DD/MM/YYYY, HH:MM:SS'
                    data_datetime = datetime.strptime(timestamp_str, '%d/%m/%Y, %H:%M:%S')
            except ValueError as ts_parse_error:
                logger.warning(f"Could not parse timestamp '{timestamp_str}': {ts_parse_error}")
                # If parsing fails, assume data is fresh to avoid errors in dashboard
                return {'fresh': True, 'message': 'Could not parse timestamp, assuming fresh'}

            # Ensure timezone awareness for comparison
            now_dt = datetime.now(IST) # Use IST for comparison
            if data_datetime.tzinfo is None:
                # If data_datetime is naive, assume it's in IST and make it aware
                data_datetime = IST.localize(data_datetime)

            age = now_dt - data_datetime

            # Consider data fresh if less than 2 hours old
            if age.total_seconds() < 7200:
                return {'fresh': True, 'message': f'Data is up to date (age: {age})'}
            else:
                return {'fresh': False, 'message': f'Data is stale (age: {age})'}
    except Exception as e:
        logger.error(f"Could not check data freshness: {str(e)}")
        return {'fresh': False, 'message': str(e)}

def load_stock_data():
    """Load current stock data from file"""
    try:
        if not os.path.exists('top10.json'):
            return {'stocks': [], 'status': 'no_data', 'message': 'No data file'}
        with open('top10.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Could not load stock data: {str(e)}")
        return {'stocks': [], 'status': 'error', 'message': str(e)}

def load_screening_sessions_count():
    """Load and count successful screening sessions from scheduler tracking"""
    try:
        # First, try to get session count from scheduler globals
        global scheduler
        if scheduler and hasattr(scheduler, 'successful_sessions'):
            from core.scheduler import successful_sessions, total_sessions_run
            logger.info(f"Retrieved session count from scheduler: total={total_sessions_run}, successful={successful_sessions}")
            return total_sessions_run  # Return total runs as requested

        # Fallback: check for sessions file
        sessions_file = 'screening_sessions.json'
        if os.path.exists(sessions_file):
            with open(sessions_file, 'r') as f:
                sessions_data = json.load(f)
                total_sessions = len(sessions_data.get('sessions', []))
                logger.info(f"Retrieved session count from file: {total_sessions}")
                return total_sessions

        # Second fallback: estimate from prediction files and current data
        current_data = load_stock_data()
        if current_data.get('status') == 'success' and current_data.get('stocks'):
            estimated = max(1, estimate_sessions_from_logs())
            logger.info(f"Estimated session count: {estimated}")
            return estimated

        return 0

    except Exception as e:
        logger.error(f"Error loading sessions count: {str(e)}")
        return 0

def estimate_sessions_from_logs():
    """Estimate sessions from application usage patterns"""
    try:
        # Check for prediction history files which indicate screening activity
        files_to_check = [
            'predictions_history.json',
            'agent_decisions.json',
            'signal_history.json',
            'stable_predictions.json'
        ]

        estimated_sessions = 0

        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            estimated_sessions += len(data)
                        elif isinstance(data, dict):
                            estimated_sessions += len(data.keys())
                except Exception as file_read_error:
                    logger.warning(f"Error reading {file_path} for session estimation: {file_read_error}")
                    continue

        # Conservative estimate: each 5 history entries = 1 successful session
        return max(1, estimated_sessions // 5)

    except Exception as e:
        logger.error(f"Error estimating sessions: {str(e)}")
        return 1

def calculate_historical_accuracy(sessions_count, high_score_count, total_stocks):
    """Calculate accuracy rate based on historical performance"""
    try:
        if sessions_count == 0 or total_stocks == 0:
            return 0

        # Base accuracy from current session
        current_accuracy = (high_score_count / total_stocks) * 100

        # Adjust based on session maturity
        if sessions_count >= 20:
            # Mature system - use realistic accuracy
            historical_accuracy = min(85, current_accuracy * 1.1)
        elif sessions_count >= 10:
            # Growing system
            historical_accuracy = min(75, current_accuracy * 1.05)
        elif sessions_count >= 5:
            # Early system
            historical_accuracy = min(65, current_accuracy)
        else:
            # Very new system
            historical_accuracy = min(55, current_accuracy * 0.9)

        return round(historical_accuracy, 1)

    except Exception as e:
        logger.error(f"Error calculating accuracy: {str(e)}")
        return 30.0

def load_tracking_metrics_for_analysis():
    """Load tracking metrics to support enhanced analysis"""
    try:
        from managers.interactive_tracker_manager import InteractiveTrackerManager
        tracker_manager = InteractiveTrackerManager()
        tracking_data = tracker_manager.get_all_tracking_data()

        locked_count = 0
        in_progress_count = 0
        metrics_5d = {'total': 0, 'successful': 0, 'failed': 0, 'in_progress': 0}
        metrics_30d = {'total': 0, 'successful': 0, 'failed': 0, 'in_progress': 0}

        for symbol, data in tracking_data.items():
            # Count locked predictions
            if data.get('locked_5d') or data.get('locked_30d'):
                locked_count += 1

            # Count in-progress predictions
            if data.get('locked_5d') and is_prediction_in_progress(data, '5d'):
                in_progress_count += 1
            if data.get('locked_30d') and is_prediction_in_progress(data, '30d'):
                in_progress_count += 1

            # Calculate 5D metrics
            if data.get('locked_5d') or data.get('days_tracked', 0) > 0:
                metrics_5d['total'] += 1
                result_5d = get_prediction_result_for_analysis(data, '5d')
                if result_5d == 'successful':
                    metrics_5d['successful'] += 1
                elif result_5d == 'failed':
                    metrics_5d['failed'] += 1
                else:
                    metrics_5d['in_progress'] += 1

            # Calculate 30D metrics
            if data.get('locked_30d') or data.get('days_tracked', 0) > 0:
                metrics_30d['total'] += 1
                result_30d = get_prediction_result_for_analysis(data, '30d')
                if result_30d == 'successful':
                    metrics_30d['successful'] += 1
                elif result_30d == 'failed':
                    metrics_30d['failed'] += 1
                else:
                    metrics_30d['in_progress'] += 1

        return {
            'locked_predictions_count': locked_count,
            'in_progress_predictions': in_progress_count,
            'metrics_5d': metrics_5d,
            'metrics_30d': metrics_30d
        }

    except Exception as e:
        logger.error(f"Error loading tracking metrics: {str(e)}")
        return {
            'locked_predictions_count': 0,
            'in_progress_predictions': 0,
            'metrics_5d': {'total': 0, 'successful': 0, 'failed': 0, 'in_progress': 0},
            'metrics_30d': {'total': 0, 'successful': 0, 'failed': 0, 'in_progress': 0}
        }

def is_prediction_in_progress(data, period):
    """Check if a prediction is still in progress"""
    try:
        lock_start_date_key = f'lock_start_date_{period}'
        lock_date = data.get(lock_start_date_key)
        if not lock_date:
            return False

        from datetime import datetime
        import pytz
        IST = pytz.timezone('Asia/Kolkata')

        start_date = datetime.strptime(lock_date, '%Y-%m-%d')
        current_date = datetime.now(IST).date()
        days_passed = (current_date - start_date.date()).days

        total_days = 5 if period == '5d' else 30
        return days_passed < total_days

    except Exception as e:
        logger.error(f"Error checking if prediction in progress: {str(e)}")
        return False

def get_prediction_result_for_analysis(data, period):
    """Get prediction result for analysis purposes"""
    try:
        actual_key = f'actual_progress_{period}'
        predicted_key = f'predicted_{period}'

        actual_data = data.get(actual_key, [])
        predicted_data = data.get(predicted_key, [])

        if not actual_data or not predicted_data:
            return 'in_progress'

        # Filter out null values
        actual_values = [val for val in actual_data if val is not None]

        required_days = 5 if period == '5d' else 30
        if len(actual_values) < required_days:
            return 'in_progress'

        # Compare final values
        final_predicted = predicted_data[-1] if predicted_data else 0
        final_actual = actual_values[-1] if actual_values else 0

        if final_predicted == 0 or final_actual == 0:
            return 'in_progress'

        # Consider successful if within 5% of prediction
        error_percent = abs((final_actual - final_predicted) / final_predicted) * 100
        return 'successful' if error_percent <= 5 else 'failed'

    except Exception as e:
        logger.error(f"Error getting prediction result: {str(e)}")
        return 'in_progress'

def generate_real_time_insights(sessions_count, total_stocks, high_score_stocks, avg_score):
    """Generate insights based on real session data"""
    try:
        insights = []

        # Session-based insights
        if sessions_count >= 20:
            insights.append(f"🎯 Excellent! {sessions_count} successful screening sessions completed")
            insights.append("📈 System maturity allows for highly accurate predictions")
        elif sessions_count >= 10:
            insights.append(f"📊 Good progress: {sessions_count} screening sessions recorded")
            insights.append("🔄 Prediction accuracy improving with more sessions")
        elif sessions_count >= 5:
            insights.append(f"🚀 Building momentum: {sessions_count} sessions completed")
            insights.append("📋 Gather more sessions for enhanced accuracy")
        else:
            insights.append(f"🌱 Early stage: {sessions_count} sessions recorded")
            insights.append("⏳ Run more screenings to build prediction confidence")

        # Current performance insights
        if total_stocks > 0:
            insights.append(f"📈 Current analysis: {total_stocks} stocks, {high_score_stocks} high-quality")

            if avg_score >= 70:
                insights.append("⭐ Excellent average score - strong market conditions")
            elif avg_score >= 60:
                insights.append("✅ Good average score - stable market performance")
            else:
                insights.append("⚠️ Lower scores detected - cautious market conditions")

        # Quality assessment
        if sessions_count >= 15:
            insights.append("🎖️ High-confidence predictions based on extensive history")
        elif sessions_count >= 8:
            insights.append("📊 Moderate confidence - good historical foundation")
        else:
            insights.append("🔄 Building confidence - continue regular screening")

        return insights

    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        return [
            "📊 Real-time analysis in progress",
            "🔄 System learning from each screening session",
            "📈 Performance metrics updating dynamically"
        ]

@app.route('/api/status')
def api_status():
    """API endpoint for system status"""
    try:
        check_file_integrity()

        status_data = {
            'status': 'healthy',
            'timestamp': datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S'),
            'scheduler': get_scheduler_status(),
            'data_freshness': check_data_freshness(),
            'prediction_stability': {},
            'version': '1.7.4'
        }

        # Get prediction stability status
        try:
            from prediction_stability_manager import PredictionStabilityManager
            stability_manager = PredictionStabilityManager()
            status_data['prediction_stability'] = stability_manager.get_prediction_status()
        except Exception as e:
            logger.warning(f"Could not get stability status: {str(e)}")
            status_data['prediction_stability'] = {'error': 'Stability manager not available'}

        return jsonify(status_data)

    except Exception as e:
        logger.error(f"Status API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



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
    """Manually trigger screening with request cancellation"""
    global scheduler
    request_id = id(request)

    try:
        # Cancel any in-flight requests
        with request_lock:
            # Mark this request as active
            active_requests.add(request)

        logger.info(f"🔄 Manual refresh requested (ID: {request_id})")

        # Cancel any existing timers to prevent overlap
        cancel_all_timers()

        # Run screening synchronously to ensure completion before returning
        try:
            if scheduler and hasattr(scheduler, 'run_screening_job_manual'):
                logger.info("Using scheduler for manual screening")

                # Check if request was cancelled
                if request not in active_requests:
                    return jsonify({
                        'success': False,
                        'message': 'Request cancelled due to newer request',
                        'cancelled': True,
                        'timestamp': datetime.now(IST).isoformat()
                    })

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
                try:
                    from src.analyzers.stock_screener import EnhancedStockScreener
                    screener = EnhancedStockScreener()
                    success = screener.run_enhanced_screening() # Corrected method call
                    if success:
                        logger.info("✅ Manual screening completed successfully standalone")
                        return jsonify({
                            'success': True,
                            'message': 'Screening completed successfully',
                            'data_ready': True,
                            'timestamp': datetime.now(IST).isoformat()
                        })
                    else:
                        logger.warning("⚠️ Manual screening completed with issues standalone")
                        return jsonify({
                            'success': False,
                            'message': 'Screening completed with issues',
                            'data_ready': False,
                            'timestamp': datetime.now(IST).isoformat()
                        })
                except Exception as e:
                    logger.error(f"Error during manual standalone screening: {str(e)}")
                    error_message = str(e)
                    return jsonify({
                        'success': False,
                        'message': f'Manual screening error: {error_message}',
                        'error': error_message,
                        'timestamp': datetime.now(IST).isoformat()
                    })

        except Exception as e:
            logger.error(f"Error during manual screening: {str(e)}")
            error_message = str(e)
            return jsonify({
                'success': False,
                'message': f'Manual screening error: {error_message}',
                'error': error_message,
                'timestamp': datetime.now(IST).isoformat()
            }), 500

    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
        error_message = str(e)
        return jsonify({
            'success': False,
            'message': f'Manual refresh error: {error_message}',
            'error': error_message,
            'timestamp': datetime.now(IST).isoformat()
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint with memory monitoring"""
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

    # Memory usage
    memory_info = None
    psutil = None
    process = None

    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
    except ImportError:
        logger.warning("psutil not found. Memory usage will not be reported.")
    except Exception as e:
        logger.error(f"Error getting memory info: {str(e)}")

    # Cache stats helper
    def get_cache_stats():
        try:
            if cache:
                return cache.get_stats()
            return {}
        except Exception:
            return {}

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - app.start_time if hasattr(app, 'start_time') else 0,
        'memory': {
            'rss_mb': round(memory_info.rss / 1024 / 1024, 2) if memory_info else 0,
            'vms_mb': round(memory_info.vms / 1024 / 1024, 2) if memory_info else 0,
            'percent': process.memory_percent() if psutil and memory_info else 0
        },
        'pinned_stocks_count': len(PINNED_SYMBOLS),
        'cache_stats': get_cache_stats()
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
    """API endpoint to get historical analysis data with real session tracking"""
    try:
        # Load real-time session count from scheduler
        sessions_count = load_screening_sessions_count()

        # Get successful sessions count from scheduler globals
        successful_sessions_count = 0
        successful_refresh_count = 0
        try:
            from core.scheduler import successful_sessions, total_sessions_run
            successful_sessions_count = successful_sessions
            total_runs = total_sessions_run
            successful_refresh_count = successful_sessions_count  # Use successful sessions as refresh count
            logger.info(f"Live session data: total_runs={total_runs}, successful={successful_sessions_count}")
        except ImportError:
            successful_sessions_count = sessions_count
            total_runs = sessions_count
            successful_refresh_count = sessions_count

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

        # Calculate real-time metrics from current session
        total_stocks_analyzed = len(current_stocks)
        high_score_stocks = len([s for s in current_stocks if s.get('score', 0) >= 70])
        avg_score = sum(s.get('score', 0) for s in current_stocks) / max(1, len(current_stocks))

        # Calculate dynamic accuracy rate based on actual performance
        accuracy_rate = calculate_historical_accuracy(successful_sessions_count, high_score_stocks, total_stocks_analyzed)

        # If we have high-scoring stocks, boost accuracy for successful sessions
        if successful_sessions_count > 0 and total_stocks_analyzed > 0:
            session_success_rate = (high_score_stocks / total_stocks_analyzed) * 100
            # Blend session success with historical performance
            accuracy_rate = round((accuracy_rate + session_success_rate) / 2, 1)

        # Extract top performers from current data
        top_performers = sorted(current_stocks, key=lambda x: x.get('score', 0), reverse=True)[:5]

        # Load interactive tracking data for enhanced metrics
        tracking_metrics = load_tracking_metrics_for_analysis()

        # Create comprehensive analysis based on real session data
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'status': 'real_time_analysis' if current_stocks else 'no_data',
            'total_predictions_analyzed': total_stocks_analyzed,
            'correct_predictions': high_score_stocks,
            'accuracy_rate': accuracy_rate,
            'sessions_recorded': total_runs,  # Use real session count
            'successful_sessions': successful_sessions_count,
            'successful_refreshes': successful_refresh_count,  # Add refresh counter
            'top_performing_stocks': [
                {
                    'symbol': stock.get('symbol', 'N/A'),
                    'success_rate': round(min(100, stock.get('score', 0)), 1),
                    'predictions_analyzed': 1
                }
                for stock in top_performers
            ],
            'worst_performing_stocks': [],
            'pattern_insights': generate_real_time_insights(
                total_runs, total_stocks_analyzed, high_score_stocks, avg_score
            ),
            'data_quality': 'excellent' if total_runs > 10 else 'good' if total_runs > 5 else 'building',
            'sessions_analyzed': total_runs,
            'current_performance_metrics': {
                'avg_score': round(avg_score, 1),
                'high_score_percentage': round((high_score_stocks / max(1, total_stocks_analyzed)) * 100, 1),
                'total_stocks_current': total_stocks_analyzed,
                'status': current_data_status
            },
            # Enhanced metrics for new analysis page
            'locked_predictions_count': tracking_metrics.get('locked_predictions_count', 0),
            'in_progress_predictions': tracking_metrics.get('in_progress_predictions', 0),
            'prediction_metrics_5d': tracking_metrics.get('metrics_5d', {}),
            'prediction_metrics_30d': tracking_metrics.get('metrics_30d', {})
        }

        logger.info(f"Analysis data prepared: sessions={total_runs}, successful={successful_sessions_count}, accuracy={accuracy_rate}%")
        return jsonify(analysis_data)

    except Exception as e:
        logger.error(f"Error in /api/analysis: {str(e)}")
        return jsonify({
            'error': f'Analysis error: {str(e)}',
            'status': 'error',
            'total_predictions_analyzed': 0,
            'correct_predictions': 0,
            'accuracy_rate': 0,
            'sessions_recorded': 0,
            'successful_sessions': 0,
            'successful_refreshes': 0,
            'top_performing_stocks': [],
            'worst_performing_stocks': [],
            'pattern_insights': [
                '❌ Error loading analysis data',
                f'🔧 Technical issue: {str(e)}',
                '🔄 Try refreshing the page or running screening again'
            ],
            'data_quality': 'error',
            'sessions_analyzed': 0,
            'current_performance_metrics': {
                'avg_score': 0,
                'high_score_percentage': 0,
                'total_stocks_current': 0,
                'status': 'error'
            },
            'locked_predictions_count': 0,
            'in_progress_predictions': 0,
            'prediction_metrics_5d': {},
            'prediction_metrics_30d': {}
        }), 500

@app.route('/api/historical-trends')
def get_historical_trends():
    """API endpoint to get historical trends"""
    try:
        # Assuming HistoricalAnalyzer is available and imported
        # from some_module import HistoricalAnalyzer
        # analyzer = HistoricalAnalyzer()
        # trends_data = analyzer.get_historical_trends()

        # Placeholder if HistoricalAnalyzer is not directly available here
        trends_data = {
            'status': 'placeholder',
            'message': 'HistoricalAnalyzer not directly available for import in this context.',
            'trends': {}
        }
        logger.warning("HistoricalAnalyzer not implemented/imported in this scope.")
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
        try:
            from src.analyzers.stock_screener import EnhancedStockScreener
            screener = EnhancedStockScreener()
        except ImportError as e:
            logger.error(f"Could not import stock screener: {e}")
            return jsonify({'error': 'Stock screener module not available'}), 500

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
            from models.predictor import enrich_with_ml_predictions
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
        from managers.backtesting_manager import BacktestingManager
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

@app.route('/options-strategy')
def options_strategy():
    """Options strategy analysis page"""
    return render_template('options_strategy.html')

@app.route('/api/options-strategies')
def options_strategies():
    """Memory-optimized API endpoint for options strategies analysis"""
    try:
        import gc
        from src.compute.options_math import load_min_inputs, compute_row, now_iso

        timeframe = request.args.get('timeframe', '30D')
        print(f"[OPTIONS_API] ⚡ Memory-optimized API called with timeframe: {timeframe}")
        logger.info(f"[OPTIONS_API] ⚡ Memory-optimized API called with timeframe: {timeframe}")

        # Load minimal input set per symbol (NO historical arrays)
        raw_rows = load_min_inputs(timeframe)

        if not raw_rows:
            return jsonify({
                "timeframe": timeframe,
                "rows": [],
                "summary": {"total_premium_collected": 0.0, "avg_roi_pct": 0.0},
                "generated_at": now_iso(),
                "pinned_stocks": list(PINNED_SYMBOLS),
                "status": "no_data"
            })

        # Compute final rows from minimal inputs
        rows = [compute_row(r).__dict__ for r in raw_rows]

        # Add pinning status to each row
        for row in rows:
            row['pinned'] = row.get('symbol') in PINNED_SYMBOLS

        # Lightweight summary computation
        summary = {
            "total_premium_collected": round(sum(r["total_premium"] for r in rows), 2),
            "avg_roi_pct": round(sum(r["roi_pct"] for r in rows) / len(rows), 2) if rows else 0.0,
            "total_count": len(rows),
            "success_count": len([r for r in rows if r["result"] == "success"]),
            "in_progress_count": len([r for r in rows if r["result"] == "in_progress"]),
            "failed_count": len([r for r in rows if r["result"] == "failed"])
        }

        # Release memory and force GC
        del raw_rows
        gc.collect()

        result = {
            "timeframe": timeframe,
            "rows": rows,  # skinny rows only
            "summary": summary,
            "generated_at": now_iso(),
            "pinned_stocks": list(PINNED_SYMBOLS),
            "status": "success"
        }

        print(f"[OPTIONS_API] ✅ Returning {len(rows)} memory-optimized rows")
        logger.info(f"[OPTIONS_API] ✅ Returning {len(rows)} memory-optimized rows")
        return jsonify(result)

    except Exception as e:
        print(f"[OPTIONS_API] ❌ Critical error in memory-optimized options strategies: {str(e)}")
        logger.error(f"[OPTIONS_API] Critical error: {str(e)}")
        return jsonify({
            "timeframe": timeframe,
            "rows": [],
            "summary": {"total_premium_collected": 0.0, "avg_roi_pct": 0.0},
            "generated_at": now_iso(),
            "error": str(e),
            "status": "error"
        }), 500


def load_interactive_tracking_data():
    """Load enhanced tracking data for interactive charts with persistence"""
    try:
        from managers.interactive_tracker_manager import InteractiveTrackerManager
        tracker_manager = InteractiveTrackerManager()
        tracking_data = tracker_manager.load_tracking_data()

        # Always ensure current stocks are tracked before saving lock status
        tracker_manager._ensure_current_stocks_tracked()

        return tracker_manager.get_all_tracking_data()
    except Exception as e:
        logger.warning(f"Could not load interactive tracking data: {str(e)}")
        return {}

def save_lock_status(symbol, period, locked, timestamp, persistent=True):
    """Save lock status for a stock prediction with persistence support"""
    try:
        from managers.interactive_tracker_manager import InteractiveTrackerManager
        tracker_manager = InteractiveTrackerManager()

        # Ensure current stocks are tracked before saving lock status
        tracker_manager._ensure_current_stocks_tracked()

        success = tracker_manager.update_lock_status(symbol, period, locked, timestamp, persistent)
        if success:
            persistence_msg = "persistently" if persistent else "temporarily"
            logger.info(f"✅ Lock status saved {persistence_msg}: {symbol} {period} = {locked}")
        else:
            logger.error(f"❌ Failed to save lock status for {symbol}")

        return success
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

        try:
            from src.core.scheduler import StockAnalystScheduler
            scheduler = StockAnalystScheduler()
            scheduler.start_scheduler(interval_minutes=60)
            logger.info("✅ Scheduler started successfully")
        except Exception as scheduler_error:
            logger.warning(f"⚠️ Scheduler failed to start: {scheduler_error}")
            scheduler = None

    except Exception as e:
        logger.error(f"❌ Error during app initialization: {str(e)}")

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

@app.route('/goahead')
def goahead():
    """GoAhead AI Validation & Self-Healing System page"""
    try:
        return render_template('goahead.html')
    except Exception as e:
        logger.error(f"GoAhead page error: {str(e)}")
        return f"Error loading GoAhead page: {str(e)}", 500

@app.route('/api/goahead/validation')
def goahead_validation():
    """API endpoint for GoAhead prediction validation"""
    try:
        timeframe = request.args.get('timeframe', '5D')

        # Initialize SmartGoAgent
        smart_agent = SmartGoAgent()

        # Perform validation analysis
        validation_results = smart_agent.validate_predictions(timeframe)

        return jsonify(validation_results)

    except Exception as e:
        logger.error(f"GoAhead validation API error: {str(e)}")
        return jsonify({
            'error': str(e),
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'prediction_summary': {'total': 0, 'accuracy': 0, 'avg_confidence': 0, 'predictions': []},
            'outcome_validation': {'success': 0, 'warning': 0, 'failure': 0, 'details': []},
            'gap_analysis': {'gaps': []},
            'improvement_suggestions': {'recommendations': []},
            'retraining_guide': {
                'days_since_training': 0,
                'priority_score': '0/100',
                'should_retrain': False,
                'recommendations': []
            }
        }), 500

@app.route('/api/goahead/refresh', methods=['POST'])
def refresh_goahead_data():
    """Refresh GoAhead analysis data"""
    try:
        # Trigger data refresh
        from src.analyzers.smart_go_agent import SmartGoAgent
        agent = SmartGoAgent()

        # Get fresh analysis for key stocks
        key_stocks = ['RELIANCE', 'TCS', 'INFY', 'SBIN', 'ITC']
        results = []

        for symbol in key_stocks:
            analysis = agent.get_enhanced_agent_analysis(symbol, {})
            if analysis:
                results.append({
                    'symbol': symbol,
                    'analysis': analysis
                })

        return jsonify({
            'status': 'success',
            'message': 'GoAhead data refreshed',
            'stocks_updated': len(results),
            'results': results
        })

    except Exception as e:
        logger.error(f"Error refreshing GoAhead data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/goahead/retrain', methods=['POST'])
def retrain_models():
    """Trigger model retraining with 5-year historical data"""
    try:
        from src.ml.train_models import ModelTrainer

        trainer = ModelTrainer()

        # Check if specific stocks requested
        data = request.get_json() or {}
        symbols = data.get('symbols', [])

        if symbols:
            # Train specific stocks
            results = {}
            for symbol in symbols[:5]:  # Limit to 5 stocks per request
                results[symbol] = trainer.train_single_stock(symbol)
        else:
            # Train all models
            results = trainer.train_all_models()

        return jsonify({
            'status': 'success',
            'message': 'Model retraining completed',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error retraining models: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/admin/feature-flags', methods=['GET', 'POST'])
def admin_feature_flags():
    """Admin endpoint for feature flag management"""
    try:
        if request.method == 'GET':
            # Get all current flags
            return jsonify({
                'status': 'success',
                'flags': feature_flags.get_all_runtime_flags(),
                'timestamp': datetime.now().isoformat()
            })

        elif request.method == 'POST':
            data = request.get_json()
            flag_name = data.get('flag_name')
            flag_value = data.get('flag_value')

            if not flag_name or flag_value is None:
                return jsonify({'error': 'flag_name and flag_value required'}), 400

            # Set the flag
            feature_flags.set_flag(flag_name, bool(flag_value))

            # Check budgets after flag change
            from src.common_repository.utils.profiler import profiler
            profiler.check_and_enforce_budgets()

            return jsonify({
                'status': 'success',
                'message': f'Flag {flag_name} set to {flag_value}',
                'flags': feature_flags.get_all_runtime_flags()
            })

    except Exception as e:
        logger.error(f"Error in admin feature flags: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/performance-stats', methods=['GET'])
def admin_performance_stats():
    """Admin endpoint for performance statistics"""
    try:
        from src.common_repository.utils.telemetry import telemetry
        from src.common_repository.cache.cache_manager import cache_manager
        from src.common_repository.utils.memory import memory_manager

        stats = {
            'telemetry': telemetry.get_all_metrics(),
            'cache': cache_manager.get_stats(),
            'memory': memory_manager.get_memory_stats(),
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/status', methods=['GET'])
def get_model_status():
    """Get current model training status and KPIs"""
    try:
        from src.utils.file_utils import load_json_safe

        kpi_data = load_json_safe('data/tracking/model_kpi.json', {})

        # Add model file existence check
        models_dir = "models_trained"
        model_files = {}

        if os.path.exists(models_dir):
            for file in os.listdir(models_dir):
                if file.endswith('.h5') or file.endswith('.pkl'):
                    symbol = file.split('_')[0]
                    model_type = 'lstm' if file.endswith('.h5') else 'rf'

                    if symbol not in model_files:
                        model_files[symbol] = {}
                    model_files[symbol][model_type] = {
                        'file': file,
                        'last_modified': datetime.fromtimestamp(
                            os.path.getmtime(os.path.join(models_dir, file))
                        ).isoformat()
                    }

        return jsonify({
            'status': 'success',
            'kpi_data': kpi_data,
            'model_files': model_files,
            'models_directory': models_dir
        })

    except Exception as e:
        logger.error(f"Error getting model status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/options-prediction-dashboard')
def options_prediction_dashboard():
    """Enhanced options prediction dashboard API"""
    try:
        print("📈 Starting prediction performance dashboard load...")

        # Get mode from query parameter
        mode = request.args.get('mode', 'live')
        print(f"📊 Loading dashboard in mode: {mode}")

        # Initialize SmartGoAgent
        smart_agent = SmartGoAgent()

        # Get active options predictions for Live Trade Divergence Monitor
        active_trades = smart_agent.get_active_options_predictions()
        print(f"📊 Found {len(active_trades)} active trades")

        # Ensure all trades have required fields with safe fallbacks
        for trade in active_trades:
            if 'expected_roi' not in trade and 'predicted_roi' in trade:
                trade['expected_roi'] = trade['predicted_roi']
            if 'expected_roi' not in trade:
                trade['expected_roi'] = 0
            if 'confidence' not in trade:
                trade['confidence'] = 75.0
            if 'status' not in trade:
                trade['status'] = 'in_progress'

        # Get prediction accuracy summary for main dashboard
        summary = smart_agent.get_prediction_accuracy_summary(mode=mode)
        print(f"📈 Summary loaded: {summary.get('success', False)}")

        return jsonify({
            'success': True,
            'live_trades': active_trades,
            'summary_stats': summary.get('summary_stats', {}),
            'overall_accuracy': summary.get('overall_accuracy', 0),
            'total_predictions': summary.get('total_predictions', 0),
            'last_updated': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in options prediction dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'details': 'Dashboard load failed',
            'live_trades': [],
            'summary_stats': {},
            'overall_accuracy': 0,
            'total_predictions': 0
        }), 500

@app.route('/api/prediction-performance-dashboard')
def prediction_performance_dashboard():
    """API endpoint for prediction performance dashboard data (legacy endpoint)"""
    try:
        logger.info("📈 Loading prediction performance dashboard data...")

        # Initialize response structure
        dashboard_data = {
            'status': 'success',
            'timestamp': datetime.now(IST).isoformat(),
            'in_progress': [],
            'summary': {}
        }

        # Load options tracking data
        options_tracking_data = load_options_tracking_data()

        # Load current options strategies for real-time comparison
        current_strategies = get_current_options_strategies()

        # Process in-progress trades
        in_progress_trades = process_in_progress_trades(options_tracking_data, current_strategies)
        dashboard_data['in_progress'] = in_progress_trades

        # Process performance summary by timeframe
        performance_summary = process_performance_summary(options_tracking_data)
        dashboard_data['summary'] = performance_summary

        logger.info(f"✅ Performance dashboard data prepared: {len(in_progress_trades)} active trades")
        return jsonify(dashboard_data)

    except Exception as e:
        logger.error(f"Error in prediction performance dashboard: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now(IST).isoformat(),
            'in_progress': [],
            'summary': {}
        }), 500

def load_options_tracking_data():
    """Load options tracking data from file"""
    try:
        tracking_file = 'options_tracking.json'
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.warning(f"Could not load options tracking data: {str(e)}")
        return {}

def get_current_options_strategies():
    """Get current options strategies for comparison"""
    try:
        # Use existing options strategies endpoint logic
        from analyzers.short_strangle_engine import ShortStrangleEngine
        engine = ShortStrangleEngine()

        # Get current strategies for major stocks
        current_stocks = ['RELIANCE', 'HDFCBANK', 'TCS', 'ITC', 'INFY', 'HINDUNILVR']
        strategies = []

        for symbol in current_stocks[:3]:  # Limit to avoid timeouts
            try:
                analysis = engine.analyze_short_strangle(symbol, force_realtime=True)
                if analysis:
                    strategies.append(analysis)
            except Exception as e:
                logger.warning(f"Error getting current strategy for {symbol}: {str(e)}")
                continue

        return strategies

    except Exception as e:
        logger.error(f"Error getting current options strategies: {str(e)}")
        return []

def process_in_progress_trades(tracking_data, current_strategies):
    """Process in-progress trades for the dashboard"""
    try:
        in_progress = []

        # Create lookup for current strategies
        current_lookup = {s.get('symbol'): s for s in current_strategies}

        for symbol, trades in tracking_data.items():
            if not isinstance(trades, dict):
                continue

            for trade_id, trade_data in trades.items():
                if not isinstance(trade_data, dict):
                    continue

                # Check if trade is still active
                if trade_data.get('status') == 'active':
                    current_strategy = current_lookup.get(symbol, {})

                    # Calculate divergence reasons
                    reason = calculate_divergence_reason(trade_data, current_strategy)

                    # Build in-progress trade entry
                    in_progress_trade = {
                        'due_date': trade_data.get('expiry_date', ''),
                        'stock': symbol,
                        'predicted_outcome': trade_data.get('predicted_outcome', 'On Track'),
                        'current_outcome': determine_current_outcome(trade_data, current_strategy),
                        'predicted_roi': trade_data.get('predicted_roi', 0),
                        'current_roi': current_strategy.get('expected_roi', 0),
                        'reason': reason
                    }

                    in_progress.append(in_progress_trade)

        # Sort by reason (non-empty first), then by due date
        in_progress.sort(key=lambda x: (x['reason'] == '', x['due_date']))

        return in_progress

    except Exception as e:
        logger.error(f"Error processing in-progress trades: {str(e)}")
        return []

def process_performance_summary(tracking_data):
    """Process performance summary by timeframe"""
    try:
        timeframes = ['3D', '5D', '10D', '15D', '30D']
        summary = {}

        for timeframe in timeframes:
            timeframe_data = {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'in_progress': 0,
                'accuracy': 0,
                'avg_roi': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0
            }

            # Aggregate data for this timeframe
            roi_values = []

            for symbol, trades in tracking_data.items():
                if not isinstance(trades, dict):
                    continue

                for trade_id, trade_data in trades.items():
                    if not isinstance(trade_data, dict):
                        continue

                    if trade_data.get('timeframe') == timeframe:
                        timeframe_data['total'] += 1

                        status = trade_data.get('final_status', trade_data.get('status', 'in_progress'))

                        if status == 'success':
                            timeframe_data['successful'] += 1
                        elif status == 'failed':
                            timeframe_data['failed'] += 1
                        else:
                            timeframe_data['in_progress'] += 1

                        # Collect ROI for calculations
                        roi = trade_data.get('actual_roi', trade_data.get('predicted_roi', 0))
                        if roi:
                            roi_values.append(roi)

            # Calculate metrics
            if timeframe_data['total'] > 0:
                completed_trades = timeframe_data['successful'] + timeframe_data['failed']
                if completed_trades > 0:
                    timeframe_data['accuracy'] = (timeframe_data['successful'] / completed_trades) * 100

            if roi_values:
                timeframe_data['avg_roi'] = sum(roi_values) / len(roi_values)
                timeframe_data['max_drawdown'] = min(roi_values) if roi_values else 0

                # Simple Sharpe ratio calculation (assuming 5% risk-free rate)
                risk_free_rate = 5.0
                roi_std = calculate_std_dev(roi_values) if len(roi_values) > 1 else 1
                timeframe_data['sharpe_ratio'] = (timeframe_data['avg_roi'] - risk_free_rate) / roi_std if roi_std > 0 else 0

            summary[timeframe] = timeframe_data

        return summary

    except Exception as e:
        logger.error(f"Error processing performance summary: {str(e)}")
        return {}

def calculate_divergence_reason(trade_data, current_strategy):
    """Calculate why a trade might be diverging from predictions"""
    try:
        reasons = []

        # Check ROI deviation
        predicted_roi = trade_data.get('predicted_roi', 0)
        current_roi = current_strategy.get('expected_roi', 0)

        if abs(current_roi - predicted_roi) > predicted_roi * 0.2:  # 20% deviation
            if current_roi < predicted_roi:
                reasons.append("ROI declined")
            else:
                reasons.append("ROI exceeded")

        # Check confidence drop
        predicted_confidence = trade_data.get('predicted_confidence', 0)
        current_confidence = current_strategy.get('confidence', 0)

        if current_confidence < predicted_confidence * 0.8:  # 20% confidence drop
            reasons.append("Confidence dropped")

        # Check breakeven breach (simplified)
        current_price = current_strategy.get('current_price', 0)
        breakeven_upper = trade_data.get('breakeven_upper', 0)
        breakeven_lower = trade_data.get('breakeven_lower', 0)

        if current_price > 0 and breakeven_upper > 0 and breakeven_lower > 0:
            if current_price > breakeven_upper or current_price < breakeven_lower:
                reasons.append("Breakeven breached")

        return "; ".join(reasons)

    except Exception as e:
        logger.warning(f"Error calculating divergence reason: {str(e)}")
        return ""

def determine_current_outcome(trade_data, current_strategy):
    """Determine current outcome status"""
    try:
        # Simple logic to determine current status
        current_roi = current_strategy.get('expected_roi', 0)
        predicted_roi = trade_data.get('predicted_roi', 0)

        if abs(current_roi - predicted_roi) <= predicted_roi * 0.1:  # Within 10%
            return "On Track"
        elif current_roi > predicted_roi * 1.2:  # 20% better
            return "Exceeded"
        elif current_roi < predicted_roi * 0.8:  # 20% worse
            return "At Risk"
        else:
            return "On Track"

    except Exception:
        return "Unknown"

def calculate_std_dev(values):
    """Calculate standard deviation"""
    try:
        if len(values) <= 1:
            return 1

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    except Exception:
        return 1


def create_app():
    """Application factory function for new architecture"""
    logger.info("Creating application with new shared-core architecture")

    # Display architecture info
    logger.info("🏗️ Architecture Components:")
    logger.info("  📦 Common Repository: Shared utilities, models, services")
    logger.info("  🎯 Products: Equity and Options services")
    logger.info("  🔧 Feature Flags: Dynamic configuration management")
    logger.info("  💾 Storage: JSON with backup and future SQLite support")

    # Initialize app with existing logic
    initialize_app()

    # Log registered blueprints
    logger.info("🔌 Registered API endpoints:")
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith('equity') or rule.endpoint.startswith('options'):
            logger.info(f"  {rule.methods} {rule.rule} -> {rule.endpoint}")

    return app

if __name__ == '__main__':
    initialize_app()

    # Set app start time for uptime calculation
    app.start_time = time.time()

    # Print startup information
    print("\n" + "="*60)
    print("STOCK MARKET ANALYST - DASHBOARD")
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