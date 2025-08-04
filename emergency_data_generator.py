
#!/usr/bin/env python3
"""
Emergency Data Generator
Creates working stock data when the main system fails
"""

import json
import random
from datetime import datetime

def generate_emergency_data():
    """Generate emergency stock data for system recovery"""
    
    # Define realistic stock symbols and their typical price ranges
    stocks_data = {
        'RELIANCE': {'price_range': (2300, 2600), 'pe_range': (12, 18)},
        'SBIN': {'price_range': (700, 900), 'pe_range': (8, 15)},
        'BHARTIARTL': {'price_range': (900, 1200), 'pe_range': (15, 25)},
        'ITC': {'price_range': (400, 500), 'pe_range': (20, 30)},
        'NTPC': {'price_range': (250, 350), 'pe_range': (10, 18)},
        'COALINDIA': {'price_range': (350, 450), 'pe_range': (8, 15)},
        'TATASTEEL': {'price_range': (120, 180), 'pe_range': (5, 12)}
    }
    
    emergency_stocks = []
    
    for symbol, data in stocks_data.items():
        # Generate realistic data
        current_price = round(random.uniform(*data['price_range']), 2)
        pe_ratio = round(random.uniform(*data['pe_range']), 1)
        score = random.uniform(45, 85)
        
        # Calculate predictions based on score
        predicted_gain = score * 0.2
        
        stock_data = {
            'symbol': symbol,
            'score': round(score, 1),
            'adjusted_score': round(score * 0.95, 1),
            'confidence': min(95, max(60, int(score * 1.1))),
            'current_price': current_price,
            'predicted_price': round(current_price * (1 + predicted_gain / 100), 2),
            'predicted_gain': round(predicted_gain, 2),
            'pred_24h': round(predicted_gain * 0.05, 2),
            'pred_5d': round(predicted_gain * 0.25, 2),
            'pred_1mo': round(predicted_gain, 2),
            'volatility': round(random.uniform(1.5, 4.0), 1),
            'time_horizon': random.randint(10, 30),
            'pe_ratio': pe_ratio,
            'pe_description': get_pe_description(pe_ratio),
            'revenue_growth': round(random.uniform(-5, 15), 1),
            'earnings_growth': round(random.uniform(-10, 20), 1),
            'risk_level': random.choice(['Low', 'Medium', 'Medium', 'High']),
            'market_cap': estimate_market_cap(symbol),
            'technical_summary': f"Emergency Data | Score: {score:.1f}",
            'last_analyzed': datetime.now().strftime('%d/%m/%Y, %H:%M:%S')
        }
        
        emergency_stocks.append(stock_data)
    
    # Sort by score
    emergency_stocks.sort(key=lambda x: x['score'], reverse=True)
    
    return emergency_stocks

def get_pe_description(pe_ratio):
    """Convert PE ratio to description"""
    if pe_ratio < 10:
        return "Very Low"
    elif pe_ratio < 15:
        return "Below Average"
    elif pe_ratio <= 20:
        return "At Par"
    elif pe_ratio <= 30:
        return "Above Average"
    else:
        return "High"

def estimate_market_cap(symbol):
    """Estimate market cap category"""
    large_caps = ['RELIANCE', 'SBIN', 'BHARTIARTL', 'ITC', 'NTPC', 'COALINDIA']
    if symbol in large_caps:
        return "Large Cap"
    else:
        return "Mid Cap"

def save_emergency_data():
    """Generate and save emergency data"""
    try:
        stocks = generate_emergency_data()
        
        emergency_data = {
            'timestamp': datetime.now().isoformat(),
            'last_updated': datetime.now().strftime('%d/%m/%Y, %H:%M:%S'),
            'status': 'emergency_data',
            'stocks': stocks,
            'total_stocks': len(stocks),
            'note': 'Emergency data generated due to system issues'
        }
        
        with open('top10.json', 'w', encoding='utf-8') as f:
            json.dump(emergency_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Emergency data saved with {len(stocks)} stocks")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save emergency data: {e}")
        return False

if __name__ == "__main__":
    save_emergency_data()
