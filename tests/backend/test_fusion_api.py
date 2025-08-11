
# tests/backend/test_fusion_api.py
import requests, time, json, os

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_fusion_dashboard_contract():
    """Test /api/fusion/dashboard returns complete contract"""
    r = requests.get(f"{BASE_URL}/api/fusion/dashboard", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    # Core contract fields
    for key in ["last_updated_utc","market_session","timeframes","ai_verdict_summary",
                "product_breakdown","pinned_summary","top_signals","alerts","generation_time_ms"]:
        assert key in data, f"Missing key {key}"
    
    # Timeframes contract
    assert isinstance(data["timeframes"], list), "timeframes must be array"
    assert len(data["timeframes"]) >= 6, "Must have at least 6 timeframes"
    
    # Pinned summary contract
    pinned = data["pinned_summary"]
    assert isinstance(pinned, dict), "pinned_summary must be object"
    for field in ["total_pinned", "categories", "recent_pins"]:
        assert field in pinned, f"Missing pinned_summary field: {field}"
    
    # Top signals contract with ai_verdict_normalized
    assert isinstance(data["top_signals"], list), "top_signals must be array"
    for signal in data["top_signals"]:
        assert "ai_verdict_normalized" in signal, "Missing ai_verdict_normalized in signal"
        valid_verdicts = {"STRONG_BUY", "BUY", "HOLD", "CAUTIOUS", "AVOID"}
        assert signal["ai_verdict_normalized"] in valid_verdicts, \
            f"Invalid verdict: {signal['ai_verdict_normalized']}"

def test_timeframes_and_kpis():
    r = requests.get(f"{BASE_URL}/api/fusion/dashboard", timeout=5)
    data = r.json()
    names = [tf.get("timeframe") for tf in data.get("timeframes",[])]
    for req in ["All","3D","5D","10D","15D","30D"]:
        assert req in names, f"Missing timeframe {req}"
    for tf in data["timeframes"]:
        for group in ["prediction_kpis","financial_kpis","risk_kpis"]:
            assert group in tf, f"KPI group {group} missing in {tf.get('timeframe')}"

def test_caching_and_force_refresh():
    r1 = requests.get(f"{BASE_URL}/api/fusion/dashboard", timeout=5)
    first = r1.json().get("last_updated_utc")
    time.sleep(0.1)
    r2 = requests.get(f"{BASE_URL}/api/fusion/dashboard", timeout=5)
    second = r2.json().get("last_updated_utc")
    assert first == second, "Cache did not hold between close requests"

    r3 = requests.get(f"{BASE_URL}/api/fusion/dashboard?forceRefresh=true", timeout=5)
    third = r3.json().get("last_updated_utc")
    assert third != first, "Force refresh did not change timestamp"

def test_verdicts_normalized():
    r = requests.get(f"{BASE_URL}/api/fusion/dashboard", timeout=5)
    data = r.json()
    valid = {"STRONG_BUY","BUY","HOLD","CAUTIOUS","AVOID"}
    for s in data.get("top_signals",[]):
        v = s.get("ai_verdict_normalized")
        assert v in valid, f"Invalid verdict {v}"

def test_perf_budget():
    r = requests.get(f"{BASE_URL}/api/fusion/dashboard", timeout=5)
    gen = r.json().get("generation_time_ms", 9999)
    assert gen <= 150, f"generation_time_ms too high: {gen}"
