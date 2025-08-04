
#!/usr/bin/env python3
"""
Verification Test for Stock Screener Fixes
"""

import sys
import traceback

def test_stock_screener_import():
    """Test that stock screener can be imported without syntax errors"""
    print("🧪 Testing Stock Screener Import...")
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        print("✅ Stock screener imports successfully")
        return True
    except Exception as e:
        print(f"❌ Stock screener import failed: {e}")
        traceback.print_exc()
        return False

def test_basic_functionality():
    """Test basic screener functionality"""
    print("🧪 Testing Basic Functionality...")
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test with a simple stock
        test_data = {
            'SBIN': {
                'fundamentals': {'pe_ratio': 15.0, 'revenue_growth': 5.0},
                'technical': {'current_price': 500.0, 'rsi_14': 45.0}
            }
        }
        
        results = screener.enhanced_score_and_rank(test_data)
        
        if results and len(results) > 0:
            print(f"✅ Basic functionality works - got {len(results)} results")
            return True
        else:
            print("❌ No results from basic functionality test")
            return False
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_scheduler_import():
    """Test scheduler functionality"""
    print("🧪 Testing Scheduler Import...")
    try:
        from scheduler import run_screening_job_manual
        print("✅ Scheduler imports successfully")
        return True
    except Exception as e:
        print(f"❌ Scheduler import failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 Starting Fix Verification Tests")
    print("=" * 50)
    
    tests = [
        test_stock_screener_import,
        test_basic_functionality,
        test_scheduler_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes should work.")
        return True
    else:
        print("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
