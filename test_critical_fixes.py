
#!/usr/bin/env python3
"""
Critical Fixes Verification Test
Tests all the major issues found in the logs
"""

import json
import os
import requests
import time
import traceback
from datetime import datetime
import pytz

class CriticalFixTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.IST = pytz.timezone('Asia/Kolkata')

    def log_result(self, test_name, success, details=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        
        if success:
            self.passed += 1
        else:
            self.failed += 1

    def test_json_corruption_handling(self):
        """Test JSON corruption handling"""
        print("\n🧪 Testing JSON Corruption Handling...")
        
        # Backup existing file
        backup_data = None
        if os.path.exists('top10.json'):
            with open('top10.json', 'r') as f:
                backup_data = f.read()
        
        try:
            # Test empty file
            with open('top10.json', 'w') as f:
                f.write('')
            
            response = requests.get('http://localhost:5000/api/stocks', timeout=5)
            self.log_result("Empty JSON File Handling", 
                          response.status_code == 200, 
                          f"Status: {response.status_code}")
            
            # Test corrupted JSON
            with open('top10.json', 'w') as f:
                f.write('{"invalid": json}')
            
            response = requests.get('http://localhost:5000/api/stocks', timeout=5)
            self.log_result("Corrupted JSON Handling", 
                          response.status_code == 200, 
                          f"Status: {response.status_code}")
            
            # Test null values in stock data
            test_data = {
                'timestamp': datetime.now(self.IST).isoformat(),
                'last_updated': 'Test',
                'status': 'test',
                'stocks': [{
                    'symbol': 'TEST',
                    'score': None,
                    'current_price': 'null',
                    'confidence': 'undefined',
                    'pe_ratio': '',
                    'pred_5d': None
                }]
            }
            
            with open('top10.json', 'w') as f:
                json.dump(test_data, f)
            
            response = requests.get('http://localhost:5000/api/stocks', timeout=5)
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('stocks', [])
                if stocks:
                    stock = stocks[0]
                    # Check if None values were properly handled
                    score_ok = isinstance(stock.get('score'), (int, float))
                    price_ok = isinstance(stock.get('current_price'), (int, float))
                    self.log_result("None Value Sanitization", 
                                  score_ok and price_ok,
                                  f"Score: {stock.get('score')}, Price: {stock.get('current_price')}")
                else:
                    self.log_result("None Value Sanitization", False, "No stocks returned")
            else:
                self.log_result("None Value Sanitization", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("JSON Corruption Test", False, f"Error: {str(e)}")
        finally:
            # Restore backup
            if backup_data:
                with open('top10.json', 'w') as f:
                    f.write(backup_data)

    def test_datetime_handling(self):
        """Test datetime handling fixes"""
        print("\n🧪 Testing DateTime Handling...")
        
        try:
            # Test API status endpoint (uses datetime)
            response = requests.get('http://localhost:5000/api/status', timeout=5)
            self.log_result("API Status DateTime", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                timestamp_ok = 'timestamp' in data
                self.log_result("Status Timestamp Generation", 
                              timestamp_ok,
                              f"Has timestamp: {timestamp_ok}")
                              
        except Exception as e:
            self.log_result("DateTime Handling", False, f"Error: {str(e)}")

    def test_api_performance(self):
        """Test API response performance"""
        print("\n🧪 Testing API Performance...")
        
        try:
            start_time = time.time()
            response = requests.get('http://localhost:5000/api/stocks', timeout=10)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            self.log_result("API Response Time", 
                          response_time < 5.0,  # Should respond within 5 seconds
                          f"Response time: {response_time:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                stocks = data.get('stocks', [])
                self.log_result("Stock Data Availability", 
                              len(stocks) > 0,
                              f"Found {len(stocks)} stocks")
        except Exception as e:
            self.log_result("API Performance", False, f"Error: {str(e)}")

    def test_error_recovery(self):
        """Test error recovery mechanisms"""
        print("\n🧪 Testing Error Recovery...")
        
        try:
            # Test manual refresh
            response = requests.post('http://localhost:5000/api/run-now', timeout=30)
            self.log_result("Manual Refresh", 
                          response.status_code == 200,
                          f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                self.log_result("Manual Refresh Success", 
                              success,
                              f"Success: {success}")
                              
        except Exception as e:
            self.log_result("Error Recovery", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all critical fix tests"""
        print("🚀 Starting Critical Fixes Verification...")
        print("=" * 60)
        
        # Wait for server to be ready
        print("⏳ Waiting for server to be ready...")
        time.sleep(3)
        
        self.test_json_corruption_handling()
        self.test_datetime_handling()
        self.test_api_performance()
        self.test_error_recovery()
        
        print("\n" + "=" * 60)
        print("📊 CRITICAL FIXES TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        if self.failed == 0:
            print("\n🎉 ALL CRITICAL FIXES VERIFIED!")
            print("💚 The application should now be stable and performant.")
            return True
        else:
            print(f"\n⚠️ {self.failed} issues still remain.")
            return False

if __name__ == "__main__":
    tester = CriticalFixTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All critical issues have been resolved!")
    else:
        print("\n❌ Some issues require additional attention.")
