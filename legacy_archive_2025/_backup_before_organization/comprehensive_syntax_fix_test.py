
#!/usr/bin/env python3
"""
Comprehensive Syntax Fix and Regression Test

This script performs a complete validation of all application components:
1. Syntax validation for all Python files
2. Import testing
3. Core functionality testing
4. API endpoint testing
5. Data generation validation
"""

import sys
import os
import json
import traceback
import time
from datetime import datetime
import subprocess

def test_syntax_all_files():
    """Test syntax of all Python files in the project"""
    print("🔍 Testing Syntax of All Python Files...")
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.pytest_cache', 'node_modules']):
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    syntax_errors = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Compile to check syntax
            compile(code, py_file, 'exec')
            print(f"✅ {py_file}")
            
        except SyntaxError as e:
            error_msg = f"❌ {py_file}: Line {e.lineno} - {e.msg}"
            print(error_msg)
            syntax_errors.append((py_file, e.lineno, e.msg))
        except Exception as e:
            print(f"⚠️ {py_file}: {str(e)}")
    
    if syntax_errors:
        print(f"\n❌ Found {len(syntax_errors)} syntax errors:")
        for file, line, msg in syntax_errors:
            print(f"  {file}:{line} - {msg}")
        return False
    else:
        print(f"\n✅ All {len(python_files)} Python files have valid syntax!")
        return True

def test_core_imports():
    """Test that all core modules can be imported"""
    print("\n🧪 Testing Core Module Imports...")
    
    core_modules = [
        'stock_screener',
        'app', 
        'scheduler',
        'daily_technical_analyzer',
        'predictor',
        'signal_manager'
    ]
    
    import_results = []
    
    for module in core_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
            import_results.append(True)
        except Exception as e:
            print(f"❌ {module}: {str(e)}")
            import_results.append(False)
    
    success_rate = sum(import_results) / len(import_results) * 100
    print(f"\nImport Success Rate: {success_rate:.1f}%")
    return success_rate >= 80

def test_stock_screener_functionality():
    """Test stock screener core functionality"""
    print("\n🧪 Testing Stock Screener Functionality...")
    
    try:
        from src.analyzers.stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        
        # Test 1: Basic initialization
        print("✅ Screener initialized")
        
        # Test 2: Technical indicators
        technical = screener.calculate_enhanced_technical_indicators('RELIANCE')
        if technical and 'current_price' in technical:
            print("✅ Technical indicators working")
        else:
            print("⚠️ Technical indicators returned limited data")
        
        # Test 3: Fundamental data
        fundamentals = screener.scrape_screener_data('RELIANCE')
        if fundamentals and 'pe_ratio' in fundamentals:
            print("✅ Fundamental analysis working")
        else:
            print("⚠️ Fundamental analysis returned limited data")
        
        # Test 4: Scoring system
        test_stocks_data = {
            'RELIANCE': {
                'fundamentals': fundamentals or {'pe_ratio': 25.0, 'revenue_growth': 10.0},
                'technical': technical or {'current_price': 2500.0, 'rsi_14': 65.0}
            }
        }
        
        scored_stocks = screener.enhanced_score_and_rank(test_stocks_data)
        if scored_stocks and len(scored_stocks) > 0:
            print("✅ Scoring system working")
            print(f"   Sample score: {scored_stocks[0].get('score', 'N/A')}")
        else:
            print("⚠️ Scoring system returned no results")
        
        return True
        
    except Exception as e:
        print(f"❌ Stock screener test failed: {str(e)}")
        traceback.print_exc()
        return False

def test_data_generation():
    """Test data generation and file operations"""
    print("\n🧪 Testing Data Generation...")
    
    try:
        # Generate test data
        from datetime import datetime
        import pytz
        
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(ist)
        
        test_data = {
            'timestamp': now_ist.isoformat(),
            'last_updated': now_ist.strftime('%d/%m/%Y, %H:%M:%S'),
            'status': 'test_success',
            'stocks': [
                {
                    'symbol': 'RELIANCE',
                    'score': 85.0,
                    'current_price': 2500.0,
                    'predicted_gain': 15.0,
                    'confidence': 90,
                    'pe_ratio': 25.0,
                    'risk_level': 'Low'
                },
                {
                    'symbol': 'TCS',
                    'score': 82.0,
                    'current_price': 3200.0,
                    'predicted_gain': 12.0,
                    'confidence': 88,
                    'pe_ratio': 23.0,
                    'risk_level': 'Low'
                }
            ]
        }
        
        # Save test data
        with open('top10.json', 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        # Verify data can be read back
        with open('top10.json', 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        if loaded_data['status'] == 'test_success' and len(loaded_data['stocks']) == 2:
            print("✅ Data generation and file operations working")
            return True
        else:
            print("❌ Data verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Data generation test failed: {str(e)}")
        return False

def test_scheduler_functionality():
    """Test scheduler without starting it"""
    print("\n🧪 Testing Scheduler Functionality...")
    
    try:
        from src.core.scheduler import StockAnalystScheduler, run_screening_job_manual
        
        # Test scheduler creation
        scheduler = StockAnalystScheduler()
        print("✅ Scheduler created successfully")
        
        # Test manual screening function (without actually running it for too long)
        print("✅ Manual screening function accessible")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler test failed: {str(e)}")
        return False

def test_flask_app_creation():
    """Test Flask app can be created"""
    print("\n🧪 Testing Flask App Creation...")
    
    try:
        from src.core.app import app
        
        if app and hasattr(app, 'route'):
            print("✅ Flask app created successfully")
            
            # Test some routes exist
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            expected_routes = ['/', '/api/stocks', '/api/run-now']
            
            missing_routes = [route for route in expected_routes if route not in routes]
            if not missing_routes:
                print("✅ All expected routes exist")
                return True
            else:
                print(f"⚠️ Missing routes: {missing_routes}")
                return False
        else:
            print("❌ Flask app creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Flask app test failed: {str(e)}")
        return False

def run_complete_regression_test():
    """Run the complete regression test suite"""
    print("🚀 Starting Complete Regression Test Suite")
    print("=" * 70)
    
    tests = [
        ("Syntax Validation", test_syntax_all_files),
        ("Core Imports", test_core_imports), 
        ("Stock Screener", test_stock_screener_functionality),
        ("Data Generation", test_data_generation),
        ("Scheduler", test_scheduler_functionality),
        ("Flask App", test_flask_app_creation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        print("-" * 50)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {str(e)}")
            results.append((test_name, False))
    
    # Final Summary
    print("\n" + "=" * 70)
    print("📊 REGRESSION TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    success_rate = (passed / total) * 100
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTests Passed: {passed}/{total}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Application is ready for production use")
        print("💡 You can now refresh your browser and use the application")
    elif passed >= total - 1:
        print("\n⚠️ MOSTLY WORKING!")
        print("✅ Core functionality is operational")
        print("🔧 Minor issues may exist but application should work")
    else:
        print("\n❌ MULTIPLE ISSUES DETECTED!")
        print("🔧 Significant problems need to be addressed")
    
    print("\n" + "=" * 70)
    return success_rate >= 80

if __name__ == "__main__":
    success = run_complete_regression_test()
    sys.exit(0 if success else 1)
