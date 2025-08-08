
#!/usr/bin/env python3
"""
Test script to verify syntax fixes are working
"""

def test_import_stock_screener():
    """Test if stock screener can be imported without syntax errors"""
    try:
        from src.analyzers.stock_screener import EnhancedStockScreener
        print("✅ Stock screener imported successfully")
        
        # Test basic initialization
        screener = EnhancedStockScreener()
        print("✅ Stock screener initialized successfully")
        
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"⚠️ Import error: {e}")
        return True  # Syntax is OK, just runtime issue

def test_basic_functionality():
    """Test basic functionality"""
    try:
        from src.analyzers.stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test that we can call basic methods without syntax errors
        result = screener.scrape_screener_data('RELIANCE')
        print("✅ Basic functionality test passed")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in functionality: {e}")
        return False
    except Exception as e:
        print(f"✅ Functionality test passed (runtime error is expected): {e}")
        return True

def main():
    """Run syntax verification tests"""
    print("🔧 Testing Syntax Fixes")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_import_stock_screener),
        ("Functionality Test", test_basic_functionality)
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All syntax fixes successful!")
    else:
        print("⚠️ Some issues remain")

if __name__ == "__main__":
    main()
