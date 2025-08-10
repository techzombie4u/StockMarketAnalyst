
# src/wsgi.py
import os, sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))  # /.../src
ROOT_DIR = os.path.dirname(SRC_DIR)                   # /.../
for p in (SRC_DIR, ROOT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from core.app import create_app
except ImportError:
    from src.core.app import create_app

app = create_app()
