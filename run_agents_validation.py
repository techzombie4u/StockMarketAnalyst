
# run_agents_validation.py
import os, sys, time, subprocess, signal
import requests

def wait_for(url, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1.5)
            if r.status_code == 200:
                return True
        except Exception:
            time.sleep(0.5)
    return False

def main():
    print("🚀 Starting Agent Orchestration Validation with Server")
    print("="*60)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    print("📡 Starting Flask server...")
    server = subprocess.Popen([sys.executable, "-u", "src/run_server.py"], env=env)

    try:
        print("⏳ Waiting for server to start...")
        if not wait_for("http://localhost:5000/health", timeout=20):
            print(" ❌ Server failed to start (health not ready).")
            server.terminate()
            server.wait(timeout=5)
            return

        print("✅ Server started successfully")
        print("🔍 Running agent validation tests...\n")
        rc = subprocess.call([sys.executable, "validate_agents.py"])
        if rc == 0:
            print("\n🎉 Agents validation passed.")
        else:
            print("\n⚠️ Agents validation reported failures.")

    finally:
        print("\n🛑 Stopping server...")
        try:
            server.send_signal(signal.SIGINT)
            server.wait(timeout=5)
        except Exception:
            server.kill()

if __name__ == "__main__":
    main()
