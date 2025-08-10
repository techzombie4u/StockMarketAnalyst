
# src/wsgi.py
import os, sys
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.app import create_app
app = create_app()
