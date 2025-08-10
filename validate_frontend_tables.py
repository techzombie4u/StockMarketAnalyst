
#!/usr/bin/env python3
"""
Frontend Tables Validation Script
Tests virtual tables, AI verdict column, and pinned stats functionality
"""

import sys
import logging
import requests
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

def test_ai_verdict_integration():
    """Test AI verdict column integration"""
    tests = []
    
    try:
        # Test equity AI verdict
        response = requests.get(f"{BASE_URL}/api/equity/analyze/RELIANCE", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'ai_verdict' in data and 'ai_confidence' in data:
                tests.append("✅ Equity AI verdict integration working")
            else:
                tests.append("❌ Equity AI verdict fields missing")
        else:
            tests.append(f"❌ Equity API error: {response.status_code}")
    
    except Exception as e:
        tests.append(f"❌ Equity AI verdict test failed: {e}")
    
    try:
        # Test options AI verdict
        response = requests.get(f"{BASE_URL}/api/options/short-strangle/RELIANCE", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'ai_verdict' in data and 'ai_confidence' in data:
                tests.append("✅ Options AI verdict integration working")
            else:
                tests.append("❌ Options AI verdict fields missing")
        else:
            tests.append(f"❌ Options API error: {response.status_code}")
    
    except Exception as e:
        tests.append(f"❌ Options AI verdict test failed: {e}")
    
    return tests

def test_pinned_stats_api():
    """Test pinned stats API endpoints"""
    tests = []
    
    try:
        # Test equity pinned stats
        response = requests.get(f"{BASE_URL}/api/equity/pinned_stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                stats = data['data']
                required_fields = ['count', 'avg_roi', 'avg_confidence', 'total_pl']
                if all(field in stats for field in required_fields):
                    tests.append("✅ Equity pinned stats API working")
                else:
                    tests.append("❌ Equity pinned stats missing required fields")
            else:
                tests.append("❌ Equity pinned stats invalid response")
        else:
            tests.append(f"❌ Equity pinned stats API error: {response.status_code}")
    
    except Exception as e:
        tests.append(f"❌ Equity pinned stats test failed: {e}")
    
    try:
        # Test options pinned stats
        response = requests.get(f"{BASE_URL}/api/options/pinned_stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                tests.append("✅ Options pinned stats API working")
            else:
                tests.append("❌ Options pinned stats invalid response")
        else:
            tests.append(f"❌ Options pinned stats API error: {response.status_code}")
    
    except Exception as e:
        tests.append(f"❌ Options pinned stats test failed: {e}")
    
    return tests

def test_pin_unpin_functionality():
    """Test pin/unpin API endpoints"""
    tests = []
    
    try:
        # Test pin symbol
        response = requests.post(f"{BASE_URL}/api/equity/pin/TESTSTOCK", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                tests.append("✅ Pin symbol API working")
                
                # Test unpin
                response = requests.post(f"{BASE_URL}/api/equity/unpin/TESTSTOCK", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        tests.append("✅ Unpin symbol API working")
                    else:
                        tests.append("❌ Unpin symbol failed")
                else:
                    tests.append(f"❌ Unpin API error: {response.status_code}")
            else:
                tests.append("❌ Pin symbol failed")
        else:
            tests.append(f"❌ Pin API error: {response.status_code}")
    
    except Exception as e:
        tests.append(f"❌ Pin/unpin test failed: {e}")
    
    return tests

def test_main_dashboard():
    """Test main dashboard loads correctly"""
    tests = []
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Check for key elements
            required_elements = [
                'pinned-stats-dashboard',
                'virtual-table',
                'AI Verdict',
                'col-pin',
                'col-symbol',
                'verdict-badge'
            ]
            
            missing = [elem for elem in required_elements if elem not in content]
            
            if not missing:
                tests.append("✅ Dashboard contains all required elements")
            else:
                tests.append(f"❌ Dashboard missing elements: {missing}")
        else:
            tests.append(f"❌ Dashboard load error: {response.status_code}")
    
    except Exception as e:
        tests.append(f"❌ Dashboard test failed: {e}")
    
    return tests

def test_feature_flags():
    """Test feature flags for new functionality"""
    tests = []
    
    try:
        from src.common_repository.config.feature_flags import feature_flags
        
        # Check AI verdict flag
        if feature_flags.is_enabled('enable_ai_verdict_column'):
            tests.append("✅ AI verdict feature flag enabled")
        else:
            tests.append("❌ AI verdict feature flag disabled")
        
        # Check pinned stats flag
        if feature_flags.is_enabled('enable_pinned_stats_dashboard'):
            tests.append("✅ Pinned stats feature flag enabled")
        else:
            tests.append("❌ Pinned stats feature flag disabled")
    
    except Exception as e:
        tests.append(f"❌ Feature flags test failed: {e}")
    
    return tests

def main():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("FRONTEND TABLES VALIDATION - PROMPT 4")
    print("="*60)
    
    all_tests = []
    
    # Run all test suites
    test_suites = [
        ("Feature Flags Tests", test_feature_flags),
        ("AI Verdict Integration Tests", test_ai_verdict_integration),
        ("Pinned Stats API Tests", test_pinned_stats_api),
        ("Pin/Unpin Functionality Tests", test_pin_unpin_functionality),
        ("Main Dashboard Tests", test_main_dashboard)
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
        print("🎉 All tests passed! Frontend tables implementation successful.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
