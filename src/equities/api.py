
from flask import Blueprint, request, jsonify
from src.core.cache import ttl_cache, now_iso
import random

equities_bp = Blueprint("equities", __name__)
_cache = ttl_cache(ttl_sec=30, namespace="equities")

# Extended fixture data with 30+ Indian tickers and required fields
_EQUITIES_DATA = [
    {"symbol":"TCS","name":"Tata Consultancy Services","sector":"IT","price":4275.3,"volRegime":"MEDIUM","verdict":"STRONG_BUY","confidence":0.74,"rsi":65.2,"macd":12.5,"momentum":0.15,"volatility":0.18,"from52wHigh":-0.12,"model":"ensemble","kpis":{"winRate":0.67,"sharpe":1.2,"mdd":-0.08},"updated":now_iso()},
    {"symbol":"RELIANCE","name":"Reliance Industries","sector":"Energy","price":2904.1,"volRegime":"LOW","verdict":"BUY","confidence":0.68,"rsi":58.7,"macd":8.3,"momentum":0.08,"volatility":0.15,"from52wHigh":-0.08,"model":"lstm","kpis":{"winRate":0.61,"sharpe":1.05,"mdd":-0.10},"updated":now_iso()},
    {"symbol":"INFY","name":"Infosys","sector":"IT","price":1588.2,"volRegime":"MEDIUM","verdict":"HOLD","confidence":0.61,"rsi":52.1,"macd":-2.1,"momentum":-0.02,"volatility":0.20,"from52wHigh":-0.15,"model":"random_forest","kpis":{"winRate":0.55,"sharpe":0.92,"mdd":-0.12},"updated":now_iso()},
    {"symbol":"HDFCBANK","name":"HDFC Bank","sector":"Banking","price":1720.5,"volRegime":"LOW","verdict":"BUY","confidence":0.72,"rsi":61.3,"macd":15.2,"momentum":0.12,"volatility":0.16,"from52wHigh":-0.05,"model":"ensemble","kpis":{"winRate":0.69,"sharpe":1.35,"mdd":-0.07},"updated":now_iso()},
    {"symbol":"ICICIBANK","name":"ICICI Bank","sector":"Banking","price":1245.8,"volRegime":"MEDIUM","verdict":"STRONG_BUY","confidence":0.78,"rsi":68.9,"macd":18.7,"momentum":0.18,"volatility":0.19,"from52wHigh":-0.03,"model":"lstm","kpis":{"winRate":0.71,"sharpe":1.42,"mdd":-0.06},"updated":now_iso()},
    {"symbol":"WIPRO","name":"Wipro","sector":"IT","price":445.7,"volRegime":"HIGH","verdict":"HOLD","confidence":0.55,"rsi":48.2,"macd":-5.3,"momentum":-0.05,"volatility":0.25,"from52wHigh":-0.22,"model":"random_forest","kpis":{"winRate":0.52,"sharpe":0.78,"mdd":-0.18},"updated":now_iso()},
    {"symbol":"BHARTIARTL","name":"Bharti Airtel","sector":"Telecom","price":1610.3,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.66,"rsi":59.8,"macd":11.4,"momentum":0.10,"volatility":0.17,"from52wHigh":-0.09,"model":"ensemble","kpis":{"winRate":0.64,"sharpe":1.18,"mdd":-0.11},"updated":now_iso()},
    {"symbol":"SBIN","name":"State Bank of India","sector":"Banking","price":812.4,"volRegime":"HIGH","verdict":"CAUTIOUS","confidence":0.58,"rsi":45.6,"macd":-8.2,"momentum":-0.08,"volatility":0.28,"from52wHigh":-0.18,"model":"lstm","kpis":{"winRate":0.48,"sharpe":0.65,"mdd":-0.20},"updated":now_iso()},
    {"symbol":"LT","name":"Larsen & Toubro","sector":"Infrastructure","price":3642.9,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.70,"rsi":62.5,"macd":14.8,"momentum":0.14,"volatility":0.18,"from52wHigh":-0.07,"model":"ensemble","kpis":{"winRate":0.66,"sharpe":1.28,"mdd":-0.09},"updated":now_iso()},
    {"symbol":"HCLTECH","name":"HCL Technologies","sector":"IT","price":1875.6,"volRegime":"LOW","verdict":"STRONG_BUY","confidence":0.75,"rsi":66.8,"macd":16.3,"momentum":0.16,"volatility":0.14,"from52wHigh":-0.04,"model":"lstm","kpis":{"winRate":0.70,"sharpe":1.45,"mdd":-0.05},"updated":now_iso()},
    {"symbol":"KOTAKBANK","name":"Kotak Mahindra Bank","sector":"Banking","price":1798.2,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.67,"rsi":60.2,"macd":12.7,"momentum":0.11,"volatility":0.17,"from52wHigh":-0.08,"model":"ensemble","kpis":{"winRate":0.65,"sharpe":1.22,"mdd":-0.10},"updated":now_iso()},
    {"symbol":"ITC","name":"ITC Limited","sector":"FMCG","price":468.9,"volRegime":"LOW","verdict":"HOLD","confidence":0.59,"rsi":53.4,"macd":3.2,"momentum":0.03,"volatility":0.13,"from52wHigh":-0.12,"model":"random_forest","kpis":{"winRate":0.56,"sharpe":0.88,"mdd":-0.14},"updated":now_iso()},
    {"symbol":"HINDUNILVR","name":"Hindustan Unilever","sector":"FMCG","price":2385.7,"volRegime":"LOW","verdict":"HOLD","confidence":0.62,"rsi":54.8,"macd":5.6,"momentum":0.05,"volatility":0.12,"from52wHigh":-0.10,"model":"ensemble","kpis":{"winRate":0.58,"sharpe":0.95,"mdd":-0.13},"updated":now_iso()},
    {"symbol":"AXISBANK","name":"Axis Bank","sector":"Banking","price":1098.5,"volRegime":"HIGH","verdict":"CAUTIOUS","confidence":0.56,"rsi":46.9,"macd":-6.8,"momentum":-0.07,"volatility":0.26,"from52wHigh":-0.19,"model":"lstm","kpis":{"winRate":0.49,"sharpe":0.72,"mdd":-0.21},"updated":now_iso()},
    {"symbol":"MARUTI","name":"Maruti Suzuki","sector":"Auto","price":11245.8,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.69,"rsi":61.7,"macd":13.9,"momentum":0.13,"volatility":0.19,"from52wHigh":-0.06,"model":"ensemble","kpis":{"winRate":0.67,"sharpe":1.31,"mdd":-0.08},"updated":now_iso()},
    {"symbol":"SUNPHARMA","name":"Sun Pharmaceutical","sector":"Pharma","price":1789.3,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.65,"rsi":58.9,"macd":10.2,"momentum":0.09,"volatility":0.18,"from52wHigh":-0.11,"model":"random_forest","kpis":{"winRate":0.63,"sharpe":1.15,"mdd":-0.12},"updated":now_iso()},
    {"symbol":"NTPC","name":"NTPC Limited","sector":"Power","price":332.4,"volRegime":"HIGH","verdict":"HOLD","confidence":0.57,"rsi":49.6,"macd":-3.5,"momentum":-0.03,"volatility":0.24,"from52wHigh":-0.16,"model":"lstm","kpis":{"winRate":0.53,"sharpe":0.82,"mdd":-0.17},"updated":now_iso()},
    {"symbol":"ASIANPAINT","name":"Asian Paints","sector":"Paints","price":2456.7,"volRegime":"MEDIUM","verdict":"HOLD","confidence":0.60,"rsi":52.8,"macd":2.8,"momentum":0.02,"volatility":0.17,"from52wHigh":-0.13,"model":"ensemble","kpis":{"winRate":0.57,"sharpe":0.91,"mdd":-0.14},"updated":now_iso()},
    {"symbol":"POWERGRID","name":"Power Grid Corp","sector":"Power","price":245.6,"volRegime":"LOW","verdict":"CAUTIOUS","confidence":0.54,"rsi":44.2,"macd":-7.1,"momentum":-0.06,"volatility":0.15,"from52wHigh":-0.20,"model":"random_forest","kpis":{"winRate":0.46,"sharpe":0.68,"mdd":-0.22},"updated":now_iso()},
    {"symbol":"TATASTEEL","name":"Tata Steel","sector":"Steel","price":140.8,"volRegime":"HIGH","verdict":"AVOID","confidence":0.72,"rsi":35.6,"macd":-12.4,"momentum":-0.15,"volatility":0.32,"from52wHigh":-0.28,"model":"ensemble","kpis":{"winRate":0.42,"sharpe":0.45,"mdd":-0.35},"updated":now_iso()},
    {"symbol":"ONGC","name":"Oil & Natural Gas Corp","sector":"Oil & Gas","price":245.3,"volRegime":"HIGH","verdict":"CAUTIOUS","confidence":0.59,"rsi":47.8,"macd":-4.6,"momentum":-0.04,"volatility":0.27,"from52wHigh":-0.17,"model":"lstm","kpis":{"winRate":0.51,"sharpe":0.76,"mdd":-0.19},"updated":now_iso()},
    {"symbol":"JSWSTEEL","name":"JSW Steel","sector":"Steel","price":948.2,"volRegime":"HIGH","verdict":"HOLD","confidence":0.56,"rsi":50.3,"macd":-1.8,"momentum":-0.01,"volatility":0.29,"from52wHigh":-0.15,"model":"random_forest","kpis":{"winRate":0.54,"sharpe":0.84,"mdd":-0.16},"updated":now_iso()},
    {"symbol":"BAJFINANCE","name":"Bajaj Finance","sector":"NBFC","price":6842.5,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.71,"rsi":63.4,"macd":17.2,"momentum":0.17,"volatility":0.21,"from52wHigh":-0.05,"model":"ensemble","kpis":{"winRate":0.68,"sharpe":1.38,"mdd":-0.07},"updated":now_iso()},
    {"symbol":"TECHM","name":"Tech Mahindra","sector":"IT","price":1654.8,"volRegime":"MEDIUM","verdict":"HOLD","confidence":0.58,"rsi":51.7,"macd":1.4,"momentum":0.01,"volatility":0.20,"from52wHigh":-0.14,"model":"lstm","kpis":{"winRate":0.55,"sharpe":0.86,"mdd":-0.15},"updated":now_iso()},
    {"symbol":"ULTRACEMCO","name":"UltraTech Cement","sector":"Cement","price":11568.9,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.64,"rsi":57.6,"macd":9.8,"momentum":0.08,"volatility":0.18,"from52wHigh":-0.09,"model":"ensemble","kpis":{"winRate":0.62,"sharpe":1.12,"mdd":-0.11},"updated":now_iso()},
    {"symbol":"COALINDIA","name":"Coal India","sector":"Mining","price":405.7,"volRegime":"LOW","verdict":"HOLD","confidence":0.55,"rsi":49.8,"macd":-2.3,"momentum":-0.02,"volatility":0.16,"from52wHigh":-0.18,"model":"random_forest","kpis":{"winRate":0.52,"sharpe":0.79,"mdd":-0.19},"updated":now_iso()},
    {"symbol":"TITAN","name":"Titan Company","sector":"Jewellery","price":3245.6,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.68,"rsi":60.8,"macd":11.7,"momentum":0.12,"volatility":0.19,"from52wHigh":-0.07,"model":"ensemble","kpis":{"winRate":0.65,"sharpe":1.25,"mdd":-0.09},"updated":now_iso()},
    {"symbol":"NESTLEIND","name":"Nestle India","sector":"FMCG","price":2156.4,"volRegime":"LOW","verdict":"HOLD","confidence":0.61,"rsi":53.9,"macd":4.1,"momentum":0.04,"volatility":0.14,"from52wHigh":-0.11,"model":"lstm","kpis":{"winRate":0.58,"sharpe":0.93,"mdd":-0.12},"updated":now_iso()},
    {"symbol":"DRREDDY","name":"Dr Reddy's Labs","sector":"Pharma","price":1298.7,"volRegime":"MEDIUM","verdict":"BUY","confidence":0.66,"rsi":59.2,"macd":8.9,"momentum":0.09,"volatility":0.17,"from52wHigh":-0.08,"model":"ensemble","kpis":{"winRate":0.64,"sharpe":1.19,"mdd":-0.10},"updated":now_iso()},
    {"symbol":"GRASIM","name":"Grasim Industries","sector":"Chemicals","price":2589.3,"volRegime":"MEDIUM","verdict":"HOLD","confidence":0.59,"rsi":52.1,"macd":2.6,"momentum":0.02,"volatility":0.18,"from52wHigh":-0.13,"model":"random_forest","kpis":{"winRate":0.56,"sharpe":0.89,"mdd":-0.14},"updated":now_iso()},
    {"symbol":"HINDALCO","name":"Hindalco Industries","sector":"Metals","price":648.9,"volRegime":"HIGH","verdict":"CAUTIOUS","confidence":0.57,"rsi":46.5,"macd":-5.8,"momentum":-0.06,"volatility":0.25,"from52wHigh":-0.19,"model":"lstm","kpis":{"winRate":0.50,"sharpe":0.74,"mdd":-0.20},"updated":now_iso()},
    {"symbol":"BRITANNIA","name":"Britannia Industries","sector":"FMCG","price":4785.2,"volRegime":"LOW","verdict":"HOLD","confidence":0.63,"rsi":54.3,"macd":6.2,"momentum":0.06,"volatility":0.15,"from52wHigh":-0.10,"model":"ensemble","kpis":{"winRate":0.59,"sharpe":0.97,"mdd":-0.12},"updated":now_iso()}
]

