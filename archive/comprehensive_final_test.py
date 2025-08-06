
#!/usr/bin/env python3
"""
Comprehensive Final Test Suite
Validates all fixes and ensures application is working correctly
"""

import sys
import os
import json
import ast
import importlib
import traceback
import subprocess
import time
import requests
import threading
from datetime import datetime

class ComprehensiveFinalTest:
    def __init__(self):
        self.issues_found = []
        self.tests_passed = 0
        self.tests_failed = 0

    def log_issue(self, category, issue, severity="ERROR"):
        """Log an issue found"""
        self.issues_found.append({
            'category': category,
            'issue': issue,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
        print(f"❌ [{severity}] {category}: {issue}")

    def log_success(self, test_name):
        """Log a successful test"""
        self.tests_passed += 1
        print(f"✅ {test_name}")

    def log_failure(self, test_name, error):
        """Log a failed test"""
        self.tests_failed += 1
        print(f"❌ {test_name}: {error}")

    def test_syntax_all_files(self):
        """Phase 1: Test syntax of all Python files"""
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
                ast.parse(code, py_file)
                
            except SyntaxError as e:
                error_msg = f"{py_file}:{e.lineno} - {e.msg}"
                syntax_errors.append((py_file, e.lineno, e.msg))
                self.log_issue("SYNTAX", error_msg)
            except Exception as e:
                self.log_issue("SYNTAX", f"{py_file}: {str(e)}")

        if not syntax_errors:
            self.log_success(f"All {len(python_files)} Python files have valid syntax")
            return True
        else:
            self.log_failure("Syntax Check", f"Found {len(syntax_errors)} syntax errors")
            return False

    def test_critical_imports(self):
        """Phase 2: Test critical module imports"""
        print("\n🔍 PHASE 2: Critical Module Imports")
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
                
                importlib.import_module(module)
                self.log_success(f"{module} imported successfully")
                
            except Exception as e:
                error_msg = f"{module}: {str(e)}"
                import_errors.append((module, str(e)))
                self.log_issue("IMPORT", error_msg)

        return len(import_errors) == 0

    def test_file_structure(self):
        """Phase 3: Test required files exist"""
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
                self.log_success(f"{file_path} exists")
            else:
                missing_files.append(file_path)
                self.log_issue("FILE", f"Missing required file: {file_path}")

        return len(missing_files) == 0

    def test_json_integrity(self):
        """Phase 4: Test JSON file integrity"""
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
            try:
                if os.path.exists(json_file):
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            json.loads(content)
                            self.log_success(f"{json_file} is valid JSON")
                        else:
                            self.log_success(f"{json_file} exists (empty)")
                else:
                    # Create empty JSON file
                    with open(json_file, 'w') as f:
                        json.dump({}, f)
                    self.log_success(f"{json_file} created")
                    
            except json.JSONDecodeError as e:
                error_msg = f"{json_file}: Invalid JSON - {str(e)}"
                json_errors.append((json_file, str(e)))
                self.log_issue("JSON", error_msg)
            except Exception as e:
                self.log_issue("JSON", f"{json_file}: {str(e)}")

        return len(json_errors) == 0

    def test_app_initialization(self):
        """Phase 5: Test Flask app can initialize"""
        print("\n🔍 PHASE 5: Flask App Initialization")
        print("=" * 60)

        try:
            # Import app module
            import app
            self.log_success("App module imported")

            # Test Flask app exists
            if hasattr(app, 'app'):
                flask_app = app.app
                self.log_success("Flask app instance exists")

                # Test app context
                with flask_app.app_context():
                    self.log_success("Flask app context works")
                
                return True
            else:
                self.log_failure("Flask App", "No Flask app instance found")
                return False
                
        except Exception as e:
            self.log_failure("Flask App", str(e))
            return False

    def test_key_functions(self):
        """Phase 6: Test key application functions"""
        print("\n🔍 PHASE 6: Key Function Tests")
        print("=" * 60)

        try:
            import app
            
            # Test file integrity function
            app.check_file_integrity()
            self.log_success("check_file_integrity() works")
            
            # Test API status function
            with app.app.test_client() as client:
                response = client.get('/api/status')
                if response.status_code == 200:
                    self.log_success("API status endpoint works")
                else:
                    self.log_failure("API Status", f"Status code: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_failure("Key Functions", str(e))
            return False

    def test_server_startup(self):
        """Phase 7: Test server can start"""
        print("\n🔍 PHASE 7: Server Startup Test")
        print("=" * 60)

        server_process = None
        try:
            # Start server in background
            server_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for server to start
            time.sleep(3)
            
            # Check if server is running
            try:
                response = requests.get('http://localhost:5000/api/health', timeout=5)
                if response.status_code == 200:
                    self.log_success("Server started and responding")
                    return True
                else:
                    self.log_failure("Server Response", f"Status: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                self.log_failure("Server Connection", str(e))
                return False
                
        except Exception as e:
            self.log_failure("Server Startup", str(e))
            return False
        finally:
            # Clean up server process
            if server_process:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()

    def run_comprehensive_test(self):
        """Run all test phases"""
        print("🚀 COMPREHENSIVE FINAL TEST SUITE")
        print("=" * 60)
        print("Testing all application components for production readiness...")
        
        test_phases = [
            ("Syntax Validation", self.test_syntax_all_files),
            ("Critical Imports", self.test_critical_imports),
            ("File Structure", self.test_file_structure),
            ("JSON Integrity", self.test_json_integrity),
            ("App Initialization", self.test_app_initialization),
            ("Key Functions", self.test_key_functions),
            ("Server Startup", self.test_server_startup)
        ]
        
        passed_phases = 0
        for phase_name, test_func in test_phases:
            print(f"\n🧪 Testing {phase_name}...")
            try:
                if test_func():
                    passed_phases += 1
                    print(f"✅ {phase_name} PASSED")
                else:
                    print(f"❌ {phase_name} FAILED")
            except Exception as e:
                print(f"❌ {phase_name} ERROR: {str(e)}")
                self.log_issue("TEST_RUNNER", f"{phase_name}: {str(e)}")
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        print(f"✅ Phases Passed: {passed_phases}/{len(test_phases)}")
        print(f"✅ Individual Tests Passed: {self.tests_passed}")
        print(f"❌ Individual Tests Failed: {self.tests_failed}")
        print(f"⚠️  Issues Found: {len(self.issues_found)}")
        
        if passed_phases == len(test_phases) and len(self.issues_found) == 0:
            print("\n🎉 ALL TESTS PASSED! APPLICATION IS READY FOR PRODUCTION!")
            return True
        else:
            print("\n⚠️  SOME ISSUES REMAIN. CHECK DETAILS ABOVE.")
            if self.issues_found:
                print("\n📋 REMAINING ISSUES:")
                for issue in self.issues_found:
                    print(f"  • {issue['category']}: {issue['issue']}")
            return False

if __name__ == "__main__":
    tester = ComprehensiveFinalTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🚀 READY TO DEPLOY!")
        sys.exit(0)
    else:
        print("\n🔧 FIXES STILL NEEDED!")
        sys.exit(1)
