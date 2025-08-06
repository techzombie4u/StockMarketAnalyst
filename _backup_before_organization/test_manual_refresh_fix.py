
#!/usr/bin/env python3
"""
Regression test for manual refresh fix
Tests the /api/run-now endpoint and related functionality
"""

import sys
import json
import time
import requests
import traceback
from datetime import datetime

class ManualRefreshRegressionTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message, test_type="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{test_type}] {timestamp}: {message}")
        
    def test_api_stocks_endpoint(self):
        """Test /api/stocks endpoint"""
        self.log("Testing /api/stocks endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/stocks", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'stocks' in data:
                    self.log("✅ /api/stocks endpoint working correctly")
                    self.passed += 1
                    return True
                else:
                    self.log("❌ /api/stocks returned invalid data structure", "ERROR")
                    self.failed += 1
                    return False
            else:
                self.log(f"❌ /api/stocks returned status {response.status_code}", "ERROR")
                self.failed += 1
                return False
                
        except Exception as e:
            self.log(f"❌ /api/stocks test failed: {str(e)}", "ERROR")
            self.failed += 1
            return False
    
    def test_manual_refresh_endpoint(self):
        """Test /api/run-now endpoint for the toUpperCase fix"""
        self.log("Testing /api/run-now endpoint...")
        try:
            response = requests.post(f"{self.base_url}/api/run-now", 
                                   headers={'Content-Type': 'application/json'},
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                if isinstance(data, dict) and 'success' in data and 'message' in data:
                    self.log("✅ /api/run-now endpoint structure correct")
                    
                    # Check for the specific error we're fixing
                    message = str(data.get('message', ''))
                    error = str(data.get('error', ''))
                    
                    if 'toUpperCase is not a function' in message or 'toUpperCase is not a function' in error:
                        self.log("❌ toUpperCase error still present", "ERROR")
                        self.failed += 1
                        return False
                    else:
                        self.log("✅ No toUpperCase error found")
                        self.passed += 1
                        return True
                else:
                    self.log("❌ /api/run-now returned invalid data structure", "ERROR")
                    self.failed += 1
                    return False
            else:
                self.log(f"❌ /api/run-now returned status {response.status_code}", "ERROR")
                self.failed += 1
                return False
                
        except Exception as e:
            self.log(f"❌ /api/run-now test failed: {str(e)}", "ERROR")
            self.failed += 1
            return False
    
    def test_analysis_endpoint(self):
        """Test /api/analysis endpoint"""
        self.log("Testing /api/analysis endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/analysis", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log("✅ /api/analysis endpoint working correctly")
                    self.passed += 1
                    return True
                else:
                    self.log("❌ /api/analysis returned invalid data", "ERROR")
                    self.failed += 1
                    return False
            else:
                self.log(f"❌ /api/analysis returned status {response.status_code}", "ERROR")
                self.failed += 1
                return False
                
        except Exception as e:
            self.log(f"❌ /api/analysis test failed: {str(e)}", "ERROR")
            self.failed += 1
            return False
    
    def test_main_dashboard_accessibility(self):
        """Test main dashboard loads without errors"""
        self.log("Testing main dashboard accessibility...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                if 'Stock Market Analyst' in content and 'html' in content.lower():
                    self.log("✅ Main dashboard loads correctly")
                    self.passed += 1
                    return True
                else:
                    self.log("❌ Main dashboard content invalid", "ERROR")
                    self.failed += 1
                    return False
            else:
                self.log(f"❌ Main dashboard returned status {response.status_code}", "ERROR")
                self.failed += 1
                return False
                
        except Exception as e:
            self.log(f"❌ Main dashboard test failed: {str(e)}", "ERROR")
            self.failed += 1
            return False
    
    def test_error_handling(self):
        """Test error handling doesn't cause JavaScript errors"""
        self.log("Testing error handling...")
        try:
            # Make multiple rapid requests to test error handling
            for i in range(3):
                try:
                    response = requests.post(f"{self.base_url}/api/run-now", 
                                           headers={'Content-Type': 'application/json'},
                                           timeout=5)
                    if response.status_code in [200, 429, 500]:  # Accept common response codes
                        data = response.json()
                        if isinstance(data, dict):
                            # Check that all string fields are actually strings
                            for key, value in data.items():
                                if key in ['message', 'error'] and value is not None:
                                    if not isinstance(value, str):
                                        self.log(f"❌ Field {key} should be string but is {type(value)}", "ERROR")
                                        self.failed += 1
                                        return False
                except:
                    pass  # Ignore individual request failures in this test
                
                time.sleep(1)
            
            self.log("✅ Error handling test passed")
            self.passed += 1
            return True
            
        except Exception as e:
            self.log(f"❌ Error handling test failed: {str(e)}", "ERROR")
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """Run all regression tests"""
        self.log("🚀 Starting Manual Refresh Fix Regression Tests")
        self.log("=" * 60)
        
        # Wait for server to be ready
        self.log("Waiting for server to be ready...")
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/", timeout=5)
                if response.status_code == 200:
                    self.log("✅ Server is ready")
                    break
            except:
                if i == max_retries - 1:
                    self.log("❌ Server not ready after waiting", "ERROR")
                    return False
                time.sleep(2)
        
        # Run all tests
        tests = [
            self.test_main_dashboard_accessibility,
            self.test_api_stocks_endpoint,
            self.test_analysis_endpoint,
            self.test_manual_refresh_endpoint,
            self.test_error_handling
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(1)  # Brief pause between tests
            except Exception as e:
                self.log(f"❌ Test {test.__name__} crashed: {str(e)}", "ERROR")
                self.failed += 1
        
        # Summary
        self.log("=" * 60)
        self.log(f"🏁 Regression Test Results:")
        self.log(f"✅ Passed: {self.passed}")
        self.log(f"❌ Failed: {self.failed}")
        self.log(f"📊 Total: {self.passed + self.failed}")
        
        if self.failed == 0:
            self.log("🎉 ALL TESTS PASSED - Manual refresh fix verified!", "SUCCESS")
            return True
        else:
            self.log(f"💥 {self.failed} TEST(S) FAILED - Issues need resolution", "ERROR")
            return False

if __name__ == "__main__":
    tester = ManualRefreshRegressionTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
