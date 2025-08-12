
import requests
import json
import time
import pytest
from datetime import datetime

BASE = "http://localhost:5000"

def test_fusion_dashboard_structure():
    """Test fusion dashboard returns complete structure"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r.raise_for_status()
    data = r.json()
    
    # Test top-level keys
    required_keys = ["timeframes", "signals", "pinned_rollup", "alerts", "insights", "last_updated_utc"]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    # Test timeframes structure
    timeframes = data["timeframes"]
    assert isinstance(timeframes, dict), "Timeframes should be a dict"
    
    expected_timeframes = ["All", "3D", "5D", "10D", "15D", "30D"]
    for tf in expected_timeframes:
        assert tf in timeframes, f"Missing timeframe: {tf}"
        
        tf_data = timeframes[tf]
        assert "timeframe" in tf_data
        assert "prediction_kpis" in tf_data
        assert "financial_kpis" in tf_data  
        assert "risk_kpis" in tf_data
        
        # Test prediction KPIs
        pred_kpis = tf_data["prediction_kpis"]
        assert "accuracy" in pred_kpis
        assert "hit_ratio" in pred_kpis
        assert "mape" in pred_kpis
        assert "precision" in pred_kpis
        assert "recall" in pred_kpis
        
        # Test financial KPIs
        fin_kpis = tf_data["financial_kpis"]
        assert "sharpe" in fin_kpis
        assert "sortino" in fin_kpis
        assert "pnl_growth" in fin_kpis
        
        # Test risk KPIs
        risk_kpis = tf_data["risk_kpis"]
        assert "mdd" in risk_kpis
        assert "var" in risk_kpis
        assert "vol_regime" in risk_kpis

def test_verdict_normalization():
    """Test that all verdicts are properly normalized"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r.raise_for_status()
    data = r.json()
    
    valid_verdicts = {'STRONG_BUY', 'BUY', 'HOLD', 'CAUTIOUS', 'AVOID'}
    
    signals = data.get("signals", [])
    assert len(signals) > 0, "Should have at least one signal"
    
    for signal in signals:
        assert "ai_verdict_normalized" in signal, "Signal missing ai_verdict_normalized"
        verdict = signal["ai_verdict_normalized"]
        assert verdict in valid_verdicts, f"Invalid normalized verdict: {verdict}"

def test_kpi_values_are_numeric():
    """Test that all KPI values are numeric and non-empty"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r.raise_for_status()
    data = r.json()
    
    timeframes = data["timeframes"]
    
    for tf_key, tf_data in timeframes.items():
        # Check prediction KPIs
        for kpi_name, kpi_value in tf_data["prediction_kpis"].items():
            assert isinstance(kpi_value, (int, float)), f"{tf_key}.prediction_kpis.{kpi_name} should be numeric"
            assert kpi_value is not None, f"{tf_key}.prediction_kpis.{kpi_name} should not be None"
        
        # Check financial KPIs
        for kpi_name, kpi_value in tf_data["financial_kpis"].items():
            assert isinstance(kpi_value, (int, float)), f"{tf_key}.financial_kpis.{kpi_name} should be numeric"
            assert kpi_value is not None, f"{tf_key}.financial_kpis.{kpi_name} should not be None"
        
        # Check risk KPIs (vol_regime can be string)
        risk_kpis = tf_data["risk_kpis"]
        for kpi_name, kpi_value in risk_kpis.items():
            if kpi_name == "vol_regime":
                assert isinstance(kpi_value, str), f"{tf_key}.risk_kpis.vol_regime should be string"
                assert kpi_value in ["LOW", "MEDIUM", "HIGH"], f"Invalid vol_regime: {kpi_value}"
            else:
                assert isinstance(kpi_value, (int, float)), f"{tf_key}.risk_kpis.{kpi_name} should be numeric"
                assert kpi_value is not None, f"{tf_key}.risk_kpis.{kpi_name} should not be None"

def test_force_refresh_changes_timestamp():
    """Test that forceRefresh=true changes the timestamp"""
    # Get initial timestamp
    r1 = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r1.raise_for_status()
    data1 = r1.json()
    timestamp1 = data1.get("last_updated_utc")
    
    # Wait a moment
    time.sleep(1.1)
    
    # Force refresh
    r2 = requests.get(f"{BASE}/api/fusion/dashboard?forceRefresh=true", timeout=10)
    r2.raise_for_status()
    data2 = r2.json()
    timestamp2 = data2.get("last_updated_utc")
    
    assert timestamp1 != timestamp2, "Force refresh should update timestamp"
    
    # Parse timestamps to ensure timestamp2 is newer
    dt1 = datetime.fromisoformat(timestamp1.replace('Z', '+00:00'))
    dt2 = datetime.fromisoformat(timestamp2.replace('Z', '+00:00'))
    assert dt2 > dt1, "Force refresh timestamp should be newer"

def test_signals_structure():
    """Test signals have required structure"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r.raise_for_status()
    data = r.json()
    
    signals = data.get("signals", [])
    assert len(signals) > 0, "Should have signals"
    
    for signal in signals:
        required_signal_keys = ["product", "symbol", "ai_verdict_normalized", "confidence", "rationale"]
        for key in required_signal_keys:
            assert key in signal, f"Signal missing required key: {key}"
        
        # Test confidence is numeric and in valid range
        confidence = signal["confidence"]
        assert isinstance(confidence, (int, float)), "Confidence should be numeric"
        assert 0 <= confidence <= 1, f"Confidence should be 0-1, got {confidence}"

def test_pinned_rollup_structure():
    """Test pinned rollup has correct structure"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r.raise_for_status()
    data = r.json()
    
    pinned_rollup = data.get("pinned_rollup", {})
    required_rollup_keys = ["total", "met", "not_met", "in_progress"]
    
    for key in required_rollup_keys:
        assert key in pinned_rollup, f"Pinned rollup missing key: {key}"
        assert isinstance(pinned_rollup[key], int), f"Pinned rollup {key} should be integer"

def test_fusion_api_legacy_compatibility():
    """Test that legacy 'updated' field is still present"""
    r = requests.get(f"{BASE}/api/fusion/dashboard", timeout=10)
    r.raise_for_status()
    data = r.json()
    
    # Legacy compatibility
    assert "updated" in data, "Should maintain 'updated' field for backward compatibility"
    assert "last_updated_utc" in data, "Should have new 'last_updated_utc' field"

if __name__ == "__main__":
    # Run tests individually for debugging
    print("Testing fusion dashboard structure...")
    test_fusion_dashboard_structure()
    print("✅ Structure test passed")
    
    print("Testing verdict normalization...")
    test_verdict_normalization()
    print("✅ Verdict normalization test passed")
    
    print("Testing KPI values...")
    test_kpi_values_are_numeric()
    print("✅ KPI values test passed")
    
    print("Testing force refresh...")
    test_force_refresh_changes_timestamp()
    print("✅ Force refresh test passed")
    
    print("Testing signals structure...")
    test_signals_structure()
    print("✅ Signals structure test passed")
    
    print("Testing pinned rollup...")
    test_pinned_rollup_structure()
    print("✅ Pinned rollup test passed")
    
    print("Testing legacy compatibility...")
    test_fusion_api_legacy_compatibility()
    print("✅ Legacy compatibility test passed")
    
    print("All fusion contract tests passed!")
