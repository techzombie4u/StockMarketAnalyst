
# src/wsgi.py
from src.core.app import create_app

# Expose WSGI app for gunicorn/flask runners and our validators
app = create_app()
