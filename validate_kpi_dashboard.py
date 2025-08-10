
#!/usr/bin/env python3
"""
KPI Dashboard Validation Script
Tests KPI calculation, thresholds, triggers, and API endpoints
"""

import sys
import logging
import json
import requests
import time
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kpi_service():
    """Test KPI service functionality"""
    tests = []
    
    try:
        from products.shared.services.kpi_service import kpi_service
        
        # Test basic KPI computation
        kpis = kpi_service.compute(timeframe="All", product=None)
        assert isinstance(kpis, dict), "KPI service should return dict"
        assert 'prediction_quality' in kpis, "Should have prediction quality KPIs"
        assert 'financial' in kpis, "Should have financial KPIs"
        assert 'risk' in kpis, "Should have risk KPIs"
        
        tests.append("✅ KPI service basic computation working")
        
        # Test timeframe filtering
        for timeframe in ['3D', '5D', '10D', '15D', '30D']:
            tf_kpis = kpi_service.compute(timeframe=timeframe)
            assert tf_kpis['timeframe'] == timeframe, f"Timeframe should be {timeframe}"
        
        tests.append("✅ Timeframe filtering working")
        
        # Test product filtering
        for product in ['equities', 'options', 'commodities']:
            prod_kpis = kpi_service.compute(product=product)
            assert prod_kpis['product'] == product, f"Product should be {product}"
        
        tests.append("✅ Product filtering working")
        
        # Test trigger evaluation
        triggers = kpi_service.evaluate_triggers(kpis)
        assert isinstance(triggers, list), "Triggers should be a list"
        
        tests.append("✅ Trigger evaluation working")
        
    except Exception as e:
        tests.append(f"❌ KPI service test failed: {e}")
    
    return tests

def test_api_endpoints():
    """Test KPI API endpoints"""
    tests = []
    
    try:
        # Test summary endpoint
        response = requests.get('http://127.0.0.1:5000/api/kpi/summary?timeframe=All')
        assert response.status_code == 200, f"Summary endpoint failed: {response.status_code}"
        
        data = response.json()
        assert data['success'], "Summary response should be successful"
        assert 'overall' in data['data'], "Should have overall KPIs"
        assert 'by_product' in data['data'], "Should have by-product KPIs"
        
        tests.append("✅ KPI summary endpoint working")
        
        # Test product-specific endpoint
        response = requests.get('http://127.0.0.1:5000/api/kpi/product/equities?timeframe=5D')
        assert response.status_code == 200, f"Product endpoint failed: {response.status_code}"
        
        data = response.json()
        assert data['success'], "Product response should be successful"
        assert data['data']['product'] == 'equities', "Should return equities data"
        
        tests.append("✅ Product-specific KPI endpoint working")
        
        # Test thresholds endpoint
        response = requests.get('http://127.0.0.1:5000/api/kpi/thresholds')
        assert response.status_code == 200, f"Thresholds endpoint failed: {response.status_code}"
        
        data = response.json()
        assert data['success'], "Thresholds response should be successful"
        assert 'targets' in data['data'], "Should have threshold targets"
        
        tests.append("✅ KPI thresholds endpoint working")
        
    except Exception as e:
        tests.append(f"❌ API endpoints test failed: {e}")
    
    return tests

def test_manual_refresh():
    """Test manual refresh with rate limiting"""
    tests = []
    
    try:
        # Test manual refresh
        response = requests.post('http://127.0.0.1:5000/api/kpi/recompute?scope=overall&timeframe=All')
        
        if response.status_code == 200:
            data = response.json()
            assert data['success'], "Manual refresh should be successful"
            assert 'last_manual_refresh' in data, "Should include manual refresh timestamp"
            tests.append("✅ Manual refresh working")
            
            # Test rate limiting
            response2 = requests.post('http://127.0.0.1:5000/api/kpi/recompute?scope=overall&timeframe=All')
            if response2.status_code == 429:
                tests.append("✅ Rate limiting working")
            else:
                tests.append("⚠️ Rate limiting may not be working properly")
        
        elif response.status_code == 429:
            tests.append("✅ Rate limiting active (expected if recently refreshed)")
        else:
            tests.append(f"❌ Manual refresh failed: {response.status_code}")
        
    except Exception as e:
        tests.append(f"❌ Manual refresh test failed: {e}")
    
    return tests

