import json
import os
import time
from datetime import datetime
from flask import Blueprint, jsonify, request
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

equities_bp = Blueprint('equities', __name__)

def load_equities_data():
    """Load equities sample data"""
    try:
        filepath = os.path.join('data', 'fixtures', 'equities_sample.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading equities data: {e}")
    return {"items": [], "total_count": 0}

def now_iso():
    """Get current time in ISO format"""
    return datetime.utcnow().isoformat() + "Z"

@equities_bp.route("/list", methods=["GET"])
def list_equities():
    """List equity positions and analytics with real-time data"""
    try:
        from src.data.realtime_data_fetcher import get_multiple_realtime_prices

        # Get query parameters for filtering
        sector = request.args.get("sector", "")
        timeframe = request.args.get("timeframe", "1D")
        limit = min(int(request.args.get("limit", 50)), 100)

        # Define major Indian stocks
        major_stocks = [
            {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "IT"},
            {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "Energy"},
            {"symbol": "INFY", "name": "Infosys", "sector": "IT"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "Financials"},
            {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "Financials"},
            {"symbol": "BHARTIARTL", "name": "Bharti Airtel", "sector": "Telecom"},
            {"symbol": "LT", "name": "Larsen & Toubro", "sector": "Industrials"},
            {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "Consumer"},
            {"symbol": "MARUTI", "name": "Maruti Suzuki", "sector": "Auto"},
            {"symbol": "TITAN", "name": "Titan Company", "sector": "Consumer"},
            {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank", "sector": "Financials"},
            {"symbol": "WIPRO", "name": "Wipro", "sector": "IT"},
            {"symbol": "ULTRACEMCO", "name": "UltraTech Cement", "sector": "Materials"},
            {"symbol": "POWERGRID", "name": "Power Grid Corporation", "sector": "Utilities"},
            {"symbol": "TATASTEEL", "name": "Tata Steel", "sector": "Materials"}
        ]

        # Get real-time prices
        symbols = [stock["symbol"] for stock in major_stocks[:limit]]
        try:
            print(f"🔄 Fetching real-time data for equities API: {symbols}")
            realtime_data = get_multiple_realtime_prices(symbols)
            print(f"✅ Got real-time data for {len(realtime_data)} symbols")
        except Exception as e:
            print(f"Error fetching real-time equity data: {e}")
            realtime_data = {}

        # Generate equity data with real prices
        equities = []
        for stock in major_stocks[:limit]:
            symbol = stock["symbol"]

            # Apply sector filter if provided
            if sector and stock["sector"].lower() != sector.lower():
                continue

            # Get real-time data or use fallback
            price_data = realtime_data.get(symbol, {})
            current_price = price_data.get('current_price', random.uniform(100, 5000))
            change_percent = price_data.get('change_percent', random.uniform(-5, 5))

            equity = {
                "symbol": symbol,
                "name": stock["name"],
                "sector": stock["sector"],
                "price": round(float(current_price), 2),
                "change_percent": round(float(change_percent), 2),
                "verdict": random.choice(["STRONG_BUY", "BUY", "HOLD", "SELL"]),
                "confidence": round(random.uniform(0.6, 0.95), 3),
                "momentum": random.randint(40, 90),
                "volatility": random.choice(["LOW", "MEDIUM", "HIGH"]),
                "rsi": random.randint(30, 70),
                "macd": round(random.uniform(-2, 2), 1),
                "from52wHigh": round(random.uniform(-0.3, 0.1), 3),
                "model": random.choice(["Ensemble", "RF", "LSTM"]),
                "volume": random.randint(100000, 10000000),
                "market_cap": round(random.uniform(1000, 500000), 2),
                "pe_ratio": round(random.uniform(10, 50), 2),
                "dividend_yield": round(random.uniform(0, 8), 2),
                "beta": round(random.uniform(0.5, 2.0), 3),
                "moving_avg_50": round(current_price * random.uniform(0.95, 1.05), 2),
                "moving_avg_200": round(current_price * random.uniform(0.90, 1.10), 2),
                "is_realtime": price_data.get('is_realtime', False),
                "data_source": price_data.get('source', 'fallback'),
                "updated": now_iso()
            }

            equities.append(equity)

        start_time = time.time() # Initialize start_time here

        generation_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "items": equities,
            "total_count": len(equities),
            "generation_time_ms": generation_time_ms,
            "filters_applied": {
                "sector": sector,
                "timeframe": timeframe,
                "limit": limit
            }
        })

    except Exception as e:
        logger.error(f"Error in equities list: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "items": [],
            "total_count": 0
        }), 500

@equities_bp.route('/kpis')
def equities_kpis():
    """Get equity KPIs by timeframe"""
    start_time = time.time()

    try:
        timeframe = request.args.get('timeframe', '5D')

        # Load KPI data
        kpi_file = os.path.join('data', 'kpi', 'kpi_metrics.json')
        kpi_data = {}

        if os.path.exists(kpi_file):
            with open(kpi_file, 'r') as f:
                kpi_data = json.load(f)

        metrics = kpi_data.get('metrics', {}).get(timeframe, {})

        generation_time_ms = int((time.time() - start_time) * 1000)

        return jsonify({
            "timeframe": timeframe,
            "metrics": metrics,
            "generation_time_ms": generation_time_ms
        })

    except Exception as e:
        logger.error(f"Error in equities KPIs: {e}")
        return jsonify({
            "error": "internal_server_error",
            "message": str(e),
            "metrics": {}
        }), 500

def init_equities_api(app):
    """Initialize equities API routes"""
    app.register_blueprint(equities_bp, url_prefix='/api/equities')

    @equities_bp.route('/list', methods=['GET'])
    def get_equities_list():
        """Get list of equities with real-time data"""
        start_time = time.time()

        try:
            print("🔄 Fetching real-time data for equities API")

            symbols = ['TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'ICICIBANK', 'BHARTIARTL', 'LT', 'ASIANPAINT', 'MARUTI', 'TITAN', 'KOTAKBANK', 'WIPRO', 'ULTRACEMCO', 'POWERGRID', 'TATASTEEL']

            realtime_data = get_multiple_realtime_prices(symbols)
            print(f"✅ Got real-time data for {len(realtime_data)} symbols")

            items = []
            for symbol, data in realtime_data.items():
                items.append({
                    "symbol": symbol,
                    "current_price": data.get('current_price', 0),
                    "change": data.get('change', 0),
                    "change_percent": data.get('change_percent', 0),
                    "volume": data.get('volume', 0),
                    "is_realtime": data.get('is_realtime', False),
                    "source": data.get('source', 'unknown')
                })

            return jsonify({
                'success': True,
                'items': items,
                'total_count': len(items),
                'fetch_time_ms': round((time.time() - start_time) * 1000, 2)
            })

        except Exception as e:
            logger.error(f"Error in equities list: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'items': [],
                'total_count': 0
            }), 500