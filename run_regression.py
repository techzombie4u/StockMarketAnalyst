
# run_regression.py
import os, sys, json, time, traceback, pathlib, subprocess
from tests.utils.server_manager import start_server, stop_server

ART = pathlib.Path("logs/regression")
ART.mkdir(parents=True, exist_ok=True)

def _run(cmd, env=None):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    out = []
    for line in p.stdout:
        print(line, end="")
        out.append(line)
    rc = p.wait()
    return rc, "".join(out)

def main():
    os.environ.setdefault("TEST_BASE_URL", "http://0.0.0.0:5000")

    print("🚀 Installing test deps (if needed)...")
    _run([sys.executable, "-m", "pip", "install", "-q", "pytest", "requests", "playwright==1.47.0"])
    _run([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])

    print("\n📡 Starting server...")
    server = None
    try:
        server = start_server(timeout=40)
        print("✅ Server started.")

        results = {"backend": {}, "frontend": {}, "started_at": time.time()}

        print("\n🧪 Running BACKEND tests...")
        rc_b, out_b = _run([sys.executable, "-m", "pytest", "-q", "tests/backend"])
        results["backend"]["rc"] = rc_b
        results["backend"]["stdout"] = out_b

        print("\n🧪 Running FRONTEND tests...")
        rc_f, out_f = _run([sys.executable, "-m", "pytest", "-q", "tests/frontend"])
        results["frontend"]["rc"] = rc_f
        results["frontend"]["stdout"] = out_f

        results["ended_at"] = time.time()
        results["passed"] = (rc_b == 0 and rc_f == 0)

        report_path = ART / f"regression_report_{int(results['ended_at'])}.json"
        report_path.write_text(json.dumps(results, indent=2))

        print("\n============================================================")
        print("📊 REGRESSION SUMMARY")
        print("============================================================")
        print(f"Backend: {'✅ PASS' if rc_b == 0 else '❌ FAIL'}")
        print(f"Frontend: {'✅ PASS' if rc_f == 0 else '❌ FAIL'}")
        print("------------------------------------------------------------")
        print(f"Report: {report_path}")
        print("Artifacts (screenshots, console logs): logs/regression/frontend/")
        print("============================================================")

        sys.exit(0 if results["passed"] else 1)

    except Exception as e:
        print("❌ Regression runner failed:", e)
        traceback.print_exc()
        sys.exit(1)
    finally:
        print("\n🛑 Stopping server...")
        stop_server(server)

if __name__ == "__main__":
    main()
