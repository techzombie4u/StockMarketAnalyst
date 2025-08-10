
#!/usr/bin/env python3
"""
Fusion Dashboard Validation Script with integrated server startup
"""

import subprocess
import time
import sys
import os

def main():
    print("🚀 Starting Fusion Dashboard Validation with Server")
    print("="*60)

    # Start the server in background
    print("📡 Starting Flask server...")
    server_process = None
    try:
        # Use the proper WSGI runner
        server_process = subprocess.Popen([
            sys.executable, "-u", "src/run_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if server is still running
        if server_process.poll() is not None:
            # Server died, show output
            output = server_process.stdout.read()
            print(f"❌ Server failed to start:\n{output}")
            return False
            
        print("✅ Server started, running validation...")
        
        # Run the validator
        from validate_fusion_dashboard import main as run_validation
        success = run_validation()
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up server process
        if server_process:
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
                print("🛑 Server stopped")
            except:
                server_process.kill()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
