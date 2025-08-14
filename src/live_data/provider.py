
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import time

@dataclass
class OptionQuote:
    strike: float
    iv: float
    delta: float
    theta: float
    bid: float
    ask: float
    type: str  # "call" | "put"

@dataclass
class Chain:
    symbol: str
    spot: float
    expiry: str  # ISO date
    step: float  # strike step
    calls: List[OptionQuote]
    puts: List[OptionQuote]

class LiveDataError(RuntimeError): 
    pass

class LiveProvider:
    def get_spot(self, symbol: str) -> float:
        raise NotImplementedError("Subclasses must implement get_spot")
    
    def get_expiries(self, symbol: str) -> List[str]:
        raise NotImplementedError("Subclasses must implement get_expiries")
    
    def get_chain(self, symbol: str, expiry: str) -> Chain:
        raise NotImplementedError("Subclasses must implement get_chain")

# 60s in-memory TTL cache (hard stop: no mock fallback)
class TTL:
    def __init__(self, secs=60): 
        self.secs = secs
        self._c = {}
    
    def get(self, k): 
        v = self._c.get(k)
        return None if not v or v[0] < time.time() else v[1]
    
    def set(self, k, val): 
        self._c[k] = (time.time() + self.secs, val)

cache = TTL(60)
