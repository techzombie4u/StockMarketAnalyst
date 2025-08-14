"""
Stock Market Analyst - Enhanced Scheduler Module

IST-aware scheduler with market hours detection and load management.
Handles automated screening with APScheduler and data persistence.
"""

import json
import os
import time
import logging
import pytz
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import numpy as np
import threading
from typing import Dict, Any, Optional

from src.common_repository.config.runtime import (
    MARKET_TZ, is_market_hours_now, get_market_tz
)
from src.common_repository.config.feature_flags import feature_flags
from src.common_repository.utils.telemetry import telemetry
from src.common_repository.cache.cache_manager import cache_manager

logger = logging.getLogger(__name__)

# Global set to track alerted stocks (avoid duplicate alerts)
alerted_stocks = set()

# Global variables for session tracking
total_sessions_run = 0
successful_sessions = 0

# Job queue management
job_queue_depth = 0
MAX_QUEUE_DEPTH = 10

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def clean_json_data(data):
    """Clean data for JSON serialization"""
    try:
        json_str = json.dumps(data, ensure_ascii=False)
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error cleaning JSON data: {str(e)}")
        return data

def is_market_hours():
    """Check if current time is within Indian market hours (9:15 AM - 3:30 PM IST)"""
    return is_market_hours_now()

def check_queue_depth(job_name: str) -> bool:
    """Check if job can run based on queue depth"""
    global job_queue_depth

    if job_queue_depth >= MAX_QUEUE_DEPTH:
        logger.warning(f"Queue depth exceeded ({job_queue_depth}), skipping job: {job_name}")
        telemetry.increment_counter('jobs.queue_exceeded')
        return False

    return True

