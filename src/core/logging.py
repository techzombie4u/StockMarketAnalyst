import json
import time
import uuid
from flask import request, g
from src.core.metrics import metrics, update_request_metrics

def before_request():
    """Initialize request tracking"""
    g._start_ts = time.time()
    g._request_id = str(uuid.uuid4())

def after_request(response):
    """Log request and collect metrics"""
    try:
        latency_ms = int((time.time() - getattr(g, "_start_ts", time.time())) * 1000)
        request_id = getattr(g, "_request_id", "unknown")

        # Log record
        rec = {
            "request_id": request_id,
            "ts": int(time.time()),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
        }
        print(json.dumps(rec))

        # Collect metrics
        metrics.increment(request.path)
        metrics.increment(f"status_{response.status_code}")
        metrics.record_latency(request.path, latency_ms)

        # Add request ID to response headers
        response.headers['X-Request-ID'] = request_id

        # Update metrics
        update_request_metrics(request.path, request.method, response.status_code, latency_ms)

    except Exception as e:
        print(f"Logging error: {e}")

    return response

def add_request_logging(app):
    """Add request logging middleware to Flask app"""
    app.before_request(before_request)
    app.after_request(after_request)
    return app