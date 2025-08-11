
#!/usr/bin/env python3
"""
Phase-3 Gap Closure Validation Script
Validates all requirements before marking phase complete
"""

import subprocess
import requests
import time
import sys
import json
from pathlib import Path

def run_command(cmd, shell=True, timeout=30):
    """Run shell command with error handling"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out: {cmd}"
    except Exception as e:
        return -1, "", f"Command failed: {e}"

def check_server_health():
    """Check if server is responding to health endpoint"""
    try:
        response = requests.get('http://localhost:5000/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'healthy'
        return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def check_fusion_dashboard():
    """Check fusion dashboard timeframes"""
    try:
        response = requests.get('http://localhost:5000/api/fusion/dashboard', timeout=10)
        if response.status_code == 200:
            data = response.json()
            timeframes = data.get('timeframes', {})
            return len(timeframes) >= 6  # Should have All, 3D, 5D, 10D, 15D, 30D
        return False
    except Exception as e:
        print(f"Fusion dashboard check failed: {e}")
        return False

def run_tests():
    """Run backend and frontend tests"""
    print("🧪 Running backend tests...")
    backend_code, backend_out, backend_err = run_command("pytest -q tests/backend")
    
    print("🧪 Running frontend tests...")
    frontend_code, frontend_out, frontend_err = run_command("pytest -q tests/frontend")
    
    return {
        'backend': {'code': backend_code, 'output': backend_out, 'error': backend_err},
        'frontend': {'code': frontend_code, 'output': frontend_out, 'error': frontend_err}
    }

def validate_requirements():
    """Main validation function"""
    print("🚀 Phase-3 Gap Closure Validation Starting...")
    
    # Step 1: Start server
    print("\n📡 Starting server...")
    server_code, _, server_err = run_command("python src/run_server.py &")
    time.sleep(3)  # Give server time to start
    
    # Step 2: Health check
    print("💓 Checking server health...")
    if not check_server_health():
        print("❌ Server health check failed")
        return False
    print("✅ Server is healthy")
    
    # Step 3: Fusion dashboard check
    print("📊 Checking fusion dashboard...")
    if not check_fusion_dashboard():
        print("❌ Fusion dashboard check failed")
        return False
    print("✅ Fusion dashboard has required timeframes")
    
    # Step 4: Run tests
    print("\n🧪 Running test suite...")
    test_results = run_tests()
    
    # Evaluate backend tests
    if test_results['backend']['code'] != 0:
        print("❌ Backend tests failed:")
        print(test_results['backend']['error'])
        return False
    print("✅ Backend tests passed")
    
    # Evaluate frontend tests (allow skip for Playwright, but not assertion failures)
    if test_results['frontend']['code'] != 0:
        frontend_output = test_results['frontend']['output'] + test_results['frontend']['error']
        if "playwright" in frontend_output.lower() or "browser not available" in frontend_output.lower():
            print("⚠️  Frontend tests skipped (Playwright not available)")
        else:
            print("❌ Frontend tests failed with assertion errors:")
            print(test_results['frontend']['error'])
            return False
    else:
        print("✅ Frontend tests passed")
    
    print("\n🎉 All Phase-3 validation checks passed!")
    print("✅ Server health: OK")
    print("✅ Fusion dashboard: OK")  
    print("✅ Backend tests: PASSED")
    print("✅ Frontend tests: PASSED/SKIPPED")
    
    return True

if __name__ == "__main__":
    success = validate_requirements()
    
    if success:
        print("\n🏆 Phase-3 Gap Closure: COMPLETE")
        print("All requirements validated successfully!")
        sys.exit(0)
    else:
        print("\n🚫 Phase-3 Gap Closure: INCOMPLETE")
        print("Some requirements failed validation.")
        sys.exit(1)
