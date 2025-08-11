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

from core.app import create_app
app = create_app()
app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)