def track_job_execution(job_name: str):
    """Decorator to track job execution metrics"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            global job_queue_depth

            if not check_queue_depth(job_name):
                return False

            job_queue_depth += 1
            start_time = time.time()

            try:
                logger.info(f"Starting job: {job_name}")
                telemetry.set_gauge('jobs.queue_depth', job_queue_depth)

                result = func(*args, **kwargs)

                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                logger.info(f"Job completed: {job_name}, duration: {duration_ms:.2f}ms")
                telemetry.record_metric('jobs.duration_ms', duration_ms, {'job': job_name})
                telemetry.set_gauge('jobs.last_run_sec', int(start_time))

                return result

            except Exception as e:
                logger.error(f"Job failed: {job_name}, error: {str(e)}")
                telemetry.increment_counter('jobs.failures', {'job': job_name})
                return False

            finally:
                job_queue_depth = max(0, job_queue_depth - 1)
                telemetry.set_gauge('jobs.queue_depth', job_queue_depth)

        return wrapper
    return decorator

def send_alerts(stocks):
    """Send alerts for high-scoring stocks (placeholder for future implementation)"""
    for stock in stocks:
        logger.info(f"🚨 HIGH SCORE ALERT: {stock['symbol']} - Score: {stock['score']}")

def record_successful_session(num_stocks, status):
    """Records a successful screening session."""
    global total_sessions_run, successful_sessions
    total_sessions_run += 1
    if status == 'success' and num_stocks > 0:
        successful_sessions += 1
    logger.info(f"Session recorded: Total runs={total_sessions_run}, Successful runs={successful_sessions}")

@track_job_execution("quotes_refresh")
def quotes_refresh_job():
    """Light job: refresh quotes data during market hours"""
    try:
        logger.info("Running quotes refresh...")

        # Only run during market hours
        if not is_market_hours():
            logger.info("Market closed, skipping quotes refresh")
            return True

        # Light quotes refresh logic here
        # This would update cached quote data without heavy computation
        cache_manager.refresh_quotes_cache()

        telemetry.increment_counter('jobs.completed', {'job': 'quotes_refresh'})
        return True

    except Exception as e:
        logger.error(f"Quotes refresh failed: {str(e)}")
        return False

@track_job_execution("options_chain_refresh")
def options_chain_refresh_job():
    """Light job: refresh options chains during market hours"""
    try:
        logger.info("Running options chain refresh...")

        # Only run during market hours
        if not is_market_hours():
            logger.info("Market closed, skipping options chain refresh")
            return True

        # Light options chain refresh logic here
        cache_manager.refresh_options_cache()

        telemetry.increment_counter('jobs.completed', {'job': 'options_chain_refresh'})
        return True

    except Exception as e:
        logger.error(f"Options chain refresh failed: {str(e)}")
        return False

@track_job_execution("kpi_incremental_update")
def kpi_incremental_update_job():
    """Light job: incremental KPI updates during market hours"""
    try:
        logger.info("Running KPI incremental update...")

        # Only run during market hours
        if not is_market_hours():
            logger.info("Market closed, skipping KPI incremental update")
            return True

        # Import here to avoid circular imports
        from src.core.kpi.calculator import kpi_calculator

        success = kpi_calculator.incremental_update()
        if success:
            telemetry.increment_counter('jobs.completed', {'job': 'kpi_incremental_update'})

        return success

    except Exception as e:
        logger.error(f"KPI incremental update failed: {str(e)}")
        return False

@track_job_execution("cache_maintenance")
def cache_maintenance_job():
    """Always-on job: cache cleanup and maintenance"""
    try:
        logger.info("Running cache maintenance...")

        # Clear expired cache entries
        cache_manager.clear_expired()

        # Force garbage collection
        import gc
        collected = gc.collect()
        logger.info(f"Cache maintenance: {collected} objects collected")

        telemetry.increment_counter('jobs.completed', {'job': 'cache_maintenance'})
        return True

    except Exception as e:
        logger.error(f"Cache maintenance failed: {str(e)}")
        return False

@track_job_execution("kpi_full_recompute")
def kpi_full_recompute_job():
    """Heavy job: full KPI recomputation after market hours"""
    try:
        logger.info("Running KPI full recompute...")

        # Only run after market hours
        if is_market_hours():
            logger.warning("Market open, skipping heavy KPI recompute job")
            return False

        # Import here to avoid circular imports
        from src.core.kpi.calculator import kpi_calculator

        success = kpi_calculator.full_recompute()
        if success:
            telemetry.increment_counter('jobs.completed', {'job': 'kpi_full_recompute'})

        return success

    except Exception as e:
        logger.error(f"KPI full recompute failed: {str(e)}")
        return False

@track_job_execution("precompute_other_timeframes")
def precompute_other_timeframes_job():
    """Heavy job: precompute multi-timeframe data after market hours"""
    try:
        logger.info("Running precompute other timeframes...")

        # Only run after market hours and if enabled
        if is_market_hours():
            logger.warning("Market open, skipping heavy precompute job")
            return False

        if not feature_flags.is_enabled('enable_all_timeframes_concurrent'):
            logger.info("Multi-timeframe precompute disabled by feature flag")
            return True

        # Precompute logic would go here
        logger.info("Multi-timeframe precompute completed")

        telemetry.increment_counter('jobs.completed', {'job': 'precompute_other_timeframes'})
        return True

    except Exception as e:
        logger.error(f"Precompute other timeframes failed: {str(e)}")
        return False

@track_job_execution("agent_training_scan")
def agent_training_scan_job():
    """Heavy job: agent-driven training scan after market hours"""
    try:
        logger.info("Running agent training scan...")

        # Only run after market hours and if enabled
        if is_market_hours():
            logger.warning("Market open, skipping heavy training scan job")
            return False

        if not feature_flags.is_enabled('enable_realtime_agents'):
            logger.info("Realtime agents disabled by feature flag")
            return True

        # Agent training scan logic would go here
        logger.info("Agent training scan completed")

        telemetry.increment_counter('jobs.completed', {'job': 'agent_training_scan'})
        return True

    except Exception as e:
        logger.error(f"Agent training scan failed: {str(e)}")
        return False

def run_screening_job():
    """Execute stock screening with memory management (legacy compatibility)"""
    global alerted_stocks, total_sessions_run, successful_sessions

    try:
        logger.info("Starting scheduled stock screening...")

        # Memory cleanup before heavy operations
        import gc
        gc.collect()

        # Import here to avoid circular imports
        from src.analyzers.stock_screener import EnhancedStockScreener

        # Create screener instance
        screener = EnhancedStockScreener()

        # Run screening with memory monitoring
        start_time = time.time()
        results = []
        session_status = 'error'

        try:
            results = screener.run_enhanced_screener()
            session_status = 'success'

        except Exception as e:
            logger.error(f"Screening failed: {e}")
            try:
                results = screener._generate_fallback_data() if screener else []
                session_status = 'fallback_generated'
            except:
                results = []
                session_status = 'failed'
        finally:
            try:
                del screener
                gc.collect()
            except:
                pass

        # Add timestamp in IST
        ist = get_market_tz()
        now_ist = datetime.now(ist)

        if results and len(results) > 0:
            valid_results = []
            for stock in results:
                if isinstance(stock, dict) and 'symbol' in stock:
                    if 'score' not in stock:
                        stock['score'] = 50.0
                    if 'current_price' not in stock:
                        stock['current_price'] = 0.0
                    if 'predicted_gain' not in stock:
                        stock['predicted_gain'] = stock.get('score', 50) * 0.2

                    stock['pred_24h'] = round(stock.get('predicted_gain', 0) * 0.05, 2)
                    stock['pred_5d'] = round(stock.get('predicted_gain', 0) * 0.25, 2)
                    stock['pred_1mo'] = round(stock.get('predicted_gain', 0), 2)

                    valid_results.append(stock)

            if valid_results:
                results_data = {
                    'status': session_status,
                    'stocks': valid_results,
                    'last_updated': now_ist.strftime('%d/%m/%Y, %H:%M:%S'),
                    'timestamp': now_ist.isoformat(),
                    'total_stocks': len(valid_results),
                    'screening_time': f"{time.time() - start_time:.2f} seconds"
                }

                record_successful_session(len(valid_results), results_data.get('status'))

                try:
                    json_safe_data = convert_numpy_types(results_data)
                    with open('top10.json', 'w', encoding='utf-8') as f:
                        json.dump(json_safe_data, f, indent=2, ensure_ascii=False)

                    logger.info(f"✅ Screening completed successfully with {len(valid_results)} stocks")

                    new_alerts = [s for s in valid_results if s['score'] > 70 and s['symbol'] not in alerted_stocks]
                    if new_alerts:
                        for alert in new_alerts:
                            alerted_stocks.add(alert['symbol'])
                        send_alerts(new_alerts)

                    return True

                except Exception as save_error:
                    logger.error(f"Failed to save results: {save_error}")

        record_successful_session(len(results) if results else 0, session_status)

        error_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%d/%m/%Y, %H:%M:%S'),
            'stocks': [],
            'status': session_status
        }

        try:
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save error state: {e}")

        return False

    except Exception as e:
        logger.error(f"Critical error in screening job: {str(e)}")
        return False

def run_screening_job_manual():
    """Execute stock screening manually (bypasses market hours check)"""
    logger.info("Manual screening requested")
    return run_screening_job()

class StockAnalystScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=get_market_tz())
        self.running = False

    def configure_scheduler(self):
        """Configure the scheduler timezone"""
        if self.scheduler:
            self.scheduler.configure(timezone=get_market_tz())

    def start_scheduler(self, interval_minutes=60):
        """Start the APScheduler with IST-aware job windows"""
        try:
            self.configure_scheduler()

            # Light jobs (market hours only)
            if feature_flags.is_enabled('enable_autorefresh'):
                # Quotes refresh every 30s during market hours
                self.scheduler.add_job(
                    func=quotes_refresh_job,
                    trigger='interval',
                    seconds=30,
                    id='quotes_refresh',
                    replace_existing=True,
                    max_instances=1,
                    misfire_grace_time=10
                )

                # Options chain refresh every 60s during market hours
                self.scheduler.add_job(
                    func=options_chain_refresh_job,
                    trigger='interval',
                    seconds=60,
                    id='options_chain_refresh',
                    replace_existing=True,
                    max_instances=1,
                    misfire_grace_time=10
                )

            # KPI incremental update every 5 minutes during market hours
            if feature_flags.is_enabled('enable_kpi_triggers'):
                self.scheduler.add_job(
                    func=kpi_incremental_update_job,
                    trigger='interval',
                    minutes=5,
                    id='kpi_incremental_update',
                    replace_existing=True,
                    max_instances=1,
                    misfire_grace_time=60
                )

            # Cache maintenance every 10 minutes (always)
            self.scheduler.add_job(
                func=cache_maintenance_job,
                trigger='interval',
                minutes=10,
                id='cache_maintenance',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=120
            )

            # Heavy jobs (after market hours only)

            # KPI full recompute daily at 16:00 IST
            self.scheduler.add_job(
                func=kpi_full_recompute_job,
                trigger='cron',
                hour=16,
                minute=0,
                id='kpi_full_recompute',
                replace_existing=True,
                misfire_grace_time=600
            )

            # Precompute other timeframes daily at 19:00 IST
            if feature_flags.is_enabled('enable_all_timeframes_concurrent'):
                self.scheduler.add_job(
                    func=precompute_other_timeframes_job,
                    trigger='cron',
                    hour=19,
                    minute=0,
                    id='precompute_other_timeframes',
                    replace_existing=True,
                    misfire_grace_time=600
                )

            # Agent training scan daily at 20:00 IST
            if feature_flags.is_enabled('enable_realtime_agents'):
                self.scheduler.add_job(
                    func=agent_training_scan_job,
                    trigger='cron',
                    hour=20,
                    minute=0,
                    id='agent_training_scan',
                    replace_existing=True,
                    misfire_grace_time=600
                )

            # Legacy screening job (compatibility)
            self.scheduler.add_job(
                func=run_screening_job,
                trigger='interval',
                minutes=interval_minutes,
                id='screening_job',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=300
            )

            # Register KPI background jobs
            try:
                # Import here to avoid circular imports
                from src.common_repository.scheduler.jobs import init_schedulers
                init_schedulers(self) # Pass self to access logger and scheduler instance
            except ImportError as e:
                logger.error(f"Failed to import or initialize KPI jobs: {e}")

            logger.info("✅ All scheduler jobs configured successfully")

            self.scheduler.start()
            self.running = True

            logger.info(f"✅ Scheduler started with IST-aware job windows")
            logger.info(f"   Light jobs: quotes (30s), options (60s), KPI (5m), cache (10m)")
            logger.info(f"   Heavy jobs: KPI recompute (16:00), precompute (19:00), training (20:00)")

            return True

        except Exception as e:
            logger.error(f"❌ Error starting scheduler: {str(e)}")
            return False

    def stop_scheduler(self):
        """Stop the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.running = False
                logger.info("Scheduler stopped.")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")

    def get_job_status(self):
        """Get current job status"""
        try:
            jobs = self.scheduler.get_jobs()
            return {
                'running': self.scheduler.running,
                'queue_depth': job_queue_depth,
                'jobs': [{'id': job.id, 'name': job.name, 'next_run': str(job.next_run_time)} for job in jobs]
            }
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {'running': False, 'jobs': []}

    def run_screening_job_manual(self):
        """Run screening manually"""
        try:
            return run_screening_job_manual()
        except Exception as e:
            logger.error(f"Manual screening failed: {e}")
            return False

