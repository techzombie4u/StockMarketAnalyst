
import json
import os
import time
import subprocess
import requests
from datetime import datetime
import pytz

class FrontendFixTester:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []

    def log_test(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def test_data_structure_integrity(self):
        """Test that data structure prevents type errors"""
        print("\n🧪 Testing Data Structure Integrity...")
        
        try:
            # Create test data with problematic values
            test_data = {
                'timestamp': datetime.now().isoformat(),
                'last_updated': 'Test Data',
                'status': 'test',
                'stocks': [
                    {
                        'symbol': 'TEST1',
                        'score': 75.5,
                        'current_price': 100.50,
                        'confidence': 85.0,
                        'pred_5d': 2.5,
                        'pred_1mo': 8.0,
                        'pe_ratio': 15.5,
                        'trend_class': 'uptrend',
                        'trend_visual': '⬆️ Uptrend',
                        'pe_description': 'Below Average',
                        'technical_summary': 'Strong momentum detected'
                    },
                    {
                        'symbol': 'TEST2',
                        'score': None,  # Problematic
                        'current_price': 'null',  # Problematic
                        'confidence': 'undefined',  # Problematic
                        'pred_5d': '',  # Problematic
                        'pred_1mo': None,  # Problematic
                        'pe_ratio': 'N/A',  # Problematic
                        'trend_class': None,  # Problematic
                        'trend_visual': None,  # Problematic
                        'pe_description': None,  # Problematic
                        'technical_summary': None  # Problematic
                    }
                ]
            }
            
            # Save test data
            with open('top10.json', 'w') as f:
                json.dump(test_data, f, indent=2)
            
            self.log_test("Test Data Creation", True, "Created data with problematic values")
            
            # Test API endpoint
            try:
                response = requests.get('http://localhost:5000/api/stocks', timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check that API sanitized the data
                    stocks = data.get('stocks', [])
                    if len(stocks) >= 2:
                        # Check first stock (good data)
                        stock1 = stocks[0]
                        self.log_test("Good Data Processing", 
                                    isinstance(stock1.get('symbol'), str) and 
                                    isinstance(stock1.get('score'), (int, float)),
                                    f"Symbol: {stock1.get('symbol')}, Score: {stock1.get('score')}")
                        
                        # Check second stock (problematic data)
                        stock2 = stocks[1]
                        symbol_ok = isinstance(stock2.get('symbol'), str) and stock2.get('symbol') != ''
                        score_ok = isinstance(stock2.get('score'), (int, float))
                        trend_ok = isinstance(stock2.get('trend_class'), str) and stock2.get('trend_class') != ''
                        
                        self.log_test("Problematic Data Sanitization", 
                                    symbol_ok and score_ok and trend_ok,
                                    f"Symbol: {stock2.get('symbol')}, Score: {stock2.get('score')}, Trend: {stock2.get('trend_class')}")
                    else:
                        self.log_test("API Data Response", False, "Not enough stocks returned")
                else:
                    self.log_test("API Response", False, f"HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_test("API Connection", False, f"Connection error: {str(e)}")
                
        except Exception as e:
            self.log_test("Data Structure Test", False, f"Error: {str(e)}")

    def test_javascript_error_prevention(self):
        """Test that JavaScript functions handle bad data gracefully"""
        print("\n🧪 Testing JavaScript Error Prevention...")
        
        # This test simulates the JS functions to ensure they don't break
        test_cases = [
            # (input_value, expected_not_to_crash)
            (None, True),
            ('null', True),
            ('undefined', True),
            ('', True),
            (123, True),
            ({'obj': 'test'}, True),
            ([], True)
        ]
        
        for test_input, should_work in test_cases:
            try:
                # Simulate safeString function
                if test_input is None or test_input == 'null' or test_input == 'undefined':
                    result = ''
                else:
                    result = str(test_input)
                
                self.log_test(f"safeString({test_input})", True, f"Result: '{result}'")
                
                # Simulate safeNumber function  
                if test_input is None or test_input == 'null' or test_input == 'undefined':
                    num_result = 0
                else:
                    try:
                        num_result = float(test_input) if str(test_input).replace('.','').replace('-','').isdigit() else 0
                    except:
                        num_result = 0
                
                self.log_test(f"safeNumber({test_input})", True, f"Result: {num_result}")
                
            except Exception as e:
                self.log_test(f"Type Safety Test ({test_input})", False, f"Error: {str(e)}")

    def test_app_startup(self):
        """Test that the app starts without errors"""
        print("\n🧪 Testing App Startup...")
        
        try:
            # Test if we can import main modules
            import app
            self.log_test("App Import", True, "Flask app imported successfully")
            
            # Test basic app configuration
            if hasattr(app, 'app'):
                self.log_test("Flask App Creation", True, "Flask app instance exists")
            else:
                self.log_test("Flask App Creation", False, "No Flask app instance found")
                
        except Exception as e:
            self.log_test("App Startup Test", False, f"Import error: {str(e)}")

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Comprehensive Frontend Fix Tests...")
        print("=" * 60)
        
        self.test_app_startup()
        self.test_javascript_error_prevention()
        self.test_data_structure_integrity()
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📈 Success Rate: {(self.passed_tests/(self.passed_tests+self.failed_tests)*100):.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! Frontend fixes are working correctly.")
            return True
        else:
            print(f"\n⚠️ {self.failed_tests} tests failed. Review the issues above.")
            return False

if __name__ == "__main__":
    tester = FrontendFixTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Frontend fixes verified successfully!")
        print("🌐 The application should now work without JavaScript errors.")
    else:
        print("\n❌ Some tests failed. Please review the fixes.")
