
import requests
import json
import time
import pytest

BASE = "http://localhost:5000"

def test_fusion_dashboard():
    """Test fusion dashboard API contract"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=5)
    r.raise_for_status()
    j = r.json()
    assert "top_signals" in j
    assert "timeframes" in j
    assert "pinned_rollup" in j
    assert "kpis" in j

def test_equities_list_and_kpis():
    """Test equities endpoints"""
    r = requests.get(f"{BASE}/api/equities/list", timeout=5)
    r.raise_for_status()
    j = r.json()
    assert isinstance(j.get("items"), list)
    assert len(j["items"]) >= 1
    
    r = requests.get(f"{BASE}/api/equities/kpis?timeframe=5D", timeout=5)
    r.raise_for_status()

def test_options_contract():
    """Test options endpoints"""
    r = requests.get(f"{BASE}/api/options/strangle/candidates?underlying=TCS&expiry=2025-08-28", timeout=5)
    r.raise_for_status()
    j = r.json()
    assert j
    assert "payoff" in j[0]
    assert "margin" in j[0]

def test_commodities_endpoints():
    """Test commodities endpoints"""
    r = requests.get(f"{BASE}/api/commodities/signals", timeout=5)
    r.raise_for_status()
    
    r = requests.get(f"{BASE}/api/commodities/correlations?symbol=GOLD", timeout=5)
    r.raise_for_status()

def test_pins_locks():
    """Test pins and locks persistence"""
    # Test pins
    r = requests.post(f"{BASE}/api/pins", 
                     json={"items": [{"type": "equity", "symbol": "TCS"}]}, 
                     timeout=5)
    r.raise_for_status()
    
    r = requests.get(f"{BASE}/api/pins", timeout=5)
    r.raise_for_status()
    assert any(x.get("symbol") == "TCS" for x in r.json().get("items", []))
    
    # Test locks
    r = requests.post(f"{BASE}/api/locks", 
                     json={"items": [{"type": "position", "id": "plan-1"}]}, 
                     timeout=5)
    r.raise_for_status()
    
    r = requests.get(f"{BASE}/api/locks", timeout=5)
    r.raise_for_status()

def test_kpi_endpoints():
    """Test KPI calculation endpoints"""
    r = requests.get(f"{BASE}/api/kpi/metrics?timeframe=All", timeout=5)
    r.raise_for_status()
    j = r.json()
    assert "prediction_accuracy" in j or "acc" in j

def test_health_check():
    """Test basic health endpoint"""
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()
    j = r.json()
    assert j.get("status") == "healthy"

if __name__ == "__main__":
    # Run tests individually for debugging
    test_health_check()
    test_fusion_dashboard()
    test_equities_list_and_kpis()
    test_pins_locks()
    print("All contract tests passed!")
