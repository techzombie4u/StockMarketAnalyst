
"""
Test Daily Technical Analysis Module

Tests the enhanced daily OHLC technical analysis functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from daily_technical_analyzer import DailyTechnicalAnalyzer, get_daily_technical_analysis
import json

def test_daily_technical_analysis():
    """Test daily technical analysis functionality"""
    print("🧪 Testing Daily Technical Analysis")
    print("=" * 50)
    
    analyzer = DailyTechnicalAnalyzer()
    
    # Test symbols
    test_symbols = ['RELIANCE', 'TCS', 'SBIN', 'ITC']
    
    for symbol in test_symbols:
        print(f"\n📊 Testing {symbol}:")
        print("-" * 30)
        
        try:
            # Test daily OHLC data fetching
            daily_data = analyzer.fetch_daily_ohlc_data(symbol)
            
            if daily_data is not None and not daily_data.empty:
                print(f"✅ Daily OHLC data: {len(daily_data)} days")
                
                # Test technical indicators calculation
                indicators = analyzer.calculate_daily_technical_indicators(symbol)
                
                if indicators:
                    print(f"✅ Technical indicators: {len(indicators)} metrics")
                    
                    # Display key indicators
                    key_indicators = [
                        'current_price', 'trend_direction', 'rsi_14', 'above_sma_20',
                        'volume_classification', 'volatility_regime', 'adx', 'macd_bullish'
                    ]
                    
                    print("📈 Key Technical Indicators:")
                    for indicator in key_indicators:
                        if indicator in indicators:
                            value = indicators[indicator]
                            print(f"   {indicator}: {value}")
                    
                    # Test technical summary
                    summary = analyzer.generate_daily_technical_summary(indicators)
                    print(f"📋 Technical Summary: {summary}")
                    
                    print(f"✅ {symbol} analysis complete")
                else:
                    print(f"❌ {symbol} technical indicators failed")
            else:
                print(f"❌ {symbol} daily data fetch failed")
                
        except Exception as e:
            print(f"❌ {symbol} test failed: {str(e)}")
    
    # Test convenience function
    print(f"\n🔧 Testing convenience function:")
    print("-" * 30)
    
    try:
        result = get_daily_technical_analysis('RELIANCE')
        if result:
            print("✅ Convenience function works")
            print(f"   Analysis type: {result.get('analysis_type', 'N/A')}")
            print(f"   Timeframe: {result.get('timeframe', 'N/A')}")
            print(f"   Data points: {result.get('data_points', 'N/A')}")
        else:
            print("❌ Convenience function failed")
    except Exception as e:
        print(f"❌ Convenience function error: {str(e)}")
    
    print(f"\n🏁 Daily Technical Analysis Testing Complete")

def test_integration_with_screener():
    """Test integration with main stock screener"""
    print(f"\n🔗 Testing Integration with Stock Screener")
    print("=" * 50)
    
    try:
        from stock_screener import EnhancedStockScreener
        
        screener = EnhancedStockScreener()
        
        # Test enhanced technical indicators with daily analysis
        test_symbol = 'RELIANCE'
        print(f"Testing enhanced indicators for {test_symbol}...")
        
        indicators = screener.calculate_enhanced_technical_indicators(test_symbol)
        
        if indicators:
            analysis_type = indicators.get('analysis_type', 'unknown')
            timeframe = indicators.get('timeframe', 'unknown')
            
            print(f"✅ Enhanced indicators successful")
            print(f"   Analysis type: {analysis_type}")
            print(f"   Timeframe: {timeframe}")
            print(f"   Current price: {indicators.get('current_price', 'N/A')}")
            print(f"   Data quality: {indicators.get('data_quality_score', 'N/A')}")
            
            # Test scoring with daily indicators
            score_boost = screener._score_technical_indicators(indicators)
            print(f"   Technical score boost: {score_boost}")
            
            # Test summary generation
            summary = screener._generate_technical_summary(indicators)
            print(f"   Technical summary: {summary}")
            
            print("✅ Integration test successful")
        else:
            print("❌ Integration test failed - no indicators returned")
            
    except Exception as e:
        print(f"❌ Integration test error: {str(e)}")

def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Daily Technical Analysis Tests")
    print("=" * 60)
    
    test_daily_technical_analysis()
    test_integration_with_screener()
    
    print(f"\n🎉 All Tests Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