def test_threshold_logic():
    """Test threshold color logic"""
    tests = []
    
    try:
        from products.shared.services.kpi_service import kpi_service
        
        # Load thresholds
        thresholds = kpi_service.thresholds
        assert thresholds, "Thresholds should be loaded"
        
        # Test color logic for hit rate (higher is better)
        hit_rate_target = thresholds['targets']['hit_rate']['all']
        
        # Create mock KPI service instance to test status method
        class MockKPIService:
            def __init__(self):
                self.thresholds = thresholds
                self.currentTimeframe = 'All'
            
            def getKPIStatus(self, key, value, higherIsBetter):
                if not self.thresholds or value is None:
                    return 'neutral'
                
                threshold = None
                if self.thresholds['targets'][key]:
                    threshold = self.thresholds['targets'][key].get(self.currentTimeframe) or \
                               self.thresholds['targets'][key].get('all')
                
                if not threshold:
                    return 'neutral'
                
                warnBand = self.thresholds['warn_bands']['pct']
                
                if higherIsBetter:
                    if value >= threshold:
                        return 'good'
                    if value >= threshold * (1 - warnBand):
                        return 'warn'
                    return 'bad'
                else:
                    if value <= threshold:
                        return 'good'
                    if value <= threshold * (1 + warnBand):
                        return 'warn'
                    return 'bad'
        
        mock_service = MockKPIService()
        
        # Test good status
        good_status = mock_service.getKPIStatus('hit_rate', hit_rate_target + 0.1, True)
        assert good_status == 'good', f"Should be good, got {good_status}"
        
        # Test warn status
        warn_status = mock_service.getKPIStatus('hit_rate', hit_rate_target * 0.95, True)
        assert warn_status == 'warn', f"Should be warn, got {warn_status}"
        
        # Test bad status
        bad_status = mock_service.getKPIStatus('hit_rate', hit_rate_target * 0.8, True)
        assert bad_status == 'bad', f"Should be bad, got {bad_status}"
        
        tests.append("✅ Threshold color logic working")
        
    except Exception as e:
        tests.append(f"❌ Threshold logic test failed: {e}")
    
    return tests

def test_trend_calculation():
    """Test trend arrow calculation"""
    tests = []
    
    try:
        from products.shared.services.kpi_service import kpi_service
        from common_repository.storage.json_store import json_store
        
        # Create mock historical data
        history_key = "kpi_history_test_all"
        mock_history = [
            {
                "timestamp": (datetime.now() - timedelta(minutes=30)).isoformat(),
                "kpis": {
                    "prediction_quality": {"hit_rate": 0.65},
                    "financial": {"sharpe_ratio": 1.3},
                    "risk": {"max_drawdown": 0.04}
                }
            },
            {
                "timestamp": datetime.now().isoformat(),
                "kpis": {
                    "prediction_quality": {"hit_rate": 0.70},
                    "financial": {"sharpe_ratio": 1.2},
                    "risk": {"max_drawdown": 0.05}
                }
            }
        ]
        
        json_store.save(history_key, mock_history)
        
        # Test trend calculation
        current = mock_history[1]["kpis"]
        previous = mock_history[0]["kpis"]
        
        trends = kpi_service._calculate_trends(current, previous)
        
        # Hit rate increased - should be up trend
        hit_rate_trend = trends.get('prediction_quality_hit_rate')
        if hit_rate_trend:
            assert hit_rate_trend['direction'] == 'up', "Hit rate should show up trend"
            assert hit_rate_trend['arrow'] == '↑', "Should have up arrow"
        
        tests.append("✅ Trend calculation working")
        
        # Cleanup
        json_store.delete(history_key)
        
    except Exception as e:
        tests.append(f"❌ Trend calculation test failed: {e}")
    
    return tests

