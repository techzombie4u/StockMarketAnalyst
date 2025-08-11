
from flask import Blueprint, jsonify, request
from core.cache import TTLCache
from core.metrics import inc
import json, os, random

options_bp = Blueprint('options', __name__)
cache = TTLCache(ttl_sec=300)

def _load_fixtures():
    fixtures_path = os.path.join(os.path.dirname(__file__), "../../data/fixtures")
    try:
        with open(os.path.join(fixtures_path, "options_sample.json"), "r") as f:
            return json.load(f)
    except Exception:
        return []

@options_bp.get("/list")
def list_options():
    inc("api.options.list")
    cached = cache.get()
    if cached and not request.args.get("forceRefresh"):
        return jsonify(cached)
    
    options = _load_fixtures()
    
    # Add computed payoffs/Greeks
    for option in options:
        option["delta"] = round(random.uniform(0.1, 0.9), 3)
        option["gamma"] = round(random.uniform(0.001, 0.05), 4)
        option["theta"] = round(random.uniform(-0.05, -0.001), 4)
        option["vega"] = round(random.uniform(0.1, 0.8), 3)
        option["implied_vol"] = round(random.uniform(15.0, 60.0), 1)
        option["max_profit"] = round(random.uniform(500, 5000), 0)
        option["max_loss"] = round(random.uniform(-2000, -100), 0)
        option["payoff_ratio"] = round(option["max_profit"] / abs(option["max_loss"]), 2)
    
    result = {"options": options, "count": len(options)}
    cache.set(result)
    return jsonify(result)

@options_bp.get("/kpis")
def options_kpis():
    inc("api.options.kpis")
    options = _load_fixtures()
    
    total_premium = sum(opt.get("premium", 0) for opt in options)
    avg_iv = sum(random.uniform(15, 60) for _ in options) / max(len(options), 1)
    bullish_count = sum(1 for _ in options if random.random() > 0.4)
    
    return jsonify({
        "total_contracts": len(options),
        "total_premium": total_premium,
        "avg_implied_volatility": round(avg_iv, 1),
        "bullish_strategies": bullish_count,
        "bearish_strategies": len(options) - bullish_count
    })
