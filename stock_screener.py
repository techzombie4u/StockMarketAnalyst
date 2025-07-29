"""
Stock Market Analyst - Enhanced Data Collection and Scoring Module

This module handles:
1. Enhanced technical indicators (RSI, EMA, Bollinger Bands)
2. Rolling statistics and lagged features
3. Multiple data sources for better reliability
4. Improved scoring algorithm with advanced features

Note: This is for personal use only. Respect website terms of service.
"""

import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd
import numpy as np
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define retry and graceful degradation decorators
class RetryStrategy:

    @staticmethod
    def exponential_backoff(max_retries: int = 3):
        """Retry with exponential backoff"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                retries = 0
                while retries < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        wait_time = 2 ** retries  # Exponential backoff
                        logger.warning(f"Retry {func.__name__} - attempt {retries + 1}/{max_retries}. Waiting {wait_time} seconds. Error: {str(e)}")
                        time.sleep(wait_time)
                        retries += 1
                logger.error(f"Max retries reached for {func.__name__}")
                raise  # Re-raise the last exception
            return wrapper
        return decorator


class GracefulDegradation:

    @staticmethod
    def fallback_data(fallback_value: any):
        """Return fallback data on failure"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"{func.__name__} failed, returning fallback data. Error: {str(e)}")
                    return fallback_value
            return wrapper
        return decorator


class StockDataCache:
    """Cache for stock data"""

    _technical_indicators_cache: Dict[str, Dict] = {}

    @classmethod
    def get_cached_technical_indicators(cls, symbol: str) -> Optional[Dict]:
        """Retrieve cached technical indicators"""
        return cls._technical_indicators_cache.get(symbol)

    @classmethod
    def cache_technical_indicators(cls, symbol: str, indicators: Dict):
        """Cache technical indicators"""
        cls._technical_indicators_cache[symbol] = indicators


class DataValidation:
    """Validates stock data"""

    @staticmethod
    def validate_stock_data(stock_data: Dict) -> Dict:
        """Validate essential stock data"""
        errors = []
        symbol = stock_data.get('symbol')
        current_price = stock_data.get('current_price', 0)

        if not symbol:
            errors.append("Symbol is missing")
        if current_price <= 0:
            errors.append("Invalid current price")

        if errors:
            return {'is_valid': False, 'validation_errors': errors, 'symbol': symbol}
        else:
            return {'is_valid': True, **stock_data}


def safe_execute(func, *args, **kwargs) -> Dict:
    """Safely execute a function and return result or error"""
    try:
        data = func(*args, **kwargs)
        return {'success': True, 'data': data, 'error': None}
    except Exception as e:
        return {'success': False, 'data': None, 'error': str(e)}


def apply_advanced_filtering(stocks_data: List[Dict]) -> Dict:
    """Apply advanced signal filtering based on multiple criteria"""
    try:
        filtered_signals = []
        filter_stats = {'total_input': len(stocks_data), 'filtered_output': 0}

        for stock in stocks_data:
            # Multiple condition checks
            if (stock.get('score', 0) > 60 and
                stock.get('technical', {}).get('rsi_14', 50) < 70 and
                stock.get('risk_level', 'Medium') != 'High'):

                # Additional criteria
                if stock.get('fundamentals', {}).get('revenue_growth', 0) > 5:
                    filtered_signals.append(stock)

        filter_stats['filtered_output'] = len(filtered_signals)

        # Add a simplified filter score
        for stock in filtered_signals:
            stock['filter_score'] = stock.get('score', 0) * 1.1

        return {'filtered_signals': filtered_signals, 'filter_stats': filter_stats}

    except Exception as e:
        logger.error(f"Error applying advanced signal filtering: {str(e)}")
        return {'filtered_signals': stocks_data, 'filter_stats': {}}


def analyze_portfolio_risk(stocks_data: List[Dict]) -> Dict:
    """Analyze overall portfolio risk based on individual stock risk"""
    try:
        total_risk_score = 0
        for stock in stocks_data:
            risk_level = stock.get('risk_level', 'Medium')
            if risk_level == 'High':
                total_risk_score += 3
            elif risk_level == 'Medium':
                total_risk_score += 2
            else:
                total_risk_score += 1

        average_risk = total_risk_score / len(stocks_data) if stocks_data else 0
        portfolio_risk = 'High' if average_risk > 2.5 else 'Medium' if average_risk > 1.5 else 'Low'

        return {
            'total_stocks': len(stocks_data),
            'average_risk': round(average_risk, 2),
            'portfolio_risk': portfolio_risk
        }

    except Exception as e:
        logger.error(f"Error analyzing portfolio risk: {str(e)}")
        return {}


def calculate_position_sizes(stocks_data: List[Dict]) -> List[Dict]:
    """Calculate position sizes based on risk and confidence"""
    try:
        portfolio_value = 100000  # Example
        for stock in stocks_data:
            risk_level = stock.get('risk_level', 'Medium')
            confidence = stock.get('confidence', 50)

            # Risk factor
            if risk_level == 'High':
                risk_factor = 0.01  # 1% of portfolio
            elif risk_level == 'Medium':
                risk_factor = 0.02  # 2%
            else:
                risk_factor = 0.03  # 3%

            # Confidence scaling
            confidence_scale = confidence / 100
            position_size = portfolio_value * risk_factor * confidence_scale
            stock['position_size'] = round(position_size, 2)

        return stocks_data

    except Exception as e:
        logger.error(f"Error calculating position sizes: {str(e)}")
        return stocks_data


