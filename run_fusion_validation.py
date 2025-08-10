
#!/usr/bin/env python3
"""
Fusion Dashboard Validation Runner
Starts Flask server and runs validation tests
"""

import subprocess
import time
import sys
import signal
import os

def main():
    """Run server and validation"""
    server_process = None
    
    try:
        print("🚀 Starting Flask server...")
        
        # Start the Flask server
        server_process = subprocess.Popen([
            sys.executable, "-m", "src.run_server"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if server is still running
        if server_process.poll() is not None:
            print("❌ Server failed to start. Output:")
            output, _ = server_process.communicate()
            print(output)
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
            except subprocess.TimeoutExpired:
                server_process.kill()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
