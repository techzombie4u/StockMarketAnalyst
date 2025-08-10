
#!/usr/bin/env python3
"""
KPI Calculator Validation Script
Tests multi-timeframe KPI calculation, threshold monitoring, and atomic writes
"""

import sys
import logging
import os
import json
import tempfile
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_kpi_structure():
    """Test KPI metrics data structure"""
    tests = []
    
    try:
        from src.core.kpi.calculator import KPIMetrics, KPICalculator
        
        # Test KPIMetrics dataclass
        metrics = KPIMetrics(
            timeframe="5D",
            total_predictions=100,
            closed_predictions=90,
            insufficient_data=False
        )
        
        assert metrics.timeframe == "5D", "Timeframe should be set correctly"
        assert metrics.total_predictions == 100, "Total predictions should be set"
        assert not metrics.insufficient_data, "Insufficient data flag should work"
        
        # Test KPICalculator instantiation
        calculator = KPICalculator()
        assert hasattr(calculator, 'kpi_file'), "Calculator should have kpi_file attribute"
        assert hasattr(calculator, 'backup_dir'), "Calculator should have backup_dir attribute"
        
        tests.append("✅ KPI data structures working correctly")
        
    except Exception as e:
        tests.append(f"❌ KPI structure test failed: {e}")
    
    return tests

def test_min_sample_logic():
    """Test minimum sample requirements"""
    tests = []
    
    try:
        from src.common_repository.config.runtime import KPI_MIN_SAMPLES
        from src.core.kpi.calculator import KPICalculator
        
        # Test min samples configuration
        assert isinstance(KPI_MIN_SAMPLES, dict), "KPI_MIN_SAMPLES should be dict"
        assert "3D" in KPI_MIN_SAMPLES, "Should have 3D minimum"
        assert "5D" in KPI_MIN_SAMPLES, "Should have 5D minimum"
        assert "30D" in KPI_MIN_SAMPLES, "Should have 30D minimum"
        
        # Test with insufficient data
        calculator = KPICalculator()
        
        # Create mock predictions with insufficient samples
        mock_predictions = [
            {'timeframe': '5D', 'resolved': True, 'symbol': 'TEST1'},
            {'timeframe': '5D', 'resolved': True, 'symbol': 'TEST2'}
        ]
        
        metrics = calculator.calculate_timeframe_metrics('5D', mock_predictions)
        assert metrics.insufficient_data, "Should mark as insufficient data when below minimum"
        
        tests.append("✅ Minimum sample logic working correctly")
        
    except Exception as e:
        tests.append(f"❌ Min sample logic test failed: {e}")
    
    return tests

def test_atomic_writes():
    """Test atomic file writes and version retention"""
    tests = []
    
    try:
        from src.core.kpi.calculator import KPICalculator
        
        calculator = KPICalculator()
        
        # Test atomic write with temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, 'test_kpi.json')
            calculator.kpi_file = test_file
            
            test_data = {
                'timestamp': datetime.now().isoformat(),
                'test': True,
                'metrics': {'overall': {'status': 'green'}}
            }
            
            # Test atomic write
            calculator.write_kpi_metrics_atomic(test_data)
            
            # Verify file exists and contains correct data
            assert os.path.exists(test_file), "File should be created atomically"
            
            with open(test_file, 'r') as f:
                loaded_data = json.load(f)
                assert loaded_data['test'] == True, "Data should be written correctly"
                assert 'timestamp' in loaded_data, "Should contain timestamp"
        
        tests.append("✅ Atomic write functionality working")
        
    except Exception as e:
        tests.append(f"❌ Atomic write test failed: {e}")
    
    return tests

def test_status_coloring():
    """Test threshold-based status coloring"""
    tests = []
    
    try:
        from src.core.kpi.calculator import KPICalculator, KPIMetrics
        
        calculator = KPICalculator()
        
        # Test green status (good metrics)
        good_metrics = KPIMetrics(
            timeframe="test",
            total_predictions=100,
            closed_predictions=90,
            insufficient_data=False,
            brier_score=0.10,  # Good (low)
            directional_hit_rate=75.0,  # Good (high)
            sharpe_ratio=1.5,  # Good (high)
            max_drawdown=5.0  # Good (low)
        )
        
        status = calculator.determine_status(good_metrics)
        assert status == "green", f"Good metrics should be green, got {status}"
        
        # Test red status (poor metrics)
        poor_metrics = KPIMetrics(
            timeframe="test",
            total_predictions=100,
            closed_predictions=90,
            insufficient_data=False,
            brier_score=0.40,  # Poor (high)
            directional_hit_rate=40.0,  # Poor (low)
            sharpe_ratio=-0.5,  # Poor (negative)
            max_drawdown=30.0  # Poor (high)
        )
        
        status = calculator.determine_status(poor_metrics)
        assert status == "red", f"Poor metrics should be red, got {status}"
        
        tests.append("✅ Status coloring logic working correctly")
        
    except Exception as e:
        tests.append(f"❌ Status coloring test failed: {e}")
    
    return tests

def test_trigger_events():
    """Test KPI trigger event creation"""
    tests = []
    
    try:
        from src.core.kpi.watcher import KPIWatcher
        
        watcher = KPIWatcher()
        
        # Test trigger event creation
        test_details = {
            'metric': 'brier_score',
            'timeframe': '5D',
            'current_value': 0.30,
            'baseline_value': 0.20,
            'increase': 0.10
        }
        
        event = watcher.create_trigger_event('kpi_breach', test_details)
        
        assert isinstance(event, dict), "Event should be dictionary"
        assert 'id' in event, "Event should have ID"
        assert 'timestamp' in event, "Event should have timestamp"
        assert event['type'] == 'kpi_breach', "Event type should be correct"
        assert event['details'] == test_details, "Details should be preserved"
        
        tests.append("✅ Trigger event creation working")
        
    except Exception as e:
        tests.append(f"❌ Trigger event test failed: {e}")
    
    return tests

def test_version_rotation():
    """Test KPI file version rotation"""
    tests = []
    
    try:
        from src.core.kpi.calculator import KPICalculator
        
        with tempfile.TemporaryDirectory() as temp_dir:
            calculator = KPICalculator()
            calculator.backup_dir = temp_dir
            calculator.max_versions = 3
            
            # Create test files beyond max versions
            for i in range(5):
                test_file = os.path.join(temp_dir, f'kpi_metrics_202501{i:02d}_120000.json')
                with open(test_file, 'w') as f:
                    json.dump({'version': i}, f)
            
            # Run backup which should clean old versions
            calculator.backup_previous_version()
            
            # Check that only max_versions files remain
            backup_files = [f for f in os.listdir(temp_dir) if f.startswith('kpi_metrics_')]
            assert len(backup_files) <= calculator.max_versions, f"Should keep only {calculator.max_versions} versions"
        
        tests.append("✅ Version rotation working correctly")
        
    except Exception as e:
        tests.append(f"❌ Version rotation test failed: {e}")
    
    return tests

def main():
    """Run all KPI calculator validation tests"""
    print("\n" + "="*60)
    print("KPI CALCULATOR VALIDATION")
    print("="*60)
    
    all_tests = []
    
    # Run all test suites
    test_suites = [
        ("KPI Structure", test_kpi_structure),
        ("Min Sample Logic", test_min_sample_logic),
        ("Atomic Writes", test_atomic_writes),
        ("Status Coloring", test_status_coloring),
        ("Trigger Events", test_trigger_events),
        ("Version Rotation", test_version_rotation)
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
        print("🎉 All KPI calculator tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
