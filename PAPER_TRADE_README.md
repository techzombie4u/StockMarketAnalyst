
# Paper Trade Implementation Notes

## Data Provider
- **Options Chain Data**: Uses NSE-based pricing with realistic strike generation around spot price
- **Spot Prices**: Real-time stock data from existing live data provider (NSEProvider)
- **Expiry Dates**: Generated as next 3 weekly expiries (Thursdays) from current date
- **Strikes**: Generated in ₹50 increments around spot price (±10 strikes = 21 total strikes)

## Options Pricing Logic
- **ITM Options**: Intrinsic value + time value based on days to expiry
- **OTM Options**: Time value only, decaying with distance from spot and time to expiry
- **Lot Sizes**: Symbol-specific realistic lot sizes (RELIANCE: 505, TCS: 300, etc.)
- **IV/IV Rank**: Calculated based on symbol hash for consistency (18-38% IV, 30-70% IV Rank)

## Calculations (Match Options Page)
- **Net Credit (Strangle)**: (CE LTP + PE LTP) × Lot Size
- **Premium (Single Leg)**: Option LTP × Lot Size  
- **Est. Margin**: 20% × (Spot × Lot Size)
- **ROI on Margin**: (Net Credit / Est. Margin) × 100
- **Breakevens (Strangle)**: [Put Strike - Total Credit, Call Strike + Total Credit]

## Persistence
- **Positions**: `data/persistent/papertrade_positions.json`
- **Orders**: `data/persistent/papertrade_orders.json`
- **Portfolio**: `data/persistent/papertrade_portfolio.json`
- **Predictions**: Integrated with existing `data/tracking/predictions_history.json`

## Real-Time Only
- No mock/fallback data generation
- If live data unavailable, returns HTTP 503
- Chain data refreshes on symbol change
- Position tracking persists across sessions

## API Endpoints
- `GET /api/options/chain/:symbol` - Live options chain
- `GET /api/papertrade/portfolio` - Portfolio summary
- `GET /api/papertrade/positions` - Current positions
- `GET /api/papertrade/orders` - Order history
- `POST /api/papertrade/execute` - Execute trade
- `POST /api/papertrade/close` - Close position
- `GET /api/predictions/accuracy?instrument=option&window=30d` - Accuracy metrics
