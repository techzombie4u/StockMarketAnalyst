
# 📈 Stock Market Analyst

A comprehensive AI-powered stock screener and analysis dashboard for Indian stock markets. This application automatically screens stocks based on fundamental analysis, technical indicators, and market sentiment to identify high-potential investment opportunities.

## 🌟 Features

### 📊 **Data Collection**
- **Fundamental Analysis**: Scrapes PE ratios, quarterly revenue/earnings growth from Screener.in
- **Technical Analysis**: Calculates 14-day ATR and momentum indicators using yfinance
- **Market Intelligence**: Monitors bulk deals from institutional investors and promoters
- **Real-time Pricing**: Fetches current stock prices with volatility metrics

### 🎯 **Smart Scoring Algorithm**
- **Multi-factor Scoring**: Combines fundamental, technical, and sentiment factors
- **Bulk Deal Bonus**: +30 points for significant institutional activity
- **Strong Fundamentals**: +20 points for low PE with high growth
- **Promoter Confidence**: +20 points for recent promoter purchases
- **Momentum Analysis**: ±10 points based on price momentum vs volatility
- **Risk Adjustment**: Emphasizes low-volatility, high-score opportunities

### 🚀 **Automated Operations**
- **Scheduled Screening**: Runs every 30 minutes with APScheduler
- **Smart Alerts**: Notifies for high-scoring stocks (>70 points)
- **Duplicate Prevention**: Tracks alerted stocks to avoid spam
- **Error Handling**: Graceful handling of network issues and rate limits

### 🖥️ **Interactive Dashboard**
- **Real-time Updates**: Auto-refreshes every 30 seconds
- **Responsive Design**: Works on desktop and mobile devices
- **Live Countdown**: Shows time until next data update
- **Manual Refresh**: Trigger immediate screening on-demand
- **Status Indicators**: Visual feedback for data loading states

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Internet connection for data scraping
- Modern web browser

### 🚀 Quick Start on Replit

1. **Fork this Repl** or upload the code to your Replit workspace
2. **Install Dependencies**: Dependencies will auto-install from `pyproject.toml`
3. **Run the Application**:
   ```bash
   python main.py
   ```
4. **Access Dashboard**: Open the web preview or navigate to the provided URL

### 💻 Local Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd stock-market-analyst
   ```

2. **Install dependencies**:
   ```bash
   pip install flask beautifulsoup4 requests yfinance apscheduler pandas numpy
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

4. **Open dashboard**: Navigate to `http://localhost:5000`

## 📁 Project Structure

```
stock-market-analyst/
├── main.py                 # Application entry point
├── app.py                  # Flask web application
├── stock_screener.py       # Core screening logic
├── scheduler.py            # APScheduler automation
├── templates/
│   └── index.html         # Dashboard HTML template
├── top10.json             # Generated stock results (auto-created)
├── jobs.sqlite            # Scheduler database (auto-created)
├── pyproject.toml         # Python dependencies
└── README.md              # This file
```

## 🎮 Usage Guide

### Dashboard Interface

1. **Stock Table**: Displays top 10 stocks with scores and predictions
2. **Status Indicator**: Shows data loading status (Loading/Success/Error)
3. **Countdown Timer**: Time remaining until next auto-refresh
4. **Refresh Button**: Manually trigger new screening
5. **Last Updated**: Timestamp of most recent data

### Understanding the Scores

- **Score (0-100)**: Overall stock attractiveness based on multiple factors
- **Adjusted Score**: Score weighted by volatility (lower volatility = higher adj score)
- **Predicted Gain %**: Expected price appreciation (Score ÷ 5)
- **Time Horizon**: Estimated days to reach target price (~100 ÷ Score)

### Stock Selection Criteria

**High-Score Stocks (70+)**:
- Recent bulk deals by institutions/promoters
- Strong fundamentals (low PE + high growth)
- Positive momentum with manageable volatility

**Medium-Score Stocks (40-69)**:
- Some positive factors but missing key criteria
- Moderate growth or higher volatility

**Low-Score Stocks (<40)**:
- Limited positive indicators
- High volatility or poor fundamentals

## ⚙️ Configuration

### Modify Watchlist
Edit the `watchlist` in `stock_screener.py`:

```python
self.watchlist = [
    'RELIANCE', 'TCS', 'HDFCBANK',  # Add your preferred stocks
    # ... more symbols
]
```

### Adjust Screening Frequency
Modify interval in `app.py`:

```python
scheduler.start_scheduler(interval_minutes=30)  # Change to desired frequency
```

### Customize Scoring Logic
Update weights in `score_and_rank()` method in `stock_screener.py`:

```python
# Bulk deal bonus (+30 points)
if symbol in bulk_deal_symbols:
    score += 30  # Adjust this value

# Strong fundamentals (+20 points)
if pe_ratio > 0 and pe_ratio < median_pe and (revenue_growth >= 20 or earnings_growth >= 20):
    score += 20  # Adjust this value
```

## 🔧 API Endpoints

- `GET /`: Main dashboard interface
- `GET /api/stocks`: JSON data of current stock results
- `GET /api/status`: Scheduler status and job information
- `POST /api/run-now`: Manually trigger screening

## 📊 Sample Output

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "last_updated": "2024-01-15 10:30:00",
  "stocks": [
    {
      "symbol": "RELIANCE",
      "score": 85.0,
      "adjusted_score": 78.3,
      "volatility": 2.1,
      "current_price": 2456.70,
      "predicted_price": 2873.34,
      "predicted_gain": 17.0,
      "time_horizon": 12
    }
  ]
}
```

## ⚠️ Important Notes

### Legal & Ethical Considerations
- **Personal Use Only**: This tool is designed for personal investment research
- **Respect Rate Limits**: Built-in delays prevent overloading data sources
- **No Investment Advice**: Results are for informational purposes only
- **DYOR**: Always conduct your own research before making investment decisions

### Technical Limitations
- **Data Dependencies**: Relies on external websites (Screener.in, Yahoo Finance)
- **Network Connectivity**: Requires stable internet for data collection
- **Rate Limiting**: May have delays during high-traffic periods
- **Market Hours**: Some data sources may be limited during market closure

### Production Considerations
- **Scheduler Persistence**: Uses SQLite for reliable job scheduling
- **Error Recovery**: Graceful handling of network timeouts and parsing errors
- **Resource Management**: Optimized for continuous operation
- **Logging**: Comprehensive logging for monitoring and debugging

## 🚀 Future Enhancements

### Planned Features
1. **Alert System**: SMS/Email notifications for high-scoring stocks
2. **Broker Integration**: Direct trading through broker APIs
3. **Advanced Analytics**: Technical indicators (RSI, MACD, Bollinger Bands)
4. **Sentiment Analysis**: News sentiment and social media monitoring
5. **Portfolio Tracking**: Track selected stocks and performance
6. **Backtesting**: Historical performance analysis of scoring algorithm

### Integration Opportunities
- **Zerodha Kite API**: For live trading and portfolio management
- **Telegram Bot**: For mobile alerts and commands
- **Discord Integration**: For community discussions and alerts
- **WhatsApp Business API**: For personalized notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your improvements
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:
1. Check the logs in the console
2. Verify internet connectivity
3. Ensure all dependencies are installed
4. Review the error messages in the dashboard

## 📄 License

This project is for educational and personal use only. Please respect the terms of service of data providers and use responsibly.

---

**⚡ Ready to discover your next investment opportunity? Run the application and start screening! 📈**
