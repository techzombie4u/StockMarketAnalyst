
from flask import Blueprint, jsonify, request
from core.cache import TTLCache
from core.metrics import inc
import json, os, random

commodities_bp = Blueprint('commodities', __name__)
cache = TTLCache(ttl_sec=300)

def _load_fixtures():
    fixtures_path = os.path.join(os.path.dirname(__file__), "../../data/fixtures")
    try:
        with open(os.path.join(fixtures_path, "commodities_sample.json"), "r") as f:
            return json.load(f)
    except Exception:
        return []

@commodities_bp.get("/list")
def list_commodities():
    inc("api.commodities.list")
    cached = cache.get()
    if cached and not request.args.get("forceRefresh"):
        return jsonify(cached)
    
    commodities = _load_fixtures()
    
    # Add computed KPIs/trends
    for commodity in commodities:
        commodity["price_change_5d"] = round(random.uniform(-8.0, 15.0), 2)
        commodity["price_change_30d"] = round(random.uniform(-25.0, 40.0), 2)
        commodity["volatility_index"] = round(random.uniform(20.0, 80.0), 1)
        commodity["supply_demand_ratio"] = round(random.uniform(0.8, 1.4), 2)
        commodity["seasonal_factor"] = round(random.uniform(-10.0, 10.0), 2)
    
    result = {"commodities": commodities, "count": len(commodities)}
    cache.set(result)
    return jsonify(result)

@commodities_bp.get("/kpis")
def commodities_kpis():
    inc("api.commodities.kpis")
    commodities = _load_fixtures()
    
    avg_price_change = sum(random.uniform(-25, 40) for _ in commodities) / max(len(commodities), 1)
    high_volatility_count = sum(1 for _ in commodities if random.random() > 0.6)
    
    return jsonify({
        "total_commodities": len(commodities),
        "avg_price_change_30d": round(avg_price_change, 2),
        "high_volatility_count": high_volatility_count,
        "trending_up": sum(1 for _ in commodities if random.random() > 0.5),
        "trending_down": sum(1 for _ in commodities if random.random() > 0.5)
    })
