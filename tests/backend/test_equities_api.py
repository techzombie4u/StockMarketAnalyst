
import requests
import os

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_equities_list_schema():
    """Test /api/equities/list returns proper schema with 30+ tickers"""
    r = requests.get(f"{BASE_URL}/api/equities/list", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required top-level fields
    assert "items" in data, "Missing items field"
    assert "total" in data, "Missing total field"
    
    # Check we have 30+ Indian tickers
    items = data["items"]
    assert len(items) >= 30, f"Expected >= 30 tickers, got {len(items)}"
    
    # Check required fields in each equity
    for equity in items:
        required_fields = [
            "symbol", "name", "sector", "price", "verdict", "confidence",
            "rsi", "macd", "momentum", "volatility", "from52wHigh", "model"
        ]
        for field in required_fields:
            assert field in equity, f"Missing field {field} in equity {equity.get('symbol', 'unknown')}"
        
        # Validate ML/technical fields
        assert isinstance(equity["rsi"], (int, float)), f"RSI should be numeric for {equity['symbol']}"
        assert isinstance(equity["macd"], (int, float)), f"MACD should be numeric for {equity['symbol']}"
        assert isinstance(equity["momentum"], (int, float)), f"Momentum should be numeric for {equity['symbol']}"
        assert isinstance(equity["volatility"], (int, float)), f"Volatility should be numeric for {equity['symbol']}"
        assert isinstance(equity["from52wHigh"], (int, float)), f"from52wHigh should be numeric for {equity['symbol']}"
        assert equity["model"] in ["ensemble", "lstm", "random_forest"], f"Invalid model for {equity['symbol']}"

def test_equities_list_filters():
    """Test sector and price filtering"""
    # Test sector filter
    r = requests.get(f"{BASE_URL}/api/equities/list?sector=IT", timeout=5)
    assert r.status_code == 200
    data = r.json()
    for equity in data["items"]:
        assert equity["sector"] == "IT", f"Sector filter failed for {equity['symbol']}"
    
    # Test price range filter
    r = requests.get(f"{BASE_URL}/api/equities/list?priceMin=1000&priceMax=2000", timeout=5)
    assert r.status_code == 200
    data = r.json()
    for equity in data["items"]:
        assert 1000 <= equity["price"] <= 2000, f"Price filter failed for {equity['symbol']}: {equity['price']}"

def test_charts_endpoint():
    """Test /api/equities/charts/<symbol> endpoint"""
    symbol = "TCS"
    r = requests.get(f"{BASE_URL}/api/equities/charts/{symbol}", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required top-level fields
    required_fields = ["symbol", "tf", "prices", "rsi", "macd", "bbands"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    
    # Validate symbol and timeframe
    assert data["symbol"] == symbol, f"Symbol mismatch: expected {symbol}, got {data['symbol']}"
    assert data["tf"] == "10D", f"Default timeframe should be 10D, got {data['tf']}"
    
    # Validate all series arrays are non-empty
    assert len(data["prices"]) > 0, "Prices array should not be empty"
    assert len(data["rsi"]) > 0, "RSI array should not be empty"
    assert len(data["macd"]) > 0, "MACD array should not be empty"
    assert len(data["bbands"]) > 0, "BBands array should not be empty"
    
    # Validate OHLC structure
    for price in data["prices"]:
        required_ohlc = ["t", "o", "h", "l", "c"]
        for field in required_ohlc:
            assert field in price, f"Missing OHLC field: {field}"
        assert isinstance(price["o"], (int, float)), "Open should be numeric"
        assert isinstance(price["h"], (int, float)), "High should be numeric"
        assert isinstance(price["l"], (int, float)), "Low should be numeric"
        assert isinstance(price["c"], (int, float)), "Close should be numeric"
    
    # Validate MACD structure
    for macd_point in data["macd"]:
        required_macd = ["macd", "signal", "hist"]
        for field in required_macd:
            assert field in macd_point, f"Missing MACD field: {field}"
    
    # Validate BBands structure
    for bb_point in data["bbands"]:
        required_bb = ["upper", "mid", "lower"]
        for field in required_bb:
            assert field in bb_point, f"Missing BBands field: {field}"

def test_charts_timeframes():
    """Test charts endpoint with different timeframes"""
    symbol = "RELIANCE"
    timeframes = ["5D", "10D", "1M", "3M"]
    
    for tf in timeframes:
        r = requests.get(f"{BASE_URL}/api/equities/charts/{symbol}?tf={tf}", timeout=5)
        assert r.status_code == 200, f"Failed for timeframe {tf}"
        data = r.json()
        assert data["tf"] == tf, f"Timeframe mismatch: expected {tf}, got {data['tf']}"
        assert len(data["prices"]) > 0, f"Empty prices for timeframe {tf}"

def test_charts_invalid_symbol():
    """Test charts endpoint with invalid symbol"""
    r = requests.get(f"{BASE_URL}/api/equities/charts/INVALID", timeout=5)
    assert r.status_code == 200  # Should still return data (mock)
    data = r.json()
    assert data["symbol"] == "INVALID"

if __name__ == "__main__":
    test_equities_list_schema()
    test_equities_list_filters()
    test_charts_endpoint()
    test_charts_timeframes()
    test_charts_invalid_symbol()
    print("✅ All equities API tests passed!")
