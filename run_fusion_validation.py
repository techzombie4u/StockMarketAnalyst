
#!/usr/bin/env python3
"""
Fusion Dashboard Validation Runner
Starts Flask server and runs validation tests with improved error handling
"""

import subprocess
import time
import sys
import signal
import os
import requests

def check_server_health(max_attempts=10, delay=1):
    """Check if server is responding to health checks"""
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://127.0.0.1:5000/healthz", timeout=5)
            if response.status_code == 200:
                print(f"✅ Server health check passed (attempt {attempt + 1})")
                return True
        except requests.exceptions.RequestException as e:
            print(f"⏳ Health check attempt {attempt + 1} failed: {e}")
        
        if attempt < max_attempts - 1:
            time.sleep(delay)
    
    return False

def main():
    """Run server and validation"""
    server_process = None
    
    try:
        print("🚀 Starting Flask server...")
        
        # Start the Flask server with output streaming
        server_process = subprocess.Popen([
            sys.executable, "scripts/dev_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        
        print("⏳ Waiting for server to start...")
        
        # Give server time to start
        time.sleep(2)
        
        # Check if server process is still running
        if server_process.poll() is not None:
            print("❌ Server process exited early. Reading output...")
            try:
                output, _ = server_process.communicate(timeout=5)
                print("Server output:")
                print(output)
            except subprocess.TimeoutExpired:
                print("❌ Could not read server output")
            return False
        
        # Verify server is responding
        if not check_server_health():
            print("❌ Server health check failed")
            if server_process.poll() is None:
                # Server process is running but not responding
                print("📋 Server process is running but not responding. Checking logs...")
                try:
                    # Try to get some output
                    server_process.send_signal(signal.SIGTERM)
                    output, _ = server_process.communicate(timeout=5)
                    print("Server output:")
                    print(output)
                except:
                    print("❌ Could not get server output")
            return False
        
        print("✅ Server started successfully")
        print("🔍 Running validation tests...")
        
        # Run the validation
        result = subprocess.run([
            sys.executable, "validate_fusion_dashboard.py"
        ], capture_output=True, text=True)
        
        print("📊 Validation Results:")
        print("=" * 60)
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if server_process and server_process.poll() is None:
            print("🛑 Stopping server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("✅ Server stopped gracefully")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing server...")
                server_process.kill()
                server_process.wait()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Validation completed successfully!")
    else:
        print("\n❌ Validation failed. Check the logs above for details.")
    sys.exit(0 if success else 1)
