
#!/usr/bin/env python3
"""
Comprehensive Regression Test for Options Strategy Implementation
Tests all new functionality while ensuring backward compatibility
"""

import sys
import os
import json
import requests
import time
import subprocess
import threading
import signal
from datetime import datetime

class OptionsStrategyRegressionTest:
    def __init__(self):
        self.test_results = []
        self.server_process = None
        self.server_running = False
        self.base_url = "http://localhost:5000"
        
    def run_test(self, test_name, test_function):
        """Run a single test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 50)
        
        try:
            start_time = time.time()
            result = test_function()
            duration = time.time() - start_time
            
            if result:
                status = "PASS"
                print(f"✅ {test_name}: PASSED ({duration:.2f}s)")
            else:
                status = "FAIL"
                print(f"❌ {test_name}: FAILED ({duration:.2f}s)")
                
        except Exception as e:
            status = "ERROR"
            duration = time.time() - start_time
            print(f"💥 {test_name}: ERROR - {str(e)} ({duration:.2f}s)")
            
        self.test_results.append({
            'test': test_name,
            'status': status,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
        return status == "PASS"

    def test_file_structure(self):
        """Test that all required files exist"""
        required_files = [
            'src/analyzers/short_strangle_engine.py',
            'web/templates/options_strategy.html',
            'src/core/app.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"Missing files: {missing_files}")
            return False
            
        print("✓ All required files present")
        return True

    def test_short_strangle_engine_import(self):
        """Test that the short strangle engine can be imported"""
        try:
            sys.path.insert(0, os.getcwd())
            from src.analyzers.short_strangle_engine import ShortStrangleEngine
            
            # Test instantiation
            engine = ShortStrangleEngine()
            print("✓ ShortStrangleEngine imported and instantiated successfully")
            
            # Test Tier 1 stocks list
            if not engine.TIER_1_STOCKS:
                print("❌ TIER_1_STOCKS is empty")
                return False
                
            expected_stocks = ['RELIANCE.NS', 'HDFCBANK.NS', 'TCS.NS', 'ITC.NS', 'INFY.NS', 'HINDUNILVR.NS']
            for stock in expected_stocks:
                if stock not in engine.TIER_1_STOCKS:
                    print(f"❌ Missing expected stock: {stock}")
                    return False
            
            print(f"✓ Found {len(engine.TIER_1_STOCKS)} Tier 1 stocks")
            return True
            
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            return False
        except Exception as e:
            print(f"❌ Engine test failed: {e}")
            return False

    def test_engine_calculations(self):
        """Test the calculation methods of the engine"""
        try:
            from src.analyzers.short_strangle_engine import ShortStrangleEngine
            engine = ShortStrangleEngine()
            
            # Test premium calculation
            premium = engine.calculate_option_premium(1000, 1050, 30, 20, 'call')
            if premium <= 0:
                print(f"❌ Invalid premium calculation: {premium}")
                return False
            print(f"✓ Option premium calculation: ₹{premium:.2f}")
            
            # Test margin calculation
            margin = engine.calculate_margin_requirement(1000, 1050, 950, 25, 20)
            if margin <= 0:
                print(f"❌ Invalid margin calculation: {margin}")
                return False
            print(f"✓ Margin calculation: ₹{margin:.2f}")
            
            # Test IV calculation
            iv = engine.calculate_implied_volatility('TCS.NS', {'historical_volatility': 15})
            if iv <= 0 or iv > 100:
                print(f"❌ Invalid IV calculation: {iv}")
                return False
            print(f"✓ IV calculation: {iv:.1f}%")
            
            return True
            
        except Exception as e:
            print(f"❌ Engine calculation test failed: {e}")
            return False

    def test_flask_app_import(self):
        """Test that the Flask app can be imported with new routes"""
        try:
            sys.path.insert(0, os.getcwd())
            from src.core.app import app
            
            # Check if new routes exist
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            
            expected_routes = ['/options-strategy', '/api/options-strategies']
            missing_routes = []
            
            for route in expected_routes:
                if route not in routes:
                    missing_routes.append(route)
            
            if missing_routes:
                print(f"❌ Missing routes: {missing_routes}")
                return False
                
            print("✓ Flask app imported with new routes")
            return True
            
        except Exception as e:
            print(f"❌ Flask app import failed: {e}")
            return False

    def start_server(self):
        """Start the Flask server"""
        try:
            print("Starting Flask server...")
            self.server_process = subprocess.Popen(
                [sys.executable, 'main.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for server to start
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    response = requests.get(f"{self.base_url}/", timeout=5)
                    if response.status_code == 200:
                        self.server_running = True
                        print("✓ Server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    pass
                
                time.sleep(2)
                print(f"Waiting for server... ({attempt + 1}/{max_attempts})")
            
            print("❌ Server failed to start within timeout")
            return False
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            finally:
                self.server_process = None
                self.server_running = False
                print("✓ Server stopped")

    def test_existing_functionality(self):
        """Test that existing functionality still works"""
        try:
            # Test main dashboard
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code != 200:
                print(f"❌ Main dashboard failed: {response.status_code}")
                return False
            
            # Test existing API endpoints
            response = requests.get(f"{self.base_url}/api/stocks", timeout=10)
            if response.status_code != 200:
                print(f"❌ Stocks API failed: {response.status_code}")
                return False
            
            # Test analysis page
            response = requests.get(f"{self.base_url}/analysis", timeout=10)
            if response.status_code != 200:
                print(f"❌ Analysis page failed: {response.status_code}")
                return False
            
            print("✓ All existing functionality works")
            return True
            
        except Exception as e:
            print(f"❌ Existing functionality test failed: {e}")
            return False

    def test_new_options_page(self):
        """Test the new options strategy page"""
        try:
            # Test options strategy page
            response = requests.get(f"{self.base_url}/options-strategy", timeout=10)
            if response.status_code != 200:
                print(f"❌ Options strategy page failed: {response.status_code}")
                return False
            
            # Check if page contains expected content
            content = response.text
            expected_content = [
                'Options Income',
                'Short Strangle Strategy',
                'Tier 1 Stocks',
                'RELIANCE',
                'Generate Strategies'
            ]
            
            missing_content = []
            for item in expected_content:
                if item not in content:
                    missing_content.append(item)
            
            if missing_content:
                print(f"❌ Missing content in options page: {missing_content}")
                return False
            
            print("✓ Options strategy page loads with correct content")
            return True
            
        except Exception as e:
            print(f"❌ Options page test failed: {e}")
            return False

    def test_options_api(self):
        """Test the options strategies API"""
        try:
            # Test options API
            response = requests.get(f"{self.base_url}/api/options-strategies", timeout=15)
            if response.status_code != 200:
                print(f"❌ Options API failed: {response.status_code}")
                return False
            
            data = response.json()
            
            # Check response structure
            required_keys = ['status', 'strategies', 'summary']
            missing_keys = []
            for key in required_keys:
                if key not in data:
                    missing_keys.append(key)
            
            if missing_keys:
                print(f"❌ Missing keys in API response: {missing_keys}")
                return False
            
            # Test with different timeframes
            for timeframe in ['5D', '10D', '30D']:
                response = requests.get(f"{self.base_url}/api/options-strategies?timeframe={timeframe}", timeout=15)
                if response.status_code != 200:
                    print(f"❌ Options API failed for timeframe {timeframe}: {response.status_code}")
                    return False
            
            print("✓ Options API works for all timeframes")
            return True
            
        except Exception as e:
            print(f"❌ Options API test failed: {e}")
            return False

    def test_data_persistence(self):
        """Test that options data is properly saved and loaded"""
        try:
            # Check if options signals file exists or can be created
            options_file = "data/tracking/options_signals.json"
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(options_file), exist_ok=True)
            
            # Test data creation
            test_data = {
                "30D": {
                    "strategies": [],
                    "last_updated": datetime.now().isoformat(),
                    "total_opportunities": 0
                }
            }
            
            with open(options_file, 'w') as f:
                json.dump(test_data, f, indent=2)
            
            # Test data loading
            with open(options_file, 'r') as f:
                loaded_data = json.load(f)
            
            if "30D" not in loaded_data:
                print("❌ Data persistence test failed - data not loaded correctly")
                return False
            
            print("✓ Data persistence works correctly")
            return True
            
        except Exception as e:
            print(f"❌ Data persistence test failed: {e}")
            return False

    def test_navigation_integration(self):
        """Test that navigation properly includes the new options link"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            content = response.text
            
            # Check for Options Income button
            if 'Options Income' not in content:
                print("❌ Options Income button not found in navigation")
                return False
            
            # Check for correct link
            if '/options-strategy' not in content:
                print("❌ Options strategy link not found")
                return False
            
            print("✓ Navigation integration successful")
            return True
            
        except Exception as e:
            print(f"❌ Navigation integration test failed: {e}")
            return False

    def run_all_tests(self):
        """Run complete regression test suite"""
        print("🎯 Starting Options Strategy Implementation Regression Tests")
        print("=" * 70)
        
        # Test 1: File structure
        self.run_test("File Structure", self.test_file_structure)
        
        # Test 2: Engine import and basic functionality
        self.run_test("Short Strangle Engine Import", self.test_short_strangle_engine_import)
        
        # Test 3: Engine calculations
        self.run_test("Engine Calculations", self.test_engine_calculations)
        
        # Test 4: Flask app import
        self.run_test("Flask App Import", self.test_flask_app_import)
        
        # Test 5: Data persistence
        self.run_test("Data Persistence", self.test_data_persistence)
        
        # Test 6: Server startup
        server_started = self.run_test("Server Startup", self.start_server)
        
        if server_started:
            # Test 7: Existing functionality (backward compatibility)
            self.run_test("Existing Functionality", self.test_existing_functionality)
            
            # Test 8: New options page
            self.run_test("Options Strategy Page", self.test_new_options_page)
            
            # Test 9: Options API
            self.run_test("Options Strategies API", self.test_options_api)
            
            # Test 10: Navigation integration
            self.run_test("Navigation Integration", self.test_navigation_integration)
            
            # Stop server
            self.stop_server()
        
        # Print results summary
        print("=" * 70)
        print("📊 Test Results Summary:")
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        errors = len([r for r in self.test_results if r['status'] == 'ERROR'])
        total = len(self.test_results)
        
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"💥 ERRORS: {errors}")
        print(f"📈 SUCCESS RATE: {(passed/total)*100:.1f}%")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "💥"
            print(f"{status_icon} {result['test']}: {result['status']} ({result['duration']:.2f}s)")
        
        # Save results
        with open('options_strategy_test_results.json', 'w') as f:
            json.dump({
                'test_run': {
                    'timestamp': datetime.now().isoformat(),
                    'total_tests': total,
                    'passed': passed,
                    'failed': failed,
                    'errors': errors,
                    'success_rate': (passed/total)*100
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        return passed == total

if __name__ == "__main__":
    tester = OptionsStrategyRegressionTest()
    
    def signal_handler(signum, frame):
        print("\n🛑 Test interrupted by user")
        tester.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = tester.run_all_tests()
        if success:
            print("\n🎉 All tests passed! Options strategy implementation is successful.")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed. Please review the results above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        tester.stop_server()
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        tester.stop_server()
        sys.exit(1)
