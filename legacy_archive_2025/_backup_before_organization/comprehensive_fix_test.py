
#!/usr/bin/env python3
"""
Comprehensive Fix Test - Identify and Fix All Issues
"""

import sys
import os
import json
import traceback
import subprocess
import ast
from datetime import datetime

class ComprehensiveFixTest:
    def __init__(self):
        self.issues_found = []
        self.fixes_applied = []
        
    def log_issue(self, category, issue, severity="ERROR"):
        """Log an issue found"""
        self.issues_found.append({
            'category': category,
            'issue': issue,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
        print(f"❌ [{severity}] {category}: {issue}")
    
    def log_fix(self, category, fix):
        """Log a fix applied"""
        self.fixes_applied.append({
            'category': category,
            'fix': fix,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✅ [FIXED] {category}: {fix}")
    
    def test_syntax_all_files(self):
        """Test syntax of all Python files"""
        print("\n🔍 PHASE 1: Testing Syntax of All Python Files...")
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
                print(f"✅ {py_file}")
                
            except SyntaxError as e:
                error_msg = f"{py_file}:{e.lineno} - {e.msg}"
                print(f"❌ {error_msg}")
                syntax_errors.append((py_file, e.lineno, e.msg, e.text))
                self.log_issue("SYNTAX", error_msg)
            except Exception as e:
                print(f"⚠️ {py_file}: {str(e)}")
        
        return len(syntax_errors) == 0
    
    def test_imports(self):
        """Test that critical modules can be imported"""
        print("\n🔍 PHASE 2: Testing Critical Imports...")
        print("=" * 60)
        
        critical_modules = [
            'app',
            'stock_screener',
            'scheduler',
            'historical_analyzer',
            'intelligent_prediction_agent',
            'interactive_tracker_manager'
        ]
        
        import_errors = []
        
        for module in critical_modules:
            try:
                if module in sys.modules:
                    del sys.modules[module]
                
                __import__(module)
                print(f"✅ {module} imports successfully")
                
            except Exception as e:
                error_msg = f"{module}: {str(e)}"
                print(f"❌ {error_msg}")
                import_errors.append((module, str(e)))
                self.log_issue("IMPORT", error_msg)
        
        return len(import_errors) == 0
    
    def test_file_structure(self):
        """Test that required files exist"""
        print("\n🔍 PHASE 3: Testing File Structure...")
        print("=" * 60)
        
        required_files = [
            'main.py',
            'app.py',
            'stock_screener.py',
            'scheduler.py',
            'templates/index.html',
            'templates/analysis.html',
            'templates/lookup.html',
            'templates/prediction_tracker.html'
        ]
        
        missing_files = []
        
        for file_path in required_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path}")
            else:
                print(f"❌ {file_path}")
                missing_files.append(file_path)
                self.log_issue("FILE_MISSING", f"Required file missing: {file_path}")
        
        return len(missing_files) == 0
    
    def test_json_files(self):
        """Test JSON file integrity"""
        print("\n🔍 PHASE 4: Testing JSON Files...")
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
                            print(f"✅ {json_file}")
                        else:
                            print(f"⚠️ {json_file} (empty)")
                except json.JSONDecodeError as e:
                    error_msg = f"{json_file}: Invalid JSON - {str(e)}"
                    print(f"❌ {error_msg}")
                    json_errors.append((json_file, str(e)))
                    self.log_issue("JSON_INVALID", error_msg)
                except Exception as e:
                    print(f"⚠️ {json_file}: {str(e)}")
            else:
                print(f"⚠️ {json_file} (missing)")
        
        return len(json_errors) == 0
    
    def test_app_startup(self):
        """Test app can start without errors"""
        print("\n🔍 PHASE 5: Testing App Startup...")
        print("=" * 60)
        
        try:
            # Test that we can import app without errors
            import app
            print("✅ App module imports successfully")
            
            # Test that we can create the Flask app
            if hasattr(app, 'app'):
                flask_app = app.app
                print("✅ Flask app instance exists")
                
                # Test that we can get app context
                with flask_app.app_context():
                    print("✅ Flask app context works")
                
                return True
            else:
                self.log_issue("APP_STARTUP", "Flask app instance not found")
                return False
                
        except Exception as e:
            error_msg = f"App startup failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.log_issue("APP_STARTUP", error_msg)
            return False
    
    def test_api_routes(self):
        """Test that API routes are accessible"""
        print("\n🔍 PHASE 6: Testing API Routes...")
        print("=" * 60)
        
        try:
            import app
            flask_app = app.app
            
            # Get all routes
            routes = []
            for rule in flask_app.url_map.iter_rules():
                routes.append(rule.rule)
            
            required_routes = [
                '/',
                '/api/stocks',
                '/api/status',
                '/api/run-now',
                '/analysis',
                '/api/analysis',
                '/lookup',
                '/prediction-tracker'
            ]
            
            route_errors = []
            
            for route in required_routes:
                if route in routes:
                    print(f"✅ {route}")
                else:
                    missing_route = f"Route missing: {route}"
                    error_msg = f"Route {route} not found in app routes"
                    print(f"❌ {error_msg}")
                    route_errors.append(missing_route)
                    self.log_issue("ROUTE_MISSING", error_msg)
            
            return len(route_errors) == 0
            
        except Exception as e:
            error_msg = f"Route testing failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.log_issue("ROUTE_TEST", error_msg)
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 STARTING COMPREHENSIVE FIX TEST")
        print("=" * 80)
        
        tests = [
            ("Syntax Check", self.test_syntax_all_files),
            ("Import Test", self.test_imports),
            ("File Structure", self.test_file_structure),
            ("JSON Validation", self.test_json_files),
            ("App Startup", self.test_app_startup),
            ("API Routes", self.test_api_routes)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}...")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name} PASSED")
                else:
                    print(f"❌ {test_name} FAILED")
            except Exception as e:
                print(f"💥 {test_name} CRASHED: {str(e)}")
                self.log_issue("TEST_CRASH", f"{test_name}: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
        print(f"❌ Issues Found: {len(self.issues_found)}")
        print(f"🔧 Fixes Applied: {len(self.fixes_applied)}")
        
        if self.issues_found:
            print("\n🔍 DETAILED ISSUES:")
            for issue in self.issues_found:
                print(f"  • {issue['category']}: {issue['issue']}")
        
        return passed_tests == total_tests and len(self.issues_found) == 0

if __name__ == "__main__":
    tester = ComprehensiveFixTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL ISSUES RESOLVED!")
        print("✅ Application is ready for production")
    else:
        print("\n⚠️ ISSUES STILL EXIST")
        print("❌ Review and fix the issues above")
