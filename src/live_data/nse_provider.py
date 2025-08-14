
import requests
import time
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from .provider import LiveProvider, Chain, OptionQuote, LiveDataError, cache

class NSEProvider(LiveProvider):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.base_url = "https://www.nseindia.com/api"
    
    def _make_request(self, url: str) -> Dict[str, Any]:
        """Make request with error handling"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise LiveDataError(f"Failed to fetch data from NSE: {str(e)}")
    
    def get_spot(self, symbol: str) -> float:
        cache_key = f"spot_{symbol}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.base_url}/quote-equity?symbol={symbol}"
            data = self._make_request(url)
            
            if 'priceInfo' not in data:
                raise LiveDataError(f"Invalid spot data for {symbol}")
            
            spot = float(data['priceInfo']['lastPrice'])
            cache.set(cache_key, spot)
            return spot
        except Exception as e:
            raise LiveDataError(f"Failed to get spot for {symbol}: {str(e)}")
    
    def get_expiries(self, symbol: str) -> List[str]:
        cache_key = f"expiries_{symbol}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            url = f"{self.base_url}/option-chain-indices?symbol={symbol}"
            data = self._make_request(url)
            
            if 'records' not in data or 'expiryDates' not in data['records']:
                raise LiveDataError(f"No expiry data for {symbol}")
            
            expiries = []
            for exp_str in data['records']['expiryDates']:
                try:
                    # Convert DD-Mon-YYYY to YYYY-MM-DD
                    exp_date = datetime.strptime(exp_str, "%d-%b-%Y")
                    expiries.append(exp_date.strftime("%Y-%m-%d"))
                except ValueError:
                    continue
            
            if not expiries:
                raise LiveDataError(f"No valid expiries found for {symbol}")
            
            cache.set(cache_key, expiries)
            return expiries
        except Exception as e:
            raise LiveDataError(f"Failed to get expiries for {symbol}: {str(e)}")
    
    def get_chain(self, symbol: str, expiry: str) -> Chain:
        cache_key = f"chain_{symbol}_{expiry}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            # Convert YYYY-MM-DD back to DD-Mon-YYYY for NSE API
            exp_date = datetime.strptime(expiry, "%Y-%m-%d")
            exp_str = exp_date.strftime("%d-%b-%Y")
            
            url = f"{self.base_url}/option-chain-indices?symbol={symbol}"
            data = self._make_request(url)
            
            if 'records' not in data:
                raise LiveDataError(f"No chain data for {symbol}")
            
            spot = float(data['records']['underlyingValue'])
            
            calls = []
            puts = []
            
            for record in data['records']['data']:
                if record.get('expiryDate') != exp_str:
                    continue
                
                strike = float(record['strikePrice'])
                
                # Process calls
                if 'CE' in record:
                    ce = record['CE']
                    calls.append(OptionQuote(
                        strike=strike,
                        iv=float(ce.get('impliedVolatility', 0)) if ce.get('impliedVolatility') else 0.0,
                        delta=float(ce.get('delta', 0)) if ce.get('delta') else 0.0,
                        theta=float(ce.get('theta', 0)) if ce.get('theta') else 0.0,
                        bid=float(ce.get('bidprice', 0)) if ce.get('bidprice') else 0.0,
                        ask=float(ce.get('askPrice', 0)) if ce.get('askPrice') else 0.0,
                        type="call"
                    ))
                
                # Process puts
                if 'PE' in record:
                    pe = record['PE']
                    puts.append(OptionQuote(
                        strike=strike,
                        iv=float(pe.get('impliedVolatility', 0)) if pe.get('impliedVolatility') else 0.0,
                        delta=float(pe.get('delta', 0)) if pe.get('delta') else 0.0,
                        theta=float(pe.get('theta', 0)) if pe.get('theta') else 0.0,
                        bid=float(pe.get('bidprice', 0)) if pe.get('bidprice') else 0.0,
                        ask=float(pe.get('askPrice', 0)) if pe.get('askPrice') else 0.0,
                        type="put"
                    ))
            
            if not calls or not puts:
                raise LiveDataError(f"Insufficient option data for {symbol} {expiry}")
            
            # Determine strike step
            strikes = sorted([q.strike for q in calls])
            step = min([strikes[i+1] - strikes[i] for i in range(len(strikes)-1)]) if len(strikes) > 1 else 100.0
            
            chain = Chain(
                symbol=symbol,
                spot=spot,
                expiry=expiry,
                step=step,
                calls=calls,
                puts=puts
            )
            
            cache.set(cache_key, chain)
            return chain
            
        except Exception as e:
            raise LiveDataError(f"Failed to get chain for {symbol} {expiry}: {str(e)}")
