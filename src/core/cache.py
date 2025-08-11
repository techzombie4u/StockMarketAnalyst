
import time
class TTLCache:
    def __init__(self, ttl_sec=30):
        self.ttl = ttl_sec; self._payload=None; self._ts=0
    def get(self):
        if self._payload is None: return None
        if time.time()-self._ts > self.ttl: return None
        return self._payload
    def set(self, payload):
        self._payload = payload; self._ts = time.time()
    def clear(self):
        self._payload=None; self._ts=0
