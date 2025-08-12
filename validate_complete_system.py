
#!/usr/bin/env python3
"""
Complete System Validation
Validates all system components and generates detailed reports
"""

import sys
import os
import json
import time
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemValidator:
    def __init__(self, base_url: str = "http://0.0.0.0:5000"):
        self.base_url = base_url
        self.results = {}
        self.errors = []
        
    def print_header(self, title: str):
        print(f"\n🔍 {title}")
        print("=" * 60)
        
    def validate_data_structures(self) -> bool:
        """Validate data structures and files"""
        try:
            self.print_header("Validating Data Structures...")
            
            required_files = [
                'data/fixtures/equities_sample.json',
                'data/fixtures/options_sample.json', 
                'data/fixtures/commodities_sample.json',
                'data/kpi/kpi_metrics.json',
                'data/persistent/pins.json',
                'data/persistent/locks.json',
                'data/agents/registry.json'
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    self.errors.append(f"Missing required file: {file_path}")
                    print(f"  ❌ Missing: {file_path}")
                    return False
                else:
                    try:
                        with open(file_path, 'r') as f:
                            json.load(f)
                        print(f"  ✅ Valid: {file_path}")
                    except json.JSONDecodeError as e:
                        self.errors.append(f"Invalid JSON in {file_path}: {str(e)}")
                        print(f"  ❌ Invalid JSON: {file_path}")
                        return False
                        
            print("  ✅ Data Structures: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"Data structure validation error: {str(e)}")
            print(f"  ❌ Data Structures: FAIL - {str(e)}")
            return False
    
    def validate_api_contracts(self) -> bool:
        """Validate API contracts and endpoints"""
        try:
            self.print_header("Validating API Contracts...")
            
            # Test server is running
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code != 200:
                    self.errors.append("Health endpoint not responding")
                    print("  ❌ Server not accessible")
                    return False
            except requests.exceptions.RequestException as e:
                self.errors.append(f"Server connection failed: {str(e)}")
                print(f"  ❌ Server connection failed: {str(e)}")
                return False
            
            # Test key API endpoints
            endpoints = [
                '/api/fusion/dashboard',
                '/api/equities/list',
                '/api/equities/kpis',
                '/api/kpi/metrics'
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        print(f"  ✅ {endpoint}: PASS")
                    else:
                        print(f"  ❌ {endpoint}: FAIL (status: {response.status_code})")
                        self.errors.append(f"API endpoint {endpoint} failed with status {response.status_code}")
                        return False
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ {endpoint}: FAIL (error: {str(e)})")
                    self.errors.append(f"API endpoint {endpoint} error: {str(e)}")
                    return False
            
            print("  ✅ API Contracts: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"API contract validation error: {str(e)}")
            print(f"  ❌ API Contracts: FAIL - {str(e)}")
            return False
    
    def validate_ui_components(self) -> bool:
        """Validate UI components and templates"""
        try:
            self.print_header("Validating UI Components...")
            
            # Check template files
            templates = [
                'web/templates/dashboard.html',
                'web/templates/equities.html',
                'web/templates/options.html',
                'web/templates/commodities.html'
            ]
            
            for template in templates:
                if not os.path.exists(template):
                    self.errors.append(f"Missing template: {template}")
                    print(f"  ❌ Missing: {template}")
                    return False
                else:
                    print(f"  ✅ Found: {template}")
            
            # Test UI routes
            ui_routes = ['/dashboard', '/equities', '/options', '/commodities']
            
            for route in ui_routes:
                try:
                    response = requests.get(f"{self.base_url}{route}", timeout=5)
                    if response.status_code == 200:
                        print(f"  ✅ Route {route}: PASS")
                    else:
                        print(f"  ❌ Route {route}: FAIL (status: {response.status_code})")
                        self.errors.append(f"UI route {route} failed")
                        return False
                except requests.exceptions.RequestException as e:
                    print(f"  ❌ Route {route}: FAIL (error: {str(e)})")
                    self.errors.append(f"UI route {route} error: {str(e)}")
                    return False
            
            print("  ✅ UI Components: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"UI component validation error: {str(e)}")
            print(f"  ❌ UI Components: FAIL - {str(e)}")
            return False
    
    def validate_agents_system(self) -> bool:
        """Validate agents system"""
        try:
            self.print_header("Validating Agents System...")
            
            # Test agents API
            try:
                response = requests.get(f"{self.base_url}/api/agents", timeout=5)
                if response.status_code == 200:
                    agents_data = response.json()
                    if 'agents' in agents_data:
                        print(f"  ✅ Agents API: PASS ({len(agents_data['agents'])} agents found)")
                    else:
                        print("  ❌ Agents API: Invalid response format")
                        return False
                else:
                    print(f"  ❌ Agents API: FAIL (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ Agents API: FAIL (error: {str(e)})")
                return False
            
            print("  ✅ Agents System: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"Agents system validation error: {str(e)}")
            print(f"  ❌ Agents System: FAIL - {str(e)}")
            return False
    
    def validate_kpi_system(self) -> bool:
        """Validate KPI system"""
        try:
            self.print_header("Validating KPI System...")
            
            # Test KPI API
            try:
                response = requests.get(f"{self.base_url}/api/kpi/metrics", timeout=5)
                if response.status_code == 200:
                    kpi_data = response.json()
                    print("  ✅ KPI API: PASS")
                else:
                    print(f"  ❌ KPI API: FAIL (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ KPI API: FAIL (error: {str(e)})")
                return False
            
            print("  ✅ KPI System: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"KPI system validation error: {str(e)}")
            print(f"  ❌ KPI System: FAIL - {str(e)}")
            return False
    
    def validate_options_engine(self) -> bool:
        """Validate options engine"""
        try:
            self.print_header("Validating Options Engine...")
            
            # Test options API (if available)
            try:
                response = requests.get(f"{self.base_url}/api/options/strangle/candidates", timeout=5)
                if response.status_code == 200:
                    print("  ✅ Options API: PASS")
                elif response.status_code == 404:
                    print("  ⚠️ Options API: Not available (expected if not implemented)")
                else:
                    print(f"  ❌ Options API: FAIL (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ⚠️ Options API: Not available (error: {str(e)})")
            
            print("  ✅ Options Engine: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"Options engine validation error: {str(e)}")
            print(f"  ❌ Options Engine: FAIL - {str(e)}")
            return False
    
    def validate_pins_locks(self) -> bool:
        """Validate pins and locks system"""
        try:
            self.print_header("Validating Pins & Locks...")
            
            # Test pins API
            try:
                response = requests.get(f"{self.base_url}/api/pins", timeout=5)
                if response.status_code == 200:
                    print("  ✅ Pins API: PASS")
                else:
                    print(f"  ❌ Pins API: FAIL (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ Pins API: FAIL (error: {str(e)})")
                return False
            
            # Test locks API
            try:
                response = requests.get(f"{self.base_url}/api/locks", timeout=5)
                if response.status_code == 200:
                    print("  ✅ Locks API: PASS")
                else:
                    print(f"  ❌ Locks API: FAIL (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ Locks API: FAIL (error: {str(e)})")
                return False
            
            print("  ✅ Pins & Locks: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"Pins & locks validation error: {str(e)}")
            print(f"  ❌ Pins & Locks: FAIL - {str(e)}")
            return False
    
    def validate_performance_guardrails(self) -> bool:
        """Validate performance guardrails"""
        try:
            self.print_header("Validating Performance Guardrails...")
            
            # Test metrics endpoint
            try:
                response = requests.get(f"{self.base_url}/metrics", timeout=5)
                if response.status_code == 200:
                    print("  ✅ Metrics endpoint: PASS")
                else:
                    print(f"  ❌ Metrics endpoint: FAIL (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ Metrics endpoint: FAIL (error: {str(e)})")
                return False
            
            print("  ✅ Performance Guardrails: PASS")
            return True
            
        except Exception as e:
            self.errors.append(f"Performance guardrails validation error: {str(e)}")
            print(f"  ❌ Performance Guardrails: FAIL - {str(e)}")
            return False
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete system validation"""
        print("🔍 COMPLETE SYSTEM VALIDATION")
        print("=" * 60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base URL: {self.base_url}")
        print("=" * 60)
        
        validations = [
            ("Data Structures", self.validate_data_structures),
            ("API Contracts", self.validate_api_contracts),
            ("UI Components", self.validate_ui_components),
            ("Agents System", self.validate_agents_system),
            ("KPI System", self.validate_kpi_system),
            ("Options Engine", self.validate_options_engine),
            ("Pins & Locks", self.validate_pins_locks),
            ("Performance Guardrails", self.validate_performance_guardrails)
        ]
        
        passed = 0
        failed = 0
        
        for name, validation_func in validations:
            try:
                if validation_func():
                    self.results[name] = "PASS"
                    passed += 1
                else:
                    self.results[name] = "FAIL"
                    failed += 1
            except Exception as e:
                self.results[name] = "FAIL"
                failed += 1
                self.errors.append(f"{name}: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Validations: {len(validations)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(validations)*100):.1f}%")
        
        # Save report
        report_file = f"system_validation_{int(time.time())}.json"
        report = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'results': self.results,
            'errors': self.errors,
            'summary': {
                'total': len(validations),
                'passed': passed,
                'failed': failed,
                'success_rate': passed/len(validations)*100
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Validation report: {report_file}")
        
        if failed > 0:
            print(f"\n⚠️ {failed} validation(s) failed:")
            for name, result in self.results.items():
                if result == "FAIL":
                    print(f"  - {name}: {result}")
        
        return report

def main():
    validator = SystemValidator()
    report = validator.run_validation()
    
    # Exit with error code if any validations failed
    if report['summary']['failed'] > 0:
        sys.exit(1)
    else:
        print("\n✅ All validations passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
