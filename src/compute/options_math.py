
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any
import json
import os
import logging

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

def load_min_inputs(timeframe: str) -> List[Dict[str, Any]]:
    """Load minimal input set per symbol (NO historical arrays)"""
    try:
        # Generate sample data for demo (replace with real data loading)
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK']
        raw_rows = []
        
        for i, symbol in enumerate(symbols):
            base_price = 1000 + (i * 200)
            raw_rows.append({
                'symbol': symbol,
                'spot': base_price,
                'current_price': base_price,
                'call': {'strike': base_price + 100, 'premium': 25},
                'put': {'strike': base_price - 100, 'premium': 20},
                'call_premium': 25,
                'put_premium': 20,
                'lot_size': 100,
                'margin_required': 5000 + (i * 1000),
                'confidence': 75 + (i * 3),
                'prediction_outcome': ['On Track', 'Exceeded', 'At Risk'][i % 3],
                'risk': ['Low', 'Medium', 'High'][i % 3],
                'result': ['success', 'in_progress', 'failed'][i % 3]
            })
        
        return raw_rows
    except Exception as e:
        logger.error(f"Error loading min inputs: {e}")
        return []

def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def clearDataCache():
    """Clear old data cache to prevent memory leaks"""
    import gc
    collected = gc.collect()
    logger.info(f"Memory cleared: {collected} objects collected")
    return collected
