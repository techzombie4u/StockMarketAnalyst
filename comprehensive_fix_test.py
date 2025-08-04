
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
        """Test required files exist and are valid"""
        print("\n🔍 PHASE 3: Testing File Structure...")
        print("=" * 60)
        
        required_files = [
            ('main.py', 'file'),
            ('app.py', 'file'),
            ('stock_screener.py', 'file'),
            ('scheduler.py', 'file'),
            ('templates', 'dir'),
            ('templates/index.html', 'file'),
            ('templates/prediction_tracker_interactive.html', 'file')
        ]
        
        missing_files = []
        
        for file_path, file_type in required_files:
            if file_type == 'file':
                if os.path.isfile(file_path):
                    print(f"✅ {file_path} exists")
                else:
                    print(f"❌ {file_path} missing")
                    missing_files.append(file_path)
                    self.log_issue("FILE_MISSING", f"Required file missing: {file_path}")
            elif file_type == 'dir':
                if os.path.isdir(file_path):
                    print(f"✅ {file_path}/ exists")
                else:
                    print(f"❌ {file_path}/ missing")
                    missing_files.append(file_path)
                    self.log_issue("DIR_MISSING", f"Required directory missing: {file_path}")
        
        return len(missing_files) == 0
    
    def test_json_files(self):
        """Test JSON files are valid"""
        print("\n🔍 PHASE 4: Testing JSON Files...")
        print("=" * 60)
        
        json_files = [
            'top10.json',
            'agent_decisions.json',
            'signal_history.json',
            'predictions_history.json',
            'stable_predictions.json'
        ]
        
        json_errors = []
        
        for json_file in json_files:
            if os.path.exists(json_file):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            json.loads(content)
                            print(f"✅ {json_file} is valid JSON")
                        else:
                            print(f"⚠️ {json_file} is empty")
                except json.JSONDecodeError as e:
                    error_msg = f"{json_file}: {str(e)}"
                    print(f"❌ {error_msg}")
                    json_errors.append((json_file, str(e)))
                    self.log_issue("JSON_INVALID", error_msg)
            else:
                print(f"ℹ️ {json_file} does not exist (will be created)")
        
        return len(json_errors) == 0
    
    def test_app_startup(self):
        """Test Flask app can start"""
        print("\n🔍 PHASE 5: Testing App Startup...")
        print("=" * 60)
        
        try:
            from app import app
            
            # Test app configuration
            if hasattr(app, 'config'):
                print("✅ Flask app configured")
            else:
                self.log_issue("APP_CONFIG", "Flask app not properly configured")
                return False
            
            # Test if we can create app context
            with app.app_context():
                print("✅ App context creation successful")
            
            return True
            
        except Exception as e:
            error_msg = f"App startup failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.log_issue("APP_STARTUP", error_msg)
            return False
    
    def test_api_routes(self):
        """Test API routes are defined"""
        print("\n🔍 PHASE 6: Testing API Routes...")
        print("=" * 60)
        
        try:
            from app import app
            
            required_routes = [
                '/',
                '/api/stocks',
                '/api/status',
                '/api/run-now',
                '/prediction-tracker-interactive',
                '/api/interactive-tracker-data'
            ]
            
            route_errors = []
            
            with app.app_context():
                for rule in app.url_map.iter_rules():
                    if rule.rule in required_routes:
                        print(f"✅ Route {rule.rule} defined")
                        required_routes.remove(rule.rule)
                
                for missing_route in required_routes:
                    error_msg = f"Route {missing_route} not defined"
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
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"❌ Issues Found: {len(self.issues_found)}")
        print(f"🔧 Fixes Applied: {len(self.fixes_applied)}")
        
        if len(self.issues_found) > 0:
            print("\n🔍 DETAILED ISSUES:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"{i}. [{issue['severity']}] {issue['category']}: {issue['issue']}")
        
        return passed_tests == total_tests and len(self.issues_found) == 0

if __name__ == "__main__":
    tester = ComprehensiveFixTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL ISSUES RESOLVED!")
        print("✅ Application is ready for production")
    else:
        print("\n⚠️ ISSUES STILL EXIST!")
        print("❌ Manual intervention required")
    
    sys.exit(0 if success else 1)
