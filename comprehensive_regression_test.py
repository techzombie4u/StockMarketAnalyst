
#!/usr/bin/env python3
"""
Comprehensive Regression Test for Stock Market Analyst
Tests all critical functionality and potential error scenarios
"""

import os
import sys
import json
import requests
import time
import logging
from datetime import datetime
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveRegressionTest:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': []
        }
        
    def log_test(self, test_name, passed, message=""):
        self.test_results['total_tests'] += 1
        if passed:
            self.test_results['passed_tests'] += 1
            print(f"✅ PASS {test_name}")
        else:
            self.test_results['failed_tests'] += 1
            self.test_results['errors'].append(f"{test_name}: {message}")
            print(f"❌ FAIL {test_name}: {message}")
        
        if message:
            logger.info(f"{test_name}: {message}")

    def wait_for_server(self, timeout=30):
        """Wait for server to be ready"""
        print("🔄 Waiting for server to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/api/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is ready")
                    return True
            except:
                time.sleep(2)
                
        print("❌ Server failed to start within timeout")
        return False

    def test_core_modules(self):
        """Test core module imports and initialization"""
        print("\n📋 Running Core Modules Test...")
        print("-" * 40)
        
        try:
            # Test stock screener import
            from stock_screener import EnhancedStockScreener
            screener = EnhancedStockScreener()
            self.log_test("Stock screener imported and initialized", True)
            
            # Test scheduler import
            from scheduler import StockAnalystScheduler
            scheduler = StockAnalystScheduler()
            self.log_test("Scheduler imported and initialized", True)
            
            # Test daily technical analyzer
            from daily_technical_analyzer import DailyTechnicalAnalyzer
            analyzer = DailyTechnicalAnalyzer()
            self.log_test("Daily technical analyzer imported and initialized", True)
            
            # Test Flask app import
            from app import app
            self.log_test("Flask app imported successfully", True)
            
            self.log_test("Core Modules Test", True)
            
        except Exception as e:
            self.log_test("Core Modules Test", False, str(e))

    def test_data_processing(self):
        """Test data processing capabilities"""
        print("\n📋 Running Data Processing Test...")
        print("-" * 40)
        
        try:
            from stock_screener import EnhancedStockScreener
            from daily_technical_analyzer import DailyTechnicalAnalyzer
            
            # Test technical analysis
            analyzer = DailyTechnicalAnalyzer()
            screener = EnhancedStockScreener()
            
            # Test with a known stock
            technical_data = analyzer.get_daily_ohlc_technical_analysis('RELIANCE')
            if technical_data and 'current_price' in technical_data:
                self.log_test("Technical indicators working for RELIANCE", True, 
                            f"Current price: {technical_data['current_price']}")
            else:
                self.log_test("Technical indicators working for RELIANCE", False, "No technical data")
            
            # Test fundamental data
            fundamental_data = screener.scrape_screener_data('RELIANCE')
            if fundamental_data and 'pe_ratio' in fundamental_data:
                self.log_test("Fundamental data working for RELIANCE", True,
                            f"PE ratio: {fundamental_data['pe_ratio']}")
            else:
                self.log_test("Fundamental data working for RELIANCE", False, "No fundamental data")
                
            self.log_test("Data Processing Test", True)
            
        except Exception as e:
            self.log_test("Data Processing Test", False, str(e))

    def test_scoring_algorithm(self):
        """Test scoring algorithm"""
        print("\n📋 Running Scoring Algorithm Test...")
        print("-" * 40)
        
        try:
            from stock_screener import EnhancedStockScreener
            screener = EnhancedStockScreener()
            
            # Test scoring with known stocks
            test_stocks = ['RELIANCE', 'TCS']
            stocks_data = {}
            
            for symbol in test_stocks:
                fundamentals = screener.scrape_screener_data(symbol)
                technical = screener.calculate_enhanced_technical_indicators(symbol)
                if fundamentals or technical:
                    stocks_data[symbol] = {
                        'fundamentals': fundamentals,
                        'technical': technical
                    }
            
            if stocks_data:
                scored_stocks = screener.enhanced_score_and_rank(stocks_data)
                if scored_stocks and len(scored_stocks) > 0:
                    for stock in scored_stocks:
                        score = stock.get('score', 0)
                        symbol = stock.get('symbol', 'Unknown')
                        self.log_test(f"Scoring works for {symbol}", True, f"{score} points")
                    self.log_test("Scoring algorithm functional", True)
                else:
                    self.log_test("Scoring algorithm functional", False, "No scored results")
            else:
                self.log_test("Scoring algorithm functional", False, "No test data available")
                
            self.log_test("Scoring Algorithm Test", True)
            
        except Exception as e:
            self.log_test("Scoring Algorithm Test", False, str(e))

    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n📋 Running API Endpoints Test...")
        print("-" * 40)
        
        try:
            # Test dashboard endpoint
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                self.log_test("Dashboard endpoint (/) working", True)
            else:
                self.log_test("Dashboard endpoint (/) working", False, f"Status: {response.status_code}")
            
            # Test stocks API endpoint
            response = requests.get(f"{self.base_url}/api/stocks", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                stock_count = len(data.get('stocks', []))
                self.log_test("Stocks API endpoint (/api/stocks) working", True,
                            f"Status: {status}, Stocks count: {stock_count}")
            else:
                self.log_test("Stocks API endpoint (/api/stocks) working", False, 
                            f"Status: {response.status_code}")
            
            # Test status API endpoint
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            if response.status_code == 200:
                self.log_test("Status API endpoint (/api/status) working", True)
            else:
                self.log_test("Status API endpoint (/api/status) working", False,
                            f"Status: {response.status_code}")
                
            self.log_test("API Endpoints Test", True)
            
        except Exception as e:
            self.log_test("API Endpoints Test", False, str(e))

    def test_data_structure_validation(self):
        """Test data structure validation and error handling"""
        print("\n📋 Running Data Structure Validation Test...")
        print("-" * 40)
        
        try:
            # Test with API response
            response = requests.get(f"{self.base_url}/api/stocks", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields in response
                required_fields = ['status', 'stocks', 'timestamp']
                for field in required_fields:
                    if field in data:
                        self.log_test(f"API response has {field} field", True)
                    else:
                        self.log_test(f"API response has {field} field", False)
                
                # Check stock data structure
                stocks = data.get('stocks', [])
                if stocks and len(stocks) > 0:
                    sample_stock = stocks[0]
                    required_stock_fields = ['symbol', 'score', 'current_price', 'confidence']
                    
                    for field in required_stock_fields:
                        if field in sample_stock:
                            field_type = type(sample_stock[field]).__name__
                            self.log_test(f"Stock has {field} field ({field_type})", True)
                        else:
                            self.log_test(f"Stock has {field} field", False)
                            
                    # Check data types
                    numeric_fields = ['score', 'current_price', 'confidence', 'pred_5d', 'pred_1mo']
                    for field in numeric_fields:
                        if field in sample_stock:
                            value = sample_stock[field]
                            if isinstance(value, (int, float)):
                                self.log_test(f"Stock {field} is numeric", True, f"Value: {value}")
                            else:
                                self.log_test(f"Stock {field} is numeric", False, f"Type: {type(value)}")
                
                self.log_test("Data Structure Validation Test", True)
            else:
                self.log_test("Data Structure Validation Test", False, "API not accessible")
                
        except Exception as e:
            self.log_test("Data Structure Validation Test", False, str(e))

    def test_manual_refresh(self):
        """Test manual refresh functionality"""
        print("\n📋 Running Manual Refresh Test...")
        print("-" * 40)
        
        try:
            # Test manual refresh endpoint
            response = requests.post(f"{self.base_url}/api/run-now", timeout=60)
            if response.status_code == 200:
                data = response.json()
                success = data.get('success', False)
                message = data.get('message', 'Unknown')
                
                if success:
                    self.log_test("Manual refresh successful", True, message)
                    
                    # Wait a bit and check if data updated
                    time.sleep(3)
                    stocks_response = requests.get(f"{self.base_url}/api/stocks", timeout=10)
                    if stocks_response.status_code == 200:
                        stocks_data = stocks_response.json()
                        stock_count = len(stocks_data.get('stocks', []))
                        self.log_test("Data available after refresh", stock_count > 0, 
                                    f"Stock count: {stock_count}")
                else:
                    self.log_test("Manual refresh successful", False, message)
            else:
                self.log_test("Manual refresh successful", False, f"HTTP {response.status_code}")
                
            self.log_test("Manual Refresh Test", True)
            
        except Exception as e:
            self.log_test("Manual Refresh Test", False, str(e))

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n📋 Running Error Handling Test...")
        print("-" * 40)
        
        try:
            # Test with invalid endpoint
            response = requests.get(f"{self.base_url}/api/invalid", timeout=10)
            if response.status_code == 404:
                self.log_test("Invalid endpoint returns 404", True)
            else:
                self.log_test("Invalid endpoint returns 404", False, f"Got {response.status_code}")
            
            # Test data file corruption handling
            if os.path.exists('top10.json'):
                # Backup original file
                with open('top10.json', 'r') as f:
                    original_data = f.read()
                
                # Create corrupted file
                with open('top10.json', 'w') as f:
                    f.write("invalid json content")
                
                # Test API response with corrupted data
                response = requests.get(f"{self.base_url}/api/stocks", timeout=10)
                if response.status_code == 200:
                    self.log_test("Handles corrupted data file", True, "API still responds")
                else:
                    self.log_test("Handles corrupted data file", False, f"API failed: {response.status_code}")
                
                # Restore original file
                with open('top10.json', 'w') as f:
                    f.write(original_data)
            
            self.log_test("Error Handling Test", True)
            
        except Exception as e:
            self.log_test("Error Handling Test", False, str(e))

    def test_frontend_functionality(self):
        """Test frontend functionality through API calls"""
        print("\n📋 Running Frontend Functionality Test...")
        print("-" * 40)
        
        try:
            # Test main dashboard
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Check for critical elements
                critical_elements = [
                    'refreshData',  # JavaScript function
                    'stock-table',  # Table structure
                    'api/stocks',   # API endpoint reference
                    'loadStocks'    # Load function
                ]
                
                for element in critical_elements:
                    if element in content:
                        self.log_test(f"Frontend has {element}", True)
                    else:
                        self.log_test(f"Frontend has {element}", False)
            else:
                self.log_test("Frontend accessible", False, f"Status: {response.status_code}")
                
            self.log_test("Frontend Functionality Test", True)
            
        except Exception as e:
            self.log_test("Frontend Functionality Test", False, str(e))

    def run_all_tests(self):
        """Run all regression tests"""
        print("🚀 Starting Comprehensive Regression Test")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Wait for server
        if not self.wait_for_server():
            print("❌ Server not ready, cannot run tests")
            return False
        
        # Run all test suites
        test_suites = [
            self.test_core_modules,
            self.test_data_processing,
            self.test_scoring_algorithm,
            self.test_api_endpoints,
            self.test_data_structure_validation,
            self.test_manual_refresh,
            self.test_error_handling,
            self.test_frontend_functionality
        ]
        
        for test_suite in test_suites:
            try:
                test_suite()
            except Exception as e:
                suite_name = test_suite.__name__.replace('_', ' ').title()
                self.log_test(suite_name, False, f"Test suite failed: {str(e)}")
        
        # Print summary
        self.print_summary()
        
        return self.test_results['failed_tests'] == 0

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 REGRESSION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.test_results['total_tests']}")
        print(f"Passed: {self.test_results['passed_tests']}")
        print(f"Failed: {self.test_results['failed_tests']}")
        
        if self.test_results['total_tests'] > 0:
            success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print()
        
        # Print individual test results
        for suite_name in ['Core Modules', 'Data Processing', 'Scoring Algorithm', 
                          'API Endpoints', 'Data Structure Validation', 'Manual Refresh',
                          'Error Handling', 'Frontend Functionality']:
            if any(suite_name in test for test in self.test_results['errors']):
                print(f"❌ FAIL {suite_name}")
            else:
                print(f"✅ PASS {suite_name}")
        
        print("=" * 60)
        
        if self.test_results['failed_tests'] == 0:
            print("🎉 ALL TESTS PASSED! Application is functioning correctly.")
        else:
            print("⚠️ SOME TESTS FAILED. Review errors above.")
            print("\nErrors:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    tester = ComprehensiveRegressionTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
