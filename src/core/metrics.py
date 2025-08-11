
from collections import defaultdict
_METRICS = defaultdict(int)
def inc(key, by=1): _METRICS[key] += by
def snapshot(): return dict(_METRICS)
