#!/usr/bin/env python3
"""
Real-Time Data Fetcher with Web Scraping
Implements comprehensive real-time data collection from multiple sources
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
import time
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import threading
from dataclasses import dataclass
import random # Import the random module

logger = logging.getLogger(__name__)

@dataclass
class MarketData:
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    source: str
    high: float
    low: float
    open: float
    previous_close: float

class RealTimeDataFetcher:
    """Comprehensive real-time data fetcher with multiple sources"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}
        self.cache_timeout = 60  # 1 minute cache
        self.last_update = {}

    def get_realtime_data(self, symbol: str) -> Optional[MarketData]:
        """Get real-time data for a symbol"""
        try:
            # Check cache first
            if self._is_cache_valid(symbol):
                return self.cache[symbol]

            # Try multiple sources
            data = (self._fetch_yahoo_finance(symbol) or 
                   self._fetch_nse_data(symbol) or 
                   self._fetch_backup_data(symbol))

            if data:
                self.cache[symbol] = data
                self.last_update[symbol] = datetime.now()

            return data

        except Exception as e:
            logger.error(f"Error fetching real-time data for {symbol}: {str(e)}")
            return self._get_fallback_data(symbol)

    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache or symbol not in self.last_update:
            return False

        age = (datetime.now() - self.last_update[symbol]).seconds
        return age < self.cache_timeout

    def _fetch_yahoo_finance(self, symbol: str) -> Optional[MarketData]:
        """Fetch data from Yahoo Finance"""
        try:
            # Add .NS suffix for NSE symbols if not present
            yf_symbol = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol

            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            hist = ticker.history(period="1d", interval="1m")

            if hist.empty:
                return None

            latest = hist.iloc[-1]

            return MarketData(
                symbol=symbol,
                price=latest['Close'],
                change=latest['Close'] - info.get('previousClose', latest['Close']),
                change_percent=((latest['Close'] - info.get('previousClose', latest['Close'])) / 
                              info.get('previousClose', latest['Close'])) * 100,
                volume=int(latest['Volume']),
                timestamp=datetime.now(),
                source='yahoo_finance',
                high=latest['High'],
                low=latest['Low'],
                open=latest['Open'],
                previous_close=info.get('previousClose', latest['Close'])
            )

        except Exception as e:
            logger.warning(f"Yahoo Finance fetch failed for {symbol}: {str(e)}")
            return None

    def _fetch_nse_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch data from NSE website (web scraping)"""
        try:
            # NSE API endpoint (public)
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.nseindia.com/'
            }

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                price_info = data.get('priceInfo', {})

                if price_info:
                    return MarketData(
                        symbol=symbol,
                        price=float(price_info.get('lastPrice', 0)),
                        change=float(price_info.get('change', 0)),
                        change_percent=float(price_info.get('pChange', 0)),
                        volume=int(price_info.get('totalTradedVolume', 0)),
                        timestamp=datetime.now(),
                        source='nse_website',
                        high=float(price_info.get('intraDayHighLow', {}).get('max', 0)),
                        low=float(price_info.get('intraDayHighLow', {}).get('min', 0)),
                        open=float(price_info.get('open', 0)),
                        previous_close=float(price_info.get('previousClose', 0))
                    )

        except Exception as e:
            logger.warning(f"NSE fetch failed for {symbol}: {str(e)}")
            return None

    def _fetch_backup_data(self, symbol: str) -> Optional[MarketData]:
        """Fetch from backup sources"""
        try:
            # Use historical data as backup
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period="5d")

            if not hist.empty:
                latest = hist.iloc[-1]
                prev = hist.iloc[-2] if len(hist) > 1 else latest

                change = latest['Close'] - prev['Close']
                change_percent = (change / prev['Close']) * 100

                return MarketData(
                    symbol=symbol,
                    price=latest['Close'],
                    change=change,
                    change_percent=change_percent,
                    volume=int(latest['Volume']),
                    timestamp=datetime.now(),
                    source='backup_historical',
                    high=latest['High'],
                    low=latest['Low'],
                    open=latest['Open'],
                    previous_close=prev['Close']
                )

        except Exception as e:
            logger.warning(f"Backup fetch failed for {symbol}: {str(e)}")
            return None

    def _get_fallback_data(self, symbol: str) -> Optional[MarketData]:
        """Get fallback data from fixtures"""
        try:
            # Load sample data as absolute fallback
            import os
            fixture_path = os.path.join("data", "fixtures", "equities_sample.json")

            if os.path.exists(fixture_path):
                with open(fixture_path, 'r') as f:
                    fixtures = json.load(f)

                for item in fixtures.get('items', []):
                    if item.get('symbol') == symbol:
                        return MarketData(
                            symbol=symbol,
                            price=item.get('current_price', 100.0),
                            change=item.get('change_amount', 0.0),
                            change_percent=item.get('change_percent', 0.0),
                            volume=item.get('volume', 1000000),
                            timestamp=datetime.now(),
                            source='fallback_fixture',
                            high=item.get('day_high', 100.0),
                            low=item.get('day_low', 100.0),
                            open=item.get('open_price', 100.0),
                            previous_close=item.get('previous_close', 100.0)
                        )

        except Exception as e:
            logger.error(f"Fallback data failed for {symbol}: {str(e)}")

        return None

    def get_multiple_symbols(self, symbols: List[str]) -> Dict[str, MarketData]:
        """Get real-time data for multiple symbols concurrently"""
        results = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_symbol = {
                executor.submit(self.get_realtime_data, symbol): symbol 
                for symbol in symbols
            }

            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data:
                        results[symbol] = data
                except Exception as e:
                    logger.error(f"Error fetching {symbol}: {str(e)}")

        return results

    def start_realtime_stream(self, symbols: List[str], callback=None):
        """Start real-time streaming for symbols"""
        def stream_worker():
            while True:
                try:
                    data = self.get_multiple_symbols(symbols)
                    if callback:
                        callback(data)
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    logger.error(f"Streaming error: {str(e)}")
                    time.sleep(60)

        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()
        return thread

# Global instance
realtime_fetcher = RealTimeDataFetcher()

# Placeholder for get_sample_price function
def get_sample_price(symbol: str) -> Dict[str, Any]:
    """Provides a sample price for a given symbol as a fallback."""
    logger.warning(f"Using sample price for {symbol}")
    base_prices = {
        "RELIANCE": 2500, "TCS": 3800, "HDFCBANK": 1600, "INFY": 1400,
        "ICICIBANK": 950, "SBIN": 600, "BHARTIARTL": 850, "ITC": 450,
        "HINDUNILVR": 2400, "KOTAKBANK": 1700, "LT": 3200, "ASIANPAINT": 3100
    }
    base_price = base_prices.get(symbol.upper(), 1000.0)
    price_variation = random.uniform(-0.02, 0.02)
    current_price = base_price * (1 + price_variation)
    change = current_price - base_price
    change_percent = (change / base_price) * 100
    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "previous_close": base_price,
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "is_realtime": False,
        "timestamp": datetime.now().isoformat(),
        "source": "sample_fallback"
    }


def get_realtime_price(symbol: str) -> Dict[str, Any]:
    """
    Get real-time price for a single symbol
    """
    try:
        # Try different ticker formats for Indian stocks
        ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]

        for ticker_format in ticker_formats:
            try:
                ticker = yf.Ticker(ticker_format)
                # Get the most recent data with longer period to ensure we get data
                data = ticker.history(period="5d", interval="1d")

                if not data.empty and len(data) > 0:
                    current_price = float(data['Close'].iloc[-1])
                    previous_close = float(data['Close'].iloc[-2]) if len(data) > 1 else current_price

                    change = current_price - previous_close
                    change_percent = (change / previous_close * 100) if previous_close != 0 else 0

                    # Get intraday data for more recent price if available
                    try:
                        intraday = ticker.history(period="1d", interval="5m")
                        if not intraday.empty:
                            current_price = float(intraday['Close'].iloc[-1])
                            change = current_price - previous_close
                            change_percent = (change / previous_close * 100) if previous_close != 0 else 0
                    except:
                        pass  # Use daily price if intraday fails

                    return {
                        "symbol": symbol,
                        "current_price": current_price,
                        "previous_close": previous_close,
                        "change": change,
                        "change_percent": change_percent,
                        "is_realtime": True,
                        "timestamp": datetime.now().isoformat(),
                        "ticker_used": ticker_format
                    }
            except Exception as e:
                logger.warning(f"Failed to get real-time data for {ticker_format}: {str(e)}")
                continue

        # Fallback to sample data if real-time fails
        logger.warning(f"Real-time data unavailable for {symbol}, using sample data")
        return get_sample_price(symbol)

    except Exception as e:
        logger.error(f"Error in get_realtime_price for {symbol}: {str(e)}")
        return get_sample_price(symbol)


def get_multiple_realtime_prices(symbols: List[str]) -> Dict[str, Dict]:
    """
    Get real-time prices for multiple symbols efficiently with enhanced batching
    """
    results = {}

    try:
        logger.info(f"📊 Fetching real-time prices for {len(symbols)} symbols")

        # Process symbols in optimized batches
        batch_size = 5  # Smaller batches for better real-time performance
        successful_count = 0

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            logger.info(f"🔄 Processing batch {i//batch_size + 1}: {batch}")

            for symbol in batch:
                try:
                    price_data = get_realtime_price(symbol)
                    results[symbol] = price_data

                    if price_data.get("is_realtime"):
                        successful_count += 1

                    # Small delay to avoid overwhelming the API
                    time.sleep(0.2)

                except Exception as e:
                    logger.error(f"❌ Error getting price for {symbol}: {e}")
                    results[symbol] = {
                        "symbol": symbol,
                        "current_price": 0.0,
                        "error": str(e),
                        "is_realtime": False,
                        "timestamp": datetime.now().isoformat(),
                        "source": "error"
                    }

            # Delay between batches to respect rate limits
            if i + batch_size < len(symbols):
                time.sleep(0.5)

        logger.info(f"✅ Completed: {successful_count}/{len(symbols)} real-time, {len(symbols)-successful_count} fallback")

    except Exception as e:
        logger.error(f"❌ Critical error in batch price fetching: {e}")
        # Return error results for all symbols
        for symbol in symbols:
            if symbol not in results:
                results[symbol] = {
                    "symbol": symbol,
                    "current_price": 0.0,
                    "error": str(e),
                    "is_realtime": False,
                    "timestamp": datetime.now().isoformat(),
                    "source": "batch_error"
                }

    return results