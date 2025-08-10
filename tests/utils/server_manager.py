
# tests/utils/server_manager.py
import os, sys, time, signal, subprocess, requests

PY_CMD = [sys.executable, "-u", "src/run_server.py"]
BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def _is_up():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=1)
        return r.status_code in (200, 404)  # /health optional; server up if any response
    except Exception:
        return False

def start_server(timeout=30):
    # Kill any leftover processes on 5000
    try:
        requests.get(f"{BASE_URL}/__stop__", timeout=0.5)
    except Exception:
        pass

    env = os.environ.copy()
    env["FLASK_ENV"] = "production"
    env.setdefault("PORT", "5000")

    proc = subprocess.Popen(
        PY_CMD,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server
    start = time.time()
    buf = []
    while time.time() - start < timeout:
        if _is_up():
            return proc
        # drain non-blocking output
        try:
            line = proc.stdout.readline()
            if line:
                buf.append(line.rstrip())
                if "Running on" in line or "Serving Flask app" in line:
                    if _is_up():
                        return proc
        except Exception:
            pass
        time.sleep(0.3)

    # If here, failed to start
    try:
        out = "".join(buf)
    except Exception:
        out = ""
    stop_server(proc)
    raise RuntimeError(f"Server failed to start within {timeout}s.\nStartup log:\n{out}")

def stop_server(proc):
    if not proc:
        return
    try:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    except Exception:
        pass
