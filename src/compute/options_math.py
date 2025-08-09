from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any
import json
import os
import logging
import gc

logger = logging.getLogger(__name__)

@dataclass
class OptionRow:
    symbol: str
    current_price: float
    call_strike: float
    put_strike: float
    total_premium: float
    breakeven_low: float
    breakeven_high: float
    margin_req: float
    roi_pct: float
    confidence: float
    prediction_outcome: str
    stop_loss_call: float
    stop_loss_put: float
    risk: str
    result: str  # "success" | "failed" | "in_progress"

class MinimalRow:
    """Minimal row class for memory efficiency"""
    def __init__(self, symbol, current_price, timeframe, timestamp):
        self.symbol = symbol
        self.current_price = current_price
        self.timeframe = timeframe
        self.timestamp = timestamp

class OptionsStrategy:
    """Options strategy result class"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def normalize_option_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize incoming data to standard schema and fix field name drift"""
    normalized = {}

    # Standard field mappings with fallbacks
    field_mappings = {
        'symbol': ['symbol', 'ticker', 'stock'],
        'current_price': ['current_price', 'spot', 'price', 'stock_price'],
        'call_strike': ['call_strike', 'callStrike', 'call_strike_price'],
        'put_strike': ['put_strike', 'putStrike', 'put_strike_price'],
        'total_premium': ['total_premium', 'premium', 'totalPremium'],
        'breakeven_low': ['breakeven_low', 'breakevenLow', 'lower_breakeven'],
        'breakeven_high': ['breakeven_high', 'breakevenHigh', 'upper_breakeven'],
        'margin_req': ['margin_req', 'margin_required', 'margin', 'required_margin'],
        'roi_pct': ['roi_pct', 'roi', 'expected_roi', 'return_pct'],
        'confidence': ['confidence', 'conf', 'confidence_score'],
        'prediction_outcome': ['prediction_outcome', 'outcome', 'status'],
        'stop_loss_call': ['stop_loss_call', 'callStopLoss', 'call_sl'],
        'stop_loss_put': ['stop_loss_put', 'putStopLoss', 'put_sl'],
        'risk': ['risk', 'risk_level', 'riskLevel'],
        'result': ['result', 'final_result', 'outcome_status']
    }

    # Map fields with fallbacks
    for target_field, source_options in field_mappings.items():
        value = None
        for source_field in source_options:
            if source_field in raw_data and raw_data[source_field] is not None:
                value = raw_data[source_field]
                break

        # Set defaults for missing fields
        if value is None:
            if target_field in ['symbol', 'prediction_outcome', 'risk', 'result']:
                value = 'N/A' if target_field == 'symbol' else 'Unknown'
            else:
                value = 0.0

        normalized[target_field] = value

    return normalized

def compute_row(raw: Dict[str, Any]) -> OptionRow:
    """Compute final row fields from minimal inputs with normalization"""
    try:
        # Normalize the raw data first
        normalized = normalize_option_data(raw)

        spot = float(normalized.get('current_price', 0))
        call_strike = float(normalized.get('call_strike', 0))
        put_strike = float(normalized.get('put_strike', 0))
        call_premium = float(raw.get('call_premium', 0))
        put_premium = float(raw.get('put_premium', 0))
        lot_size = int(raw.get('lot_size', 1))

        total_premium = (call_premium + put_premium) * lot_size
        breakeven_low = put_strike - (total_premium / lot_size) if lot_size > 0 else 0
        breakeven_high = call_strike + (total_premium / lot_size) if lot_size > 0 else 0

        margin_required = float(raw.get('margin_required', total_premium * 0.2))
        roi_pct = (total_premium / margin_required) * 100.0 if margin_required > 0 else 0

        return OptionRow(
            symbol=str(normalized['symbol']),
            current_price=round(spot, 2),
            call_strike=round(call_strike, 2),
            put_strike=round(put_strike, 2),
            total_premium=round(total_premium, 2),
            breakeven_low=round(breakeven_low, 2),
            breakeven_high=round(breakeven_high, 2),
            margin_req=round(margin_required, 2),
            roi_pct=round(roi_pct, 2),
            confidence=float(normalized.get('confidence', 75.0)),
            prediction_outcome=str(normalized.get('prediction_outcome', 'On Track')),
            stop_loss_call=float(normalized.get('stop_loss_call', 0)),
            stop_loss_put=float(normalized.get('stop_loss_put', 0)),
            risk=str(normalized.get('risk', 'Medium')),
            result=str(normalized.get('result', 'in_progress'))
        )
    except Exception as e:
        logger.error(f"Error computing row for {raw.get('symbol', 'unknown')}: {e}")
        # Return safe defaults
        return OptionRow(
            symbol=str(raw.get('symbol', 'ERROR')),
            current_price=0.0, call_strike=0.0, put_strike=0.0,
            total_premium=0.0, breakeven_low=0.0, breakeven_high=0.0,
            margin_req=0.0, roi_pct=0.0, confidence=0.0,
            prediction_outcome='Error', stop_loss_call=0.0, stop_loss_put=0.0,
            risk='High', result='failed'
        )

