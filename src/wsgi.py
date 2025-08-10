
# src/wsgi.py
import os, sys, pathlib

# Ensure project root on sys.path here as well, for any WSGI runner
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.app import create_app
app = create_app()
