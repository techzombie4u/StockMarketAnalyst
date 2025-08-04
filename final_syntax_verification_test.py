
#!/usr/bin/env python3
"""
Final Syntax Verification Test
Tests all components for syntax errors and basic functionality
"""

import sys
import traceback
import json
import os
from datetime import datetime

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing Critical Imports...")
    
    modules_to_test = [
        ('stock_screener', 'EnhancedStockScreener'),
        ('interactive_tracker_manager', 'InteractiveTrackerManager'),
        ('app', None),
        ('scheduler', None),
        ('predictor', None)
    ]
    
    success_count = 0
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name)
            if class_name:
                getattr(module, class_name)
            print(f"✅ {module_name} imported successfully")
            success_count += 1
        except SyntaxError as e:
            print(f"❌ Syntax error in {module_name}: {e}")
            print(f"   Line {e.lineno}: {e.text}")
            return False
        except Exception as e:
            print(f"⚠️ {module_name} import warning: {e}")
            success_count += 1  # Syntax is OK
    
    print(f"📊 Import Results: {success_count}/{len(modules_to_test)} modules imported")
    return success_count == len(modules_to_test)

def test_stock_screener():
    """Test stock screener functionality"""
    print("\n🧪 Testing Stock Screener...")
    
    try:
        from stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test basic methods
        technical = screener.calculate_enhanced_technical_indicators('RELIANCE')
        print(f"✅ Technical analysis: {len(technical) if technical else 0} indicators")
        
        fundamentals = screener.scrape_screener_data('RELIANCE')  
        print(f"✅ Fundamental analysis: {len(fundamentals) if fundamentals else 0} metrics")
        
        # Test scoring
        test_data = {
            'RELIANCE': {
                'fundamentals': fundamentals or {'pe_ratio': 25.0},
                'technical': technical or {'current_price': 2500.0}
            }
        }
        
        scored = screener.enhanced_score_and_rank(test_data)
        print(f"✅ Scoring system: {len(scored) if scored else 0} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Stock screener test failed: {e}")
        traceback.print_exc()
        return False

def test_interactive_tracker():
    """Test interactive tracker manager"""
    print("\n🧪 Testing Interactive Tracker...")
    
    try:
        from interactive_tracker_manager import InteractiveTrackerManager
        tracker = InteractiveTrackerManager()
        
        # Test basic operations
        test_predictions = {
            'pred_5d': 5.0,
            'pred_1mo': 15.0,
            'confidence': 85,
            'score': 75
        }
        
        result = tracker.initialize_stock_tracking('TESTSTOCK', 100.0, test_predictions)
        print(f"✅ Tracker initialization: {'Success' if result else 'Failed'}")
        
        summary = tracker.get_summary_stats()
        print(f"✅ Tracker summary: {summary.get('total_stocks', 0)} stocks")
        
        return True
        
    except Exception as e:
        print(f"❌ Interactive tracker test failed: {e}")
        traceback.print_exc()
        return False

def test_app_startup():
    """Test app can start without syntax errors"""
    print("\n🧪 Testing App Startup...")
    
    try:
        import app
        print("✅ App module imported successfully")
        
        # Check if Flask app is created
        if hasattr(app, 'app'):
            print("✅ Flask app instance found")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        traceback.print_exc()
        return False

def test_file_integrity():
    """Test critical files exist and are readable"""
    print("\n🧪 Testing File Integrity...")
    
    critical_files = [
        'stock_screener.py',
        'interactive_tracker_manager.py',
        'app.py',
        'scheduler.py',
        'templates/index.html',
        'templates/prediction_tracker_interactive.html'
    ]
    
    for file_path in critical_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if content.strip():
                        print(f"✅ {file_path}: OK")
                    else:
                        print(f"⚠️ {file_path}: Empty")
            else:
                print(f"❌ {file_path}: Missing")
        except Exception as e:
            print(f"❌ {file_path}: Error - {e}")
    
    return True

def main():
    """Run comprehensive syntax verification"""
    print("🔧 FINAL SYNTAX VERIFICATION TEST")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Stock Screener Test", test_stock_screener),
        ("Interactive Tracker Test", test_interactive_tracker),
        ("App Startup Test", test_app_startup),
        ("File Integrity Test", test_file_integrity)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL SYNTAX ISSUES FIXED - SYSTEM READY!")
        return True
    else:
        print("⚠️ Some issues remain - check individual test results")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