def _generate_chart_data(symbol, timeframe="10D"):
    """Generate mock OHLC and technical indicator data"""
    import datetime
    from datetime import timedelta
    
    # Generate date range
    end_date = datetime.datetime.now()
    days = {"5D": 5, "10D": 10, "1M": 30, "3M": 90, "6M": 180, "1Y": 365}.get(timeframe, 10)
    start_date = end_date - timedelta(days=days)
    
    # Generate OHLC data
    prices = []
    base_price = next((eq["price"] for eq in _EQUITIES_DATA if eq["symbol"] == symbol), 1000)
    current_price = base_price
    
    for i in range(days):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        # Mock price movement
        change = random.uniform(-0.03, 0.03)
        current_price = current_price * (1 + change)
        high = current_price * (1 + random.uniform(0, 0.02))
        low = current_price * (1 - random.uniform(0, 0.02))
        
        prices.append({
            "t": date,
            "o": round(current_price * (1 + random.uniform(-0.01, 0.01)), 2),
            "h": round(high, 2),
            "l": round(low, 2),
            "c": round(current_price, 2)
        })
    
    # Generate RSI data
    rsi = [round(50 + random.uniform(-20, 20), 1) for _ in range(days)]
    
    # Generate MACD data
    macd = []
    for i in range(days):
        macd.append({
            "macd": round(random.uniform(-15, 15), 2),
            "signal": round(random.uniform(-10, 10), 2),
            "hist": round(random.uniform(-5, 5), 2)
        })
    
    # Generate Bollinger Bands
    bbands = []
    for price in prices:
        mid = price["c"]
        bbands.append({
            "upper": round(mid * 1.02, 2),
            "mid": round(mid, 2),
            "lower": round(mid * 0.98, 2)
        })
    
    return {
        "symbol": symbol,
        "tf": timeframe,
        "prices": prices,
        "rsi": rsi,
        "macd": macd,
        "bbands": bbands
    }

