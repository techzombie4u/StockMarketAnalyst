
#!/usr/bin/env python3
"""
Simple runner for SmartGoAgent backend tests
Usage: python run_backend_test.py
"""

import subprocess
import sys
import os

def main():
    """Run the backend test"""
    print("🚀 Starting SmartGoAgent Backend Data Validation Test...")
    
    # Ensure tests directory exists
    if not os.path.exists('tests'):
        print("❌ Tests directory not found!")
        return 1
    
    # Try different ways to run the test
    test_file = 'tests/test_smart_go_agent_data.py'
    
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found!")
        return 1
    
    try:
        # Method 1: Direct execution
        print("📊 Running test directly...")
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out after 60 seconds")
        return 1
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
