
# src/run_server.py
import os, sys

# Ensure 'src' (this dir) is importable as the project root for 'core', 'fusion', 'agents'
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # No reloader; single process; thread-safe blueprints
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
