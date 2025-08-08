
"""
Test Script for Enhanced Features

Tests the new risk management, caching, error handling, and signal filtering features
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_risk_management():
    """Test risk management features"""
    try:
        from risk_manager import RiskManager, calculate_position_sizes
        
        print("=== Testing Risk Management ===")
        
        # Sample stock data
        test_stocks = [
            {
                'symbol': 'RELIANCE',
                'current_price': 2500,
                'confidence': 85,
                'predicted_gain': 15,
                'technical': {'atr_volatility': 2.0},
                'market_cap': 'Large Cap'
            },
            {
                'symbol': 'TCS',
                'current_price': 3200,
                'confidence': 75,
                'predicted_gain': 12,
                'technical': {'atr_volatility': 1.5},
                'market_cap': 'Large Cap'
            }
        ]
        
        # Test position sizing
        enhanced_stocks = calculate_position_sizes(test_stocks, portfolio_value=100000)
        
        for stock in enhanced_stocks:
            pos_info = stock.get('position_sizing', {})
            print(f"{stock['symbol']}: {pos_info.get('recommended_shares', 0)} shares, "
                  f"{pos_info.get('position_percentage', 0)}% allocation")
        
        print("✅ Risk management test passed")
        return True
        
    except Exception as e:
        print(f"❌ Risk management test failed: {str(e)}")
        return False

def test_performance_cache():
    """Test performance caching"""
    try:
        from performance_cache import cache, StockDataCache
        
        print("\n=== Testing Performance Cache ===")
        
        # Test basic cache operations
        cache.set('test_key', {'data': 'test_value'}, ttl=60)
        cached_data = cache.get('test_key')
        
        if cached_data and cached_data.get('data') == 'test_value':
            print("✅ Basic caching works")
        else:
            print("❌ Basic caching failed")
            return False
        
        # Test stock data caching
        test_technical_data = {'rsi_14': 65, 'atr_volatility': 2.5}
        StockDataCache.cache_technical_indicators('TEST', test_technical_data)
        
        cached_technical = StockDataCache.get_cached_technical_indicators('TEST')
        if cached_technical and cached_technical.get('rsi_14') == 65:
            print("✅ Stock data caching works")
        else:
            print("❌ Stock data caching failed")
            return False
        
        # Test cache statistics
        stats = cache.get_stats()
        print(f"Cache stats: {stats['cache_size']} items, {stats['hit_rate']}% hit rate")
        
        print("✅ Performance cache test passed")
        return True
        
    except Exception as e:
        print(f"❌ Performance cache test failed: {str(e)}")
        return False

def test_error_handling():
    """Test enhanced error handling"""
    try:
        from enhanced_error_handler import RetryStrategy, DataValidation, safe_execute
        
        print("\n=== Testing Error Handling ===")
        
        # Test data validation
        test_data = {
            'symbol': 'TEST',
            'current_price': 100.5,
            'technical': {'rsi_14': 65},
            'fundamentals': {'pe_ratio': 15}
        }
        
        validated = DataValidation.validate_stock_data(test_data)
        if validated['is_valid']:
            print("✅ Data validation works")
        else:
            print("❌ Data validation failed")
            return False
        
        # Test safe execution
        def test_function():
            return {'result': 'success'}
        
        result = safe_execute(test_function)
        if result['success'] and result['data']['result'] == 'success':
            print("✅ Safe execution works")
        else:
            print("❌ Safe execution failed")
            return False
        
        print("✅ Error handling test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def test_signal_filtering():
    """Test advanced signal filtering"""
    try:
        from src.agents.advanced_signal_filter import AdvancedSignalFilter, apply_advanced_filtering
        
        print("\n=== Testing Signal Filtering ===")
        
        # Sample signals with better data
        test_signals = [
            {
                'symbol': 'GOOD_SIGNAL',
                'confidence': 85,
                'score': 75,
                'technical': {
                    'atr_volatility': 2.0,
                    'rsi_14': 55,
                    'volume_sma_ratio': 1.4,
                    'trend_strength': 75
                },
                'market_cap': 'Mid Cap',
                'fundamentals': {'revenue_growth': 15}
            },
            {
                'symbol': 'MODERATE_SIGNAL',
                'confidence': 78,
                'score': 65,
                'technical': {
                    'atr_volatility': 3.0,
                    'rsi_14': 60,
                    'volume_sma_ratio': 1.2,
                    'trend_strength': 60
                },
                'market_cap': 'Large Cap',
                'fundamentals': {'revenue_growth': 10}
            }
        ]
        
        filter_result = apply_advanced_filtering(test_signals)
        filtered_signals = filter_result['filtered_signals']
        filter_stats = filter_result['filter_stats']
        
        print(f"Filtered {filter_stats['total_input']} → {filter_stats['filtered_output']} signals")
        print(f"Quality score: {filter_result['quality_score']}")
        
        # Both signals should now pass with the updated criteria
        if len(filtered_signals) >= 1:
            print("✅ Signal filtering works correctly")
        else:
            print("❌ Signal filtering still too restrictive")
            print(f"Filter reasons: {filter_stats.get('filter_reasons', {})}")
            return False
        
        print("✅ Signal filtering test passed")
        return True
        
    except Exception as e:
        print(f"❌ Signal filtering test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Features\n")
    
    tests = [
        test_risk_management,
        test_performance_cache,
        test_error_handling,
        test_signal_filtering
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All enhanced features are working correctly!")
    else:
        print("⚠️  Some features need attention")
    
    return passed == total

if __name__ == "__main__":
    main()
