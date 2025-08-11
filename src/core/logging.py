
import json, time
from flask import request, g

def before_request():
    g._start_ts = time.time()

def after_request(response):
    try:
        latency_ms = int((time.time() - getattr(g, "_start_ts", time.time())) * 1000)
        rec = {
            "ts": int(time.time()),
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "latency_ms": latency_ms,
        }
        print(json.dumps(rec))
    except Exception:
        pass
    return response
