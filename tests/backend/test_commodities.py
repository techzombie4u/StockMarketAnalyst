
import requests, os, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_commodities_signals_schema():
    """Test /api/commodities/signals returns proper schema"""
    r = requests.get(f"{BASE_URL}/api/commodities/signals", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required fields
    for field in ["signals", "metadata", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"
    
    # Check signals structure
    assert isinstance(data["signals"], list), "signals must be array"
    if data["signals"]:
        signal = data["signals"][0]
        required_fields = ["commodity", "signal_type", "strength", "price",
                          "change_percent", "volume", "ai_verdict_normalized"]
        for field in required_fields:
            assert field in signal, f"Missing signal field: {field}"
        
        # Validate signal strength is numeric
        assert isinstance(signal["strength"], (int, float)), "strength must be numeric"

def test_commodities_correlations_shape():
    """Test /api/commodities/correlations returns proper shape"""
    r = requests.get(f"{BASE_URL}/api/commodities/correlations", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required fields
    for field in ["correlations", "matrix", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"
    
    # Check correlations structure
    correlations = data["correlations"]
    assert isinstance(correlations, dict), "correlations must be object"
    
    # Check matrix shape
    matrix = data["matrix"]
    assert isinstance(matrix, list), "matrix must be array"
    if matrix:
        # Each row should be array of same length
        row_length = len(matrix[0])
        for row in matrix:
            assert len(row) == row_length, "Matrix rows must have equal length"
            for val in row:
                assert isinstance(val, (int, float)), "Matrix values must be numeric"
                assert -1 <= val <= 1, "Correlation values must be between -1 and 1"

def test_commodities_api_endpoint():
    """Test /api/commodities general endpoint"""
    r = requests.get(f"{BASE_URL}/api/commodities", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check basic structure
    assert isinstance(data, dict), "Response must be object"
    assert "commodities" in data, "Missing commodities field"
    assert isinstance(data["commodities"], list), "commodities must be array"
