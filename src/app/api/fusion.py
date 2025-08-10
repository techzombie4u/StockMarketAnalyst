"""
Fusion API - KPI + AI Verdict Dashboard endpoint
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import Blueprint, jsonify, request

from ...common_repository.config.feature_flags import feature_flags
from ...common_repository.utils.date_utils import get_ist_now, IST
from ...core.fusion.fusion_schema import (
    FusionDashboardPayload, MarketSession, Alert, AlertSeverity, TopSignal
)
from ...core.fusion.kpi_mapper import kpi_mapper
from ...core.fusion.verdict_aggregator import verdict_aggregator
from ...core.fusion.pinned_rollup import pinned_rollup

logger = logging.getLogger(__name__)

# Create blueprint
fusion_bp = Blueprint('fusion', __name__, url_prefix='/api/fusion')

# Simple in-memory cache
_fusion_cache = {
    'data': None,
    'timestamp': None,
    'ttl_seconds': 120
}

@fusion_bp.route('/dashboard', methods=['GET'])
def get_fusion_dashboard():
    """Get complete fusion dashboard data"""
    start_time = time.time()

    try:
        # Check feature flag
        if not feature_flags.is_enabled('ui_fusion_dashboard_enabled'):
            return jsonify({'disabled': True, 'message': 'Fusion dashboard is disabled'})

        # Check for force refresh
        force_refresh = request.args.get('forceRefresh', '').lower() == 'true'

        # Check cache unless force refresh
        if not force_refresh and _is_cache_valid():
            _fusion_cache['data'].cache_hit = True
            _fusion_cache['data'].generation_time_ms = (time.time() - start_time) * 1000
            return jsonify(_fusion_cache['data'].to_dict())

        # Generate fresh data
        fusion_data = _generate_fusion_data()

        # Update cache
        _fusion_cache['data'] = fusion_data
        _fusion_cache['timestamp'] = time.time()
        _fusion_cache['ttl_seconds'] = feature_flags.get_flag_value('ui_fusion_cache_ttl_seconds', 120)

        fusion_data.generation_time_ms = (time.time() - start_time) * 1000
        fusion_data.cache_hit = False

        logger.info(f"Fusion dashboard generated in {fusion_data.generation_time_ms:.1f}ms")

        return jsonify(fusion_data.to_dict())

    except Exception as e:
        logger.error(f"Error generating fusion dashboard: {e}")
        return jsonify({
            'error': 'Failed to generate fusion dashboard',
            'message': str(e),
            'generation_time_ms': (time.time() - start_time) * 1000
        }), 500

def _is_cache_valid() -> bool:
    """Check if cached data is still valid"""
    if not _fusion_cache['data'] or not _fusion_cache['timestamp']:
        return False

    age_seconds = time.time() - _fusion_cache['timestamp']
    return age_seconds < _fusion_cache['ttl_seconds']

def _generate_fusion_data() -> FusionDashboardPayload:
    """Generate complete fusion dashboard data"""
    try:
        # Load source data with timeout protection
        kpi_data = _load_kpi_data()
        predictions_data = _load_predictions_data()
        pinned_symbols = _load_pinned_symbols()
        alerts = _load_alerts()

        # Map timeframe KPIs
        timeframes = []
        for tf in ['All', '3D', '5D', '10D', '15D', '30D']:
            timeframe_kpis = kpi_mapper.map_timeframe_kpis(kpi_data, tf)
            timeframes.append(timeframe_kpis)

        # Aggregate AI verdicts
        verdict_data = verdict_aggregator.aggregate_verdicts(predictions_data)

        # Calculate pinned summary
        pinned_summary = pinned_rollup.calculate_pinned_summary(pinned_symbols, predictions_data)

        # Generate top signals
        top_signals = _generate_top_signals(predictions_data, pinned_symbols)

        # Determine market session
        market_session = _determine_market_session()

        return FusionDashboardPayload(
            last_updated_utc=datetime.now(timezone.utc).isoformat(),
            market_session=market_session,
            timeframes=timeframes,
            ai_verdict_summary=verdict_data['verdict_summary'],
            product_breakdown=verdict_data['product_breakdown'],
            pinned_summary=pinned_summary,
            top_signals=top_signals,
            alerts=alerts
        )

    except Exception as e:
        logger.error(f"Error generating fusion data: {e}")
        raise

def _load_kpi_data() -> Dict[str, Any]:
    """Load KPI data from service"""
    try:
        from ...products.shared.services.kpi_service import kpi_service
        return kpi_service.get_all_kpis()
    except Exception as e:
        logger.warning(f"Error loading KPI data: {e}")
        return {}

def _load_predictions_data() -> list:
    """Load predictions data"""
    try:
        from ...common_repository.storage.json_store import json_store

        # Load from various sources
        predictions = []

        # Load current stock data
        stock_data = json_store.load('top10', {})
        stocks = stock_data.get('stocks', [])

        for stock in stocks:
            predictions.append({
                'symbol': stock.get('symbol', ''),
                'product': 'equities',
                'timeframe': '5D',
                'ai_verdict': stock.get('ai_verdict', 'HOLD'),
                'confidence': stock.get('confidence', 0.0),
                'score': stock.get('score', 0.0),
                'predicted_value': stock.get('predicted_price'),
                'current_value': stock.get('current_price'),
                'outcome_status': 'IN_PROGRESS',
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'due_date': (datetime.now()).strftime('%Y-%m-%d')
            })

        # Load tracking data for outcomes
        tracking_data = json_store.load('interactive_tracking', {})
        if isinstance(tracking_data, list):
            for entry in tracking_data:
                if isinstance(entry, dict):
                    predictions.append({
                        'symbol': entry.get('symbol', ''),
                        'product': 'options' if 'strangle' in str(entry).lower() else 'equities',
                        'timeframe': entry.get('timeframe', '5D'),
                        'ai_verdict': entry.get('ai_verdict', 'HOLD'),
                        'confidence': entry.get('confidence', 0.0),
                        'score': entry.get('score', 0.0),
                        'outcome_status': entry.get('status', 'IN_PROGRESS'),
                        'start_date': entry.get('start_date', ''),
                        'due_date': entry.get('expiry_date', '')
                    })

        return predictions

    except Exception as e:
        logger.warning(f"Error loading predictions data: {e}")
        return []

def _load_pinned_symbols() -> list:
    """Load pinned symbols"""
    try:
        from ...common_repository.utils.pinned_manager import pinned_manager
        return pinned_manager.get_all_pinned_symbols()
    except Exception as e:
        logger.warning(f"Error loading pinned symbols: {e}")
        return []

def _load_alerts() -> list:
    """Load system alerts"""
    alerts = []

    try:
        # Load GoAhead alerts
        goahead_alerts = _load_goahead_alerts()
        alerts.extend(goahead_alerts)

        # Load Trainer Agent alerts  
        trainer_alerts = _load_trainer_alerts()
        alerts.extend(trainer_alerts)

        # Load system alerts
        system_alerts = _load_system_alerts()
        alerts.extend(system_alerts)

    except Exception as e:
        logger.warning(f"Error loading alerts: {e}")

    return alerts

def _load_goahead_alerts() -> list:
    """Load alerts from GoAhead agent"""
    alerts = []
    try:
        # Check for KPI breaches that would trigger GoAhead
        kpi_data = _load_kpi_data()

        for timeframe, data in kpi_data.items():
            if isinstance(data, dict):
                hit_rate = data.get('hit_rate', 0.0)
                if hit_rate < 0.60:  # Below 60% threshold
                    alerts.append(Alert(
                        type='kpi_breach',
                        message=f'{timeframe} hit rate at {hit_rate:.1%} - below threshold',
                        severity=AlertSeverity.WARNING,
                        timestamp=datetime.now(),
                        source='GoAhead'
                    ))
    except Exception as e:
        logger.warning(f"Error loading GoAhead alerts: {e}")

    return alerts

def _load_trainer_alerts() -> list:
    """Load alerts from Trainer Agent"""
    alerts = []
    try:
        from ...common_repository.storage.json_store import json_store

        # Check recent training events
        model_kpi = json_store.load('model_kpi', {})
        last_training = model_kpi.get('last_training_date')

        if last_training:
            alerts.append(Alert(
                type='model_retrain',
                message=f'Models retrained on {last_training}',
                severity=AlertSeverity.INFO,
                timestamp=datetime.now(),
                source='Trainer Agent'
            ))

    except Exception as e:
        logger.warning(f"Error loading Trainer alerts: {e}")

    return alerts

def _load_system_alerts() -> list:
    """Load system-level alerts"""
    alerts = []

    # Add performance alerts
    try:
        import psutil
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 85:
            alerts.append(Alert(
                type='resource',
                message=f'High memory usage: {memory_percent:.1f}%',
                severity=AlertSeverity.WARNING,
                timestamp=datetime.now(),
                source='System'
            ))
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Error checking system resources: {e}")

    return alerts

def _generate_top_signals(predictions_data: list, pinned_symbols: list) -> list:
    """Generate top 10 signals by score/confidence"""
    try:
        # Convert to TopSignal objects
        signals = []
        for pred in predictions_data:
            signal = TopSignal(
                symbol=pred.get('symbol', ''),
                product=pred.get('product', 'unknown'),
                timeframe=pred.get('timeframe', '5D'),
                ai_verdict=pred.get('ai_verdict', 'HOLD'),
                ai_verdict_normalized=verdict_aggregator.normalize_verdict(pred.get('ai_verdict', 'HOLD')),
                confidence=pred.get('confidence', 0.0),
                score=pred.get('score', 0.0),
                predicted_value=pred.get('predicted_value'),
                current_value=pred.get('current_value'),
                outcome_status=pred.get('outcome_status', 'IN_PROGRESS'),
                start_date=pred.get('start_date', ''),
                due_date=pred.get('due_date', ''),
                is_pinned=pred.get('symbol', '') in pinned_symbols
            )
            signals.append(signal)

        # Sort by score/confidence and take top 10
        signals.sort(key=lambda x: (x.score, x.confidence), reverse=True)
        return signals[:10]

    except Exception as e:
        logger.error(f"Error generating top signals: {e}")
        return []

def _determine_market_session() -> MarketSession:
    """Determine current market session"""
    try:
        now_ist = datetime.now(IST)
        hour = now_ist.hour

        # Market hours: 9:15 AM to 3:30 PM IST
        if 9 <= hour < 15:
            return MarketSession.OPEN
        elif hour == 15 and now_ist.minute <= 30:
            return MarketSession.OPEN
        elif 6 <= hour < 9:
            return MarketSession.PRE_MARKET
        elif (hour == 15 and now_ist.minute > 30) or (16 <= hour < 18):
            return MarketSession.POST_MARKET
        else:
            return MarketSession.CLOSED

    except Exception as e:
        logger.warning(f"Error determining market session: {e}")
        return MarketSession.CLOSED