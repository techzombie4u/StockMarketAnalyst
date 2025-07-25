
"""
Stock Market Analyst - Enhanced Backtesting Module

Implements advanced backtesting with:
1. Time-series aware cross-validation
2. Walk-forward analysis
3. Performance metrics calculation
4. Risk-adjusted returns analysis
"""

import pandas as pd
import numpy as np
import yfinance as yf
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)

class EnhancedBacktester:
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.transaction_cost = 0.001  # 0.1% transaction cost
        self.results = {}
        
    def time_series_backtest(self, 
                           symbols: List[str], 
                           start_date: str, 
                           end_date: str,
                           rebalance_frequency: str = 'monthly') -> Dict:
        """
        Perform time-series backtesting with walk-forward analysis
        """
        logger.info(f"Starting time-series backtest from {start_date} to {end_date}")
        
        try:
            # Fetch historical data for all symbols
            price_data = self._fetch_historical_data(symbols, start_date, end_date)
            
            if price_data.empty:
                logger.error("No price data available for backtesting")
                return {}
            
            # Generate rebalancing dates
            rebalance_dates = self._generate_rebalance_dates(
                start_date, end_date, rebalance_frequency
            )
            
            # Initialize portfolio tracking
            portfolio_values = []
            holdings = {}
            cash = self.initial_capital
            
            # Walk-forward backtesting
            for i, rebalance_date in enumerate(rebalance_dates[:-1]):
                next_rebalance = rebalance_dates[i + 1]
                
                logger.info(f"Rebalancing on {rebalance_date}")
                
                # Get scoring for this period
                scores = self._get_historical_scores(symbols, rebalance_date)
                
                # Select top stocks
                selected_stocks = self._select_stocks(scores, top_n=10)
                
                # Rebalance portfolio
                cash, holdings = self._rebalance_portfolio(
                    selected_stocks, price_data, rebalance_date, cash, holdings
                )
                
                # Track portfolio performance until next rebalance
                period_values = self._track_portfolio_performance(
                    holdings, price_data, rebalance_date, next_rebalance, cash
                )
                
                portfolio_values.extend(period_values)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                portfolio_values, price_data, start_date, end_date
            )
            
            # Generate detailed results
            results = {
                'portfolio_values': portfolio_values,
                'performance_metrics': performance_metrics,
                'rebalance_dates': rebalance_dates,
                'final_value': portfolio_values[-1]['total_value'] if portfolio_values else self.initial_capital,
                'total_return': ((portfolio_values[-1]['total_value'] / self.initial_capital) - 1) * 100 if portfolio_values else 0
            }
            
            logger.info(f"Backtesting completed. Final portfolio value: {results['final_value']:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error in time-series backtesting: {str(e)}")
            return {}
    
    def cross_validation_backtest(self, 
                                symbols: List[str], 
                                start_date: str, 
                                end_date: str,
                                n_splits: int = 5) -> Dict:
        """
        Perform time-series cross-validation backtesting
        """
        logger.info(f"Starting {n_splits}-fold time-series cross-validation")
        
        try:
            # Fetch historical data
            price_data = self._fetch_historical_data(symbols, start_date, end_date)
            
            if price_data.empty:
                return {}
            
            # Create time series splits
            tscv = TimeSeriesSplit(n_splits=n_splits)
            
            # Get date index for splitting
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            dates = [d for d in dates if d in price_data.index]
            
            cv_results = []
            
            for fold, (train_idx, test_idx) in enumerate(tscv.split(dates)):
                logger.info(f"Processing fold {fold + 1}/{n_splits}")
                
                train_start = dates[train_idx[0]]
                train_end = dates[train_idx[-1]]
                test_start = dates[test_idx[0]]
                test_end = dates[test_idx[-1]]
                
                logger.info(f"Train: {train_start} to {train_end}")
                logger.info(f"Test: {test_start} to {test_end}")
                
                # Train on training period (score calculation)
                training_scores = self._calculate_training_scores(
                    symbols, train_start, train_end, price_data
                )
                
                # Test on testing period
                fold_results = self._test_on_period(
                    training_scores, symbols, test_start, test_end, price_data
                )
                
                fold_results['fold'] = fold + 1
                fold_results['train_period'] = f"{train_start} to {train_end}"
                fold_results['test_period'] = f"{test_start} to {test_end}"
                
                cv_results.append(fold_results)
            
            # Aggregate cross-validation results
            aggregated_results = self._aggregate_cv_results(cv_results)
            
            return {
                'cv_results': cv_results,
                'aggregated_metrics': aggregated_results,
                'n_splits': n_splits
            }
            
        except Exception as e:
            logger.error(f"Error in cross-validation backtesting: {str(e)}")
            return {}
    
    def _fetch_historical_data(self, 
                             symbols: List[str], 
                             start_date: str, 
                             end_date: str) -> pd.DataFrame:
        """Fetch historical price data for multiple symbols"""
        try:
            # Add .NS suffix for NSE stocks
            tickers = [f"{symbol}.NS" for symbol in symbols]
            
            # Download data
            data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            
            if data.empty:
                logger.warning("No data downloaded")
                return pd.DataFrame()
            
            # Handle single symbol case
            if len(symbols) == 1:
                data.columns = pd.MultiIndex.from_product([data.columns, symbols])
            
            # Clean data and forward fill missing values
            data = data.fillna(method='ffill').fillna(method='bfill')
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return pd.DataFrame()
    
    def _generate_rebalance_dates(self, 
                                start_date: str, 
                                end_date: str, 
                                frequency: str) -> List[datetime]:
        """Generate rebalancing dates based on frequency"""
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            if frequency == 'monthly':
                dates = pd.date_range(start=start, end=end, freq='MS')  # Month start
            elif frequency == 'weekly':
                dates = pd.date_range(start=start, end=end, freq='W-MON')  # Weekly Monday
            elif frequency == 'quarterly':
                dates = pd.date_range(start=start, end=end, freq='QS')  # Quarter start
            else:
                # Default to monthly
                dates = pd.date_range(start=start, end=end, freq='MS')
            
            return dates.tolist()
            
        except Exception as e:
            logger.error(f"Error generating rebalance dates: {str(e)}")
            return []
    
    def _get_historical_scores(self, symbols: List[str], date: datetime) -> Dict:
        """
        Simulate historical scoring at a given date
        In a real implementation, this would use historical data to calculate scores
        """
        try:
            # For simulation, we'll use a simplified scoring based on momentum
            scores = {}
            
            for symbol in symbols:
                ticker = f"{symbol}.NS"
                
                # Get data up to the scoring date
                hist_data = yf.download(ticker, 
                                      start=date - timedelta(days=90), 
                                      end=date, 
                                      progress=False)
                
                if hist_data.empty or len(hist_data) < 20:
                    scores[symbol] = 30  # Default score
                    continue
                
                # Calculate simplified score based on momentum and volatility
                returns = hist_data['Close'].pct_change().dropna()
                
                # Momentum score (20-day return)
                momentum_20d = (hist_data['Close'].iloc[-1] / hist_data['Close'].iloc[-21] - 1) * 100 if len(hist_data) >= 21 else 0
                
                # Volatility score (lower volatility = higher score)
                volatility = returns.rolling(20).std().iloc[-1] * np.sqrt(252) * 100
                volatility_score = max(0, 50 - volatility * 2)
                
                # Volume score
                volume_ratio = hist_data['Volume'].iloc[-5:].mean() / hist_data['Volume'].iloc[-21:-5].mean() if len(hist_data) >= 21 else 1
                volume_score = min(20, volume_ratio * 10)
                
                # Combined score
                total_score = 30 + momentum_20d + volatility_score + volume_score
                scores[symbol] = max(0, min(100, total_score))
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating historical scores: {str(e)}")
            return {symbol: 50 for symbol in symbols}  # Default scores
    
    def _select_stocks(self, scores: Dict, top_n: int = 10) -> List[str]:
        """Select top N stocks based on scores"""
        try:
            # Sort by score and select top N
            sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            selected = [stock[0] for stock in sorted_stocks[:top_n]]
            
            logger.info(f"Selected stocks: {selected}")
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting stocks: {str(e)}")
            return list(scores.keys())[:top_n]
    
    def _rebalance_portfolio(self, 
                           selected_stocks: List[str], 
                           price_data: pd.DataFrame, 
                           date: datetime, 
                           cash: float, 
                           current_holdings: Dict) -> Tuple[float, Dict]:
        """Rebalance portfolio to equal weights"""
        try:
            # Sell all current holdings
            for symbol, shares in current_holdings.items():
                if shares > 0:
                    try:
                        # Get price at rebalance date
                        if ('Close', symbol) in price_data.columns:
                            price = price_data.loc[date, ('Close', symbol)]
                            cash += shares * price * (1 - self.transaction_cost)
                    except (KeyError, IndexError):
                        logger.warning(f"Could not find price for {symbol} on {date}")
            
            # Clear holdings
            new_holdings = {}
            
            # Calculate equal allocation
            if selected_stocks and cash > 0:
                allocation_per_stock = cash / len(selected_stocks)
                
                # Buy selected stocks
                for symbol in selected_stocks:
                    try:
                        if ('Close', symbol) in price_data.columns:
                            price = price_data.loc[date, ('Close', symbol)]
                            if price > 0:
                                shares = (allocation_per_stock * (1 - self.transaction_cost)) / price
                                new_holdings[symbol] = shares
                                cash -= allocation_per_stock
                    except (KeyError, IndexError):
                        logger.warning(f"Could not buy {symbol} on {date}")
            
            return cash, new_holdings
            
        except Exception as e:
            logger.error(f"Error rebalancing portfolio: {str(e)}")
            return cash, current_holdings
    
    def _track_portfolio_performance(self, 
                                   holdings: Dict, 
                                   price_data: pd.DataFrame, 
                                   start_date: datetime, 
                                   end_date: datetime, 
                                   cash: float) -> List[Dict]:
        """Track portfolio performance over a period"""
        try:
            performance_data = []
            
            # Get date range for this period
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            date_range = [d for d in date_range if d in price_data.index]
            
            for date in date_range:
                portfolio_value = cash
                
                # Calculate holdings value
                for symbol, shares in holdings.items():
                    try:
                        if ('Close', symbol) in price_data.columns:
                            price = price_data.loc[date, ('Close', symbol)]
                            portfolio_value += shares * price
                    except (KeyError, IndexError):
                        # Use last known price if current date not available
                        continue
                
                performance_data.append({
                    'date': date,
                    'total_value': portfolio_value,
                    'cash': cash,
                    'holdings_value': portfolio_value - cash
                })
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error tracking portfolio performance: {str(e)}")
            return []
    
    def _calculate_performance_metrics(self, 
                                     portfolio_values: List[Dict], 
                                     price_data: pd.DataFrame,
                                     start_date: str,
                                     end_date: str) -> Dict:
        """Calculate comprehensive performance metrics"""
        try:
            if not portfolio_values:
                return {}
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(portfolio_values)
            df.set_index('date', inplace=True)
            
            # Calculate returns
            returns = df['total_value'].pct_change().dropna()
            
            # Basic metrics
            total_return = (df['total_value'].iloc[-1] / df['total_value'].iloc[0] - 1) * 100
            annualized_return = ((df['total_value'].iloc[-1] / df['total_value'].iloc[0]) ** (252 / len(df)) - 1) * 100
            
            # Risk metrics
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
            
            # Sharpe ratio (assuming 5% risk-free rate)
            risk_free_rate = 0.05
            sharpe_ratio = (annualized_return / 100 - risk_free_rate) / (volatility / 100) if volatility > 0 else 0
            
            # Maximum drawdown
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100
            
            # Win rate
            win_rate = (returns > 0).sum() / len(returns) * 100 if len(returns) > 0 else 0
            
            # Benchmark comparison (using NIFTY 50 proxy)
            benchmark_metrics = self._calculate_benchmark_metrics(start_date, end_date)
            
            metrics = {
                'total_return_pct': round(total_return, 2),
                'annualized_return_pct': round(annualized_return, 2),
                'volatility_pct': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'max_drawdown_pct': round(max_drawdown, 2),
                'win_rate_pct': round(win_rate, 2),
                'total_trades': len(portfolio_values),
                'benchmark_comparison': benchmark_metrics
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}
    
    def _calculate_benchmark_metrics(self, start_date: str, end_date: str) -> Dict:
        """Calculate benchmark (Nifty 50) metrics for comparison"""
        try:
            # Use NIFTY 50 ETF as proxy
            benchmark = yf.download("^NSEI", start=start_date, end=end_date, progress=False)
            
            if benchmark.empty:
                return {}
            
            # Calculate benchmark returns
            benchmark_returns = benchmark['Close'].pct_change().dropna()
            total_benchmark_return = (benchmark['Close'].iloc[-1] / benchmark['Close'].iloc[0] - 1) * 100
            benchmark_volatility = benchmark_returns.std() * np.sqrt(252) * 100
            
            return {
                'benchmark_total_return_pct': round(total_benchmark_return, 2),
                'benchmark_volatility_pct': round(benchmark_volatility, 2),
                'alpha': 0  # Will be calculated in comparison
            }
            
        except Exception as e:
            logger.error(f"Error calculating benchmark metrics: {str(e)}")
            return {}
    
    def _calculate_training_scores(self, 
                                 symbols: List[str], 
                                 start_date: datetime, 
                                 end_date: datetime, 
                                 price_data: pd.DataFrame) -> Dict:
        """Calculate scores based on training period data"""
        try:
            scores = {}
            
            for symbol in symbols:
                try:
                    if ('Close', symbol) not in price_data.columns:
                        scores[symbol] = 50
                        continue
                    
                    # Get training period data
                    symbol_data = price_data.loc[start_date:end_date, ('Close', symbol)]
                    
                    if len(symbol_data) < 20:
                        scores[symbol] = 50
                        continue
                    
                    # Calculate features for scoring
                    returns = symbol_data.pct_change().dropna()
                    
                    # Momentum features
                    momentum_5d = symbol_data.pct_change(5).iloc[-1] if len(symbol_data) >= 5 else 0
                    momentum_20d = symbol_data.pct_change(20).iloc[-1] if len(symbol_data) >= 20 else 0
                    
                    # Volatility features
                    volatility = returns.std() * np.sqrt(252) if len(returns) > 0 else 0.2
                    
                    # Trend features
                    ma_short = symbol_data.rolling(5).mean().iloc[-1] if len(symbol_data) >= 5 else symbol_data.iloc[-1]
                    ma_long = symbol_data.rolling(20).mean().iloc[-1] if len(symbol_data) >= 20 else symbol_data.iloc[-1]
                    trend_strength = (ma_short - ma_long) / ma_long if ma_long > 0 else 0
                    
                    # Calculate score
                    score = 50  # Base score
                    
                    # Momentum contribution (0-20 points)
                    momentum_score = min(20, max(-20, (momentum_5d + momentum_20d) * 100))
                    score += momentum_score
                    
                    # Volatility contribution (-10 to +10 points, lower vol = higher score)
                    vol_score = max(-10, min(10, (0.3 - volatility) * 50))
                    score += vol_score
                    
                    # Trend contribution (-10 to +20 points)
                    trend_score = min(20, max(-10, trend_strength * 100))
                    score += trend_score
                    
                    scores[symbol] = max(0, min(100, score))
                    
                except Exception as e:
                    logger.warning(f"Error calculating score for {symbol}: {str(e)}")
                    scores[symbol] = 50
            
            return scores
            
        except Exception as e:
            logger.error(f"Error in training score calculation: {str(e)}")
            return {symbol: 50 for symbol in symbols}
    
    def _test_on_period(self, 
                       training_scores: Dict, 
                       symbols: List[str], 
                       start_date: datetime, 
                       end_date: datetime, 
                       price_data: pd.DataFrame) -> Dict:
        """Test the strategy on a specific period"""
        try:
            # Select top stocks based on training scores
            selected_stocks = self._select_stocks(training_scores, top_n=10)
            
            # Simulate portfolio performance
            initial_value = 100000
            cash = initial_value
            holdings = {}
            
            # Buy selected stocks at start of test period
            if selected_stocks:
                allocation_per_stock = cash / len(selected_stocks)
                
                for symbol in selected_stocks:
                    try:
                        if ('Close', symbol) in price_data.columns:
                            start_price = price_data.loc[start_date, ('Close', symbol)]
                            shares = (allocation_per_stock * (1 - self.transaction_cost)) / start_price
                            holdings[symbol] = shares
                            cash -= allocation_per_stock
                    except (KeyError, IndexError):
                        continue
            
            # Calculate final value at end of test period
            final_value = cash
            for symbol, shares in holdings.items():
                try:
                    if ('Close', symbol) in price_data.columns:
                        end_price = price_data.loc[end_date, ('Close', symbol)]
                        final_value += shares * end_price
                except (KeyError, IndexError):
                    continue
            
            # Calculate metrics
            total_return = (final_value / initial_value - 1) * 100
            
            return {
                'selected_stocks': selected_stocks,
                'initial_value': initial_value,
                'final_value': final_value,
                'total_return_pct': round(total_return, 2),
                'num_stocks': len(selected_stocks)
            }
            
        except Exception as e:
            logger.error(f"Error in test period: {str(e)}")
            return {}
    
    def _aggregate_cv_results(self, cv_results: List[Dict]) -> Dict:
        """Aggregate cross-validation results"""
        try:
            if not cv_results:
                return {}
            
            # Extract returns
            returns = [result.get('total_return_pct', 0) for result in cv_results]
            
            # Calculate aggregate metrics
            aggregated = {
                'mean_return_pct': round(np.mean(returns), 2),
                'std_return_pct': round(np.std(returns), 2),
                'min_return_pct': round(np.min(returns), 2),
                'max_return_pct': round(np.max(returns), 2),
                'positive_periods': sum(1 for r in returns if r > 0),
                'total_periods': len(returns),
                'win_rate_pct': round((sum(1 for r in returns if r > 0) / len(returns)) * 100, 2) if returns else 0
            }
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating CV results: {str(e)}")
            return {}
    
    def generate_backtest_report(self, results: Dict, output_file: str = None) -> str:
        """Generate a comprehensive backtest report"""
        try:
            report = []
            report.append("=" * 60)
            report.append("ENHANCED STOCK SCREENER BACKTEST REPORT")
            report.append("=" * 60)
            report.append("")
            
            if 'performance_metrics' in results:
                metrics = results['performance_metrics']
                report.append("PERFORMANCE METRICS:")
                report.append("-" * 30)
                report.append(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
                report.append(f"Annualized Return: {metrics.get('annualized_return_pct', 0):.2f}%")
                report.append(f"Volatility: {metrics.get('volatility_pct', 0):.2f}%")
                report.append(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                report.append(f"Maximum Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
                report.append(f"Win Rate: {metrics.get('win_rate_pct', 0):.2f}%")
                report.append("")
            
            if 'cv_results' in results:
                report.append("CROSS-VALIDATION RESULTS:")
                report.append("-" * 30)
                for i, cv_result in enumerate(results['cv_results']):
                    report.append(f"Fold {i+1}: {cv_result.get('total_return_pct', 0):.2f}%")
                
                if 'aggregated_metrics' in results:
                    agg = results['aggregated_metrics']
                    report.append("")
                    report.append("AGGREGATED METRICS:")
                    report.append(f"Mean Return: {agg.get('mean_return_pct', 0):.2f}%")
                    report.append(f"Std Return: {agg.get('std_return_pct', 0):.2f}%")
                    report.append(f"Win Rate: {agg.get('win_rate_pct', 0):.2f}%")
            
            report.append("")
            report.append("=" * 60)
            
            report_text = "\n".join(report)
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(report_text)
                logger.info(f"Report saved to {output_file}")
            
            return report_text
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return "Error generating report"


def main():
    """Example usage of the enhanced backtester"""
    backtester = EnhancedBacktester(initial_capital=100000)
    
    # Example symbols (Nifty 50 subset)
    symbols = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'WIPRO', 'SBIN', 'ITC', 'LT', 'ONGC', 'NTPC']
    
    # Time-series backtest
    logger.info("Running time-series backtest...")
    ts_results = backtester.time_series_backtest(
        symbols=symbols,
        start_date='2023-01-01',
        end_date='2024-01-01',
        rebalance_frequency='monthly'
    )
    
    if ts_results:
        print(f"Time-series backtest completed!")
        print(f"Final portfolio value: {ts_results['final_value']:,.2f}")
        print(f"Total return: {ts_results['total_return']:.2f}%")
    
    # Cross-validation backtest
    logger.info("Running cross-validation backtest...")
    cv_results = backtester.cross_validation_backtest(
        symbols=symbols,
        start_date='2023-01-01',
        end_date='2024-01-01',
        n_splits=5
    )
    
    if cv_results and 'aggregated_metrics' in cv_results:
        print(f"\nCross-validation completed!")
        agg = cv_results['aggregated_metrics']
        print(f"Mean return: {agg['mean_return_pct']:.2f}%")
        print(f"Win rate: {agg['win_rate_pct']:.2f}%")
    
    # Generate report
    if ts_results:
        report = backtester.generate_backtest_report(ts_results, 'backtest_report.txt')
        print("\nBacktest Report:")
        print(report)


if __name__ == "__main__":
    main()
