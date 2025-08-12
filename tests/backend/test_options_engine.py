
"""
Tests for options calculation engine
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.options.engine import OptionsEngine, Greeks
import math

def test_black_scholes_call_put_parity():
    """Test Black-Scholes call-put parity relationship"""
    engine = OptionsEngine()
    
    S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.2
    
    call_price = engine.black_scholes_price(S, K, T, r, sigma, 'call')
    put_price = engine.black_scholes_price(S, K, T, r, sigma, 'put')
    
    # Call-Put parity: C - P = S - K*e^(-rT)
    parity_diff = call_price - put_price
    expected_diff = S - K * math.exp(-r * T)
    
    assert abs(parity_diff - expected_diff) < 0.01, f"Call-put parity violated: {parity_diff} vs {expected_diff}"

def test_greeks_calculation():
    """Test Greeks calculation for reasonable values"""
    engine = OptionsEngine()
    
    S, K, T, r, sigma = 100, 100, 0.25, 0.05, 0.2
    
    call_greeks = engine.calculate_greeks(S, K, T, r, sigma, 'call')
    put_greeks = engine.calculate_greeks(S, K, T, r, sigma, 'put')
    
    # Delta tests
    assert 0 < call_greeks.delta < 1, f"Call delta out of range: {call_greeks.delta}"
    assert -1 < put_greeks.delta < 0, f"Put delta out of range: {put_greeks.delta}"
    
    # Gamma should be positive and equal for calls and puts
    assert call_greeks.gamma > 0, f"Call gamma should be positive: {call_greeks.gamma}"
    assert abs(call_greeks.gamma - put_greeks.gamma) < 0.0001, "Call and put gamma should be equal"
    
    # Theta should be negative (time decay)
    assert call_greeks.theta < 0, f"Call theta should be negative: {call_greeks.theta}"
    assert put_greeks.theta < 0, f"Put theta should be negative: {put_greeks.theta}"

def test_strangle_metrics_calculation():
    """Test complete strangle metrics calculation"""
    engine = OptionsEngine()
    
    metrics = engine.calculate_strangle_metrics(
        symbol="TEST",
        spot=100,
        call_strike=105,
        put_strike=95,
        days_to_expiry=30,
        implied_vol=0.25
    )
    
    # Check all required fields
    required_fields = ['symbol', 'spot_price', 'call_strike', 'put_strike', 
                      'call_price', 'put_price', 'credit', 'breakeven_low', 
                      'breakeven_high', 'margin', 'roi_pct', 'probability_profit',
                      'greeks', 'payoff']
    
    for field in required_fields:
        assert field in metrics, f"Missing field: {field}"
    
    # Validate calculations
    assert metrics['credit'] == metrics['call_price'] + metrics['put_price'], "Credit calculation incorrect"
    assert metrics['breakeven_low'] == metrics['put_strike'] - metrics['credit'], "Breakeven low incorrect"
    assert metrics['breakeven_high'] == metrics['call_strike'] + metrics['credit'], "Breakeven high incorrect"
    assert metrics['roi_pct'] == (metrics['credit'] / metrics['margin']) * 100, "ROI calculation incorrect"

def test_payoff_diagram_generation():
    """Test payoff diagram data generation"""
    engine = OptionsEngine()
    
    payoff = engine.generate_payoff_diagram(spot=100, call_strike=105, put_strike=95, credit=8)
    
    assert 'x' in payoff and 'y' in payoff, "Payoff must have x and y arrays"
    assert len(payoff['x']) == len(payoff['y']), "Payoff arrays must be same length"
    assert len(payoff['x']) >= 10, "Payoff should have multiple points for smooth curve"
    
    # Check that maximum profit is at the credit level (between strikes)
    max_profit = max(payoff['y'])
    assert abs(max_profit - 8) < 0.1, f"Max profit should be near credit: {max_profit}"

def test_position_persistence():
    """Test position saving and loading"""
    engine = OptionsEngine()
    
    # Clear existing positions for clean test
    if os.path.exists(engine.positions_file):
        os.remove(engine.positions_file)
    
    position_data = {
        'symbol': 'TEST',
        'strategy_type': 'short_strangle',
        'credit': 50,
        'margin': 1000,
        'roi_pct': 5.0,
        'greeks': {'delta': 0.01, 'gamma': -0.02, 'theta': 0.5, 'vega': -0.3},
        'payoff': {'x': [90, 100, 110], 'y': [0, 50, 0]},
        'call_strike': 105,
        'put_strike': 95
    }
    
    # Save position
    position_id = engine.save_position(position_data)
    assert position_id, "Position ID should be returned"
    
    # Load and verify
    positions = engine.load_positions()
    assert len(positions) == 1, "Should have one position"
    
    saved_position = positions[0]
    assert saved_position['symbol'] == 'TEST', "Symbol not saved correctly"
    assert saved_position['strategy_type'] == 'short_strangle', "Strategy type not saved"
    assert saved_position['status'] == 'open', "Default status should be open"

if __name__ == "__main__":
    test_black_scholes_call_put_parity()
    test_greeks_calculation()
    test_strangle_metrics_calculation()
    test_payoff_diagram_generation()
    test_position_persistence()
    print("✅ All options engine tests passed!")
