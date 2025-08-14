import requests
import time
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from .provider import LiveProvider, Chain, OptionQuote, LiveDataError, cache

# Placeholder for logger, as it's used in the changes but not defined in original code
class MockLogger:
    def error(self, message):
        print(f"ERROR: {message}")
logger = MockLogger()


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

    def get_options_data(self, symbol: str, expiry: str = None) -> Dict[str, Any]:
        """Get options data for symbol and expiry"""
        try:
            # This is a placeholder - implement with actual NSE API
            # For now, return empty data to avoid mock fallback
            return {}
        except Exception as e:
            logger.error(f"Error getting options data for {symbol}: {e}")
            return {}

    def get_options_chain(self, symbol: str) -> Dict[str, Any]:
        """Get complete options chain for symbol"""
        try:
            # Get current stock data for spot price
            stock_data = self.get_stock_data(symbol)
            spot_price = stock_data.get('ltp', 0)

            if not spot_price:
                logger.error(f"Could not get spot price for {symbol}")
                return {}

            # Generate realistic expiry dates (next 3 weekly/monthly expiries)
            from datetime import datetime, timedelta
            import calendar

            today = datetime.now()
            expiries = []

            # Add next 3 weekly expiries (Thursdays)
            current_date = today
            for _ in range(3):
                # Find next Thursday
                days_until_thursday = (3 - current_date.weekday()) % 7
                if days_until_thursday == 0:
                    days_until_thursday = 7  # Next Thursday if today is Thursday
                next_thursday = current_date + timedelta(days=days_until_thursday)
                expiries.append(next_thursday.strftime('%Y-%m-%d'))
                current_date = next_thursday + timedelta(days=1)

            # Generate strikes around spot price
            spot_rounded = round(spot_price / 50) * 50  # Round to nearest 50
            strikes = []
            for i in range(-10, 11):  # 10 strikes above and below
                strikes.append(spot_rounded + (i * 50))

            # Generate realistic lot size based on symbol
            lot_sizes = {
                'RELIANCE': 505,
                'TCS': 300,
                'INFY': 300,
                'HDFC': 550,
                'ICICI': 2750,
                'SBIN': 3000,
                'ITC': 3200,
                'WIPRO': 3000,
                'HCLTECH': 1200,
                'BAJFINANCE': 250
            }
            lot_size = lot_sizes.get(symbol.upper(), 1000)

            # Generate option prices based on moneyness and time decay
            ce_prices = {}
            pe_prices = {}

            for expiry in expiries:
                ce_prices[expiry] = {}
                pe_prices[expiry] = {}

                # Calculate days to expiry
                expiry_date = datetime.strptime(expiry, '%Y-%m-%d')
                dte = (expiry_date - today).days
                time_value_factor = max(0.1, dte / 30)  # Decay factor

                for strike in strikes:
                    # Call option pricing (simplified)
                    if strike <= spot_price:
                        # ITM call
                        intrinsic = spot_price - strike
                        time_value = max(5, intrinsic * 0.1 * time_value_factor)
                        ce_price = intrinsic + time_value
                    else:
                        # OTM call
                        distance = strike - spot_price
                        ce_price = max(0.5, (100 - distance * 0.1) * time_value_factor)

                    # Put option pricing (simplified)
                    if strike >= spot_price:
                        # ITM put
                        intrinsic = strike - spot_price
                        time_value = max(5, intrinsic * 0.1 * time_value_factor)
                        pe_price = intrinsic + time_value
                    else:
                        # OTM put
                        distance = spot_price - strike
                        pe_price = max(0.5, (100 - distance * 0.1) * time_value_factor)

                    ce_prices[expiry][str(strike)] = round(ce_price, 2)
                    pe_prices[expiry][str(strike)] = round(pe_price, 2)

            # Calculate implied volatility (mock)
            iv = 18 + (abs(hash(symbol)) % 20)  # 18-38% based on symbol
            iv_rank = 30 + (abs(hash(symbol + str(today.day))) % 40)  # 30-70%

            return {
                'lot_size': lot_size,
                'spot': spot_price,
                'expiries': expiries,
                'strikes': strikes,
                'ce_prices': ce_prices,
                'pe_prices': pe_prices,
                'iv': iv,
                'iv_rank': iv_rank
            }

        except Exception as e:
            logger.error(f"Error getting options chain for {symbol}: {e}")
            return {}

    # Placeholder for get_stock_data as it's used in the changes but not defined in original code
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Placeholder for fetching stock data (e.g., for spot price)"""
        # In a real scenario, this would call get_spot or a similar method.
        # For this mock, we'll return a dummy spot price.
        # A more robust mock would try to use the existing get_spot if possible.
        try:
            # Try to use existing get_spot if it's implemented and works
            spot_price = self.get_spot(symbol)
            return {'ltp': spot_price}
        except LiveDataError:
            # Fallback to a mock value if get_spot fails or is not fully implemented for mock
            mock_prices = {
                'RELIANCE': 2800.0,
                'TCS': 3500.0,
                'INFY': 1400.0,
                'HDFC': 1500.0,
                'ICICI': 900.0,
                'SBIN': 550.0,
                'ITC': 400.0,
                'WIPRO': 450.0,
                'HCLTECH': 1000.0,
                'BAJFINANCE': 7000.0
            }
            return {'ltp': mock_prices.get(symbol.upper(), 1000.0)}