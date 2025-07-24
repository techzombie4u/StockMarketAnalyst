"""
Stock Market Analyst - Data Collection and Scoring Module

This module handles:
1. Data collection from Screener.in and Trendlyne
2. Technical analysis using yfinance
3. Stock scoring and ranking algorithm
4. Error handling and rate limiting

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StockScreener:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        # Top 20 Nifty 50 stocks by market cap (updated dynamically)
        self.nifty50_symbols = [
            'JSW INFRA', 'WIPRO', 'FORCEMOT'
            # 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
            # 'ICICIBANK', 'BHARTIARTL', 'SBIN', 'LT', 'ITC',
            # 'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'ASIANPAINT', 'MARUTI',
            # 'SUNPHARMA', 'ULTRACEMCO', 'TITAN', 'NESTLEIND', 'BAJFINANCE',
            # 'WIPRO', 'ONGC', 'NTPC', 'POWERGRID', 'TECHM',
            # 'M&M', 'TATAMOTORS', 'BAJAJFINSV', 'DRREDDY', 'JSWSTEEL',
            # 'COALINDIA', 'TATASTEEL', 'HDFCLIFE', 'SBILIFE', 'GRASIM',
            # 'BRITANNIA', 'APOLLOHOSP', 'CIPLA', 'DIVISLAB', 'HEROMOTOCO',
            # 'ADANIENT', 'EICHERMOT', 'HINDALCO', 'UPL', 'INDUSINDBK',
            # 'BAJAJ-AUTO', 'BPCL', 'TATACONSUM', 'SHRIRAMFIN', 'LTIM'
        ]

        # Get top 20 by market cap for this screening session
        # self.watchlist = self.get_top_20_nifty_stocks()
        # Updated watchlist to use expanded stock list
        self.watchlist = self.get_expanded_stock_list()

        self.bulk_deals = []
        self.fundamentals = {}
        self.technical_data = {}

    def get_expanded_stock_list(self) -> List[str]:
        """Get expanded list of Indian stocks for broader screening, filtered by price <= ₹1000"""
        try:
            logger.info("Fetching expanded stock list (price <= ₹1000)...")

            # Expanded list including Nifty 50, Nifty Next 50, and other popular stocks
            expanded_symbols = [
                # Nifty 50
                'RELIANCE',
                'TCS',
                'HDFCBANK',
                'INFY',
                'HINDUNILVR',
                'ICICIBANK',
                'BHARTIARTL',
                'SBIN',
                'LT',
                'ITC',
                'KOTAKBANK',
                'AXISBANK',
                'HCLTECH',
                'ASIANPAINT',
                'MARUTI',
                'SUNPHARMA',
                'ULTRACEMCO',
                'TITAN',
                'NESTLEIND',
                'BAJFINANCE',
                'WIPRO',
                'ONGC',
                'NTPC',
                'POWERGRID',
                'TECHM',
                'M&M',
                'TATAMOTORS',
                'BAJAJFINSV',
                'DRREDDY',
                'JSWSTEEL',
                'COALINDIA',
                'TATASTEEL',
                'HDFCLIFE',
                'SBILIFE',
                'GRASIM',
                'BRITANNIA',
                'APOLLOHOSP',
                'CIPLA',
                'DIVISLAB',
                'HEROMOTOCO',
                'ADANIENT',
                'EICHERMOT',
                'HINDALCO',
                'UPL',
                'INDUSINDBK',
                'BAJAJ-AUTO',
                'BPCL',
                'TATACONSUM',
                'SHRIRAMFIN',
                'LTIM',
                # Additional popular stocks
                'VEDL',
                'SAIL',
                'NMDC',
                'BANKBARODA',
                'PNB',
                'CANBK',
                'IOC',
                'HPCL',
                'GODREJCP',
                'DABUR',
                'MARICO',
                'COLPAL',
                'PIDILITIND',
                'BERGEPAINT',
                'AUROPHARMA',
                'LUPIN',
                'ZYDUSLIFE',
                'TORNTPHARM',
                'JINDALSTEL',
                'ADANIPOWER',
                'ADANIGREEN',
                'ADANIPORTS',
                'AMBUJACEM',
                'ACC',
                'SHREECEM',
                'RAMCO',
                'SIEMENS',
                'ABB',
                'HAVELLS',
                'CROMPTON',
                'VOLTAS',
                'BLUESTARCO',
                'WHIRLPOOL',
                'DIXON',
                'AMBER',
                'FEDERALBNK',
                'RBLBANK',
                'BANDHANBNK',
                'IDFCFIRSTB',
                'PVR',
                'JUBLFOOD',
                'WESTLIFE',
                'TRENT',
                'SHOPERSTOP',
                'ADITIYABIRLA'
            ]

            # Get price data and filter
            stock_data = []

            for symbol in expanded_symbols:
                try:
                    ticker = f"{symbol}.NS"
                    hist = yf.Ticker(ticker).history(period="1d")

                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]

                        # Only include stocks with price <= ₹1000
                        if current_price <= 1000:
                            stock_data.append((symbol, current_price))

                    # Small delay to avoid rate limiting
                    time.sleep(0.05)

                except Exception as e:
                    logger.warning(
                        f"Could not fetch data for {symbol}: {str(e)}")
                    continue

            # Sort by price (ascending for affordable options)
            stock_data.sort(key=lambda x: x[1])
            selected_symbols = [symbol for symbol, _ in stock_data]

            logger.info(
                f"Selected {len(selected_symbols)} stocks under ₹1000 for screening"
            )

            return selected_symbols

        except Exception as e:
            logger.error(f"Error getting expanded stock list: {str(e)}")
            # Return comprehensive fallback list
            return [
                'SBIN', 'ITC', 'ONGC', 'NTPC', 'POWERGRID', 'COALINDIA',
                'BPCL', 'HINDALCO', 'JSWSTEEL', 'TATASTEEL', 'GRASIM', 'UPL',
                'INDUSINDBK', 'WIPRO', 'TECHM', 'M&M', 'TATAMOTORS', 'DRREDDY',
                'CIPLA', 'DIVISLAB', 'VEDL', 'SAIL', 'NMDC', 'BANKBARODA',
                'PNB', 'CANBK', 'IOC', 'HPCL', 'GODREJCP', 'DABUR', 'MARICO',
                'COLPAL', 'AUROPHARMA', 'LUPIN'
            ]

    def scrape_screener_data(self, symbol: str) -> Dict:
        """Scrape fundamental data from Screener.in"""
        try:
            url = f"https://www.screener.in/company/{symbol}/consolidated/"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(
                    f"Failed to fetch data for {symbol}: {response.status_code}"
                )
                return {}

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract PE ratio
            pe_ratio = 0
            pe_element = soup.find('span', string='Stock P/E')
            if pe_element and pe_element.parent.find_next('span',
                                                          class_='number'):
                pe_text = pe_element.parent.find_next(
                    'span', class_='number').text.strip()
                try:
                    pe_ratio = float(pe_text.replace(',', ''))
                except ValueError:
                    pe_ratio = 0

            # Extract quarterly growth data
            revenue_growth = 0
            earnings_growth = 0

            # Look for quarterly results table
            quarterly_table = soup.find('table', {'class': 'data-table'})
            if quarterly_table:
                rows = quarterly_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        if 'Sales' in cells[0].text:
                            try:
                                current = float(cells[1].text.replace(
                                    ',', '').replace('%', ''))
                                previous = float(cells[2].text.replace(
                                    ',', '').replace('%', ''))
                                revenue_growth = (
                                    (current - previous) /
                                    previous) * 100 if previous != 0 else 0
                            except (ValueError, IndexError):
                                pass
                        elif 'Net Profit' in cells[0].text:
                            try:
                                current = float(cells[1].text.replace(
                                    ',', '').replace('%', ''))
                                previous = float(cells[2].text.replace(
                                    ',', '').replace('%', ''))
                                earnings_growth = (
                                    (current - previous) /
                                    previous) * 100 if previous != 0 else 0
                            except (ValueError, IndexError):
                                pass

            # Check for promoter buying (simplified - look for recent announcements)
            promoter_buying = False
            news_section = soup.find('div', {'class': 'company-ratios'})
            if news_section and 'promoter' in news_section.text.lower():
                promoter_buying = True

            return {
                'pe_ratio': pe_ratio,
                'revenue_growth': revenue_growth,
                'earnings_growth': earnings_growth,
                'promoter_buying': promoter_buying
            }

        except Exception as e:
            logger.error(f"Error scraping {symbol}: {str(e)}")
            return {}

    def scrape_bulk_deals(self) -> List[Dict]:
        """Scrape bulk deals from Trendlyne (simplified mock implementation)"""
        try:
            # In a real implementation, this would scrape from Trendlyne
            # For demo purposes, we'll simulate some bulk deals
            mock_deals = [{
                'symbol': 'RELIANCE',
                'type': 'FII',
                'percentage': 0.8
            }, {
                'symbol': 'TCS',
                'type': 'Promoter',
                'percentage': 1.2
            }, {
                'symbol': 'INFY',
                'type': 'FII',
                'percentage': 0.6
            }]

            # Filter deals >= 0.5%
            significant_deals = [
                deal for deal in mock_deals if deal['percentage'] >= 0.5
            ]

            logger.info(
                f"Found {len(significant_deals)} significant bulk deals")
            return significant_deals

        except Exception as e:
            logger.error(f"Error scraping bulk deals: {str(e)}")
            return []

    def calculate_technical_indicators(self, symbol: str) -> Dict:
        """Calculate ATR and momentum using yfinance"""
        try:
            # Add .NS suffix for NSE stocks
            ticker = f"{symbol}.NS"
            stock = yf.Ticker(ticker)

            # Get 30 days of data for ATR calculation
            hist = stock.history(period="1mo")

            if hist.empty:
                logger.warning(f"No data found for {symbol}")
                return {}

            # Calculate 14-day ATR
            high_low = hist['High'] - hist['Low']
            high_close = np.abs(hist['High'] - hist['Close'].shift())
            low_close = np.abs(hist['Low'] - hist['Close'].shift())

            true_range = np.maximum(high_low,
                                    np.maximum(high_close, low_close))
            atr_14 = true_range.rolling(
                window=14).mean().iloc[-1] if len(true_range) >= 14 else 0

            # Calculate 2-day momentum
            if len(hist) >= 3:
                recent_change = hist['Close'].iloc[-1] - hist['Close'].iloc[-3]
                momentum_ratio = recent_change / atr_14 if atr_14 > 0 else 0
            else:
                momentum_ratio = 0

            current_price = hist['Close'].iloc[-1]

            return {
                'atr_14':
                float(atr_14),
                'current_price':
                float(current_price),
                'momentum_ratio':
                float(momentum_ratio),
                'volatility':
                float(atr_14 / current_price * 100) if current_price > 0 else 0
            }

        except Exception as e:
            logger.error(
                f"Error calculating technical indicators for {symbol}: {str(e)}"
            )
            return {}

    def score_and_rank(self, stocks_data: Dict) -> List[Dict]:
        """Score and rank stocks based on multiple factors"""
        scored_stocks = []

        # Calculate median PE for normalization
        pe_ratios = [
            data.get('fundamentals', {}).get('pe_ratio', 0)
            for data in stocks_data.values()
            if data.get('fundamentals', {}).get('pe_ratio', 0) > 0
        ]
        median_pe = np.median(pe_ratios) if pe_ratios else 20

        bulk_deal_symbols = {deal['symbol'] for deal in self.bulk_deals}

        for symbol, data in stocks_data.items():
            fundamentals = data.get('fundamentals', {})
            technical = data.get('technical', {})

            score = 0

            # Bulk deal bonus (+30 points)
            if symbol in bulk_deal_symbols:
                score += 30

            # Strong fundamentals (+20 points)
            pe_ratio = fundamentals.get('pe_ratio', 0)
            revenue_growth = fundamentals.get('revenue_growth', 0)
            earnings_growth = fundamentals.get('earnings_growth', 0)

            if pe_ratio > 0 and pe_ratio < median_pe and (
                    revenue_growth >= 20 or earnings_growth >= 20):
                score += 20

            # Promoter buying (+20 points)
            if fundamentals.get('promoter_buying', False):
                score += 20

            # Momentum check (±10 points)
            momentum_ratio = technical.get('momentum_ratio', 0)
            if momentum_ratio > 0.5:
                score += 10
            elif momentum_ratio < -0.5:
                score -= 10

            # Normalize score to 0-100
            normalized_score = max(0, min(100, score))

            # Calculate adjusted score (emphasize low volatility)
            volatility = technical.get('volatility', 5)
            volatility_factor = max(0.5, 1 - (volatility / 100))
            adjusted_score = normalized_score * volatility_factor

            # Calculate predictions
            predicted_gain = normalized_score / 5 if normalized_score > 0 else 0
            time_horizon = max(
                10, 100 / normalized_score) if normalized_score > 0 else 100

            current_price = technical.get('current_price', 0)
            predicted_price = current_price * (
                1 + predicted_gain / 100) if current_price > 0 else 0

            # Calculate multiple time horizon predictions
            momentum_ratio = technical.get('momentum_ratio', 0)
            base_score_factor = (normalized_score -
                                 50) * 0.01  # Base momentum from score

            # 3-hour prediction: short-term momentum
            three_hour_change = momentum_ratio * 0.3 + base_score_factor * 0.5
            three_hour_price = current_price * (
                1 + three_hour_change / 100) if current_price > 0 else 0
            three_hour_gain = three_hour_change

            # 24-hour prediction: daily momentum + score impact
            daily_change = momentum_ratio * 0.8 + base_score_factor * 1.2
            daily_price = current_price * (
                1 + daily_change / 100) if current_price > 0 else 0
            daily_gain = daily_change

            # 5-day prediction: weekly trend + fundamental strength
            weekly_change = base_score_factor * 3.0 + (
                normalized_score / 20) + (momentum_ratio * 0.5)
            weekly_price = current_price * (
                1 + weekly_change / 100) if current_price > 0 else 0
            weekly_gain = weekly_change

            # 4-week prediction: monthly trend based on fundamentals
            monthly_change = (normalized_score / 10) + base_score_factor * 8.0
            # Add fundamental boost
            if fundamentals.get('revenue_growth', 0) > 15:
                monthly_change += 2.0
            if fundamentals.get('pe_ratio', 0) > 0 and fundamentals.get(
                    'pe_ratio', 0) < 25:
                monthly_change += 1.5
            monthly_price = current_price * (
                1 + monthly_change / 100) if current_price > 0 else 0
            monthly_gain = monthly_change

            # Risk assessment
            risk_level = "Low" if volatility < 3 else "Medium" if volatility < 6 else "High"

            # Market cap estimation (simplified)
            market_cap_category = "Large Cap" if symbol in ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY'] else \
                                 "Mid Cap" if symbol in ['TITAN', 'ASIANPAINT', 'ULTRACEMCO'] else "Small Cap"

            # Confidence score based on data quality
            data_quality = (1 if fundamentals.get('pe_ratio', 0) > 0 else 0) + \
                          (1 if technical.get('current_price', 0) > 0 else 0) + \
                          (1 if fundamentals.get('revenue_growth', 0) != 0 else 0)
            confidence = round((data_quality / 3) * 100, 0)

            stock_result = {
                'symbol': symbol,
                'score': round(normalized_score, 1),
                'adjusted_score': round(adjusted_score, 1),
                'confidence': int(confidence),
                'current_price': round(current_price, 2),
                'three_hour_price': round(three_hour_price, 2),
                'three_hour_gain': round(three_hour_gain, 2),
                'daily_price': round(daily_price, 2),
                'daily_gain': round(daily_gain, 2),
                'weekly_price': round(weekly_price, 2),
                'weekly_gain': round(weekly_gain, 2),
                'monthly_price': round(monthly_price, 2),
                'monthly_gain': round(monthly_gain, 2),
                'volatility': round(volatility, 2),
                'predicted_price': round(predicted_price, 2),
                'predicted_gain': round(predicted_gain, 1),
                'time_horizon': round(time_horizon, 0),
                'risk_level': risk_level,
                'market_cap': market_cap_category,
                'pe_ratio': round(fundamentals.get('pe_ratio', 0), 1),
                'revenue_growth': round(fundamentals.get('revenue_growth', 0),
                                        1),
                'fundamentals': fundamentals,
                'technical': technical
            }

            scored_stocks.append(stock_result)

        # Sort by adjusted score
        scored_stocks.sort(key=lambda x: x['adjusted_score'], reverse=True)

        # Filter stocks with score >= 30 and return top 20
        filtered_stocks = [
            stock for stock in scored_stocks if stock['score'] >= 30
        ]
        return filtered_stocks[:20]

    def run_screener(self) -> List[Dict]:
        """Main screening function"""
        logger.info("Starting stock screening process...")

        # Step 1: Scrape bulk deals
        self.bulk_deals = self.scrape_bulk_deals()

        # Step 2: Collect data for watchlist
        stocks_data = {}

        for i, symbol in enumerate(self.watchlist):
            logger.info(f"Processing {symbol} ({i+1}/{len(self.watchlist)})")

            # Scrape fundamentals
            fundamentals = self.scrape_screener_data(symbol)

            # Calculate technical indicators
            technical = self.calculate_technical_indicators(symbol)

            if fundamentals or technical:
                stocks_data[symbol] = {
                    'fundamentals': fundamentals,
                    'technical': technical
                }

            # Rate limiting
            time.sleep(1)

        # Step 3: Score and rank
        top_stocks = self.score_and_rank(stocks_data)

        logger.info(f"Screening complete. Found {len(top_stocks)} stocks.")

        return top_stocks


def main():
    """Test function"""
    screener = StockScreener()
    results = screener.run_screener()

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
