
# src/run_server.py
import os, sys, pathlib

# Add project root to sys.path so "src" is importable everywhere
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.wsgi import app  # now import works

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    # no reloader (CI/validators), no debug
    print("🚀 Starting Flask server...")
    app.run(host=host, port=port, debug=False, use_reloader=False)
