
import requests, os, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_strangle_candidates_schema():
    """Test /api/options/strangle/candidates returns proper schema"""
    r = requests.get(f"{BASE_URL}/api/options/strangle/candidates", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required fields
    for field in ["candidates", "metadata", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"
    
    # Check candidates structure
    assert isinstance(data["candidates"], list), "candidates must be array"
    if data["candidates"]:
        candidate = data["candidates"][0]
        required_fields = ["symbol", "underlying_price", "call_strike", "put_strike",
                          "call_premium", "put_premium", "total_premium", "max_profit",
                          "probability_profit", "dte", "ai_verdict_normalized"]
        for field in required_fields:
            assert field in candidate, f"Missing candidate field: {field}"

def test_strangle_plan_flow():
    """Test strangle plan creation and position flow"""
    # Create a plan
    plan_data = {
        "symbol": "TCS",
        "call_strike": 4000,
        "put_strike": 3800,
        "quantity": 1,
        "expiry": "2025-01-30"
    }
    
    r = requests.post(f"{BASE_URL}/api/options/strangle/plan", 
                     json=plan_data, timeout=5)
    assert r.status_code == 200, f"Plan creation failed: {r.text}"
    plan_result = r.json()
    
    # Check plan response
    assert "plan_id" in plan_result, "Missing plan_id"
    assert "estimated_premium" in plan_result, "Missing estimated_premium"
    assert "max_profit" in plan_result, "Missing max_profit"

def test_options_positions_schema():
    """Test /api/options/positions returns proper schema"""
    r = requests.get(f"{BASE_URL}/api/options/positions", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required fields
    for field in ["positions", "summary", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"
    
    # Check positions structure
    assert isinstance(data["positions"], list), "positions must be array"
    if data["positions"]:
        position = data["positions"][0]
        required_fields = ["position_id", "symbol", "strategy_type", "entry_date",
                          "status", "pnl", "current_value"]
        for field in required_fields:
            assert field in position, f"Missing position field: {field}"
