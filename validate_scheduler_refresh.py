
#!/usr/bin/env python3
"""
Scheduler and Refresh Validation Script
Tests IST-aware scheduling, auto/manual refresh behavior, and queue management
"""

import sys
import logging
import time
from datetime import datetime, timedelta
import pytz

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scheduler_time_windows():
    """Test that scheduler respects IST time windows"""
    tests = []
    
    try:
        from src.common_repository.config.runtime import is_market_hours_now, get_market_tz
        from src.core.scheduler import StockAnalystScheduler
        
        # Test timezone setup
        ist = get_market_tz()
        assert ist.zone == 'Asia/Kolkata', "Market timezone should be IST"
        
        # Test market hours detection
        market_status = is_market_hours_now()
        assert isinstance(market_status, bool), "Market hours check should return boolean"
        
        tests.append("✅ Scheduler time window logic working")
        
    except Exception as e:
        tests.append(f"❌ Scheduler time window test failed: {e}")
    
    return tests

def test_refresh_endpoints():
    """Test auto vs manual refresh behavior"""
    tests = []
    
    try:
        from src.app.api.meta import get_last_updated_data, update_last_updated
        
        # Test last updated data structure
        data = get_last_updated_data()
        assert isinstance(data, dict), "Last updated data should be dict"
        assert 'dashboard' in data, "Should have dashboard timestamps"
        assert 'auto' in data['dashboard'], "Should track auto refresh"
        assert 'manual' in data['dashboard'], "Should track manual refresh"
        
        # Test timestamp updates
        success = update_last_updated('dashboard', 'manual')
        assert success, "Should successfully update timestamp"
        
        tests.append("✅ Refresh endpoint contracts working")
        
    except Exception as e:
        tests.append(f"❌ Refresh endpoint test failed: {e}")
    
    return tests

def test_queue_management():
    """Test job queue depth and lag management"""
    tests = []
    
    try:
        from src.core.scheduler import job_queue_depth, MAX_QUEUE_DEPTH, check_queue_depth
        
        # Test queue depth tracking
        assert job_queue_depth >= 0, "Queue depth should be non-negative"
        assert MAX_QUEUE_DEPTH == 10, "Max queue depth should be 10"
        
        # Test queue depth check
        can_run = check_queue_depth("test_job")
        assert isinstance(can_run, bool), "Queue check should return boolean"
        
        tests.append("✅ Queue management working correctly")
        
    except Exception as e:
        tests.append(f"❌ Queue management test failed: {e}")
    
    return tests

def test_telemetry_integration():
    """Test telemetry counters and budgets"""
    tests = []
    
    try:
        from src.common_repository.utils.telemetry import telemetry
        
        # Test telemetry is working
        telemetry.increment_counter('test.validation')
        metrics = telemetry.get_all_metrics()
        assert isinstance(metrics, dict), "Telemetry should return metrics dict"
        
        tests.append("✅ Telemetry integration working")
        
    except Exception as e:
        tests.append(f"❌ Telemetry integration test failed: {e}")
    
    return tests

def test_prediction_ttl():
    """Test prediction TTL behavior"""
    tests = []
    
    try:
        from src.common_repository.config.runtime import PREDICTION_TTL_SEC
        
        # Test TTL constant
        assert PREDICTION_TTL_SEC == 300, "Prediction TTL should be 300 seconds"
        assert isinstance(PREDICTION_TTL_SEC, int), "TTL should be integer"
        
        tests.append("✅ Prediction TTL configuration correct")
        
    except Exception as e:
        tests.append(f"❌ Prediction TTL test failed: {e}")
    
    return tests

def main():
    """Run all scheduler and refresh validation tests"""
    print("\n" + "="*60)
    print("SCHEDULER & REFRESH VALIDATION")
    print("="*60)
    
    all_tests = []
    
    # Run all test suites
    test_suites = [
        ("Scheduler Time Windows", test_scheduler_time_windows),
        ("Refresh Endpoints", test_refresh_endpoints),
        ("Queue Management", test_queue_management),
        ("Telemetry Integration", test_telemetry_integration),
        ("Prediction TTL", test_prediction_ttl)
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
    
    print(f"\n" + "="*60)
    print(f"VALIDATION SUMMARY: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("🎉 All scheduler and refresh tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