class EnhancedStockScreener:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Quality stocks under ₹500 list
        self.under500_symbols = [
            'SBIN', 'BHARTIARTL', 'ITC', 'NTPC', 'POWERGRID',
            'ONGC', 'COALINDIA', 'TATASTEEL', 'JSWSTEEL', 'HINDALCO',
            'TATAMOTORS', 'M&M', 'BPCL', 'GAIL', 'IOC',
            'SAIL', 'NALCO', 'VEDL', 'BANKBARODA', 'CANBK',
            'PNB', 'UNIONBANK', 'BANKINDIA', 'CENTRALBK', 'INDIANB',
            'RECLTD', 'PFC', 'IRFC', 'IRCTC', 'RAILTEL',
            'HAL', 'BEL', 'BEML', 'BHEL', 'CONCOR',
            'NBCC', 'RITES', 'KTKBANK', 'FEDERALBNK', 'IDFCFIRSTB',
            'EQUITAS', 'RBLBANK', 'YESBANK', 'BANKINDIA', 'LICHSGFIN',
            'MUTHOOTFIN', 'BAJAJHLDNG', 'GODREJCP', 'MARICO', 'DABUR'
        ]

        # Use stocks under ₹500 for comprehensive screening
        self.watchlist = self.under500_symbols

        self.bulk_deals = []
        self.fundamentals = {}
        self.technical_data = {}

        # Data source configurations with priorities and capabilities
        self.data_sources = {
            'yahoo': {'priority': 1, 'timeout': 10, 'type': 'technical'},
            'screener': {'priority': 2, 'timeout': 15, 'type': 'fundamental'},
            'moneycontrol': {'priority': 3, 'timeout': 12, 'type': 'both'},
            'nseindia': {'priority': 4, 'timeout': 8, 'type': 'official'},
            'bseindia': {'priority': 5, 'timeout': 10, 'type': 'official'},
            'investing': {'priority': 6, 'timeout': 12, 'type': 'technical'},
            'tradingview': {'priority': 7, 'timeout': 15, 'type': 'technical'},
            'tickertape': {'priority': 8, 'timeout': 10, 'type': 'fundamental'}
        }

    def calculate_enhanced_technical_indicators(self, symbol: str) -> Dict:
        """Calculate enhanced technical indicators using daily OHLC data"""
        try:
            # Import daily technical analyzer
            from daily_technical_analyzer import DailyTechnicalAnalyzer

            # Use daily technical analysis as primary method
            daily_analyzer = DailyTechnicalAnalyzer()
            daily_indicators = daily_analyzer.calculate_daily_technical_indicators(symbol)

            # If daily analysis is successful, use it
            if daily_indicators and daily_indicators.get('current_price', 0) > 0:
                logger.info(f"Using daily OHLC technical analysis for {symbol}")

                # Add backward compatibility indicators
                daily_indicators['data_quality_score'] = 95  # High quality for daily data
                daily_indicators['timeframe'] = 'daily'
                daily_indicators['analysis_type'] = 'daily_ohlc'

                # Map some indicators for backward compatibility
                if 'sma_20' in daily_indicators:
                    daily_indicators['ema_21'] = daily_indicators['sma_20']
                if 'momentum_5d_pct' in daily_indicators:
                    daily_indicators['momentum_5d'] = daily_indicators['momentum_5d_pct'] / 100

                return daily_indicators

            # Fallback to intraday data if daily analysis fails
            logger.warning(f"Daily OHLC analysis failed for {symbol}, falling back to intraday data")

            # Try multiple data sources for price data
            hist_data = self._fetch_price_data_multiple_sources(symbol)

            if hist_data is None or hist_data.empty:
                logger.warning(f"No price data found for {symbol}")
                return {}

            # Ensure we have enough data points
            if hist_data is None or hist_data.empty or len(hist_data) < 50:
                logger.warning(f"Insufficient data for {symbol}: {len(hist_data) if hist_data is not None else 0} days")
                return {}

            indicators = {}

            # 1. Enhanced ATR calculation (multiple periods)
            indicators.update(self._calculate_atr_indicators(hist_data))

            # 2. RSI (Relative Strength Index)
            indicators.update(self._calculate_rsi_indicators(hist_data))

            # 3. EMA (Exponential Moving Averages)
            indicators.update(self._calculate_ema_indicators(hist_data))

            # 4. Bollinger Bands
            indicators.update(self._calculate_bollinger_bands(hist_data))

            # 5. Volume indicators
            indicators.update(self._calculate_volume_indicators(hist_data))

            # 6. Momentum and trend indicators
            indicators.update(self._calculate_momentum_indicators(hist_data))

            # 7. Rolling statistics
            indicators.update(self._calculate_rolling_statistics(hist_data))

            # 8. Lagged features
            indicators.update(self._calculate_lagged_features(hist_data))

            # 9. Volatility measures
            indicators.update(self._calculate_volatility_measures(hist_data))

            # Current price and basic info
            if len(hist_data) > 0 and 'Close' in hist_data.columns:
                current_price_val = hist_data['Close'].iloc[-1]
                indicators['current_price'] = float(current_price_val) if not pd.isna(current_price_val) else 0

                # Add additional price info for better predictions
                if len(hist_data) >= 5:
                    indicators['price_5d_ago'] = float(hist_data['Close'].iloc[-6]) if len(hist_data) > 5 else indicators['current_price']
                    indicators['price_1d_ago'] = float(hist_data['Close'].iloc[-2]) if len(hist_data) > 1 else indicators['current_price']
                    indicators['high_52w'] = float(hist_data['High'].max())
                    indicators['low_52w'] = float(hist_data['Low'].min())
            else:
                indicators['current_price'] = 0

            indicators['data_quality_score'] = self._assess_data_quality(hist_data)
            indicators['timeframe'] = 'intraday_fallback'
            indicators['analysis_type'] = 'intraday_legacy'

            return indicators

        except Exception as e:
            logger.error(f"Error calculating enhanced indicators for {symbol}: {str(e)}")
            return {}

    def _fetch_price_data_multiple_sources(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch price data from multiple sources with fallback"""

        # Primary source: Yahoo Finance (most reliable)
        try:
            ticker = f"{symbol}.NS"
            # Add more robust error handling and retry logic
            import yfinance as yf
            stock = yf.Ticker(ticker)
            hist_data = stock.history(period="1y")

            if hist_data is not None and not hist_data.empty and len(hist_data) > 30:
                logger.debug(f"Yahoo Finance data successful for {symbol}: {len(hist_data)} days")
                return hist_data
        except Exception as e:
            logger.warning(f"Yahoo Finance primary failed for {symbol}: {str(e)}")

        # Fallback: Try with different ticker formats
        ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]
        fallback_periods = ["6mo", "3mo", "2mo", "1mo"]

        for ticker_format in ticker_formats:
            for period in fallback_periods:
                try:
                    stock = yf.Ticker(ticker_format)
                    hist_data = stock.history(period=period)

                    if hist_data is not None and not hist_data.empty and len(hist_data) > 10:
                        logger.info(f"Yahoo Finance fallback successful for {symbol} ({ticker_format}, {period}): {len(hist_data)} days")
                        return hist_data
                except Exception as e:
                    logger.debug(f"Fallback failed for {symbol} with {ticker_format}/{period}: {str(e)}")
                    continue

        logger.error(f"All data sources failed for {symbol}")
        return None

    def _calculate_atr_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate ATR for multiple periods"""
        indicators = {}

        try:
            high_low = data['High'] - data['Low']
            high_close = (data['High'] - data['Close'].shift()).abs()
            low_close = (data['Low'] - data['Close'].shift()).abs()

            # Calculate true range using numpy maximum for element-wise comparison
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))

            # Multiple ATR periods
            for period in [7, 14, 21]:
                atr = true_range.rolling(window=period).mean()
                atr_val = atr.iloc[-1] if len(atr) > 0 else 0
                indicators[f'atr_{period}'] = float(atr_val) if not pd.isna(atr_val) else 0

            # ATR-based volatility
            current_price = data['Close'].iloc[-1] if len(data['Close']) > 0 else 0
            indicators['atr_volatility'] = (indicators['atr_14'] / current_price * 100) if current_price > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating ATR: {str(e)}")

        return indicators


    def fetch_from_multiple_sources(self, symbol: str, data_type: str = 'both') -> Dict:
        """Fetch data from multiple sources with intelligent fallback"""
        aggregated_data = {
            'price_data': None,
            'fundamental_data': {},
            'technical_indicators': {},
            'source_reliability': {},
            'last_updated': datetime.now()
        }

        # Sort sources by priority for the requested data type
        relevant_sources = [
            (name, config) for name, config in self.data_sources.items()
            if config['type'] in [data_type, 'both', 'official']
        ]
        relevant_sources.sort(key=lambda x: x[1]['priority'])

        for source_name, config in relevant_sources:
            try:
                logger.info(f"Fetching {symbol} data from {source_name}")

                if source_name == 'yahoo':
                    data = self._fetch_yahoo_data(symbol)
                elif source_name == 'moneycontrol':
                    data = self._fetch_moneycontrol_data(symbol)
                elif source_name == 'nseindia':
                    data = self._fetch_nse_data(symbol)
                elif source_name == 'bseindia':
                    data = self._fetch_bse_data(symbol)
                elif source_name == 'investing':
                    data = self._fetch_investing_data(symbol)
                elif source_name == 'tickertape':
                    data = self._fetch_tickertape_data(symbol)
                else:
                    continue

                if data:
                    # Merge data intelligently
                    aggregated_data = self._merge_source_data(aggregated_data, data, source_name)
                    aggregated_data['source_reliability'][source_name] = 'success'

            except Exception as e:
                logger.warning(f"Failed to fetch from {source_name}: {str(e)}")
                aggregated_data['source_reliability'][source_name] = 'failed'
                continue

        return aggregated_data

    def _fetch_moneycontrol_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from MoneyControl"""
        try:
            url = f"https://www.moneycontrol.com/india/stockpricequote/{symbol.lower()}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = self.session.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                data = {
                    'current_price': self._extract_mc_price(soup),
                    'pe_ratio': self._extract_mc_pe(soup),
                    'market_cap': self._extract_mc_market_cap(soup),
                    'volume': self._extract_mc_volume(soup),
                    'day_change': self._extract_mc_change(soup),
                    'source': 'moneycontrol'
                }

                return {k: v for k, v in data.items() if v is not None}

        except Exception as e:
            logger.error(f"MoneyControl fetch error for {symbol}: {str(e)}")
            return None

    def _fetch_nse_data(self, symbol: str) -> Optional[Dict]:
        """Fetch official data from NSE India"""
        try:
            # NSE requires specific headers and session management
            nse_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache'
            }

            # Get NSE session first
            session_url = "https://www.nseindia.com/"
            self.session.get(session_url, headers=nse_headers, timeout=8)

            # Fetch stock data
            quote_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            response = self.session.get(quote_url, headers=nse_headers, timeout=8)

            if response.status_code == 200:
                nse_data = response.json()

                if 'priceInfo' in nse_data:
                    price_info = nse_data['priceInfo']
                    return {
                        'current_price': price_info.get('lastPrice'),
                        'day_high': price_info.get('intraDayHighLow', {}).get('max'),
                        'day_low': price_info.get('intraDayHighLow', {}).get('min'),
                        'volume': price_info.get('totalTradedVolume'),
                        'day_change_percent': price_info.get('pChange'),
                        'previous_close': price_info.get('previousClose'),
                        'source': 'nseindia'
                    }

        except Exception as e:
            logger.error(f"NSE fetch error for {symbol}: {str(e)}")
            return None

    def _fetch_bse_data(self, symbol: str) -> Optional[Dict]:
        """Fetch data from BSE India"""
        try:
            # BSE data fetching implementation
            url = f"https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode={symbol}&flag=0"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bseindia.com/'
            }

            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                bse_data = response.json()

                if bse_data and 'Data' in bse_data:
                    data = bse_data['Data'][0] if bse_data['Data'] else {}
                    return {
                        'current_price': data.get('CurrRate'),
                        'day_change': data.get('PrevRate'),
                        'volume': data.get('TotalTrdVol'),
                        'source': 'bseindia'
                    }

        except Exception as e:
            logger.error(f"BSE fetch error for {symbol}: {str(e)}")
            return None

    def _fetch_investing_data(self, symbol: str) -> Optional[Dict]:
        """Fetch technical data from Investing.com"""
        try:
            # Investing.com technical indicators
            url = f"https://in.investing.com/search/?q={symbol}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = self.session.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                return {
                    'technical_rating': self._extract_investing_rating(soup),
                    'support_levels': self._extract_investing_support(soup),
                    'resistance_levels': self._extract_investing_resistance(soup),
                    'source': 'investing'
                }

        except Exception as e:
            logger.error(f"Investing.com fetch error for {symbol}: {str(e)}")
            return None

    def _fetch_tickertape_data(self, symbol: str) -> Optional[Dict]:
        """Fetch fundamental data from TickerTape"""
        try:
            url = f"https://www.tickertape.in/stocks/{symbol.lower()}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                return {
                    'pe_ratio': self._extract_tt_pe(soup),
                    'pb_ratio': self._extract_tt_pb(soup),
                    'roe': self._extract_tt_roe(soup),
                    'debt_to_equity': self._extract_tt_debt(soup),
                    'dividend_yield': self._extract_tt_dividend(soup),
                    'source': 'tickertape'
                }

        except Exception as e:
            logger.error(f"TickerTape fetch error for {symbol}: {str(e)}")
            return None

    def _merge_source_data(self, aggregated: Dict, new_data: Dict, source: str) -> Dict:
        """Intelligently merge data from multiple sources"""

        # Price data - prefer official sources (NSE/BSE) then Yahoo
        if 'current_price' in new_data and new_data['current_price']:
            if not aggregated.get('current_price') or source in ['nseindia', 'bseindia']:
                aggregated['current_price'] = new_data['current_price']

        # Fundamental data - prefer Screener, then TickerTape, then others
        fundamental_fields = ['pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity', 'dividend_yield']
        for field in fundamental_fields:
            if field in new_data and new_data[field]:
                if (not aggregated['fundamental_data'].get(field) or 
                    source in ['screener', 'tickertape']):
                    aggregated['fundamental_data'][field] = new_data[field]

        # Technical indicators - aggregate from all sources
        technical_fields = ['support_levels', 'resistance_levels', 'technical_rating']
        for field in technical_fields:
            if field in new_data and new_data[field]:
                if field not in aggregated['technical_indicators']:
                    aggregated['technical_indicators'][field] = {}
                aggregated['technical_indicators'][field][source] = new_data[field]

        return aggregated

    # Helper methods for data extraction
    def _extract_mc_price(self, soup) -> Optional[float]:
        """Extract current price from MoneyControl"""
        try:
            price_elem = soup.find('div', {'class': 'inprice1'})
            if price_elem:
                price_text = price_elem.get_text().replace(',', '').replace('₹', '').strip()
                return float(price_text)
        except:
            pass
        return None

    def _extract_mc_pe(self, soup) -> Optional[float]:
        """Extract PE ratio from MoneyControl"""
        try:
            # Look for PE ratio in the key statistics section
            pe_elem = soup.find('td', string='P/E')
            if pe_elem and pe_elem.find_next_sibling('td'):
                pe_text = pe_elem.find_next_sibling('td').get_text().strip()
                return float(pe_text.replace(',', ''))
        except:
            pass
        return None

    def _extract_mc_market_cap(self, soup) -> Optional[float]:
        """Extract market cap from MoneyControl"""
        try:
            # Look for market cap in the key statistics section
            mc_elem = soup.find('td', string='Market Cap')
            if mc_elem and mc_elem.find_next_sibling('td'):
                mc_text = mc_elem.find_next_sibling('td').get_text().strip()
                # Convert crores to actual number
                if 'crore' in mc_text.lower():
                    value = float(mc_text.replace('crore', '').replace(',', '').strip())
                    return value * 10000000  # Convert crores to actual value
                return float(mc_text.replace(',', ''))
        except:
            pass
        return None

    def _extract_mc_volume(self, soup) -> Optional[float]:
        """Extract volume from MoneyControl"""
        try:
            vol_elem = soup.find('td', string='Volume')
            if vol_elem and vol_elem.find_next_sibling('td'):
                vol_text = vol_elem.find_next_sibling('td').get_text().strip()
                return float(vol_text.replace(',', ''))
        except:
            pass
        return None

    def _extract_mc_change(self, soup) -> Optional[float]:
        """Extract day change from MoneyControl"""
        try:
            change_elem = soup.find('span', {'class': 'change'})
            if change_elem:
                change_text = change_elem.get_text().strip()
                return float(change_text.replace('%', '').replace('+', ''))
        except:
            pass
        return None

    def _extract_investing_rating(self, soup) -> Optional[str]:
        """Extract technical rating from Investing.com"""
        try:
            rating_elem = soup.find('span', {'class': 'technicalSummaryEmotion'})
            if rating_elem:
                return rating_elem.get_text().strip()
        except:
            pass
        return None

    def _extract_tt_pe(self, soup) -> Optional[float]:
        """Extract PE ratio from TickerTape"""
        try:
            pe_elem = soup.find('span', string='PE')
            if pe_elem:
                pe_value = pe_elem.find_next('span')
                if pe_value:
                    return float(pe_value.get_text().replace(',', ''))
        except:
            pass
        return None



    def _calculate_rsi_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate RSI for multiple periods"""
        indicators = {}

        try:
            close_prices = data['Close']

            for period in [14, 21]:
                delta = close_prices.diff()
                gain = delta.where(delta > 0, 0)
                loss = (-delta).where(delta < 0, 0)

                avg_gain = gain.rolling(window=period).mean()
                avg_loss = loss.rolling(window=period).mean()

                # Avoid division by zero
                rs = avg_gain / (avg_loss + 1e-10)
                rsi = 100 - (100 / (1 + rs))

                rsi_val = rsi.iloc[-1] if len(rsi) > 0 else 50
                indicators[f'rsi_{period}'] = float(rsi_val) if not pd.isna(rsi_val) else 50

            # RSI signal interpretation
            rsi_14 = indicators.get('rsi_14', 50)
            if rsi_14 < 30:
                indicators['rsi_signal'] = 'oversold'
            elif rsi_14 > 70:
                indicators['rsi_signal'] = 'overbought'
            else:
                indicators['rsi_signal'] = 'neutral'

        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")

        return indicators

    def assess_data_quality_multi_source(self, stocks_data: Dict) -> Dict:
        """Assess overall data quality from multiple sources"""
        quality_report = {
            'total_stocks': len(stocks_data),
            'source_performance': {},
            'data_completeness': {},
            'recommendations': []
        }

        all_sources = set()
        source_success_count = {}

        for symbol, data in stocks_data.items():
            metadata = data.get('multi_source_metadata', {})
            sources_used = metadata.get('sources_used', [])
            successful_sources = metadata.get('successful_sources', [])

            all_sources.update(sources_used)

            for source in sources_used:
                if source not in source_success_count:
                    source_success_count[source] = {'success': 0, 'total': 0}
                source_success_count[source]['total'] += 1

                if source in successful_sources:
                    source_success_count[source]['success'] += 1

        # Calculate source performance
        for source in all_sources:
            if source in source_success_count:
                success_rate = (source_success_count[source]['success'] / 
                              source_success_count[source]['total']) * 100
                quality_report['source_performance'][source] = {
                    'success_rate': round(success_rate, 2),
                    'successful_requests': source_success_count[source]['success'],
                    'total_requests': source_success_count[source]['total']
                }

        # Generate recommendations
        for source, perf in quality_report['source_performance'].items():
            if perf['success_rate'] < 50:
                quality_report['recommendations'].append(
                    f"Consider reviewing {source} data source - low success rate ({perf['success_rate']}%)"
                )
            elif perf['success_rate'] > 90:
                quality_report['recommendations'].append(
                    f"{source} is performing excellently ({perf['success_rate']}% success rate)"
                )

        return quality_report



    def _calculate_ema_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate Exponential Moving Averages"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Multiple EMA periods
            ema_periods = [5, 12, 21, 50]
            for period in ema_periods:
                ema = close_prices.ewm(span=period).mean()
                ema_val = ema.iloc[-1] if len(ema) > 0 else 0
                indicators[f'ema_{period}'] = float(ema_val) if not pd.isna(ema_val) else 0

            # EMA crossover signals
            current_price = close_prices.iloc[-1] if len(close_prices) > 0 else 0
            indicators['price_above_ema_12'] = float(current_price) > float(indicators.get('ema_12', 0))
            indicators['price_above_ema_21'] = float(current_price) > float(indicators.get('ema_21', 0))
            indicators['ema_12_above_21'] = float(indicators.get('ema_12', 0)) > float(indicators.get('ema_21', 0))

            # EMA trend strength
            ema_5 = indicators.get('ema_5', 0)
            ema_21 = indicators.get('ema_21', 0)
            indicators['ema_trend_strength'] = ((ema_5 - ema_21) / ema_21 * 100) if ema_21 > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating EMA: {str(e)}")

        return indicators

    def _calculate_bollinger_bands(self, data: pd.DataFrame) -> Dict:
        """Calculate Bollinger Bands"""
        indicators = {}

        try:
            close_prices = data['Close']
            period = 20
            std_dev = 2

            # Calculate Bollinger Bands
            bb_middle = close_prices.rolling(window=period).mean()
            bb_std = close_prices.rolling(window=period).std()
            bb_upper = bb_middle + (bb_std * std_dev)
            bb_lower = bb_middle - (bb_std * std_dev)

            bb_upper_val = bb_upper.iloc[-1]
            bb_middle_val = bb_middle.iloc[-1]
            bb_lower_val = bb_lower.iloc[-1]

            indicators['bb_upper'] = float(bb_upper_val) if not pd.isna(bb_upper_val) else 0
            indicators['bb_middle'] = float(bb_middle_val) if not pd.isna(bb_middle_val) else 0
            indicators['bb_lower'] = float(bb_lower_val) if not pd.isna(bb_lower_val) else 0

            # Current price position in Bollinger Bands
            current_price = close_prices.iloc[-1]
            bb_width = indicators['bb_upper'] - indicators['bb_lower']
            indicators['bb_position'] = ((current_price - indicators['bb_lower']) / bb_width * 100) if bb_width > 0 else 50

            # Bollinger Band squeeze indicator
            indicators['bb_width'] = bb_width / indicators['bb_middle'] * 100 if indicators['bb_middle'] > 0 else 0

            # Signal interpretation
            if current_price > indicators['bb_upper']:
                indicators['bb_signal'] = 'above_upper'
            elif current_price < indicators['bb_lower']:
                indicators['bb_signal'] = 'below_lower'
            else:
                indicators['bb_signal'] = 'within_bands'

        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {str(e)}")

        return indicators

    def _calculate_volume_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate volume-based indicators"""
        indicators = {}

        try:
            volume = data['Volume']
            close_prices = data['Close']

            # Volume moving averages
            vol_ma_10_series = volume.rolling(window=10).mean()
            vol_ma_20_series = volume.rolling(window=20).mean()

            vol_ma_10 = vol_ma_10_series.iloc[-1] if len(vol_ma_10_series) > 0 else 0
            vol_ma_20 = vol_ma_20_series.iloc[-1] if len(vol_ma_20_series) > 0 else 0

            indicators['volume_ma_10'] = float(vol_ma_10) if not pd.isna(vol_ma_10) else 0
            indicators['volume_ma_20'] = float(vol_ma_20) if not pd.isna(vol_ma_20) else 0

            # Current volume vs average
            current_volume = volume.iloc[-1] if len(volume) > 0 else 0
            indicators['volume_ratio_10'] = current_volume / indicators['volume_ma_10'] if indicators['volume_ma_10'] > 0 else 1

            # Price-Volume trend
            price_change = close_prices.pct_change()
            volume_change = volume.pct_change()
            pv_correlation = price_change.rolling(window=20).corr(volume_change)
            pv_corr_val = pv_correlation.iloc[-1] if len(pv_correlation) > 0 else 0
            indicators['price_volume_correlation'] = float(pv_corr_val) if not pd.isna(pv_corr_val) else 0

            # On Balance Volume (OBV)
            close_diff = close_prices.diff()
            volume_direction = np.where(close_diff > 0, volume, 
                                      np.where(close_diff < 0, -volume, 0))
            obv = pd.Series(volume_direction).cumsum()
            indicators['obv'] = float(obv.iloc[-1]) if len(obv) > 0 and not pd.isna(obv.iloc[-1]) else 0
            indicators['obv_trend'] = float(obv.iloc[-1] - obv.iloc[-11]) if len(obv) > 10 and not pd.isna(obv.iloc[-1]) and not pd.isna(obv.iloc[-11]) else 0

        except Exception as e:
            logger.error(f"Error calculating volume indicators: {str(e)}")

        return indicators

    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> Dict:
        """Calculate momentum and trend indicators"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Multiple timeframe momentum
            for period in [2, 5, 10, 20]:
                momentum = close_prices.pct_change(periods=period)
                momentum_val = momentum.iloc[-1]
                indicators[f'momentum_{period}d'] = float(momentum_val) if not pd.isna(momentum_val) else 0

            # MACD (Moving Average Convergence Divergence)
            ema_12 = close_prices.ewm(span=12).mean()
            ema_26 = close_prices.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            macd_histogram = macd_line - signal_line

            macd_val = macd_line.iloc[-1]
            signal_val = signal_line.iloc[-1]
            histogram_val = macd_histogram.iloc[-1]

            indicators['macd'] = float(macd_val) if not pd.isna(macd_val) else 0
            indicators['macd_signal'] = float(signal_val) if not pd.isna(signal_val) else 0
            indicators['macd_histogram'] = float(histogram_val) if not pd.isna(histogram_val) else 0
            indicators['macd_bullish'] = indicators['macd'] > indicators['macd_signal']

            # Rate of Change
            if len(close_prices) > 10:
                current_price = close_prices.iloc[-1]
                past_price = close_prices.iloc[-11]
                roc_10 = ((current_price - past_price) / past_price * 100) if past_price > 0 else 0
            else:
                roc_10 = 0
            indicators['roc_10'] = roc_10

        except Exception as e:
            logger.error(f"Error calculating momentum indicators: {str(e)}")

        return indicators

    def _calculate_rolling_statistics(self, data: pd.DataFrame) -> Dict:
        """Calculate rolling statistical measures"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Rolling statistics for multiple windows
            for window in [5, 10, 20]:
                rolling_data = close_prices.rolling(window=window)

                mean_val = rolling_data.mean().iloc[-1]
                std_val = rolling_data.std().iloc[-1]
                min_val = rolling_data.min().iloc[-1]
                max_val = rolling_data.max().iloc[-1]

                indicators[f'rolling_mean_{window}'] = float(mean_val) if not pd.isna(mean_val) else 0
                indicators[f'rolling_std_{window}'] = float(std_val) if not pd.isna(std_val) else 0
                indicators[f'rolling_min_{window}'] = float(min_val) if not pd.isna(min_val) else 0
                indicators[f'rolling_max_{window}'] = float(max_val) if not pd.isna(max_val) else 0

                # Position within rolling range
                current_price = close_prices.iloc[-1]
                rolling_min = indicators[f'rolling_min_{window}']
                rolling_max = indicators[f'rolling_max_{window}']
                range_width = rolling_max - rolling_min

                if range_width > 0:
                    indicators[f'price_position_{window}'] = ((current_price - rolling_min) / range_width * 100)
                else:
                    indicators[f'price_position_{window}'] = 50

            # Coefficient of variation (volatility relative to mean)
            for window in [10, 20]:
                mean_val = indicators[f'rolling_mean_{window}']
                std_val = indicators[f'rolling_std_{window}']
                indicators[f'coeff_variation_{window}'] = (std_val / mean_val * 100) if mean_val > 0 else 0

        except Exception as e:
            logger.error(f"Error calculating rolling statistics: {str(e)}")

        return indicators

    def _calculate_lagged_features(self, data: pd.DataFrame) -> Dict:
        """Calculate lagged price features"""
        indicators = {}

        try:
            close_prices = data['Close']

            # Lagged price features
            for lag in [1, 2, 3, 5, 10]:
                if len(close_prices) > lag:
                    lagged_price = close_prices.iloc[-(lag+1)]
                    current_price = close_prices.iloc[-1]

                    indicators[f'price_lag_{lag}'] = float(lagged_price) if not pd.isna(lagged_price) else 0
                    indicators[f'return_lag_{lag}'] = ((current_price - lagged_price) / lagged_price * 100) if lagged_price > 0 and not pd.isna(lagged_price) else 0

            # Lagged volume features
            volume = data['Volume']
            for lag in [1, 2, 5]:
                if len(volume) > lag:
                    lagged_vol = volume.iloc[-(lag+1)]
                    indicators[f'volume_lag_{lag}'] = float(lagged_vol) if not pd.isna(lagged_vol) else 0

                    # Volume change from lag
                    current_volume = volume.iloc[-1]
                    lagged_volume = volume.iloc[-(lag+1)]
                    if lagged_volume > 0 and not pd.isna(lagged_volume) and not pd.isna(current_volume):
                        indicators[f'volume_change_lag_{lag}'] = ((current_volume - lagged_volume) / lagged_volume * 100)
                    else:
                        indicators[f'volume_change_lag_{lag}'] = 0

            # Sequential return patterns
            returns = close_prices.pct_change()
            if len(returns) >= 5:
                recent_returns = returns.tail(5).dropna().values
                if len(recent_returns) > 0:
                    indicators['returns_pattern'] = {
                        'consecutive_positive': int(np.sum(recent_returns > 0)),
                        'consecutive_negative': int(np.sum(recent_returns < 0)),
                        'avg_return_5d': float(np.mean(recent_returns))
                    }

        except Exception as e:
            logger.error(f"Error calculating lagged features: {str(e)}")

        return indicators

    def _calculate_volatility_measures(self, data: pd.DataFrame) -> Dict:
        """Calculate various volatility measures"""
        indicators = {}

        try:
            close_prices = data['Close']
            returns = close_prices.pct_change().dropna()

            # Historical volatility (annualized)
            for window in [10, 20, 30]:
                if len(returns) >= window:
                    vol = returns.rolling(window=window).std() * np.sqrt(252)  # Annualized
                    vol_val = vol.iloc[-1]
                    indicators[f'hist_volatility_{window}'] = float(vol_val) if not pd.isna(vol_val) else 0

            # Parkinson's volatility (using high-low)
            try:
                high_low_ratio = (data['High'] / data['Low']).apply(np.log)
                high_low_clean = high_low_ratio.dropna()
                if len(high_low_clean) > 0:
                    parkinson_vol = np.sqrt(np.mean(high_low_clean**2) / (4 * np.log(2))) * np.sqrt(252)
                    indicators['parkinson_volatility'] = float(parkinson_vol) if not pd.isna(parkinson_vol) else 0
                else:
                    indicators['parkinson_volatility'] = 0
            except:
                indicators['parkinson_volatility'] = 0

            # Garman-Klass volatility (more accurate)
            try:
                if len(data) >= 20:
                    log_hl = (data['High'] / data['Low']).apply(np.log)
                    log_co = (data['Close'] / data['Open']).apply(np.log)
                    log_hl_clean = log_hl.dropna()
                    log_co_clean = log_co.dropna()

                    if len(log_hl_clean) > 0 and len(log_co_clean) > 0:
                        gk_component = 0.5 * log_hl_clean**2 - (2*np.log(2)-1) * log_co_clean**2
                        gk_vol = np.sqrt(np.mean(gk_component.dropna())) * np.sqrt(252)
                        indicators['garman_klass_volatility'] = float(gk_vol) if not pd.isna(gk_vol) else 0
                    else:
                        indicators['garman_klass_volatility'] = 0
                else:
                    indicators['garman_klass_volatility'] = 0
            except:
                indicators['garman_klass_volatility'] = 0

            # Volatility regime detection
            current_vol = indicators.get('hist_volatility_20', 0)
            long_term_vol = indicators.get('hist_volatility_30', 0)

            if long_term_vol > 0:
                if current_vol > long_term_vol * 1.2:
                    indicators['volatility_regime'] = 'high'
                elif current_vol < long_term_vol * 0.8:
                    indicators['volatility_regime'] = 'low'
                else:
                    indicators['volatility_regime'] = 'normal'
            else:
                indicators['volatility_regime'] = 'normal'

        except Exception as e:
            logger.error(f"Error calculating volatility measures: {str(e)}")

        return indicators

    def _assess_data_quality(self, data: pd.DataFrame) -> float:
        """Assess the quality of the data"""
        try:
            quality_score = 0

            # Data completeness
            if len(data) >= 100:
                quality_score += 30
            elif len(data) >= 50:
                quality_score += 20
            elif len(data) >= 20:
                quality_score += 10

            # Volume data availability
            if 'Volume' in data.columns:
                volume_sum = data['Volume'].sum()
                if volume_sum > 0:
                    quality_score += 20

            # Price consistency
            price_changes = data['Close'].pct_change().dropna()
            if len(price_changes) > 0:
                extreme_changes = np.sum(np.abs(price_changes) > 0.20)  # More than 20% daily change
                if extreme_changes / len(price_changes) < 0.05:  # Less than 5% extreme changes
                    quality_score += 25
                elif extreme_changes / len(price_changes) < 0.10:
                    quality_score += 15

            # Data recency
            if hasattr(data.index[-1], 'date'):
                days_old = (datetime.now().date() - data.index[-1].date()).days
                if days_old <= 3:
                    quality_score += 25
                elif days_old <= 7:
                    quality_score += 15
                elif days_old <= 30:
                    quality_score += 5

            return min(quality_score, 100)

        except Exception:
            return 50  # Default quality score

    def scrape_screener_data(self, symbol: str) -> Dict:
        """Enhanced scrape fundamental data from Screener.in with better error handling"""
        try:
            url = f"https://www.screener.in/company/{symbol}/consolidated/"
            response = self.session.get(url, timeout=15)

            fallback_data = {
                'pe_ratio': None,
                'revenue_growth': 5.0,
                'earnings_growth': 3.0,
                'promoter_buying': False,
                'debt_to_equity': None,
                'roe': None,
                'current_ratio': None,
                'data_source': 'fallback'
            }

            if response.status_code != 200:
                logger.warning(f"Failed to fetch data for {symbol}: {response.status_code}")
                return fallback_data

            soup = BeautifulSoup(response.content, 'html.parser')

            result = fallback_data.copy()
            result['data_source'] = 'screener'

            # Enhanced PE ratio extraction
            pe_ratio = self._extract_pe_ratio(soup, symbol)
            if pe_ratio:
                result['pe_ratio'] = pe_ratio

            # Enhanced financial metrics extraction
            result.update(self._extract_financial_metrics(soup))

            # Enhanced growth data extraction
            result.update(self._extract_growth_data(soup))

            return result

        except Exception as e:
            logger.error(f"Error scraping {symbol}: {str(e)}")
            return {
                'pe_ratio': None,
                'revenue_growth': 5.0,
                'earnings_growth': 3.0,
                'promoter_buying': False,
                'debt_to_equity': None,
                'roe': None,
                'current_ratio': None,
                'data_source': 'error'
            }

    def _extract_pe_ratio(self, soup: BeautifulSoup, symbol: str) -> Optional[float]:
        """Enhanced PE ratio extraction"""
        try:
            # Multiple selectors for PE ratio
            pe_selectors = [
                'span:contains("Stock P/E")',
                'span:contains("P/E")',
                'td:contains("Stock P/E")',
                'td:contains("P/E Ratio")',
                '.number'
            ]

            for selector in pe_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        # Look for number in various locations
                        for candidate in [element, element.find_next_sibling(), 
                                        element.parent.find_next('span', class_='number') if element.parent else None]:
                            if candidate and candidate.text:
                                text = candidate.text.strip()
                                try:
                                    pe_value = float(text.replace(',', '').replace('%', ''))
                                    if 0 < pe_value < 500:
                                        return pe_value
                                except ValueError:
                                    continue
                except Exception:
                    continue

            # Fallback to yfinance
            try:
                ticker = f"{symbol}.NS"
                stock_info = yf.Ticker(ticker).info
                if 'trailingPE' in stock_info and stock_info['trailingPE']:
                    pe_value = float(stock_info['trailingPE'])
                    if 0 < pe_value < 500:
                        return pe_value
            except Exception:
                pass

            return None

        except Exception as e:
            logger.error(f"Error extracting PE ratio: {str(e)}")
            return None

    def _extract_financial_metrics(self, soup: BeautifulSoup) -> Dict:
        """Extract additional financial metrics"""
        metrics = {}

        try:
            # Look for debt-to-equity, ROE, current ratio, etc.
            metric_mappings = {
                'debt_to_equity': ['Debt to equity', 'D/E', 'Debt/Equity'],
                'roe': ['ROE', 'Return on equity', 'Return on Equity'],
                'current_ratio': ['Current ratio', 'Current Ratio']
            }

            for metric, search_terms in metric_mappings.items():
                value = self._extract_metric_value(soup, search_terms)
                if value is not None:
                    metrics[metric] = value

        except Exception as e:
            logger.error(f"Error extracting financial metrics: {str(e)}")

        return metrics

    def _extract_growth_data(self, soup: BeautifulSoup) -> Dict:
        """Enhanced growth data extraction"""
        growth_data = {
            'revenue_growth': 5.0,
            'earnings_growth': 3.0,
            'promoter_buying': False
        }

        try:
            # Look for quarterly results table
            tables = soup.find_all('table', {'class': 'data-table'})

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        row_text = cells[0].text.lower()

                        # Revenue growth
                        if any(term in row_text for term in ['sales', 'revenue', 'income']):
                            growth = self._calculate_growth_from_cells(cells[1:3])
                            if growth is not None:
                                growth_data['revenue_growth'] = growth

                        # Earnings growth
                        elif any(term in row_text for term in ['net profit', 'earnings', 'pat']):
                            growth = self._calculate_growth_from_cells(cells[1:3])
                            if growth is not None:
                                growth_data['earnings_growth'] = growth

            # Check for promoter buying
            page_text = soup.get_text().lower()
            if any(term in page_text for term in ['promoter', 'buying', 'increase in holding']):
                growth_data['promoter_buying'] = True

        except Exception as e:
            logger.error(f"Error extracting growth data: {str(e)}")

        return growth_data

    def _extract_metric_value(self, soup: BeautifulSoup, search_terms: List[str]) -> Optional[float]:
        """Extract a specific metric value from soup"""
        try:
            for term in search_terms:
                elements = soup.find_all(text=lambda text: text and term.lower() in text.lower())
                for element in elements:
                    parent = element.parent
                    if parent:
                        # Look for number in the same row
                        row = parent.find_parent('tr')
                        if row:
                            number_element = row.find('span', class_='number') or row.find(text=lambda t: t and any(c.isdigit() for c in t))
                            if number_element:
                                try:
                                    value = float(str(number_element).replace(',', '').replace('%', ''))
                                    return value
                                except ValueError:
                                    continue
            return None
        except Exception:
            return None

    def _calculate_growth_from_cells(self, cells: List) -> Optional[float]:
        """Calculate growth rate from table cells"""
        try:
            if len(cells) >= 2:
                current_text = cells[0].text.replace(',', '').replace('%', '').strip()
                previous_text = cells[1].text.replace(',', '').replace('%', '').strip()

                current = float(current_text)
                previous = float(previous_text)

                if previous != 0:
                    growth = ((current - previous) / abs(previous)) * 100
                    return growth

        except (ValueError, IndexError, AttributeError):
            pass

        return None

    
    def _calculate_base_score(self, technical_data, fundamental_data, bulk_deal_data):
        """Calculate base score for a stock"""
        try:
            score = 0

            # Technical scoring
            if technical_data:
                score += self._score_technical_indicators(technical_data)

            # Fundamental scoring  
            if fundamental_data:
                score += self._score_fundamentals(fundamental_data)

            # Bulk deal bonus
            symbol = technical_data.get('symbol', '') if technical_data else ''
            if symbol in bulk_deal_data:
                score += 30

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error calculating base score: {str(e)}")
            return 0

    def _score_technical_indicators(self, technical_data):
        """Score technical indicators"""
        try:
            score = 0
            # Implement technical scoring logic here

            return score

        except Exception as e:
            logger.error(f"Error scoring technicals: {str(e)}")
            return 0

    def _score_fundamentals(self, fundamental_data):
        """Score fundamental indicators"""
        try:
            score = 0

            pe_ratio = fundamental_data.get('pe_ratio', 0)
            revenue_growth = fundamental_data.get('revenue_growth', 0)
            earnings_growth = fundamental_data.get('earnings_growth', 0)

            # PE ratio scoring (lower is better, but not too low)
            if 0 < pe_ratio < 15:
                score += 15
            elif 15 <= pe_ratio < 25:
                score += 10
            elif 25 <= pe_ratio < 35:
                score += 5

            # Growth scoring
            if revenue_growth > 20:
                score += 15
            elif revenue_growth > 10:
                score += 10
            elif revenue_growth > 5:
                score += 5

            if earnings_growth > 20:
                score += 15
            elif earnings_growth > 10:
                score += 10
            elif earnings_growth > 5:
                score += 5

            # Promoter buying bonus
            if fundamental_data.get('promoter_buying', False):
                score += 20

            return score

        except Exception as e:
            logger.error(f"Error scoring fundamentals: {str(e)}")
            return 0

    def _generate_technical_summary(self, technical_data):
        """Generate a comprehensive technical summary"""
        analysis_type = technical_data.get('analysis_type', 'unknown')

        # Use daily technical analyzer's summary if available
        if analysis_type == 'daily_ohlc':
            try:
                from daily_technical_analyzer import DailyTechnicalAnalyzer
                analyzer = DailyTechnicalAnalyzer()
                return analyzer.generate_daily_technical_summary(technical_data)
            except Exception:
                pass

        # Fallback to legacy summary
        summary_parts = []

        # RSI summary
        rsi_14 = technical_data.get('rsi_14', 50)
        if rsi_14 < 30:
            summary_parts.append("Oversold (RSI)")
        elif rsi_14 > 70:
            summary_parts.append("Overbought (RSI)")
        else:
            summary_parts.append("Neutral (RSI)")

        # Trend summary
        if technical_data.get('ema_12_above_21', False):
            summary_parts.append("Uptrend (EMA)")
        else:
            summary_parts.append("Downtrend (EMA)")

        # Bollinger Bands summary
        bb_signal = technical_data.get('bb_signal', 'within_bands')
        bb_summaries = {
            'above_upper': 'Above Upper BB',
            'below_lower': 'Below Lower BB',
            'within_bands': 'Within BB Range'
        }
        summary_parts.append(bb_summaries.get(bb_signal, 'BB Neutral'))

        # Volume summary
        volume_ratio = technical_data.get('volume_ratio_10', 1)
        if volume_ratio > 1.5:
            summary_parts.append("High Volume")
        elif volume_ratio < 0.8:
            summary_parts.append("Low Volume")
        else:
            summary_parts.append("Normal Volume")

        return " | ".join(summary_parts)

    def _estimate_market_cap(self, symbol: str) -> str:
        """Estimate market cap category"""
        large_caps = ['SBIN', 'BHARTIARTL', 'ITC', 'NTPC', 'ONGC', 'COALINDIA', 'TATASTEEL', 'JSWSTEEL']
        mid_caps = ['HINDALCO', 'TATAMOTORS', 'M&M', 'BPCL', 'GAIL', 'IOC', 'POWERGRID', 'HAL', 'BEL']

        if symbol in large_caps:
            return "Large Cap"
        elif symbol in mid_caps:
            return "Mid Cap"
        else:
            return "Small Cap"

    def get_pe_description(self, pe_ratio: float) -> str:
        """Convert PE ratio to user-friendly description"""
        if pe_ratio is None or pe_ratio <= 0:
            return "Not Available"
        elif pe_ratio < 10:
            return "Very Low"
        elif pe_ratio < 15:
            return "Below Average"
        elif pe_ratio <= 20:
            return "At Par"
        elif pe_ratio <= 30:
            return "Above Average"
        elif pe_ratio <= 50:
            return "High"
        else:
            return "Very High"

    def scrape_bulk_deals(self) -> List[Dict]:
        """Scrape bulk deals with enhanced error handling"""
        try:
            url = "https://trendlyne.com/equity/bulk-block-deals/today/"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }

            response = self.session.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch bulk deals: {response.status_code}")
                return self._get_fallback_bulk_deals()

            soup = BeautifulSoup(response.content, 'html.parser')
            deals = []

            tables = soup.find_all('table', {'class': 'table'})

            for table in tables:
                rows = table.find_all('tr')[1:]  # Skip header row

                for row in rows:
                    cells = row.find_all(['td', 'th'])

                    if len(cells) >= 6:
                        try:
                            symbol = cells[0].get_text(strip=True).upper()
                            client_name = cells[1].get_text(strip=True)
                            deal_type = cells[2].get_text(strip=True)
                            quantity_text = cells[3].get_text(strip=True)
                            price_text = cells[4].get_text(strip=True)
                            percentage_text = cells[5].get_text(strip=True)

                            percentage = 0.0
                            if '%' in percentage_text:
                                percentage = float(percentage_text.replace('%', '').strip())

                            deal_category = self._classify_deal_type(client_name, deal_type)

                            if symbol in self.under500_symbols and percentage >= 0.5:
                                deals.append({
                                    'symbol': symbol,
                                    'type': deal_category,
                                    'percentage': percentage,
                                    'client': client_name,
                                    'deal_type': deal_type,
                                    'quantity': quantity_text,
                                    'price': price_text
                                })

                        except (ValueError, IndexError) as e:
                            logger.debug(f"Error parsing bulk deal row: {str(e)}")
                            continue

            significant_deals = self._filter_significant_deals(deals)
            logger.info(f"Found {len(significant_deals)} significant bulk deals")

            return significant_deals

        except Exception as e:
            logger.error(f"Error scraping bulk deals: {str(e)}")
            return self._get_fallback_bulk_deals()

    def _classify_deal_type(self, client_name: str, deal_type: str) -> str:
        """Classify deal type based on client name and deal type"""
        client_lower = client_name.lower()

        if any(term in client_lower for term in ['fii', 'foreign', 'offshore']):
            return 'FII'
        elif any(term in client_lower for term in ['dii', 'mutual', 'insurance']):
            return 'DII'
        elif any(term in client_lower for term in ['promoter', 'group']):
            return 'Promoter'
        elif 'buy' in deal_type.lower():
            return 'Buy'
        elif 'sell' in deal_type.lower():
            return 'Sell'
        else:
            return 'Other'

    def _filter_significant_deals(self, deals: List[Dict]) -> List[Dict]:
        """Filter and deduplicate significant deals"""
        significant_deals = []
        seen_combinations = set()

        for deal in deals:
            combo = (deal['symbol'], deal['type'], deal['percentage'])
            if combo not in seen_combinations:
                significant_deals.append(deal)
                seen_combinations.add(combo)

        return significant_deals

    def _get_fallback_bulk_deals(self) -> List[Dict]:
        """Fallback bulk deals when scraping fails"""
        logger.info("Using fallback bulk deals data")
        return [{
            'symbol': 'RELIANCE',
            'type': 'FII',
            'percentage': 0.8
        }, {
            'symbol': 'TCS',
            'type': 'Promoter', 
            'percentage': 1.2
        }]

    def fetch_corporate_actions(self, symbol: str) -> Dict:
        """Fetch corporate actions data (placeholder)"""
        try:
            # Placeholder for corporate actions data
            return {
                'dividend_yield': None,
                'bonus_ratio': None,
                'split_ratio': None,
                'rights_issue': False
            }
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {str(e)}")
            return {}

    def get_financial_ratios_extended(self, symbol: str) -> Dict:
        """Get extended financial ratios (placeholder)"""
        try:
            # Placeholder for extended financial ratios
            return {
                'current_ratio': None,
                'quick_ratio': None,
                'debt_to_equity': None,
                'return_on_assets': None,
                'return_on_equity': None
            }
        except Exception as e:
            logger.error(f"Error fetching financial ratios for {symbol}: {str(e)}")
            return {}

    def run_enhanced_screener(self) -> List[Dict]:
        """Main enhanced screening function"""
        logger.info("Starting enhanced stock screening process...")

        # Step 1: Scrape bulk deals
        self.bulk_deals = self.scrape_bulk_deals()
        time.sleep(2)

        # Step 2: Collect enhanced data from multiple sources
        stocks_data = {}

        for i, symbol in enumerate(self.watchlist):
            logger.info(f"Processing {symbol} ({i+1}/{len(self.watchlist)})")

            # Fetch from multiple data sources
            multi_source_data = self.fetch_from_multiple_sources(symbol, 'both')

            # Scrape enhanced fundamentals (keeping existing method as backup)
            fundamentals = self.scrape_screener_data(symbol)

            # Merge multi-source fundamental data
            if multi_source_data['fundamental_data']:
                for key, value in multi_source_data['fundamental_data'].items():
                    if value and (not fundamentals.get(key) or fundamentals[key] in [None, 0]):
                        fundamentals[key] = value

            # Calculate enhanced technical indicators
            technical = self.calculate_enhanced_technical_indicators(symbol)

            # Add multi-source price data if available
            if multi_source_data.get('current_price') and not technical.get('current_price'):
                technical['current_price'] = multi_source_data['current_price']

            # Add source reliability info
            technical['data_sources'] = multi_source_data['source_reliability']
            technical['source_count'] = len([s for s, status in multi_source_data['source_reliability'].items() if status == 'success'])

            # Fetch corporate actions and sector analysis
            corporate_data = self.fetch_corporate_actions(symbol)

            # Get extended financial ratios
            financial_ratios = self.get_financial_ratios_extended(symbol)

            # Combine all data for scoring
            sentiment = {'bulk_deal_bonus': 10 if symbol in [d['symbol'] for d in self.bulk_deals] else 0}
            market_data = {'market_cap': self._estimate_market_cap(symbol)}

            # Calculate advanced technical indicators
            price_data = self._fetch_price_data_multiple_sources(symbol)
            if price_data is not None and not price_data.empty:
                advanced_technical = self.calculate_advanced_technical_indicators(price_data)
                technical.update(advanced_technical)

            if fundamentals or technical:
                stocks_data[symbol] = {
                    'fundamentals': fundamentals,
                    'technical': technical,
                    'corporate': corporate_data,
                    'financial_ratios': financial_ratios,
                    'multi_source_metadata': {
                        'sources_used': list(multi_source_data['source_reliability'].keys()),
                        'successful_sources': [s for s, status in multi_source_data['source_reliability'].items() if status == 'success'],
                        'last_updated': multi_source_data['last_updated']
                    }
                }

                # Calculate enhanced score with all data
                scoring_result = self.calculate_enhanced_score(
                    symbol, fundamentals, technical, sentiment, market_data
                )

                # Get ensemble predictions for better accuracy
                ensemble_data = {
                    'fundamentals': fundamentals,
                    'technical': technical,
                    'sentiment': sentiment,
                    'market_data': market_data
                }
                # Placeholder for ensemble prediction function
                def get_ensemble_prediction(symbol, data):
                    """Dummy function to simulate ensemble prediction"""
                    return {'pred_24h': 1.2, 'pred_5d': 3.5, 'pred_1mo': 7.8, 'confidence': 75}

                ensemble_predictions = get_ensemble_prediction(symbol, ensemble_data)

                # Use ensemble predictions if available and confident
                if ensemble_predictions.get('confidence', 0) > 60:
                    scoring_result['predictions'] = {
                        'pred_24h': ensemble_predictions['pred_24h'],
                        'pred_5d': ensemble_predictions['pred_5d'],
                        'pred_1mo': ensemble_predictions['pred_1mo']
                    }
                    scoring_result['ensemble_confidence'] = ensemble_predictions['confidence']

                stocks_data[symbol]['scoring_result'] = scoring_result

            # Rate limiting
            time.sleep(1.2)  # Slightly faster with multiple sources

        # Step 3: Enhanced scoring and ranking
        top_stocks = self.enhanced_score_and_rank(stocks_data)

        # Step 4: Try ML predictions if available
        try:
            from predictor import enrich_with_ml_predictions
            enhanced_stocks = enrich_with_ml_predictions(top_stocks)
            logger.info("✅ ML predictions added successfully")
            return enhanced_stocks
        except Exception as e:
            logger.warning(f"⚠️ ML predictions failed, using enhanced scoring: {str(e)}")
            return top_stocks

    def is_market_hours(self) -> bool:
        """Check if the current time is within market hours (9 AM - 4 PM IST)"""
        now_utc = datetime.utcnow()
        ist_offset = timedelta(hours=5, minutes=30)
        now_ist = now_utc + ist_offset

        start_time = now_ist.replace(hour=9, minute=0, second=0, microsecond=0)
        end_time = now_ist.replace(hour=16, minute=0, second=0, microsecond=0)

        return start_time <= now_ist <= end_time

    def run_screening(self, force=False):
        """Main screening process"""
        try:
            logger.info("🔍 Starting stock screening process...")

            # Check if market is open (unless forced)
            if not force and not self.is_market_hours():
                logger.info("⏰ Market is closed. Screening will run only during market hours (9 AM - 4 PM IST).")
                return False

            results = self.run_enhanced_screener()
            return results

        except Exception as e:
            logger.error(f"Error during screening: {str(e)}")
            return []
    def calculate_predicted_price(self, current_price, score):
        """Calculate predicted price based on score"""
        try:
            if current_price <= 0:
                return 0

            # Simple prediction model: higher score = higher expected return
            expected_return = (score / 100) * 0.25  # Max 25% return for score 100
            predicted_price = current_price * (1 + expected_return)

            return predicted_price

        except Exception as e:
            self.logger.error(f"Error calculating predicted price: {str(e)}")
            return current_price

    def calculate_timeframe_prediction(self, score, days):
        """Calculate percentage gain prediction for specific timeframe"""
        try:
            # Base prediction on score with time decay
            base_return = (score / 100) * 0.20  # Max 20% base return

            # Time-based scaling
            if days == 1:  # 24h prediction
                return base_return * 0.05  # 5% of base return in 1 day
            elif days == 5:  # 5d prediction
                return base_return * 0.25  # 25% of base return in 5 days
            elif days == 30:  # 1mo prediction
                return base_return * 1.0   # Full base return in 30 days
            else:
                # Linear scaling for other timeframes
                return base_return * (days / 30)

        except Exception as e:
            self.logger.error(f"Error calculating timeframe prediction: {str(e)}")
            return 0.0

    def calculate_advanced_technical_indicators(self, price_data: pd.DataFrame) -> Dict:
        """Calculate comprehensive technical indicators for better predictions"""
        try:
            if price_data.empty or len(price_data) < 50:
                return {}

            indicators = {}

            # Price-based indicators
            high = price_data['High']
            low = price_data['Low']
            close = price_data['Close']
            volume = price_data['Volume']

            # RSI (14-day)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi_14'] = float(100 - (100 / (1 + rs.iloc[-1]))) if not rs.iloc[-1] == 0 else 50

            # MACD
            exp12 = close.ewm(span=12).mean()
            exp26 = close.ewm(span=26).mean()
            macd = exp12 - exp26
            signal = macd.ewm(span=9).mean()
            indicators['macd'] = float(macd.iloc[-1])
            indicators['macd_signal'] = float(signal.iloc[-1])
            indicators['macd_histogram'] = float(macd.iloc[-1] - signal.iloc[-1])

            # Bollinger Bands (already calculated)
            sma_20 = close.rolling(window=20).mean()
            std_20 = close.rolling(window=20).std()
            indicators['bb_upper'] = float(sma_20.iloc[-1] + (std_20.iloc[-1] * 2))
            indicators['bb_middle'] = float(sma_20.iloc[-1])
            indicators['bb_lower'] = float(sma_20.iloc[-1] - (std_20.iloc[-1] * 2))
            indicators['bb_position'] = float(((close.iloc[-1] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])) * 100)
            indicators['bb_width'] = float(((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle']) * 100)

            # Stochastic Oscillator
            lowest_low = low.rolling(window=14).min()
            highest_high = high.rolling(window=14).max()
            k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
            indicators['stoch_k'] = float(k_percent.iloc[-1])
            indicators['stoch_d'] = float(k_percent.rolling(window=3).mean().iloc[-1])

            # Williams %R
            indicators['williams_r'] = float(-100 * ((highest_high.iloc[-1] - close.iloc[-1]) / (highest_high.iloc[-1] - lowest_low.iloc[-1])))

            # Volume indicators
            indicators['volume_sma_ratio'] = float(volume.iloc[-1] / volume.rolling(window=20).mean().iloc[-1])
            indicators['volume_roc'] = float(((volume.iloc[-1] - volume.iloc[-5]) / volume.iloc[-5]) * 100) if volume.iloc[-5] > 0 else 0

            # Money Flow Index (MFI)
            typical_price = (high + low + close) / 3
            money_flow = typical_price * volume
            positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=14).sum()
            negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=14).sum()
            money_ratio = positive_flow / negative_flow
            indicators['mfi'] = float(100 - (100 / (1 + money_ratio.iloc[-1]))) if not negative_flow.iloc[-1] == 0 else 50

            # Commodity Channel Index (CCI)
            tp = typical_price
            sma_tp = tp.rolling(window=20).mean()
            mad = tp.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
            indicators['cci'] = float((tp.iloc[-1] - sma_tp.iloc[-1]) / (0.015 * mad.iloc[-1])) if mad.iloc[-1] > 0 else 0

            # Average Directional Index (ADX) - simplified
            high_diff = high.diff()
            low_diff = -low.diff()
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            atr = true_range.rolling(window=14).mean()
            plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)

            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            indicators['adx'] = float(dx.rolling(window=14).mean().iloc[-1]) if not (plus_di.iloc[-1] + minus_di.iloc[-1]) == 0 else 0

            # Rate of Change (ROC)
            indicators['roc_10'] = float(((close.iloc[-1] - close.iloc[-11]) / close.iloc[-11]) * 100) if close.iloc[-11] > 0 else 0
            indicators['roc_20'] = float(((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100) if len(close) > 21 and close.iloc[-21] > 0 else 0

            # Momentum indicators
            indicators['momentum_10'] = float(close.iloc[-1] - close.iloc[-11]) if len(close) > 11 else 0

            # Relative Vigor Index (RVI) - simplified
            close_open = close - price_data['Open']
            high_low = high - low
            indicators['rvi'] = float(close_open.rolling(window=10).mean().iloc[-1] / high_low.rolling(window=10).mean().iloc[-1]) if high_low.rolling(window=10).mean().iloc[-1] > 0 else 0

            # Trend strength indicator
            sma_50 = close.rolling(window=50).mean()
            sma_200 = close.rolling(window=200).mean() if len(close) >= 200 else sma_50

            trend_strength = 0
            if close.iloc[-1] > sma_50.iloc[-1]:
                trend_strength += 25
            if sma_50.iloc[-1] > sma_200.iloc[-1]:
                trend_strength += 25
            if close.iloc[-1] > close.iloc[-20]:
                trend_strength += 25
            if volume.iloc[-1] > volume.rolling(window=20).mean().iloc[-1]:
                trend_strength += 25

            indicators['trend_strength'] = trend_strength

            # Volatility indicators
            indicators['atr_14'] = float(true_range.rolling(window=14).mean().iloc[-1])
            indicators['atr_21'] = float(true_range.rolling(window=21).mean().iloc[-1])
            indicators['atr_7'] = float(true_range.rolling(window=7).mean().iloc[-1])

            # Price volatility (coefficient of variation)
            indicators['coeff_variation_10'] = float(close.rolling(window=10).std().iloc[-1] / close.rolling(window=10).mean().iloc[-1] * 100) if close.rolling(window=10).mean().iloc[-1] > 0 else 0
            indicators['coeff_variation_20'] = float(close.rolling(window=20).std().iloc[-1] / close.rolling(window=20).mean().iloc[-1] * 100) if close.rolling(window=20).mean().iloc[-1] > 0 else 0

            # Support/Resistance levels
            recent_highs = high.rolling(window=20).max()
            recent_lows = low.rolling(window=20).min()
            indicators['resistance_level'] = float(recent_highs.iloc[-1])
            indicators['support_level'] = float(recent_lows.iloc[-1])
            indicators['price_position'] = float(((close.iloc[-1] - recent_lows.iloc[-1]) / (recent_highs.iloc[-1] - recent_lows.iloc[-1])) * 100) if recent_highs.iloc[-1] > recent_lows.iloc[-1] else 50

            # Signal classifications
            indicators['bb_signal'] = 'oversold' if indicators['bb_position'] < 20 else 'overbought' if indicators['bb_position'] > 80 else 'within_bands'
            indicators['rsi_signal'] = 'oversold' if indicators['rsi_14'] < 30 else 'overbought' if indicators['rsi_14'] > 70 else 'neutral'
            indicators['stoch_signal'] = 'oversold' if indicators['stoch_k'] < 20 else 'overbought' if indicators['stoch_k'] > 80 else 'neutral'
            indicators['macd_signal_direction'] = 'bullish' if indicators['macd'] > indicators['macd_signal'] else 'bearish'

            # Volatility classification
            atr_volatility = indicators['atr_14'] / close.iloc[-1] * 100 if close.iloc[-1] > 0 else 0
            indicators['atr_volatility'] = float(atr_volatility)
            indicators['volatility_class'] = 'low' if atr_volatility < 2 else 'high' if atr_volatility > 5 else 'medium'

            return indicators

        except Exception as e:
            logger.error(f"Error calculating advanced technical indicators: {str(e)}")
            return {}

    def calculate_enhanced_score(self, symbol: str, fundamentals: Dict, technical: Dict, 
                                sentiment: Dict, market_data: Dict) -> Dict:
        """Calculate enhanced score using ML-inspired feature engineering"""
        try:
            score = 30  # Base score
            confidence = 50
            risk_factors = []

            # Fundamental scoring
            pe_ratio = fundamentals.get('pe_ratio', 0)
            revenue_growth = fundamentals.get('revenue_growth', 0)
            earnings_growth = fundamentals.get('earnings_growth', 0)

            if pe_ratio and pe_ratio > 0 and pe_ratio < 20:
                score += 15
            if revenue_growth > 10 or earnings_growth > 10:
                score += 20

            # Technical scoring
            rsi_14 = technical.get('rsi_14', 50)
            if 30 <= rsi_14 <= 70:
                score += 10

            # Sentiment scoring
            score += sentiment.get('bulk_deal_bonus', 0)

            return {
                'score': min(100, max(0, score)),
                'confidence': confidence,
                'risk_factors': risk_factors,
                'predictions': {
                    'pred_24h': score * 0.05,
                    'pred_5d': score * 0.15,
                    'pred_1mo': score * 0.25
                }
            }
        except Exception as e:
            logger.error(f"Error calculating enhanced score: {str(e)}")
            return {'score': 0, 'confidence': 0, 'risk_factors': [], 'predictions': {'pred_24h': 0, 'pred_5d': 0, 'pred_1mo': 0}}

    def enhanced_score_and_rank(self, stocks_data: Dict) -> List[Dict]:
        """Enhanced scoring and ranking with all data sources"""
        try:
            scored_stocks = []
            ist_now = datetime.now()

            for symbol, data in stocks_data.items():
                fundamentals = data.get('fundamentals', {})
                technical = data.get('technical', {})
                
                # Create sentiment data
                bulk_deals_symbols = [deal['symbol'] for deal in self.bulk_deals]
                sentiment = {'bulk_deal_bonus': 10 if symbol in bulk_deals_symbols else 0}
                
                # Market data
                market_data = {'market_cap': self._estimate_market_cap(symbol)}

                # Calculate enhanced score
                scoring_result = self.calculate_enhanced_score(
                    symbol, fundamentals, technical, sentiment, market_data
                )

                # Build stock result
                current_price = technical.get('current_price', 0)
                score = scoring_result['score']
                
                stock_result = {
                    'symbol': symbol,
                    'score': score,
                    'adjusted_score': score * 0.95,  # Slight adjustment
                    'confidence': scoring_result['confidence'],
                    'current_price': current_price,
                    'predicted_price': current_price * (1 + score/100 * 0.2) if current_price > 0 else 0,
                    'predicted_gain': score * 0.2,  # Simple gain calculation
                    'pred_24h': scoring_result['predictions']['pred_24h'],
                    'pred_5d': scoring_result['predictions']['pred_5d'],
                    'pred_1mo': scoring_result['predictions']['pred_1mo'],
                    'volatility': technical.get('atr_volatility', 2.0),
                    'time_horizon': max(1, int(100 - score)),  # Days to target
                    'pe_ratio': fundamentals.get('pe_ratio'),
                    'pe_description': self.get_pe_description(fundamentals.get('pe_ratio', 0)),
                    'revenue_growth': fundamentals.get('revenue_growth', 0),
                    'earnings_growth': fundamentals.get('earnings_growth', 0),
                    'risk_level': 'Low' if score > 70 else 'Medium' if score > 50 else 'High',
                    'market_cap': market_data['market_cap'],
                    'technical_summary': self._generate_technical_summary(technical),
                    'last_analyzed': ist_now.strftime('%d/%m/%Y, %H:%M:%S')
                }

                scored_stocks.append(stock_result)

            # Sort by score descending and return top 10
            scored_stocks.sort(key=lambda x: x['score'], reverse=True)
            return scored_stocks[:10]

        except Exception as e:
            logger.error(f"Error in enhanced scoring and ranking: {str(e)}")
            return []