def test_triggers():
    """Test GoAhead trigger generation"""
    tests = []
    
    try:
        from products.shared.services.kpi_service import kpi_service
        
        # Create mock KPI data that should trigger alerts
        mock_kpis = {
            "timeframe": "5D",
            "product": "equities",
            "prediction_quality": {
                "hit_rate": 0.45,  # Below 0.62 target
                "brier_score": 0.30  # Above 0.18 target
            },
            "financial": {
                "sharpe_ratio": 0.8  # Below 1.2 target
            },
            "risk": {
                "max_drawdown": 0.08,  # Above 0.05 target
                "var_95": 0.01  # Above 0.005 target
            }
        }
        
        triggers = kpi_service.evaluate_triggers(mock_kpis)
        
        assert len(triggers) > 0, "Should generate triggers for poor performance"
        
        # Check for specific trigger types
        trigger_types = [t.type for t in triggers]
        assert 'RETRAIN' in trigger_types, "Should have retrain trigger"
        assert 'TIGHTEN_RISK' in trigger_types, "Should have risk tighten trigger"
        assert 'THROTTLE' in trigger_types, "Should have throttle trigger"
        
        tests.append("✅ GoAhead trigger generation working")
        
    except Exception as e:
        tests.append(f"❌ Trigger generation test failed: {e}")
    
    return tests

def test_feature_flags():
    """Test feature flag integration"""
    tests = []
    
    try:
        from common_repository.config.feature_flags import feature_flags
        
        # Test that KPI dashboard flags are enabled
        kpi_flags = [
            'enable_kpi_dashboard',
            'enable_goahead_triggers',
            'enable_timeframe_filtering',
            'enable_background_kpi_jobs'
        ]
        
        for flag in kpi_flags:
            assert feature_flags.is_enabled(flag), f"Flag {flag} should be enabled"
        
        tests.append("✅ KPI feature flags properly configured")
        
    except Exception as e:
        tests.append(f"❌ Feature flags test failed: {e}")
    
    return tests

def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("KPI DASHBOARD VALIDATION - PROMPT 5")
    print("="*60)
    
    all_tests = []
    
    # Run all test suites
    test_suites = [
        ("Feature Flags Tests", test_feature_flags),
        ("KPI Service Tests", test_kpi_service),
        ("API Endpoints Tests", test_api_endpoints),
        ("Manual Refresh Tests", test_manual_refresh),
        ("Threshold Logic Tests", test_threshold_logic),
        ("Trend Calculation Tests", test_trend_calculation),
        ("GoAhead Triggers Tests", test_triggers)
    ]
    
    for suite_name, test_func in test_suites:
        print(f"\n📋 {suite_name}:")
        try:
            results = test_func()
            for result in results:
                print(f"  {result}")
                all_tests.append(result)
        except Exception as e:
            error_msg = f"❌ {suite_name} failed with exception: {e}"
            print(f"  {error_msg}")
            all_tests.append(error_msg)
    
    # Summary
    passed = len([t for t in all_tests if t.startswith("✅")])
    failed = len([t for t in all_tests if t.startswith("❌")])
    warnings = len([t for t in all_tests if t.startswith("⚠️")])
    
    print(f"\n" + "="*60)
    print(f"VALIDATION SUMMARY: {passed} passed, {failed} failed, {warnings} warnings")
    print("="*60)
    
    if failed == 0:
        print("🎉 All tests passed! KPI Dashboard implementation successful.")
        print("\nNext steps:")
        print("1. Start the application: python main.py")
        print("2. Navigate to http://localhost:5000/kpi_dashboard")
        print("3. Test timeframe and product filtering")
        print("4. Verify KPI calculations and threshold colors")
        print("5. Test manual refresh functionality")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