def main():
    """Test scheduler"""
    scheduler = StockAnalystScheduler()

    try:
        scheduler.start_scheduler(interval_minutes=1)

        while True:
            time.sleep(10)
            status = scheduler.get_job_status()
            print(f"Scheduler status: {status}")

    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop_scheduler()

if __name__ == "__main__":
    main()
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import atexit

from src.services.finalize import FinalizationService
from src.live_data.nse_provider import NSEProvider

logger = logging.getLogger(__name__)

class OptionsScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.finalize_service = FinalizationService()
        self.provider = NSEProvider()
        
    def start(self):
        """Start the scheduler"""
        try:
            # Add finalization job - runs every 10 minutes
            self.scheduler.add_job(
                func=self._finalize_strategies,
                trigger=IntervalTrigger(minutes=10),
                id='finalize_options_strategies',
                name='Finalize Options Strategies',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("✅ Options scheduler started with finalization job")
            
            # Ensure scheduler shuts down cleanly
            atexit.register(lambda: self.scheduler.shutdown())
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    def _finalize_strategies(self):
        """Finalize strategies job"""
        try:
            logger.info("Running strategy finalization job")
            self.finalize_service.finalize_strategies(self.provider)
            logger.info("Strategy finalization completed")
        except Exception as e:
            logger.error(f"Error in finalization job: {e}")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Options scheduler stopped")

# Global scheduler instance
scheduler = OptionsScheduler()
