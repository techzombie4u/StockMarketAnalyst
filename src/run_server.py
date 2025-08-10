# src/run_server.py
import os, sys

# Absolute paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))           # /.../src
ROOT_DIR = os.path.dirname(SRC_DIR)                            # /.../

# Make both 'src' and its parent importable:
# - so 'core', 'fusion', 'agents' (from SRC_DIR) import works
# - and 'src.core', 'src.fusion' (from ROOT_DIR) import works
for p in (SRC_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    # Prefer non-prefixed import (since SRC_DIR is on sys.path)
    from core.app import create_app
except ImportError:
    # Fallback to 'src.'-prefixed import (requires ROOT_DIR on sys.path)
    from src.core.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print("🚀 Starting Stock Analyst Server...")
    print(f"📊 Dashboard will be available at: http://0.0.0.0:{port}/")
    print(f"🔥 Fusion Dashboard at: http://0.0.0.0:{port}/fusion-dashboard")
    app.run(debug=True, host="0.0.0.0", port=port, threaded=True)