
from dataclasses import dataclass
from datetime import datetime
import gc

@dataclass
class OptionRow:
    symbol: str
    current_price: float
    call_strike: float
    put_strike: float
    total_premium: float
    breakeven_low: float
    breakeven_high: float
    margin_required: float
    roi_pct: float
    confidence: float
    prediction_outcome: str
    stop_loss_call: float
    stop_loss_put: float
    risk: str
    result: str  # "success" | "failed" | "in_progress"

def compute_row(raw) -> OptionRow:
    """Compute final row fields from minimal raw inputs"""
    spot = float(raw.get("spot", 0))
    call_data = raw.get("call", {})
    put_data = raw.get("put", {})
    lot = int(raw.get("lot_size", 1))
    
    call_premium = float(call_data.get("premium", 0))
    put_premium = float(put_data.get("premium", 0))
    
    total_premium = (call_premium + put_premium) * lot
    breakeven_low = spot - (total_premium / lot) if lot > 0 else 0
    breakeven_high = spot + (total_premium / lot) if lot > 0 else 0
    
    margin_required = float(raw.get("margin_required", 0))
    roi_pct = (total_premium / margin_required) * 100.0 if margin_required > 0 else 0
    
    # Determine result based on ROI
    if roi_pct >= 25:
        result = "success"
    elif roi_pct >= 15:
        result = "in_progress"
    else:
        result = "failed"
    
    return OptionRow(
        symbol=str(raw.get("symbol", "UNKNOWN")),
        current_price=round(spot, 2),
        call_strike=round(float(call_data.get("strike", 0)), 2),
        put_strike=round(float(put_data.get("strike", 0)), 2),
        total_premium=round(total_premium, 2),
        breakeven_low=round(breakeven_low, 2),
        breakeven_high=round(breakeven_high, 2),
        margin_required=round(margin_required, 2),
        roi_pct=round(roi_pct, 2),
        confidence=round(float(raw.get("confidence", 75.0)), 1),
        prediction_outcome=str(raw.get("prediction_outcome", "On Track")),
        stop_loss_call=round(float(raw.get("stop_loss_call", 0)), 2),
        stop_loss_put=round(float(raw.get("stop_loss_put", 0)), 2),
        risk=str(raw.get("risk", "Low")),
        result=result,
    )

def load_min_inputs(timeframe: str) -> list:
    """Load minimal input data for options computation"""
    # Import here to avoid circular imports
    try:
        from src.analyzers.short_strangle_engine import ShortStrangleEngine
        engine = ShortStrangleEngine()
        
        # Top tier stocks for options
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ITC', 'HINDUNILVR']
        raw_inputs = []
        
        for symbol in symbols:
            try:
                # Get minimal data needed for computation
                analysis = engine.analyze_short_strangle(symbol, manual_refresh=True, force_realtime=True)
                
                if analysis and analysis.get('current_price', 0) > 0:
                    # Convert to minimal input format
                    raw_input = {
                        "symbol": symbol,
                        "spot": analysis.get('current_price', 0),
                        "call": {
                            "strike": analysis.get('call_strike', 0),
                            "premium": analysis.get('call_premium', 0)
                        },
                        "put": {
                            "strike": analysis.get('put_strike', 0),
                            "premium": analysis.get('put_premium', 0)
                        },
                        "lot_size": analysis.get('lot_size', 1),
                        "margin_required": analysis.get('margin_required', 0),
                        "confidence": analysis.get('confidence', 75.0),
                        "prediction_outcome": analysis.get('prediction_outcome', 'On Track'),
                        "stop_loss_call": analysis.get('call_sl', 0),
                        "stop_loss_put": analysis.get('put_sl', 0),
                        "risk": analysis.get('risk_level', 'Low')
                    }
                    raw_inputs.append(raw_input)
                    
            except Exception as e:
                print(f"Error loading data for {symbol}: {e}")
                continue
        
        return raw_inputs
        
    except Exception as e:
        print(f"Error in load_min_inputs: {e}")
        return []

def now_iso() -> str:
    """Return current timestamp in ISO format"""
    return datetime.now().isoformat()
