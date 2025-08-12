
import requests, os, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_commodities_detail_endpoint():
    """Test /api/commodities/{symbol}/detail returns proper structure"""
    symbols = ["GOLD", "SILVER", "CRUDE"]
    
    for symbol in symbols:
        r = requests.get(f"{BASE_URL}/api/commodities/{symbol}/detail?tf=30D", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        
        # Check required fields
        required_fields = ["symbol", "timeframe", "prices", "seasonality", "atr_bands", "last_updated_utc"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Validate prices array
        assert isinstance(data["prices"], list), "prices must be array"
        assert len(data["prices"]) > 0, "prices array cannot be empty"
        
        if data["prices"]:
            price_item = data["prices"][0]
            assert "date" in price_item, "price item must have date"
            assert "price" in price_item, "price item must have price"
            assert isinstance(price_item["price"], (int, float)), "price must be numeric"
        
        # Validate seasonality array
        assert isinstance(data["seasonality"], list), "seasonality must be array"
        assert len(data["seasonality"]) == 12, "seasonality must have 12 months"
        
        for month_data in data["seasonality"]:
            assert "month" in month_data, "seasonality item must have month"
            assert "avg_return" in month_data, "seasonality item must have avg_return"
            assert 1 <= month_data["month"] <= 12, "month must be 1-12"
            assert isinstance(month_data["avg_return"], (int, float)), "avg_return must be numeric"
        
        # Validate ATR bands
        atr_bands = data["atr_bands"]
        assert isinstance(atr_bands, dict), "atr_bands must be object"
        
        required_atr_fields = ["upper", "middle", "lower", "atr_value", "regime"]
        for field in required_atr_fields:
            assert field in atr_bands, f"Missing ATR field: {field}"
        
        # Validate ATR band order
        assert atr_bands["upper"] > atr_bands["middle"], "Upper band must be > middle"
        assert atr_bands["middle"] > atr_bands["lower"], "Middle must be > lower band"
        assert atr_bands["atr_value"] > 0, "ATR value must be positive"

def test_commodities_correlations_endpoint():
    """Test /api/commodities/correlations returns proper correlations"""
    symbols = ["GOLD", "SILVER", "CRUDE", "COPPER"]
    
    for symbol in symbols:
        r = requests.get(f"{BASE_URL}/api/commodities/correlations?symbol={symbol}", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        
        # Check required correlation fields
        required_fields = ["usdInr", "nifty"]
        for field in required_fields:
            assert field in data, f"Missing correlation field: {field}"
            
            # Validate correlation values are within [-1, 1]
            corr_value = data[field]
            assert isinstance(corr_value, (int, float)), f"{field} must be numeric"
            assert -1 <= corr_value <= 1, f"{field} correlation must be between -1 and 1, got {corr_value}"

def test_commodities_detail_timeframe_parameter():
    """Test detail endpoint with different timeframe parameters"""
    timeframes = ["10D", "30D"]
    
    for tf in timeframes:
        r = requests.get(f"{BASE_URL}/api/commodities/GOLD/detail?tf={tf}", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = r.json()
        
        assert data["timeframe"] == tf, f"Timeframe mismatch: expected {tf}, got {data['timeframe']}"
        assert len(data["prices"]) > 0, f"No price data for timeframe {tf}"

def test_commodities_signals_schema():
    """Test /api/commodities/signals returns proper schema"""
    r = requests.get(f"{BASE_URL}/api/commodities/signals", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check data is array
    assert isinstance(data, list), "signals must be array"
    
    if data:
        signal = data[0]
        required_fields = ["ticker", "contract", "verdict", "confidence", "atrPct", "rsi", "breakout", "updated"]
        for field in required_fields:
            assert field in signal, f"Missing signal field: {field}"
        
        # Validate signal strength is numeric
        assert isinstance(signal["confidence"], (int, float)), "confidence must be numeric"
        assert 0 <= signal["confidence"] <= 1, "confidence must be between 0 and 1"

def test_commodities_correlations_shape():
    """Test /api/commodities/correlations returns proper shape"""
    r = requests.get(f"{BASE_URL}/api/commodities/correlations", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required fields
    assert isinstance(data, dict), "correlations must be object"
    
    # Validate all correlation values
    for key, value in data.items():
        assert isinstance(value, (int, float)), f"{key} correlation must be numeric"
        assert -1 <= value <= 1, f"{key} correlation must be between -1 and 1"

def test_commodities_api_endpoint():
    """Test /api/commodities general endpoint"""
    r = requests.get(f"{BASE_URL}/api/commodities", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check basic structure
    assert isinstance(data, dict), "Response must be object"
    assert "signals" in data, "Missing signals field"
    assert isinstance(data["signals"], list), "signals must be array"
