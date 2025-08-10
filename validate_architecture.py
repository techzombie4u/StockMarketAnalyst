
#!/usr/bin/env python3
"""
Architecture Validation Script
Tests that the new shared-core + product-plugins architecture works correctly
"""

import sys
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all new modules can be imported"""
    tests = []
    
    # Test common repository imports
    try:
        from common_repository.config.feature_flags import feature_flags
        from common_repository.utils.date_utils import get_ist_now
        from common_repository.utils.math_utils import safe_divide
        from common_repository.utils.error_handler import ErrorContext
        from common_repository.storage.json_store import json_store
        from common_repository.models.instrument import Instrument, InstrumentType
        from common_repository.models.prediction import Prediction, PredictionType
        tests.append("✅ Common repository imports successful")
    except Exception as e:
        tests.append(f"❌ Common repository imports failed: {e}")
    
    # Test product imports
    try:
        from products.equities.service import equity_service
        from products.equities.api import equity_bp
        from products.options.service import options_service
        from products.options.api import options_bp
        tests.append("✅ Product imports successful")
    except Exception as e:
        tests.append(f"❌ Product imports failed: {e}")
    
    return tests

def test_feature_flags():
    """Test feature flags functionality"""
    tests = []
    
    try:
        from common_repository.config.feature_flags import feature_flags
        
        # Test basic functionality
        flags = feature_flags.get_all_flags()
        assert isinstance(flags, dict), "Feature flags should return dict"
        
        # Test specific flag
        dynamic_confidence = feature_flags.is_enabled('enable_dynamic_confidence')
        assert isinstance(dynamic_confidence, bool), "Feature flag should return boolean"
        
        tests.append("✅ Feature flags working correctly")
    except Exception as e:
        tests.append(f"❌ Feature flags test failed: {e}")
    
    return tests

def test_storage():
    """Test storage functionality"""
    tests = []
    
    try:
        from common_repository.storage.json_store import json_store
        
        # Test save and load
        test_data = {"test": "data", "timestamp": "2025-01-08"}
        
        success = json_store.save('test_key', test_data)
        assert success, "Save should return True"
        
        loaded_data = json_store.load('test_key')
        assert loaded_data == test_data, "Loaded data should match saved data"
        
        # Test cleanup
        json_store.delete('test_key')
        
        tests.append("✅ Storage system working correctly")
    except Exception as e:
        tests.append(f"❌ Storage test failed: {e}")
    
    return tests

def test_models():
    """Test domain models"""
    tests = []
    
    try:
        from common_repository.models.instrument import Instrument, InstrumentType, MarketSegment
        from common_repository.models.prediction import Prediction, PredictionType, PredictionTimeframe
        from datetime import datetime
        
        # Test instrument model
        instrument = Instrument(
            symbol="TEST",
            name="Test Stock",
            instrument_type=InstrumentType.EQUITY,
            market_segment=MarketSegment.NSE
        )
        
        assert instrument.symbol == "TEST", "Instrument symbol should be set"
        assert instrument.is_equity, "Should be identified as equity"
        
        # Test prediction model
        prediction = Prediction(
            symbol="TEST",
            prediction_type=PredictionType.PRICE,
            timeframe=PredictionTimeframe.SHORT_TERM,
            predicted_value=100.0,
            confidence=75.0,
            model_name="test_model"
        )
        
        assert prediction.symbol == "TEST", "Prediction symbol should be set"
        assert prediction.confidence == 75.0, "Confidence should be set"
        
        tests.append("✅ Domain models working correctly")
    except Exception as e:
        tests.append(f"❌ Models test failed: {e}")
    
    return tests

def test_services():
    """Test product services"""
    tests = []
    
    try:
        from products.equities.service import equity_service
        from products.options.service import options_service
        
        # Test basic service properties
        assert equity_service.name == "equity_service", "Equity service should have correct name"
        assert options_service.name == "options_service", "Options service should have correct name"
        
        # Test that services have required methods
        assert hasattr(equity_service, 'analyze_equity'), "Equity service should have analyze_equity method"
        assert hasattr(options_service, 'analyze_short_strangle'), "Options service should have analyze_short_strangle method"
        
        tests.append("✅ Product services initialized correctly")
    except Exception as e:
        tests.append(f"❌ Services test failed: {e}")
    
    return tests

def test_app_integration():
    """Test Flask app integration"""
    tests = []
    
    try:
        from src.core.app import create_app
        
        app = create_app()
        assert app is not None, "App should be created"
        
        # Test that blueprints are registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'equity' in blueprint_names, "Equity blueprint should be registered"
        assert 'options' in blueprint_names, "Options blueprint should be registered"
        
        tests.append("✅ Flask app integration working correctly")
    except Exception as e:
        tests.append(f"❌ App integration test failed: {e}")
        tests.append(f"   Error details: {traceback.format_exc()}")
    
    return tests

def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("ARCHITECTURE VALIDATION - PHASE 1")
    print("="*60)
    
    all_tests = []
    
    # Run all test suites
    test_suites = [
        ("Import Tests", test_imports),
        ("Feature Flags Tests", test_feature_flags),
        ("Storage Tests", test_storage),
        ("Models Tests", test_models),
        ("Services Tests", test_services),
        ("App Integration Tests", test_app_integration)
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
        print("🎉 All tests passed! Architecture restructure successful.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
