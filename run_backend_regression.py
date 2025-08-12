
#!/usr/bin/env python3
"""
Focused Backend Regression Test
Concentrates on API contracts and backend functionality
"""

import subprocess
import sys
import os
import time
import json
from pathlib import Path

def run_backend_tests():
    """Run all backend tests with detailed reporting"""
    print("🧪 BACKEND REGRESSION TEST SUITE")
    print("=" * 60)
    
    # Set environment variables
    os.environ.setdefault("TEST_BASE_URL", "http://0.0.0.0:5000")
    
    # Install test dependencies
    print("📦 Installing test dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pytest", "requests"], 
                   capture_output=True)
    
    # Start server
    from tests.utils.server_manager import start_server, stop_server
    
    print("🚀 Starting server for backend tests...")
    server = None
    
    try:
        server = start_server(timeout=40)
        print("✅ Server ready for testing")
        
        # Run backend test suite
        print("\n🧪 Running Backend Contract Tests...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/backend/", 
            "-v", 
            "--tb=short",
            "--json-report",
            "--json-report-file=backend_test_results.json"
        ], capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Generate summary
        if result.returncode == 0:
            print("\n✅ ALL BACKEND TESTS PASSED!")
        else:
            print(f"\n❌ Backend tests failed with exit code {result.returncode}")
            
        # Try to parse JSON report if available
        json_report_file = Path("backend_test_results.json")
        if json_report_file.exists():
            try:
                with open(json_report_file, 'r') as f:
                    report = json.load(f)
                    
                summary = report.get("summary", {})
                print(f"\n📊 Test Summary:")
                print(f"  Total: {summary.get('total', 0)}")
                print(f"  Passed: {summary.get('passed', 0)}")
                print(f"  Failed: {summary.get('failed', 0)}")
                print(f"  Errors: {summary.get('error', 0)}")
                print(f"  Skipped: {summary.get('skipped', 0)}")
            except:
                print("⚠️ Could not parse JSON test report")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Backend test execution failed: {e}")
        return False
    finally:
        if server:
            print("\n🛑 Stopping server...")
            stop_server(server)

if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)