@equities_bp.get("/list")
def list_equities():
    force = request.args.get("forceRefresh","").lower() in ("1","true","yes")
    if not force:
        c=_cache.get("list"); 
        if c is not None: return jsonify(c)
    
    sector = request.args.get("sector","")
    price_min = float(request.args.get("priceMin","0") or 0)
    price_max = float(request.args.get("priceMax","999999") or 999999)
    scoreMin = float(request.args.get("scoreMin","0") or 0)
    
    items = [x for x in _EQUITIES_DATA if 
             (not sector or x["sector"]==sector) and 
             (x["confidence"]>=scoreMin) and
             (price_min <= x["price"] <= price_max)]
    
    payload = {"page":1,"pageSize":len(items),"total":len(items),"items":items}
    _cache.set("list", payload)
    return jsonify(payload)

@equities_bp.get("/charts/<symbol>")
def get_equity_charts(symbol):
    """Get OHLC and technical indicator data for charting"""
    timeframe = request.args.get("tf", "10D")
    
    # Check cache first
    cache_key = f"charts_{symbol}_{timeframe}"
    cached = _cache.get(cache_key)
    if cached:
        return jsonify(cached)
    
    # Generate chart data
    chart_data = _generate_chart_data(symbol, timeframe)
    
    # Cache for 5 minutes
    _cache.set(cache_key, chart_data)
    
    return jsonify(chart_data)

@equities_bp.get("/positions")
def get_positions():
    return jsonify({"items": _EQUITIES_DATA[:10]})  # Return subset for positions

@equities_bp.get("/kpis")
def eq_kpis():
    tf = request.args.get("timeframe","All")
    return jsonify({"timeframe":tf,"momentum":72,"volatility":"MEDIUM","trendADX":23,"breakoutProb":0.58,"earningsDays":12,"modelAcc":0.67,"avgHoldDays":9,"hitRate":0.64})

@equities_bp.get("/analytics")
def get_analytics():
    return jsonify({"portfolioValue": 1250000, "totalPnL": 85000, "winRate": 0.65, "sharpeRatio": 1.12})
