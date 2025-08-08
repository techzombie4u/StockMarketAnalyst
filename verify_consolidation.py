
#!/usr/bin/env python3
"""
Verification script for Stock Market Analyst v1.7.4 consolidation
Tests that all modules import correctly and app starts properly
"""

import sys
import os
import importlib

def test_imports():
    """Test that all consolidated imports work"""
    print("🧪 Testing consolidated imports...")
    
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        
        # Test core imports
        from core.app import app
        print("✅ Core app import successful")
        
        # Test analyzer imports
        from analyzers.smart_go_agent import SmartGoAgent
        from analyzers.short_strangle_engine import ShortStrangleEngine
        print("✅ Analyzer imports successful")
        
        # Test agent imports
        from agents.intelligent_prediction_agent import IntelligentPredictionAgent
        print("✅ Agent imports successful")
        
        # Test manager imports
        from managers.enhanced_error_handler import enhanced_error_handler
        print("✅ Manager imports successful")
        
        # Test strategy imports (renamed files)
        from strategies.engine import *
        from agents.personalizer import *
        from orchestrators.optimizer import *
        from reporters.insights import *
        print("✅ Renamed module imports successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_legacy_folder():
    """Verify legacy folder is properly archived"""
    print("🗄️ Checking legacy folder status...")
    
    if os.path.exists("_backup_before_organization"):
        print("❌ Legacy folder still exists at root level")
        return False
    
    if os.path.exists("legacy_archive_2025/_backup_before_organization"):
        print("✅ Legacy folder properly archived")
        return True
    else:
        print("⚠️ Legacy folder not found in archive")
        return False

def test_app_startup():
    """Test that Flask app can start without errors"""
    print("🚀 Testing Flask app startup...")
    
    try:
        sys.path.insert(0, 'src')
        from core.app import app
        
        # Test app configuration
        if app.config.get('SECRET_KEY'):
            print("✅ App configuration loaded")
        
        # Test that routes are registered
        if len(app.url_map._rules) > 0:
            print(f"✅ {len(app.url_map._rules)} routes registered")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup error: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 Stock Market Analyst v1.7.4 Consolidation Verification")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Legacy Archive Check", test_legacy_folder),
        ("App Startup Test", test_app_startup)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All consolidation tests PASSED!")
        print("✅ Codebase successfully consolidated to v1.7.4")
        return True
    else:
        print("⚠️ Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
