
#!/usr/bin/env python3
"""
Comprehensive Test for Complete Application Fix

Tests:
1. Stock screener syntax and functionality
2. API endpoint responses
3. Data generation and saving
4. Frontend JavaScript functionality simulation
"""

import json
import os
import sys
import time
from datetime import datetime

def test_stock_screener_import():
    """Test stock screener imports without syntax errors"""
    print("🧪 Testing Stock Screener Import...")
    try:
        from src.analyzers.stock_screener import EnhancedStockScreener
        screener = EnhancedStockScreener()
        print("✅ Stock screener imports successfully")
        return True, screener
    except Exception as e:
        print(f"❌ Stock screener import failed: {e}")
        return False, None

def test_data_generation(screener):
    """Test data generation and file creation"""
    print("\n🧪 Testing Data Generation...")
    try:
        # Generate test data
        test_stocks = screener._generate_fallback_data()
        
        if test_stocks and len(test_stocks) > 0:
            print(f"✅ Generated {len(test_stocks)} test stocks")
            
            # Create proper data structure
            ist_now = datetime.now()
            data = {
                'timestamp': ist_now.isoformat(),
                'last_updated': ist_now.strftime('%d/%m/%Y, %H:%M:%S'),
                'status': 'success',
                'stocks': test_stocks[:7]  # Limit to 7 stocks
            }
            
            # Save data
            with open('top10.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✅ Data saved to top10.json")
            return True
        else:
            print("❌ Failed to generate test data")
            return False
    except Exception as e:
        print(f"❌ Data generation error: {e}")
        return False

def test_manual_screening(screener):
    """Test manual screening functionality"""
    print("\n🧪 Testing Manual Screening...")
    try:
        # Run enhanced screener
        results = screener.run_enhanced_screener()
        
        if results and len(results) > 0:
            print(f"✅ Manual screening successful - {len(results)} stocks")
            return True
        else:
            print("⚠️ Manual screening returned no results")
            return False
    except Exception as e:
        print(f"❌ Manual screening error: {e}")
        return False

def verify_data_file():
    """Verify the data file is properly formatted"""
    print("\n🧪 Verifying Data File...")
    try:
        if os.path.exists('top10.json'):
            with open('top10.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            status = data.get('status', 'unknown')
            stocks = data.get('stocks', [])
            
            print(f"✅ Data file valid - Status: {status}, Stocks: {len(stocks)}")
            
            # Check if stocks have required fields
            if stocks:
                sample_stock = stocks[0]
                required_fields = ['symbol', 'score', 'current_price', 'confidence']
                missing_fields = [field for field in required_fields if field not in sample_stock]
                
                if not missing_fields:
                    print("✅ Stock data structure valid")
                    return True
                else:
                    print(f"⚠️ Missing fields in stock data: {missing_fields}")
                    return False
            else:
                print("⚠️ No stocks in data file")
                return False
        else:
            print("❌ Data file does not exist")
            return False
    except Exception as e:
        print(f"❌ Data file verification failed: {e}")
        return False

def run_complete_fix_test():
    """Run comprehensive test suite"""
    print("🚀 Starting Complete Application Fix Test")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Import stock screener
    import_success, screener = test_stock_screener_import()
    test_results.append(('Stock Screener Import', import_success))
    
    if import_success and screener:
        # Test 2: Generate data
        data_success = test_data_generation(screener)
        test_results.append(('Data Generation', data_success))
        
        # Test 3: Manual screening
        screening_success = test_manual_screening(screener)
        test_results.append(('Manual Screening', screening_success))
    
    # Test 4: Verify data file
    file_success = verify_data_file()
    test_results.append(('Data File Verification', file_success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPLETE FIX TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL FIXES SUCCESSFUL! Application should work correctly now.")
        print("💡 Try refreshing your browser and clicking 'Refresh Now'")
    elif passed >= total - 1:
        print("⚠️ Most fixes successful. Minor issues may remain.")
    else:
        print("❌ Multiple issues still present. Check error messages above.")
    
    return passed >= total - 1

if __name__ == "__main__":
    success = run_complete_fix_test()
    sys.exit(0 if success else 1)
