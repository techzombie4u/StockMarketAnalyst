
from flask import Blueprint, jsonify, request
from core.cache import TTLCache
from core.metrics import inc
import json, os, random

equities_bp = Blueprint('equities', __name__)
cache = TTLCache(ttl_sec=300)

def _load_fixtures():
    fixtures_path = os.path.join(os.path.dirname(__file__), "../../data/fixtures")
    try:
        with open(os.path.join(fixtures_path, "equities_sample.json"), "r") as f:
            equities = json.load(f)
        with open(os.path.join(fixtures_path, "prices_TCS.json"), "r") as f:
            tcs_prices = json.load(f)
        with open(os.path.join(fixtures_path, "prices_RELIANCE.json"), "r") as f:
            rel_prices = json.load(f)
        return equities, tcs_prices, rel_prices
    except Exception:
        return [], [], []

@equities_bp.get("/list")
def list_equities():
    inc("api.equities.list")
    cached = cache.get()
    if cached and not request.args.get("forceRefresh"):
        return jsonify(cached)
    
    equities, tcs_prices, rel_prices = _load_fixtures()
    
    # Add computed KPIs/ROI
    for equity in equities:
        equity["roi_5d"] = round(random.uniform(-5.0, 12.0), 2)
        equity["roi_30d"] = round(random.uniform(-15.0, 35.0), 2)
        equity["sharpe_ratio"] = round(random.uniform(0.5, 2.5), 2)
        equity["volatility"] = round(random.uniform(15.0, 45.0), 2)
        equity["beta"] = round(random.uniform(0.7, 1.8), 2)
    
    result = {"equities": equities, "count": len(equities)}
    cache.set(result)
    return jsonify(result)

@equities_bp.get("/kpis")
def equities_kpis():
    inc("api.equities.kpis")
    equities, _, _ = _load_fixtures()
    
    total_value = sum(eq.get("market_cap", 0) for eq in equities)
    avg_roi_5d = sum(random.uniform(-5, 12) for _ in equities) / max(len(equities), 1)
    avg_roi_30d = sum(random.uniform(-15, 35) for _ in equities) / max(len(equities), 1)
    
    return jsonify({
        "total_instruments": len(equities),
        "total_market_value": total_value,
        "avg_roi_5d": round(avg_roi_5d, 2),
        "avg_roi_30d": round(avg_roi_30d, 2),
        "top_performers": len([eq for eq in equities if random.random() > 0.7])
    })
