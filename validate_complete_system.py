
#!/usr/bin/env python3
"""
Complete System Validation Script
Validates all major system components and functionality
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime

class SystemValidator:
    def __init__(self):
        self.base_url = "http://0.0.0.0:5000"
        self.results = {"timestamp": time.time(), "validations": []}
        
    def validate(self, name, test_func):
        """Run validation and record result"""
        print(f"🔍 Validating {name}...")
        try:
            result = test_func()
            status = "PASS" if result else "FAIL"
            self.results["validations"].append({
                "name": name,
                "status": status,
                "timestamp": time.time()
            })
            print(f"  {'✅' if result else '❌'} {name}: {status}")
            return result
        except Exception as e:
            self.results["validations"].append({
                "name": name,
                "status": "ERROR",
                "error": str(e),
                "timestamp": time.time()
            })
            print(f"  💥 {name}: ERROR - {e}")
            return False
    
    def validate_data_structures(self):
        """Validate data file structures"""
        try:
            # Check equities sample data
            equities_file = Path("data/fixtures/equities_sample.json")
            if equities_file.exists():
                with open(equities_file, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, dict) or "items" not in data:
                        return False
            
            # Check KPI data structure
            kpi_file = Path("data/kpi/kpi_metrics.json")
            if kpi_file.exists():
                with open(kpi_file, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        return False
            
            # Check pins/locks data
            pins_file = Path("data/persistent/pins.json")
            locks_file = Path("data/persistent/locks.json")
            
            for file_path in [pins_file, locks_file]:
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        if not isinstance(data, (dict, list)):
                            return False
            
            return True
        except:
            return False
    
    def validate_api_contracts(self):
        """Validate API contracts match OpenAPI spec"""
        try:
            # Test fusion dashboard contract
            response = requests.get(f"{self.base_url}/api/fusion/dashboard", timeout=15)
            if response.status_code != 200:
                return False
            
            data = response.json()
            required_fields = ["timeframes", "pinned_summary", "top_signals", "generation_time_ms"]
            if not all(field in data for field in required_fields):
                return False
            
            # Validate timeframes structure
            timeframes = data.get("timeframes", {})
            if not isinstance(timeframes, dict):
                return False
            
            # Validate top_signals structure
            top_signals = data.get("top_signals", [])
            if not isinstance(top_signals, list):
                return False
            
            return True
        except:
            return False
    
    def validate_ui_components(self):
        """Validate UI components are accessible"""
        try:
            pages = [
                ("/dashboard", ["KPI Dashboard", "timeframe-chips"]),
                ("/equities", ["Equities"]),
                ("/options", ["Options"]),
                ("/commodities", ["Commodities"])
            ]
            
            for path, required_elements in pages:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                if response.status_code != 200:
                    return False
                
                html_content = response.text
                if not any(element in html_content for element in required_elements):
                    return False
            
            return True
        except:
            return False
    
    def validate_agents_system(self):
        """Validate agents system functionality"""
        try:
            # Check agents config
            response = requests.get(f"{self.base_url}/api/agents/config", timeout=10)
            if response.status_code != 200:
                return False
            
            # Check agent registry file
            registry_file = Path("data/agents/registry.json")
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry = json.load(f)
                    if not isinstance(registry, dict):
                        return False
            
            return True
        except:
            return False
    
    def validate_kpi_system(self):
        """Validate KPI calculation system"""
        try:
            # Test KPI metrics endpoint
            response = requests.get(f"{self.base_url}/api/kpi/metrics", timeout=10)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "metrics" not in data:
                return False
            
            # Test with timeframe parameter
            response = requests.get(f"{self.base_url}/api/kpi/metrics?timeframe=5D", timeout=10)
            if response.status_code != 200:
                return False
            
            return True
        except:
            return False
    
    def validate_options_engine(self):
        """Validate options engine functionality"""
        try:
            # Test strangle candidates
            response = requests.get(f"{self.base_url}/api/options/strangle/candidates", timeout=15)
            if response.status_code != 200:
                return False
            
            data = response.json()
            if "candidates" not in data:
                return False
            
            # Validate candidate structure
            candidates = data["candidates"]
            if candidates:
                sample = candidates[0]
                required_fields = ["underlying", "strike_call", "strike_put", "margin", "payoff"]
                if not all(field in sample for field in required_fields):
                    return False
            
            return True
        except:
            return False
    
    def validate_pins_locks_system(self):
        """Validate pins and locks system"""
        try:
            # Test pins API
            response = requests.get(f"{self.base_url}/api/pins", timeout=10)
            if response.status_code != 200:
                return False
            
            # Test locks API
            response = requests.get(f"{self.base_url}/api/locks", timeout=10)
            if response.status_code != 200:
                return False
            
            # Test pin operation
            payload = {"symbol": "TEST", "action": "pin"}
            response = requests.post(f"{self.base_url}/api/pins", json=payload, timeout=10)
            if response.status_code not in [200, 201]:
                return False
            
            return True
        except:
            return False
    
    def validate_performance_guardrails(self):
        """Validate performance monitoring and guardrails"""
        try:
            # Test metrics endpoint
            response = requests.get(f"{self.base_url}/metrics", timeout=10)
            if response.status_code != 200:
                return False
            
            # Test that responses are reasonably fast
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/fusion/dashboard", timeout=20)
            response_time = time.time() - start_time
            
            if response.status_code != 200 or response_time > 15.0:
                return False
            
            return True
        except:
            return False
    
    def run_complete_validation(self):
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
            ("Pins & Locks", self.validate_pins_locks_system),
            ("Performance Guardrails", self.validate_performance_guardrails)
        ]
        
        passed = 0
        total = len(validations)
        
        for name, validator in validations:
            if self.validate(name, validator):
                passed += 1
        
        # Generate summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Validations: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Save results
        self.results["summary"] = {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed/total)*100
        }
        
        report_file = f"system_validation_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"📄 Validation report: {report_file}")
        
        if passed == total:
            print("\n🎉 ALL VALIDATIONS PASSED! System is fully operational.")
            return True
        else:
            failed = [v for v in self.results["validations"] if v["status"] != "PASS"]
            print(f"\n⚠️ {len(failed)} validation(s) failed:")
            for failure in failed:
                print(f"  - {failure['name']}: {failure['status']}")
            return False

def main():
    validator = SystemValidator()
    success = validator.run_complete_validation()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