def get_active_symbols(timeframe):
    """Get active symbols for timeframe"""
    # Return a limited set of symbols based on timeframe
    base_symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'ICICIBANK', 'INFY']
    if timeframe == '30D':
        return base_symbols[:3]  # Further limit for longer timeframes
    return base_symbols

def get_current_symbol_data(symbol):
    """Get current data for symbol without historical arrays"""
    try:
        # Fetch only current price and essential metrics
        # This would connect to your data source
        return {'price': 100.0}  # Placeholder
    except:
        return None

def compute_row(min_row):
    """Compute final row from minimal inputs"""
    try:
        # Compute options strategy from minimal data
        return OptionsStrategy(
            symbol=min_row.symbol,
            call_strike=min_row.current_price * 1.05,
            put_strike=min_row.current_price * 0.95,
            total_premium=min_row.current_price * 0.02,
            breakeven_low=min_row.current_price * 0.93,
            breakeven_high=min_row.current_price * 1.07,
            margin_req=min_row.current_price * 0.1,
            roi_pct=5.0,
            confidence=75,
            stop_loss_call=min_row.current_price * 1.1,
            stop_loss_put=min_row.current_price * 0.9,
            risk='Medium',
            result='in_progress'
        )
    except Exception as e:
        logger.error(f"Error computing row for {min_row.symbol}: {e}")
        return OptionsStrategy(symbol=min_row.symbol, **get_default_strategy())

def get_default_strategy():
    """Get default strategy values"""
    return {
        'call_strike': 0, 'put_strike': 0, 'total_premium': 0,
        'breakeven_low': 0, 'breakeven_high': 0, 'margin_req': 0,
        'roi_pct': 0, 'confidence': 0, 'stop_loss_call': 0,
        'stop_loss_put': 0, 'risk': 'Unknown', 'result': 'error'
    }

def load_min_inputs(timeframe: str) -> List[Dict[str, Any]]:
    """Load minimal input set per symbol (NO historical arrays) - Memory optimized"""
    try:
        raw_rows = []

        # Load only essential data for current timeframe
        symbols = get_active_symbols(timeframe)

        for symbol in symbols[:50]:  # Limit to prevent memory issues
            try:
                # Load only current price and essential metrics
                current_data = get_current_symbol_data(symbol)
                if current_data:
                    # Create minimal row object with only required fields
                    min_row = MinimalRow(
                        symbol=symbol,
                        current_price=current_data.get('price', 0),
                        timeframe=timeframe,
                        timestamp=now_iso()
                    )
                    raw_rows.append(min_row)
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
                continue

        # Force garbage collection
        gc.collect()
        logger.info(f"Loaded {len(raw_rows)} minimal input rows")
        return raw_rows

    except Exception as e:
        logger.error(f"Error loading minimal inputs: {e}")
        return []

def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def clearDataCache():
    """Clear old data cache to prevent memory leaks"""
    collected = gc.collect()
    logger.info(f"Memory cleared: {collected} objects collected")
    return collected