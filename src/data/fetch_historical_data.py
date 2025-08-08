
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class HistoricalDataFetcher:
    """Enhanced historical data fetcher with 5-year support and fallback mechanisms"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Comprehensive stock universe
        self.tracked_stocks = [
            'RELIANCE', 'HDFCBANK', 'TCS', 'ITC', 'INFY', 'HUL', 'SBIN', 
            'BHARTIARTL', 'NTPC', 'POWERGRID', 'ONGC', 'COALINDIA',
            'TATASTEEL', 'JSWSTEEL', 'HINDALCO', 'TATAMOTORS', 'M&M', 
            'BPCL', 'GAIL', 'IOC', 'SAIL', 'VEDL', 'BANKBARODA', 'CANBK', 
            'PNB', 'UNIONBANK', 'BANKINDIA', 'CENTRALBK', 'INDIANB'
        ]

    def get_stock_history(self, symbol: str, period: str = "5y", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Fetch 5-year historical data with multiple fallback mechanisms
        """
        try:
            logger.info(f"📈 Fetching {period} data for {symbol}")
            
            # Try different ticker formats
            ticker_formats = [f"{symbol}.NS", f"{symbol}.BO", symbol]
            
            for ticker_format in ticker_formats:
                try:
                    logger.debug(f"  Trying {ticker_format}")
                    ticker = yf.Ticker(ticker_format)
                    
                    # Get historical data
                    hist_data = ticker.history(period=period, interval=interval, progress=False)
                    
                    if not hist_data.empty and len(hist_data) > 1000:  # At least 4+ years
                        logger.info(f"  ✅ Success: {len(hist_data)} days from {ticker_format}")
                        
                        # Reset index and clean data
                        hist_data.reset_index(inplace=True)
                        hist_data['Symbol'] = symbol
                        
                        # Add metadata
                        try:
                            info = ticker.info
                            hist_data['Market_Cap'] = info.get('marketCap', 0)
                            hist_data['PE_Ratio'] = info.get('trailingPE', 0)
                            hist_data['Sector'] = info.get('sector', 'Unknown')
                        except:
                            hist_data['Market_Cap'] = 0
                            hist_data['PE_Ratio'] = 0
                            hist_data['Sector'] = 'Unknown'
                        
                        return self._validate_and_clean_data(hist_data, symbol)
                        
                except Exception as e:
                    logger.debug(f"  Failed {ticker_format}: {str(e)}")
                    time.sleep(1)  # Rate limiting
                    continue
            
            # Fallback to NSE scraping
            return self._fallback_nse_scraping(symbol, period)
            
        except Exception as e:
            logger.error(f"Error fetching history for {symbol}: {str(e)}")
            return None

    def _validate_and_clean_data(self, df: pd.DataFrame, symbol: str) -> Optional[pd.DataFrame]:
        """Validate and clean historical data"""
        try:
            if df is None or df.empty:
                return None
            
            # Check required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.warning(f"Missing columns for {symbol}: {missing_cols}")
                return None
            
            # Check data quality
            if len(df) < 500:  # Less than 2 years
                logger.warning(f"Insufficient data for {symbol}: {len(df)} rows")
                return None
            
            # Remove invalid data
            df = df[df[required_cols] > 0].copy()
            
            # Fill NaN values
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # Calculate basic technical indicators
            df = self._add_technical_indicators(df)
            
            logger.info(f"✅ Data validated for {symbol}: {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Data validation failed for {symbol}: {str(e)}")
            return None

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add essential technical indicators"""
        try:
            # Price changes and momentum
            df['Price_Change'] = df['Close'].pct_change().fillna(0)
            df['Momentum_5d'] = df['Close'].pct_change(periods=5).fillna(0)
            df['Momentum_20d'] = df['Close'].pct_change(periods=20).fillna(0)

            # Moving averages
            for window in [5, 10, 20, 50]:
                df[f'MA_{window}'] = df['Close'].rolling(window=window).mean()
                df[f'Price_vs_MA{window}'] = ((df['Close'] - df[f'MA_{window}']) / df[f'MA_{window}']).fillna(0)

            # ATR
            high_low = df['High'] - df['Low']
            high_close = np.abs(df['High'] - df['Close'].shift())
            low_close = np.abs(df['Low'] - df['Close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['ATR'] = true_range.rolling(window=14).mean()

            # Volume indicators
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = (df['Volume'] / df['Volume_MA']).fillna(1.0)

            # Volatility
            df['Volatility'] = df['Price_Change'].rolling(window=20).std().fillna(0)

            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-8)
            df['RSI'] = (100 - (100 / (1 + rs))).fillna(50)

            # Fill any remaining NaN
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error adding technical indicators: {str(e)}")
            return df

    def _fallback_nse_scraping(self, symbol: str, period: str) -> Optional[pd.DataFrame]:
        """Fallback NSE data scraping"""
        try:
            logger.info(f"🔄 Attempting NSE fallback for {symbol}")
            # Simplified fallback - would need full implementation
            return None
        except Exception as e:
            logger.debug(f"NSE fallback failed for {symbol}: {str(e)}")
            return None

    def fetch_all_tracked_stocks(self, output_dir: str = "data/historical/downloaded_historical_data") -> Dict:
        """Fetch 5-year data for all tracked stocks"""
        results = {'successful': [], 'failed': [], 'total': len(self.tracked_stocks)}
        
        logger.info(f"🚀 Fetching 5-year data for {len(self.tracked_stocks)} stocks")
        
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        for i, symbol in enumerate(self.tracked_stocks, 1):
            logger.info(f"Processing {symbol} ({i}/{len(self.tracked_stocks)})")
            
            try:
                hist_data = self.get_stock_history(symbol, period="5y")
                
                if hist_data is not None:
                    # Save to CSV
                    csv_path = os.path.join(output_dir, f"{symbol}.csv")
                    hist_data.to_csv(csv_path, index=False)
                    results['successful'].append(symbol)
                    logger.info(f"✅ Saved {symbol}: {len(hist_data)} rows")
                else:
                    results['failed'].append(symbol)
                    logger.warning(f"❌ Failed to fetch {symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                results['failed'].append(symbol)
            
            # Rate limiting
            time.sleep(1)
        
        logger.info(f"📊 Fetch Summary: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results

def main():
    """Test the historical data fetcher"""
    fetcher = HistoricalDataFetcher()
    
    # Test single stock
    data = fetcher.get_stock_history('RELIANCE', period='5y')
    if data is not None:
        print(f"✅ RELIANCE data: {len(data)} rows")
        print(data.tail())
    
    # Fetch all stocks (uncomment to run)
    # results = fetcher.fetch_all_tracked_stocks()
    # print(f"Results: {results}")

if __name__ == "__main__":
    main()
