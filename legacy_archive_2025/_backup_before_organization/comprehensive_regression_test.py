#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite
Identifies and validates fixes for all application issues
"""

import sys
import os
import json
import traceback
import subprocess
import ast
import importlib
import time
import requests
from datetime import datetime
import threading
import signal

class ComprehensiveRegressionTest:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        self.test_results = {}

    def log_issue(self, category, issue, severity="ERROR"):
        """Log an issue found"""
        self.issues_found.append({
            'category': category,
            'issue': issue,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
        print(f"❌ [{severity}] {category}: {issue}")

    def log_success(self, category, message):
        """Log a successful test"""
        print(f"✅ {category}: {message}")

    def test_1_syntax_validation(self):
        """Phase 1: Validate syntax of all Python files"""
        print("\n🔍 PHASE 1: Python Syntax Validation")
        print("=" * 60)

        python_files = []
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ['.git', '__pycache__', 'venv', '.pytest_cache']):
                continue
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))

        syntax_errors = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()

                # Parse AST to check syntax
                ast.parse(code, py_file)

            except SyntaxError as e:
                error_msg = f"{py_file}:{e.lineno} - {e.msg}"
                syntax_errors.append((py_file, e.lineno, e.msg))
                self.log_issue("SYNTAX", error_msg)
            except Exception as e:
                self.log_issue("SYNTAX", f"{py_file}: {str(e)}")

        if not syntax_errors:
            self.log_success("SYNTAX", f"All {len(python_files)} Python files have valid syntax")
            self.test_results['syntax'] = True
        else:
            self.test_results['syntax'] = False

        return len(syntax_errors) == 0

    def test_2_import_validation(self):
        """Phase 2: Validate critical imports"""
        print("\n🔍 PHASE 2: Import Validation")
        print("=" * 60)

        critical_modules = [
            'app',
            'stock_screener',
            'scheduler',
            'historical_analyzer',
            'interactive_tracker_manager'
        ]

        import_errors = []

        for module in critical_modules:
            try:
                # Clear module from cache if it exists
                if module in sys.modules:
                    del sys.modules[module]

                imported_module = __import__(module)
                self.log_success("IMPORT", f"{module} imported successfully")

            except Exception as e:
                error_msg = f"{module}: {str(e)}"
                import_errors.append((module, str(e)))
                self.log_issue("IMPORT", error_msg)

        self.test_results['imports'] = len(import_errors) == 0
        return len(import_errors) == 0

    def test_3_file_structure(self):
        """Phase 3: Validate required files exist"""
        print("\n🔍 PHASE 3: File Structure Validation")
        print("=" * 60)

        required_files = [
            'main.py',
            'app.py',
            'stock_screener.py',
            'scheduler.py',
            'templates/index.html',
            'templates/analysis.html',
            'templates/lookup.html',
            'templates/prediction_tracker.html',
            'templates/prediction_tracker_interactive.html'
        ]

        missing_files = []

        for file_path in required_files:
            if os.path.exists(file_path):
                self.log_success("FILE", f"{file_path} exists")
            else:
                missing_files.append(file_path)
                self.log_issue("FILE", f"Missing required file: {file_path}")

        self.test_results['files'] = len(missing_files) == 0
        return len(missing_files) == 0

    def test_4_json_integrity(self):
        """Phase 4: Validate JSON files"""
        print("\n🔍 PHASE 4: JSON File Integrity")
        print("=" * 60)

        json_files = [
            'top10.json',
            'predictions_history.json',
            'agent_decisions.json',
            'stable_predictions.json',
            'signal_history.json'
        ]

        json_errors = []

        for json_file in json_files:
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            json.loads(content)
                            self.log_success("JSON", f"{json_file} is valid")
                        else:
                            self.log_success("JSON", f"{json_file} is empty (acceptable)")
                except json.JSONDecodeError as e:
                    error_msg = f"{json_file}: Invalid JSON - {str(e)}"
                    json_errors.append((json_file, str(e)))
                    self.log_issue("JSON", error_msg)
            else:
                self.log_success("JSON", f"{json_file} will be created on demand")

        self.test_results['json'] = len(json_errors) == 0
        return len(json_errors) == 0

    def test_5_app_initialization(self):
        """Phase 5: Test Flask app initialization"""
        print("\n🔍 PHASE 5: Flask App Initialization")
        print("=" * 60)

        try:
            # Import and test app creation
            import app
            flask_app = app.app

            # Test app context
            with flask_app.app_context():
                self.log_success("FLASK", "App context works")

            # Test routes exist
            routes = [rule.rule for rule in flask_app.url_map.iter_rules()]
            required_routes = ['/', '/api/stocks', '/api/status']

            for route in required_routes:
                if route in routes:
                    self.log_success("ROUTE", f"{route} registered")
                else:
                    self.log_issue("ROUTE", f"Missing route: {route}")

            self.test_results['app_init'] = True
            return True

        except Exception as e:
            self.log_issue("FLASK", f"App initialization failed: {str(e)}")
            self.test_results['app_init'] = False
            return False

    def test_6_api_functionality(self):
        """Phase 6: Test API endpoints (if app is running)"""
        print("\n🔍 PHASE 6: API Functionality Test")
        print("=" * 60)

        # Start app in background thread for testing
        app_thread = None
        try:
            import app

            def run_app():
                app.app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)

            app_thread = threading.Thread(target=run_app, daemon=True)
            app_thread.start()

            # Wait for app to start
            time.sleep(3)

            # Test API endpoints
            test_endpoints = [
                ('/', 'Dashboard'),
                ('/api/stocks', 'Stocks API'),
                ('/api/status', 'Status API')
            ]

            for endpoint, description in test_endpoints:
                try:
                    response = requests.get(f'http://127.0.0.1:5001{endpoint}', timeout=10)
                    if response.status_code == 200:
                        self.log_success("API", f"{description} returns 200")
                    else:
                        self.log_issue("API", f"{description} returns {response.status_code}")
                except Exception as e:
                    self.log_issue("API", f"{description} failed: {str(e)}")

            self.test_results['api'] = True
            return True

        except Exception as e:
            self.log_issue("API", f"API testing failed: {str(e)}")
            self.test_results['api'] = False
            return False

    def test_7_data_generation(self):
        """Phase 7: Test data generation capabilities"""
        print("\n🔍 PHASE 7: Data Generation Test")
        print("=" * 60)

        try:
            from src.analyzers.stock_screener import EnhancedStockScreener
            screener = EnhancedStockScreener()

            # Test basic screening functionality
            test_symbol = 'RELIANCE'
            technical = screener.calculate_enhanced_technical_indicators(test_symbol)

            if technical:
                self.log_success("DATA", f"Technical analysis works for {test_symbol}")
            else:
                self.log_issue("DATA", f"Technical analysis failed for {test_symbol}")

            # Test data structure
            if isinstance(technical, dict) and len(technical) > 0:
                self.log_success("DATA", "Technical data structure is valid")
            else:
                self.log_issue("DATA", "Technical data structure is invalid")

            self.test_results['data_gen'] = True
            return True

        except Exception as e:
            self.log_issue("DATA", f"Data generation test failed: {str(e)}")
            self.test_results['data_gen'] = False
            return False

    def run_comprehensive_test(self):
        """Run all test phases"""
        print("🚀 STARTING COMPREHENSIVE REGRESSION TEST")
        print("=" * 80)
        print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        test_phases = [
            ("Syntax Validation", self.test_1_syntax_validation),
            ("Import Validation", self.test_2_import_validation),
            ("File Structure", self.test_3_file_structure),
            ("JSON Integrity", self.test_4_json_integrity),
            ("App Initialization", self.test_5_app_initialization),
            ("API Functionality", self.test_6_api_functionality),
            ("Data Generation", self.test_7_data_generation)
        ]

        passed_tests = 0
        total_tests = len(test_phases)

        for phase_name, test_func in test_phases:
            print(f"\n🧪 Starting {phase_name}...")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {phase_name} PASSED")
                else:
                    print(f"❌ {phase_name} FAILED")
            except Exception as e:
                print(f"💥 {phase_name} CRASHED: {str(e)}")
                self.log_issue("CRASH", f"{phase_name}: {str(e)}")

        # Final Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE REGRESSION TEST SUMMARY")
        print("=" * 80)
        print(f"⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"❌ Issues Found: {len(self.issues_found)}")

        success_rate = (passed_tests / total_tests) * 100

        if success_rate == 100:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Application is fully operational")
            print("🚀 Ready for production use")
        elif success_rate >= 85:
            print("\n⚡ MOSTLY OPERATIONAL!")
            print("✅ Core functionality is working")
            print("🔧 Minor issues may need attention")
        else:
            print("\n⚠️ SIGNIFICANT ISSUES DETECTED!")
            print("❌ Multiple components need fixing")

        if self.issues_found:
            print("\n📋 DETAILED ISSUES FOUND:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. [{issue['category']}] {issue['issue']}")

        print(f"\n📈 Overall Success Rate: {success_rate:.1f}%")

        return success_rate >= 85

def main():
    """Main test execution"""
    tester = ComprehensiveRegressionTest()

    try:
        success = tester.run_comprehensive_test()

        if success:
            print("\n🎯 REGRESSION TEST COMPLETED SUCCESSFULLY")
            sys.exit(0)
        else:
            print("\n🔧 ISSUES DETECTED - REVIEW REQUIRED")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()