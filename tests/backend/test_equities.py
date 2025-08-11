
import requests, os, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_equities_list_schema():
    """Test /api/equities/list returns proper schema"""
    r = requests.get(f"{BASE_URL}/api/equities/list", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Check required top-level fields
    for field in ["equities", "metadata", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"
    
    # Check equities array structure
    assert isinstance(data["equities"], list), "equities must be array"
    if data["equities"]:
        equity = data["equities"][0]
        required_fields = ["symbol", "name", "current_price", "change_percent", 
                          "volume", "market_cap", "pe_ratio", "ai_verdict_normalized"]
        for field in required_fields:
            assert field in equity, f"Missing equity field: {field}"
        
        # Validate ai_verdict_normalized
        valid_verdicts = {"STRONG_BUY", "BUY", "HOLD", "CAUTIOUS", "AVOID"}
        assert equity["ai_verdict_normalized"] in valid_verdicts, \
            f"Invalid verdict: {equity['ai_verdict_normalized']}"

def test_equities_filter_behavior():
    """Test filtering behavior works correctly"""
    # Test with filter
    r = requests.get(f"{BASE_URL}/api/equities/list?filter=BUY", timeout=5)
    assert r.status_code == 200
    data = r.json()
    
    # If results exist, all should match filter
    for equity in data.get("equities", []):
        verdict = equity.get("ai_verdict_normalized", "")
        assert verdict in ["STRONG_BUY", "BUY"], f"Filter failed: {verdict}"

def test_equities_pagination():
    """Test pagination parameters"""
    r = requests.get(f"{BASE_URL}/api/equities/list?limit=5&offset=0", timeout=5)
    assert r.status_code == 200
    data = r.json()
    
    # Should respect limit
    assert len(data.get("equities", [])) <= 5, "Limit not respected"
    
    # Metadata should include pagination info
    metadata = data.get("metadata", {})
    assert "total_count" in metadata, "Missing total_count in metadata"
