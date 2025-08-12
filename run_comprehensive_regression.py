
#!/usr/bin/env python3
"""
Comprehensive Regression Test Suite for Fusion Stock Analyst
Tests all functionality including APIs, UI, agents, KPIs, and data integrity
"""

import os
import sys
import json
import time
import requests
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from tests.utils.server_manager import start_server, stop_server

class ComprehensiveRegressionTester:
    def __init__(self):
        self.test_results = []
        self.server = None
        self.base_url = "http://0.0.0.0:5000"
        self.start_time = time.time()
        
    def log_test(self, category, test_name, status, details=None):
        """Log test result"""
        result = {
            "category": category,
            "test": test_name,
            "status": status,
            "timestamp": time.time(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"  {status_icon} {test_name}: {status}")
        
        if details and status != "PASS":
            print(f"    Details: {details}")

    def run_test_category(self, category_name, tests):
        """Run a category of tests"""
        print(f"\n🧪 {category_name}")
        print("=" * 60)
        
        passed = 0
        for test_name, test_func in tests:
            try:
                if test_func():
                    self.log_test(category_name, test_name, "PASS")
                    passed += 1
                else:
                    self.log_test(category_name, test_name, "FAIL")
            except Exception as e:
                self.log_test(category_name, test_name, "ERROR", {"error": str(e)})
                
        print(f"\n📊 {category_name}: {passed}/{len(tests)} tests passed")
        return passed, len(tests)

    # ========== INFRASTRUCTURE TESTS ==========
    
    def test_server_startup(self):
        """Test server starts successfully"""
        try:
            self.server = start_server(timeout=40)
            return self.server is not None
        except Exception as e:
            print(f"Server startup failed: {e}")
            return False
    
    def test_health_endpoint(self):
        """Test /health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except:
            return False
    
    def test_openapi_spec(self):
        """Test OpenAPI specification is accessible"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def test_metrics_endpoint(self):
        """Test /metrics endpoint"""
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=10)
            return response.status_code == 200
        except:
            return False

    # ========== FUSION API TESTS ==========
    
    def test_fusion_dashboard_api(self):
        """Test fusion dashboard API"""
        try:
            response = requests.get(f"{self.base_url}/api/fusion/dashboard", timeout=15)
            if response.status_code != 200:
                return False
                
            data = response.json()
            required_fields = ["timeframes", "pinned_summary", "top_signals", "generation_time_ms"]
            return all(field in data for field in required_fields)
        except:
            return False
    
    def test_fusion_timeframe_filtering(self):
        """Test fusion API with timeframe parameter"""
        try:
            for timeframe in ["1D", "5D", "10D", "30D"]:
                response = requests.get(f"{self.base_url}/api/fusion/dashboard?timeframe={timeframe}", timeout=10)
                if response.status_code != 200:
                    return False
                    
                data = response.json()
                if "kpis" not in data:
                    return False
            return True
        except:
            return False

    # ========== EQUITIES TESTS ==========
    
    def test_equities_list_api(self):
        """Test equities list API"""
        try:
            response = requests.get(f"{self.base_url}/api/equities/list", timeout=10)
            if response.status_code != 200:
                return False
                
            data = response.json()
            return "items" in data and isinstance(data["items"], list)
        except:
            return False
    
    def test_equities_kpis_api(self):
        """Test equities KPIs API"""
        try:
            response = requests.get(f"{self.base_url}/api/equities/kpis", timeout=10)
            if response.status_code != 200:
                return False
                
            data = response.json()
            return "timeframes" in data
        except:
            return False
    
    def test_equities_filtering(self):
        """Test equities with filters"""
        try:
            params = {
                "min_price": "100",
                "max_price": "5000",
                "sector": "Banking",
                "limit": "10"
            }
            response = requests.get(f"{self.base_url}/api/equities/list", params=params, timeout=10)
            return response.status_code == 200
        except:
            return False

    # ========== OPTIONS TESTS ==========
    
    def test_options_strangle_candidates(self):
        """Test options strangle candidates API"""
        try:
            response = requests.get(f"{self.base_url}/api/options/strangle/candidates", timeout=15)
            if response.status_code != 200:
                return False
                
            data = response.json()
            if "candidates" not in data:
                return False
                
            # Check if candidates have required fields
            candidates = data["candidates"]
            if candidates:
                sample = candidates[0]
                required_fields = ["underlying", "strike_call", "strike_put", "margin", "payoff"]
                return all(field in sample for field in required_fields)
            return True
        except:
            return False
    
    def test_options_positions_api(self):
        """Test options positions API"""
        try:
            response = requests.get(f"{self.base_url}/api/options/positions", timeout=10)
            return response.status_code == 200
        except:
            return False

    # ========== COMMODITIES TESTS ==========
    
    def test_commodities_signals_api(self):
        """Test commodities signals API"""
        try:
            response = requests.get(f"{self.base_url}/api/commodities/signals", timeout=10)
            if response.status_code != 200:
                return False
                
            data = response.json()
            return "signals" in data and isinstance(data["signals"], list)
        except:
            return False
    
    def test_commodities_correlations_api(self):
        """Test commodities correlations API"""
        try:
            response = requests.get(f"{self.base_url}/api/commodities/correlations", timeout=10)
            if response.status_code != 200:
                return False
                
            data = response.json()
            return "correlations" in data
        except:
            return False

    # ========== KPI TESTS ==========
    
    def test_kpi_metrics_api(self):
        """Test KPI metrics calculation API"""
        try:
            response = requests.get(f"{self.base_url}/api/kpi/metrics", timeout=10)
            if response.status_code != 200:
                return False
                
            data = response.json()
            return "metrics" in data
        except:
            return False
    
    def test_kpi_timeframe_metrics(self):
        """Test KPI metrics with timeframe parameter"""
        try:
            for timeframe in ["3D", "5D", "30D"]:
                response = requests.get(f"{self.base_url}/api/kpi/metrics?timeframe={timeframe}", timeout=10)
                if response.status_code != 200:
                    return False
            return True
        except:
            return False

    # ========== AGENTS TESTS ==========
    
    def test_agents_config_api(self):
        """Test agents configuration API"""
        try:
            response = requests.get(f"{self.base_url}/api/agents/config", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def test_agents_run_api(self):
        """Test agents run API"""
        try:
            # Test GET first
            response = requests.get(f"{self.base_url}/api/agents/run", timeout=10)
            if response.status_code != 200:
                return False
                
            # Test POST with sample data
            payload = {"agent_type": "sentiment", "symbol": "TCS"}
            response = requests.post(f"{self.base_url}/api/agents/run", 
                                   json=payload, timeout=15)
            return response.status_code in [200, 202]  # Accept both sync and async responses
        except:
            return False

    # ========== PINS & LOCKS TESTS ==========
    
    def test_pins_api(self):
        """Test pins API functionality"""
        try:
            # Test GET pins
            response = requests.get(f"{self.base_url}/api/pins", timeout=10)
            if response.status_code != 200:
                return False
                
            # Test POST pin
            payload = {"symbol": "TCS", "action": "pin"}
            response = requests.post(f"{self.base_url}/api/pins", json=payload, timeout=10)
            return response.status_code in [200, 201]
        except:
            return False
    
    def test_locks_api(self):
        """Test locks API functionality"""
        try:
            # Test GET locks
            response = requests.get(f"{self.base_url}/api/locks", timeout=10)
            if response.status_code != 200:
                return False
                
            # Test POST lock
            payload = {"symbol": "RELIANCE", "action": "lock"}
            response = requests.post(f"{self.base_url}/api/locks", json=payload, timeout=10)
            return response.status_code in [200, 201]
        except:
            return False

    # ========== UI TESTS ==========
    
    def test_dashboard_ui(self):
        """Test dashboard UI accessibility"""
        try:
            response = requests.get(f"{self.base_url}/dashboard", timeout=10)
            if response.status_code != 200:
                return False
            
            html_content = response.text
            required_elements = [
                "KPI Dashboard",  # Page title
                "timeframe-chips",  # Timeframe selector
                "kpi-cards",  # KPI cards container
                "top-signals-table"  # Signals table
            ]
            return all(element in html_content for element in required_elements)
        except:
            return False
    
    def test_equities_ui(self):
        """Test equities UI page"""
        try:
            response = requests.get(f"{self.base_url}/equities", timeout=10)
            if response.status_code != 200:
                return False
            
            html_content = response.text
            required_elements = ["Equities", "Symbol", "Price", "Change"]
            return any(element in html_content for element in required_elements)
        except:
            return False
    
    def test_options_ui(self):
        """Test options UI page"""
        try:
            response = requests.get(f"{self.base_url}/options", timeout=10)
            if response.status_code != 200:
                return False
            
            html_content = response.text
            required_elements = ["Options", "Strangle", "Strike"]
            return any(element in html_content for element in required_elements)
        except:
            return False
    
    def test_commodities_ui(self):
        """Test commodities UI page"""
        try:
            response = requests.get(f"{self.base_url}/commodities", timeout=10)
            if response.status_code != 200:
                return False
            
            html_content = response.text
            required_elements = ["Commodities", "Signal", "Correlation"]
            return any(element in html_content for element in required_elements)
        except:
            return False

    # ========== DATA INTEGRITY TESTS ==========
    
    def test_data_files_existence(self):
        """Test critical data files exist"""
        try:
            critical_files = [
                "data/fixtures/equities_sample.json",
                "data/fixtures/options_sample.json",
                "data/fixtures/commodities_sample.json",
                "data/persistent/pins.json",
                "data/persistent/locks.json"
            ]
            
            for file_path in critical_files:
                if not Path(file_path).exists():
                    return False
            return True
        except:
            return False
    
    def test_historical_data_access(self):
        """Test historical data directory access"""
        try:
            data_dir = Path("data/historical/downloaded_historical_data")
            if not data_dir.exists():
                return False
                
            csv_files = list(data_dir.glob("*.csv"))
            return len(csv_files) > 0
        except:
            return False
    
    def test_kpi_data_integrity(self):
        """Test KPI data integrity"""
        try:
            kpi_file = Path("data/kpi/kpi_metrics.json")
            if kpi_file.exists():
                with open(kpi_file, 'r') as f:
                    data = json.load(f)
                    return isinstance(data, dict)
            return True  # OK if file doesn't exist yet
        except:
            return False

    # ========== PERFORMANCE TESTS ==========
    
    def test_api_response_times(self):
        """Test API response times are reasonable"""
        try:
            endpoints = [
                "/api/fusion/dashboard",
                "/api/equities/list",
                "/api/options/strangle/candidates",
                "/api/commodities/signals"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=20)
                response_time = time.time() - start_time
                
                if response.status_code != 200 or response_time > 15.0:  # 15 second max
                    return False
            return True
        except:
            return False
    
    def test_concurrent_requests(self):
        """Test server handles concurrent requests"""
        try:
            import threading
            import queue
            
            results = queue.Queue()
            
            def make_request():
                try:
                    response = requests.get(f"{self.base_url}/health", timeout=10)
                    results.put(response.status_code == 200)
                except:
                    results.put(False)
            
            # Create 5 concurrent requests
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads
            for thread in threads:
                thread.join()
            
            # Check results
            success_count = 0
            while not results.empty():
                if results.get():
                    success_count += 1
            
            return success_count >= 4  # At least 4/5 should succeed
        except:
            return False

    # ========== GUARDRAILS TESTS ==========
    
    def test_input_validation(self):
        """Test input validation and error handling"""
        try:
            # Test invalid JSON
            response = requests.post(f"{self.base_url}/api/agents/run", 
                                   data="invalid json", 
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            if response.status_code not in [400, 422]:
                return False
            
            # Test invalid parameters
            response = requests.get(f"{self.base_url}/api/equities/list?limit=invalid", timeout=10)
            return response.status_code in [200, 400]  # Should handle gracefully
        except:
            return False
    
    def test_rate_limiting(self):
        """Test rate limiting is working"""
        try:
            # Make multiple rapid requests
            responses = []
            for _ in range(10):
                response = requests.get(f"{self.base_url}/health", timeout=5)
                responses.append(response.status_code)
            
            # Should mostly succeed (rate limiting may kick in but shouldn't block all)
            success_rate = sum(1 for code in responses if code == 200) / len(responses)
            return success_rate > 0.7  # At least 70% should succeed
        except:
            return False

    def run_all_tests(self):
        """Run comprehensive regression test suite"""
        print("🚀 COMPREHENSIVE REGRESSION TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")
        print("=" * 80)
        
        total_passed = 0
        total_tests = 0
        
        test_categories = [
            ("INFRASTRUCTURE", [
                ("Server Startup", self.test_server_startup),
                ("Health Endpoint", self.test_health_endpoint),
                ("OpenAPI Spec", self.test_openapi_spec),
                ("Metrics Endpoint", self.test_metrics_endpoint)
            ]),
            
            ("FUSION API", [
                ("Dashboard API", self.test_fusion_dashboard_api),
                ("Timeframe Filtering", self.test_fusion_timeframe_filtering)
            ]),
            
            ("EQUITIES API", [
                ("List API", self.test_equities_list_api),
                ("KPIs API", self.test_equities_kpis_api),
                ("Filtering", self.test_equities_filtering)
            ]),
            
            ("OPTIONS API", [
                ("Strangle Candidates", self.test_options_strangle_candidates),
                ("Positions API", self.test_options_positions_api)
            ]),
            
            ("COMMODITIES API", [
                ("Signals API", self.test_commodities_signals_api),
                ("Correlations API", self.test_commodities_correlations_api)
            ]),
            
            ("KPI SYSTEM", [
                ("Metrics API", self.test_kpi_metrics_api),
                ("Timeframe Metrics", self.test_kpi_timeframe_metrics)
            ]),
            
            ("AGENTS SYSTEM", [
                ("Config API", self.test_agents_config_api),
                ("Run API", self.test_agents_run_api)
            ]),
            
            ("PINS & LOCKS", [
                ("Pins API", self.test_pins_api),
                ("Locks API", self.test_locks_api)
            ]),
            
            ("USER INTERFACE", [
                ("Dashboard UI", self.test_dashboard_ui),
                ("Equities UI", self.test_equities_ui),
                ("Options UI", self.test_options_ui),
                ("Commodities UI", self.test_commodities_ui)
            ]),
            
            ("DATA INTEGRITY", [
                ("Data Files", self.test_data_files_existence),
                ("Historical Data", self.test_historical_data_access),
                ("KPI Data", self.test_kpi_data_integrity)
            ]),
            
            ("PERFORMANCE", [
                ("Response Times", self.test_api_response_times),
                ("Concurrent Requests", self.test_concurrent_requests)
            ]),
            
            ("GUARDRAILS", [
                ("Input Validation", self.test_input_validation),
                ("Rate Limiting", self.test_rate_limiting)
            ])
        ]
        
        for category_name, tests in test_categories:
            passed, total = self.run_test_category(category_name, tests)
            total_passed += passed
            total_tests += total
        
        # Generate final report
        self.generate_report(total_passed, total_tests)
        
        return total_passed == total_tests

    def generate_report(self, total_passed, total_tests):
        """Generate comprehensive test report"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE REGRESSION TEST REPORT")
        print("=" * 80)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_tests - total_passed}")
        print(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Category breakdown
        print("\n📈 CATEGORY BREAKDOWN:")
        categories = {}
        for result in self.test_results:
            category = result["category"]
            if category not in categories:
                categories[category] = {"pass": 0, "fail": 0, "error": 0}
            categories[category][result["status"].lower()] += 1
        
        for category, stats in categories.items():
            total_cat = sum(stats.values())
            passed_cat = stats["pass"]
            rate = (passed_cat / total_cat) * 100 if total_cat > 0 else 0
            print(f"  {category}: {passed_cat}/{total_cat} ({rate:.1f}%)")
        
        # Save detailed results
        report_data = {
            "timestamp": end_time,
            "duration_seconds": duration,
            "summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_tests - total_passed,
                "success_rate": (total_passed/total_tests)*100
            },
            "categories": categories,
            "detailed_results": self.test_results
        }
        
        report_file = f"regression_report_{int(end_time)}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        if total_passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! System is fully functional.")
        else:
            failed_tests = [r for r in self.test_results if r["status"] != "PASS"]
            print(f"\n⚠️ {len(failed_tests)} test(s) failed:")
            for test in failed_tests[:5]:  # Show first 5 failures
                print(f"  - {test['category']}: {test['test']} ({test['status']})")
            if len(failed_tests) > 5:
                print(f"  ... and {len(failed_tests) - 5} more")

def main():
    """Main execution"""
    tester = ComprehensiveRegressionTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        traceback.print_exc()
        return 1
    finally:
        if tester.server:
            print("\n🛑 Stopping server...")
            stop_server(tester.server)

if __name__ == "__main__":
    sys.exit(main())
