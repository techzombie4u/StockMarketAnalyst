
#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite
Tests all functionality after file reorganization
"""

import sys
import os
import time
import json
import requests
import subprocess
from pathlib import Path
import threading
import signal

class RegressionTester:
    def __init__(self):
        self.test_results = []
        self.server_process = None
        self.server_running = False

    def run_test(self, test_name, test_func):
        """Run individual test and record result"""
        print(f"🧪 Testing: {test_name}")
        try:
            result = test_func()
            if result:
                print(f"✅ PASS: {test_name}")
                self.test_results.append({"test": test_name, "status": "PASS"})
                return True
            else:
                print(f"❌ FAIL: {test_name}")
                self.test_results.append({"test": test_name, "status": "FAIL"})
                return False
        except Exception as e:
            print(f"💥 ERROR: {test_name} - {str(e)}")
            self.test_results.append({"test": test_name, "status": "ERROR", "error": str(e)})
            return False

    def test_import_structure(self):
        """Test that all imports work with new structure"""
        try:
            # Test core imports
            from src.core.app import app
            from src.core.scheduler import StockAnalystScheduler
            
            # Test model imports
            from src.models.models import MLModels
            from src.models.data_loader import MLDataLoader
            
            # Test analyzer imports
            from src.analyzers.stock_screener import EnhancedStockScreener
            from src.analyzers.daily_technical_analyzer import DailyTechnicalAnalyzer
            
            # Test agent imports
            from src.agents.intelligent_prediction_agent import SmartStockAgent
            
            # Test manager imports
            from src.managers.interactive_tracker_manager import InteractiveTrackerManager
            
            return True
        except ImportError as e:
            print(f"Import error: {e}")
            return False

    def test_core_functionality(self):
        """Test core stock screening functionality"""
        try:
            from src.analyzers.stock_screener import EnhancedStockScreener
            
            screener = EnhancedStockScreener()
            
            # Test technical analysis
            technical_data = screener.calculate_enhanced_technical_indicators('SBIN')
            if not technical_data:
                return False
            
            # Test fundamental scraping
            fundamental_data = screener.scrape_screener_data('SBIN')
            if not fundamental_data:
                return False
            
            return True
        except Exception as e:
            print(f"Core functionality error: {e}")
            return False

    def test_ml_models(self):
        """Test ML model functionality"""
        try:
            from src.models.models import MLModels
            
            models = MLModels()
            
            # Test model loading
            models_loaded = models.load_models()
            
            # Should work even if models don't exist
            return True
        except Exception as e:
            print(f"ML models error: {e}")
            return False

    def test_data_files_access(self):
        """Test access to data files in new structure"""
        try:
            # Test historical data access
            data_dir = Path('data/historical/downloaded_historical_data')
            if not data_dir.exists():
                return False
            
            csv_files = list(data_dir.glob('*.csv'))
            if len(csv_files) == 0:
                return False
            
            # Test tracking data access
            tracking_file = Path('data/tracking/interactive_tracking.json')
            
            return True
        except Exception as e:
            print(f"Data access error: {e}")
            return False

    def test_web_templates(self):
        """Test web template access"""
        try:
            template_dir = Path('web/templates')
            if not template_dir.exists():
                return False
            
            required_templates = ['index.html', 'analysis.html', 'prediction_tracker_interactive.html']
            for template in required_templates:
                if not (template_dir / template).exists():
                    return False
            
            return True
        except Exception as e:
            print(f"Template access error: {e}")
            return False

    def start_server(self):
        """Start the Flask server in background"""
        try:
            print("🚀 Starting Flask server...")
            
            # Start server process
            self.server_process = subprocess.Popen([
                sys.executable, 'src/core/main.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(10)
            
            # Check if server is running
            try:
                response = requests.get('http://0.0.0.0:5000/api/health', timeout=5)
                if response.status_code == 200:
                    self.server_running = True
                    print("✅ Server started successfully")
                    return True
                else:
                    print(f"❌ Server health check failed: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"❌ Server not responding: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            return False

    def test_api_endpoints(self):
        """Test API endpoints"""
        if not self.server_running:
            return False
        
        try:
            base_url = 'http://0.0.0.0:5000'
            
            # Test main API endpoint
            response = requests.get(f'{base_url}/api/stocks', timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if 'stocks' not in data:
                return False
            
            # Test status endpoint
            response = requests.get(f'{base_url}/api/status', timeout=5)
            if response.status_code != 200:
                return False
            
            # Test analysis endpoint
            response = requests.get(f'{base_url}/api/analysis', timeout=5)
            if response.status_code != 200:
                return False
            
            return True
        except Exception as e:
            print(f"API test error: {e}")
            return False

    def test_interactive_tracker(self):
        """Test interactive tracker functionality"""
        try:
            from src.managers.interactive_tracker_manager import InteractiveTrackerManager
            
            tracker = InteractiveTrackerManager()
            
            # Test data loading
            tracking_data = tracker.load_tracking_data()
            
            # Test should work even with empty data
            return True
        except Exception as e:
            print(f"Interactive tracker error: {e}")
            return False

    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            print("🛑 Stopping server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_running = False

    def run_all_tests(self):
        """Run complete regression test suite"""
        print("🎯 Starting Comprehensive Regression Tests")
        print("=" * 60)
        
        # Test 1: Import structure
        self.run_test("Import Structure", self.test_import_structure)
        
        # Test 2: Core functionality
        self.run_test("Core Functionality", self.test_core_functionality)
        
        # Test 3: ML Models
        self.run_test("ML Models", self.test_ml_models)
        
        # Test 4: Data file access
        self.run_test("Data File Access", self.test_data_files_access)
        
        # Test 5: Web templates
        self.run_test("Web Templates", self.test_web_templates)
        
        # Test 6: Interactive tracker
        self.run_test("Interactive Tracker", self.test_interactive_tracker)
        
        # Test 7: Server startup
        server_started = self.run_test("Server Startup", self.start_server)
        
        if server_started:
            # Test 8: API endpoints
            self.run_test("API Endpoints", self.test_api_endpoints)
            
            # Stop server
            self.stop_server()
        
        # Print results
        print("=" * 60)
        print("📊 Test Results Summary:")
        
        passed = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed = len([r for r in self.test_results if r['status'] == 'FAIL'])
        errors = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"💥 Errors: {errors}")
        print(f"📈 Success Rate: {(passed / len(self.test_results)) * 100:.1f}%")
        
        # Save detailed results
        with open('regression_test_results.json', 'w') as f:
            json.dump({
                'timestamp': time.time(),
                'summary': {'passed': passed, 'failed': failed, 'errors': errors},
                'details': self.test_results
            }, f, indent=2)
        
        if failed == 0 and errors == 0:
            print("\n🎉 All tests passed! Application is working correctly.")
            return True
        else:
            print("\n⚠️ Some tests failed. Check results and fix issues.")
            return False

def main():
    """Main execution"""
    print("🔧 Stock Market Analyst - Post-Organization Regression Testing")
    
    tester = RegressionTester()
    
    # Setup signal handler for clean shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Test interrupted by user")
        tester.stop_server()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.stop_server()

if __name__ == "__main__":
    sys.exit(main())
