import pytest
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000" # Assuming the backend runs on port 8000

def test_strangle_candidates_schema():
    """Test /api/options/strangle/candidates returns proper schema with Greeks and calculations"""
    r = requests.get(f"{BASE_URL}/api/options/strangle/candidates", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()

    # Check required fields
    for field in ["candidates", "metadata", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"

    # Check candidates structure
    assert isinstance(data["candidates"], list), "candidates must be array"
    assert len(data["candidates"]) > 0, "Should have at least one candidate"

    candidate = data["candidates"][0]

    # Check required fields
    required_fields = ["symbol", "underlying_price", "call_strike", "put_strike",
                      "call_premium", "put_premium", "total_premium", "max_profit",
                      "probability_profit", "dte", "ai_verdict_normalized", "roi_pct",
                      "margin", "breakeven_low", "breakeven_high", "greeks", "payoff"]
    for field in required_fields:
        assert field in candidate, f"Missing candidate field: {field}"

    # Validate Greeks structure
    greeks = candidate["greeks"]
    for greek in ["delta", "gamma", "theta", "vega"]:
        assert greek in greeks, f"Missing Greek: {greek}"
        assert isinstance(greeks[greek], (int, float)), f"Greek {greek} must be numeric"

    # Validate breakevens calculation
    assert candidate["breakeven_low"] < candidate["underlying_price"], "Breakeven low should be below spot"
    assert candidate["breakeven_high"] > candidate["underlying_price"], "Breakeven high should be above spot"

    # Validate ROI calculation
    expected_roi = (candidate["total_premium"] / candidate["margin"]) * 100
    assert abs(candidate["roi_pct"] - expected_roi) < 1.0, "ROI calculation incorrect"

    # Validate payoff arrays
    payoff = candidate["payoff"]
    assert "x" in payoff and "y" in payoff, "Payoff must have x and y arrays"
    assert len(payoff["x"]) == len(payoff["y"]), "Payoff x and y arrays must be same length"
    assert len(payoff["x"]) >= 3, "Payoff arrays should have at least 3 points"

def test_options_positions_schema():
    """Test /api/options/positions returns proper schema with complete data"""
    r = requests.get(f"{BASE_URL}/api/options/positions", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()

    # Check required fields
    for field in ["positions", "summary", "last_updated_utc"]:
        assert field in data, f"Missing field: {field}"

    # Check positions structure
    assert isinstance(data["positions"], list), "positions must be array"

    # Test with created position if any exist
    if data["positions"]:
        position = data["positions"][0]
        required_fields = ["position_id", "symbol", "strategy_type", "entry_date",
                          "status", "pnl", "current_value", "roi_pct", "margin",
                          "payoff", "greeks", "call_strike", "put_strike", "credit",
                          "breakeven_low", "breakeven_high"]
        for field in required_fields:
            assert field in position, f"Missing position field: {field}"

        # Validate Greeks in position
        greeks = position["greeks"]
        for greek in ["delta", "gamma", "theta", "vega"]:
            assert greek in greeks, f"Missing Greek in position: {greek}"

        # Validate payoff structure
        payoff = position["payoff"]
        assert "x" in payoff and "y" in payoff, "Position payoff must have x and y arrays"
        assert len(payoff["x"]) == len(payoff["y"]), "Position payoff arrays must be same length"

        # Validate ROI sign (should be positive for credit strategies)
        if position["strategy_type"] == "short_strangle":
            assert position["roi_pct"] >= 0, "ROI should be positive for credit strategies"

def test_greeks_calculation_accuracy():
    """Test that Greeks calculations are reasonable"""
    r = requests.get(f"{BASE_URL}/api/options/strangle/candidates", timeout=5)
    assert r.status_code == 200
    data = r.json()

    if data["candidates"]:
        candidate = data["candidates"][0]
        greeks = candidate["greeks"]

        # Delta should be close to zero for short strangle (delta neutral)
        assert abs(greeks["delta"]) < 0.2, f"Delta too high for strangle: {greeks['delta']}"

        # Gamma should be negative (short gamma)
        assert greeks["gamma"] <= 0, f"Gamma should be negative for short strangle: {greeks['gamma']}"

        # Theta should be positive (time decay benefits short position)
        assert greeks["theta"] >= 0, f"Theta should be positive for short strangle: {greeks['theta']}"

        # Vega should be negative (short vega)
        assert greeks["vega"] <= 0, f"Vega should be negative for short strangle: {greeks['vega']}"

def test_breakeven_calculation():
    """Test breakeven calculation accuracy"""
    r = requests.get(f"{BASE_URL}/api/options/strangle/candidates", timeout=5)
    assert r.status_code == 200
    data = r.json()

    if data["candidates"]:
        candidate = data["candidates"][0]

        # Breakevens should be: put_strike - credit, call_strike + credit
        expected_low = candidate["put_strike"] - candidate["total_premium"]
        expected_high = candidate["call_strike"] + candidate["total_premium"]

        assert abs(candidate["breakeven_low"] - expected_low) < 0.01, "Breakeven low calculation incorrect"
        assert abs(candidate["breakeven_high"] - expected_high) < 0.01, "Breakeven high calculation incorrect"

def test_position_update_flow():
    """Test position creation and update flow"""
    # Create a position
    plan_data = {
        "symbol": "TCS",
        "call_strike": 4400,
        "put_strike": 4100,
        "quantity": 1,
        "days_to_expiry": 30
    }

    r = requests.post(f"{BASE_URL}/api/options/strangle/plan", json=plan_data, timeout=5)
    assert r.status_code == 200
    plan_result = r.json()
    assert "plan_id" in plan_result, "Missing plan_id in response"

    # Update position with new spot price
    position_id = plan_result["plan_id"]
    update_data = {"current_spot": 4300}

    r = requests.post(f"{BASE_URL}/api/options/positions/{position_id}/update", 
                     json=update_data, timeout=5)
    assert r.status_code == 200
    update_result = r.json()
    assert update_result.get("success") is True, "Position update failed"