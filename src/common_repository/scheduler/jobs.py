
"""
Scheduler Jobs
Background jobs for KPI calculation and other tasks
"""

import logging
from datetime import datetime

from common_repository.config.feature_flags import feature_flags
from common_repository.config.runtime import is_market_hours_now
from common_repository.utils.date_utils import get_ist_now

logger = logging.getLogger(__name__)

def job_kpi_refresh():
    """Background job to refresh KPIs during market hours"""
    if not feature_flags.is_enabled('enable_background_kpi_jobs'):
        logger.debug("KPI background jobs disabled")
        return
    
    try:
        logger.info("Starting KPI background refresh")
        
        # Import here to avoid circular imports
        from products.shared.services.kpi_service import kpi_service
        
        # Check if we should run (market hours or EOD)
        current_time = get_ist_now()
        is_market_time = is_market_hours_now()
        is_eod = current_time.hour == 16  # After market close
        
        if not (is_market_time or is_eod):
            logger.debug("Skipping KPI refresh - outside market hours")
            return
        
        # Compute KPIs for all timeframes and products
        timeframes = ['3D', '5D', '10D', '15D', '30D', 'All']
        products = [None, 'equities', 'options', 'commodities']  # None = overall
        
        refresh_count = 0
        for timeframe in timeframes:
            for product in products:
                try:
                    kpis = kpi_service.compute(timeframe=timeframe, product=product)
                    if kpis.get('sample_size', 0) > 0:
                        refresh_count += 1
                        
                        # Evaluate triggers
                        triggers = kpi_service.evaluate_triggers(kpis)
                        if triggers:
                            logger.info(f"Generated {len(triggers)} triggers for {product or 'overall'}/{timeframe}")
                            
                except Exception as e:
                    logger.error(f"Error computing KPIs for {product or 'overall'}/{timeframe}: {e}")
                    continue
        
        logger.info(f"KPI background refresh completed: {refresh_count} KPI sets updated")
        
    except Exception as e:
        logger.error(f"KPI background refresh failed: {e}")

def register_kpi_jobs(scheduler):
    """Register KPI jobs with the scheduler"""
    if not feature_flags.is_enabled('enable_background_kpi_jobs'):
        logger.info("KPI background jobs disabled - not registering")
        return
    
    try:
        # Add KPI refresh job - every 15 minutes during market hours
        scheduler.add_job(
            func=job_kpi_refresh,
            trigger="interval",
            minutes=15,
            id="kpi_refresh",
            name="KPI Background Refresh",
            replace_existing=True
        )
        
        logger.info("✅ KPI background jobs registered")
        
    except Exception as e:
        logger.error(f"Failed to register KPI jobs: {e}")
