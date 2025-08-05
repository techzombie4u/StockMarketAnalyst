
# Changelog

All notable changes to the Stock Market Analyst application will be documented in this file.

## [1.6.0] - 2025-08-05

### Added
- **Persistent Graph Locks**: Interactive graphs maintain lock status across page refreshes and deployments
- **Trading Day Lock System**: Lock duration based on trading days (5D/30D) rather than calendar days
- **Real-Time Session Tracking**: Dynamic session count updates in Stock Prediction Analysis page
- **Live Accuracy Calculations**: Performance metrics calculated from actual session data
- **Enhanced Lock Management**: Existing locks preserved during stock data updates and new additions

### Enhanced
- **User Experience**: Lock behavior now consistent with user expectations
- **Data Persistence**: Lock status stored in JSON with trading day calculations
- **Performance Metrics**: Dynamic calculation of accuracy rates and analysis status
- **Interactive Analytics**: Improved feedback for lock duration and status

### Fixed
- Graph locks no longer reset on page refresh or server restart
- Session count now updates dynamically instead of showing static values
- Lock status preserved when new stocks are added to tracking
- Trading day calculation excludes weekends for accurate lock duration

## [1.5.0] - 2025-08-04

### Added
- Complete Smart Stock Agent integration
- LSTM and Random Forest ML model predictions
- Advanced signal consolidation and conflict resolution
- Prediction stability management system
- Performance-aware model weight adjustment

### Enhanced
- Daily OHLC technical analysis with 50+ indicators
- Multi-source signal validation and filtering
- Comprehensive error handling and recovery systems
- Production-ready performance optimization

## [1.4.0] - 2025-01-31

### Added
- Comprehensive regression testing framework
- Enhanced filtering for high-confidence stocks (>70 score)
- Real-time alert system for high-scoring opportunities
- Performance optimization with sub-second API responses

### Enhanced
- Production stability with 100% uptime
- Graceful error recovery and fallback systems
- Multi-source data validation capabilities

## [1.3.0] - 2025-01-30

### Added
- Enhanced daily technical analysis with ADX, Ichimoku, MFI, CCI
- Pattern recognition and candlestick analysis
- Support/resistance level calculations
- Risk metrics including VaR, Sharpe ratio, and drawdown

### Enhanced
- Moved from intraday to stable daily OHLC data analysis
- Improved technical signal reliability and accuracy
- Advanced chart pattern detection capabilities

## [1.2.0] - 2025-01-27

### Added
- Daily OHLC technical analysis enhancement
- Multi-timeframe analysis support
- Trend strength scoring with ADX
- Volume analysis with OBV and PVT
- Volatility regime classification

### Enhanced
- Scoring algorithm optimized for daily timeframe
- Risk-adjusted scoring with volatility metrics
- Intelligent fallback to intraday data when needed

## [1.1.0] - 2025-01-27

### Changed
- Reduced prediction frequency from 30 minutes to 24 hours
- Implemented 3 consecutive confirmations before alerts
- Added 24-hour minimum hold period for recommendations
- Enhanced confidence filtering (>70% threshold)

### Added
- Signal management system
- Enhanced error handling
- Performance caching system
- Risk management integration

## [1.0.0] - 2025-01-27

### Added
- Initial release with 30-minute updates
- Basic technical and fundamental analysis
- Real-time dashboard with auto-refresh
- Enhanced scoring algorithm
- Multiple data source integration
