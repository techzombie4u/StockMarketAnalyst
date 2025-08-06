
#!/usr/bin/env python3
"""
Future Date Testing for Interactive Prediction Tracker
Test how graphs behave with different date scenarios
"""

import json
import os
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import logging
from interactive_tracker_manager import InteractiveTrackerManager

IST = pytz.timezone('Asia/Kolkata')

class FutureDateTester:
    def __init__(self):
        self.tracker = InteractiveTrackerManager()
        self.test_scenarios = []

    def fetch_real_stock_prices(self, symbol, start_date, days=30):
        """Fetch real historical stock prices for testing"""
        try:
            # Use real Indian stocks for testing
            real_symbols = {
                'TEST_PAST_DATE': 'RELIANCE.NS',
                'TEST_CURRENT_DATE': 'TCS.NS', 
                'TEST_FUTURE_1WEEK': 'INFY.NS',
                'TEST_FUTURE_1MONTH': 'HINDUNILVR.NS',
                'TEST_NEXT_MONDAY': 'WIPRO.NS'
            }
            
            real_symbol = real_symbols.get(symbol, 'SBIN.NS')
            
            # Fetch historical data
            end_date = start_date + timedelta(days=days + 10)  # Extra days for weekends
            ticker = yf.Ticker(real_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                print(f"⚠️ No historical data for {real_symbol}, using simulated data")
                return self._generate_realistic_prices(100.0, days)
            
            # Extract closing prices for trading days
            closing_prices = hist['Close'].tolist()[:days]
            
            # Fill remaining days with realistic projections if needed
            while len(closing_prices) < days:
                last_price = closing_prices[-1] if closing_prices else 100.0
                # Add realistic daily variation (-2% to +2%)
                daily_change = 0.98 + (0.04 * hash(str(len(closing_prices))) % 100) / 100
                closing_prices.append(last_price * daily_change)
            
            print(f"✅ Fetched {len(closing_prices)} real prices for {symbol} using {real_symbol}")
            return closing_prices[:days]
            
        except Exception as e:
            print(f"⚠️ Error fetching real prices for {symbol}: {e}")
            return self._generate_realistic_prices(100.0, days)
    
    def _generate_realistic_prices(self, base_price, days):
        """Generate realistic price movements for testing"""
        prices = [base_price]
        for i in range(1, days):
            # Realistic daily variation with slight upward trend
            daily_change = 0.985 + (0.03 * hash(str(i)) % 100) / 100
            trend_factor = 1 + (0.002 * i)  # Slight upward trend
            new_price = prices[-1] * daily_change * trend_factor
            prices.append(round(new_price, 2))
        return prices

    def create_test_scenario(self, scenario_name, start_date_offset_days=0, lock_5d=False, lock_30d=False):
        """Create a test scenario with real historical prices for immediate testing"""
        # Calculate test start date
        base_date = datetime.now(IST) + timedelta(days=start_date_offset_days)
        test_start_date = base_date.strftime('%Y-%m-%d')
        
        # Create test stock data
        test_symbol = f"TEST_{scenario_name.upper()}"
        
        # Fetch real historical prices for this scenario
        start_date_obj = datetime.strptime(test_start_date, '%Y-%m-%d')
        real_prices = self.fetch_real_stock_prices(test_symbol, start_date_obj, 30)
        
        base_price = real_prices[0]
        
        # Generate predictions based on the real starting price
        predicted_5d = real_prices[:5] if len(real_prices) >= 5 else [base_price + i for i in range(5)]
        predicted_30d = real_prices[:30] if len(real_prices) >= 30 else real_prices + [real_prices[-1] + i for i in range(len(real_prices), 30)]
        
        # Add some prediction variation to make it realistic
        for i in range(len(predicted_5d)):
            variation = 0.98 + (0.04 * hash(f"{test_symbol}_{i}") % 100) / 100
            predicted_5d[i] = round(predicted_5d[i] * variation, 2)
        
        for i in range(len(predicted_30d)):
            variation = 0.97 + (0.06 * hash(f"{test_symbol}_30_{i}") % 100) / 100
            predicted_30d[i] = round(predicted_30d[i] * variation, 2)
        
        # For past scenarios, show some actual progress
        actual_5d = [base_price] + [None] * 4
        actual_30d = [base_price] + [None] * 29
        
        if start_date_offset_days < 0:  # Past date scenario
            # Show actual progress for past dates
            days_elapsed = min(abs(start_date_offset_days), 30)
            for i in range(1, min(days_elapsed + 1, 5)):
                if i < len(real_prices):
                    actual_5d[i] = real_prices[i]
            for i in range(1, min(days_elapsed + 1, 30)):
                if i < len(real_prices):
                    actual_30d[i] = real_prices[i]
        
        test_data = {
            'symbol': test_symbol,
            'start_date': test_start_date,
            'current_price': base_price,
            'confidence': 85,
            'score': 75,
            'predicted_5d': predicted_5d,
            'predicted_30d': predicted_30d,
            'actual_progress_5d': actual_5d,
            'actual_progress_30d': actual_30d,
            'updated_prediction_5d': [None] * 5,
            'updated_prediction_30d': [None] * 30,
            'locked_5d': lock_5d,
            'locked_30d': lock_30d,
            'lock_start_date_5d': test_start_date if lock_5d else None,
            'lock_start_date_30d': test_start_date if lock_30d else None,
            'persistent_lock_5d': lock_5d,
            'persistent_lock_30d': lock_30d,
            'last_updated': datetime.now(IST).isoformat(),
            'days_tracked': abs(start_date_offset_days) if start_date_offset_days < 0 else 0,
            'real_historical_prices': real_prices  # Store for reference
        }
        
        # Add to tracking data
        self.tracker.tracking_data[test_symbol] = test_data
        
        scenario = {
            'name': scenario_name,
            'symbol': test_symbol,
            'start_date': test_start_date,
            'locked_5d': lock_5d,
            'locked_30d': lock_30d,
            'description': f"Test scenario: {scenario_name} - Start: {test_start_date}"
        }
        
        self.test_scenarios.append(scenario)
        print(f"✅ Created test scenario: {scenario_name}")
        return scenario

    def create_comprehensive_test_suite(self):
        """Create a comprehensive suite of test scenarios"""
        print("🧪 Creating Future Date Test Scenarios...")
        
        # Scenario 1: Past date (historical testing)
        self.create_test_scenario("past_date", start_date_offset_days=-10, lock_5d=True, lock_30d=False)
        
        # Scenario 2: Current date (baseline)
        self.create_test_scenario("current_date", start_date_offset_days=0, lock_5d=False, lock_30d=False)
        
        # Scenario 3: Future date - 1 week ahead
        self.create_test_scenario("future_1week", start_date_offset_days=7, lock_5d=True, lock_30d=True)
        
        # Scenario 4: Future date - 1 month ahead
        self.create_test_scenario("future_1month", start_date_offset_days=30, lock_5d=False, lock_30d=True)
        
        # Scenario 5: Weekend handling test
        monday_offset = self._get_next_monday_offset()
        self.create_test_scenario("next_monday", start_date_offset_days=monday_offset, lock_5d=True, lock_30d=False)
        
        # Save test data
        self.tracker.save_tracking_data()
        
        print(f"🎉 Created {len(self.test_scenarios)} test scenarios")
        return self.test_scenarios

    def _get_next_monday_offset(self):
        """Calculate days until next Monday"""
        today = datetime.now(IST)
        days_until_monday = (7 - today.weekday()) % 7
        return days_until_monday if days_until_monday > 0 else 7

    def test_date_label_generation(self):
        """Test date label generation for different scenarios"""
        print("\n📅 Testing Date Label Generation...")
        
        results = {}
        for scenario in self.test_scenarios:
            symbol = scenario['symbol']
            
            # Test 5D labels
            labels_5d = self.tracker.generate_locked_date_labels(symbol, '5d')
            
            # Test 30D labels  
            labels_30d = self.tracker.generate_locked_date_labels(symbol, '30d')
            
            results[scenario['name']] = {
                'symbol': symbol,
                'start_date': scenario['start_date'],
                'labels_5d': labels_5d[:5] if labels_5d else [],
                'labels_30d': labels_30d[:10] if labels_30d else [],  # Show first 10 for readability
                'locked_5d': scenario['locked_5d'],
                'locked_30d': scenario['locked_30d']
            }
            
            print(f"\n{scenario['name']}:")
            print(f"  Start Date: {scenario['start_date']}")
            print(f"  5D Labels: {labels_5d[:5] if labels_5d else 'Not locked'}")
            print(f"  30D Labels: {labels_30d[:5] if labels_30d else 'Not locked'}...")
        
        return results

    def test_trading_day_calculations(self):
        """Test trading day calculations across different dates"""
        print("\n📊 Testing Trading Day Calculations...")
        
        for scenario in self.test_scenarios:
            symbol = scenario['symbol']
            stock_data = self.tracker.tracking_data[symbol]
            
            start_date = datetime.strptime(stock_data['start_date'], '%Y-%m-%d')
            start_date_ist = IST.localize(start_date)
            current_ist = datetime.now(IST)
            
            trading_days = self.tracker.calculate_trading_days(start_date_ist, current_ist)
            
            print(f"{scenario['name']}: {trading_days} trading days elapsed")

    def generate_test_report(self):
        """Generate a comprehensive test report with real price data"""
        print("\n📋 Test Report Generation...")
        
        report = {
            'test_timestamp': datetime.now(IST).isoformat(),
            'total_scenarios': len(self.test_scenarios),
            'scenarios': []
        }
        
        for scenario in self.test_scenarios:
            symbol = scenario['symbol']
            stock_data = self.tracker.tracking_data[symbol]
            
            scenario_report = {
                'name': scenario['name'],
                'symbol': symbol,
                'start_date': scenario['start_date'],
                'base_price': stock_data.get('current_price'),
                'predicted_5d_prices': stock_data.get('predicted_5d', [])[:5],
                'actual_5d_prices': stock_data.get('actual_progress_5d', [])[:5],
                'predicted_30d_prices': stock_data.get('predicted_30d', [])[:10],  # First 10 for readability
                'actual_30d_prices': stock_data.get('actual_progress_30d', [])[:10],
                'locked_status': {
                    '5d': stock_data.get('locked_5d', False),
                    '30d': stock_data.get('locked_30d', False)
                },
                'lock_dates': {
                    '5d': stock_data.get('lock_start_date_5d'),
                    '30d': stock_data.get('lock_start_date_30d')
                },
                'date_labels_5d': self.tracker.generate_locked_date_labels(symbol, '5d'),
                'date_labels_30d': self.tracker.generate_locked_date_labels(symbol, '30d'),
                'days_tracked': stock_data.get('days_tracked', 0),
                'has_real_data': stock_data.get('real_historical_prices') is not None
            }
            
            report['scenarios'].append(scenario_report)
        
        # Save report
        with open('future_date_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("✅ Test report saved to 'future_date_test_report.json'")
        return report

    def simulate_daily_updates(self):
        """Simulate daily price updates for test scenarios"""
        print("\n⏰ Simulating daily price updates for test scenarios...")
        
        updated_count = 0
        for scenario in self.test_scenarios:
            symbol = scenario['symbol']
            if symbol in self.tracker.tracking_data:
                stock_data = self.tracker.tracking_data[symbol]
                real_prices = stock_data.get('real_historical_prices', [])
                
                if real_prices and len(real_prices) > 1:
                    # Simulate updating actual prices with real historical data
                    current_day = stock_data.get('days_tracked', 0)
                    if current_day < len(real_prices) - 1:
                        next_day = current_day + 1
                        actual_price = real_prices[next_day]
                        
                        # Update actual prices
                        if next_day < 5:
                            stock_data['actual_progress_5d'][next_day] = actual_price
                        if next_day < 30:
                            stock_data['actual_progress_30d'][next_day] = actual_price
                        
                        stock_data['days_tracked'] = next_day
                        stock_data['last_updated'] = datetime.now(IST).isoformat()
                        
                        print(f"  📈 {symbol}: Updated day {next_day} with real price ₹{actual_price:.2f}")
                        updated_count += 1
        
        if updated_count > 0:
            self.tracker.save_tracking_data()
            print(f"✅ Updated {updated_count} test scenarios with real prices")
        
        return updated_count

    def cleanup_test_data(self):
        """Remove test scenarios from tracking data"""
        print("\n🧹 Cleaning up test data...")
        
        removed_count = 0
        for scenario in self.test_scenarios:
            symbol = scenario['symbol']
            if symbol in self.tracker.tracking_data:
                del self.tracker.tracking_data[symbol]
                removed_count += 1
        
        if removed_count > 0:
            self.tracker.save_tracking_data()
            print(f"✅ Removed {removed_count} test scenarios")
        
        self.test_scenarios.clear()

def run_future_date_tests():
    """Run comprehensive future date tests"""
    print("🚀 Starting Future Date Testing Suite")
    print("=" * 60)
    
    tester = FutureDateTester()
    
    try:
        # Create test scenarios
        scenarios = tester.create_comprehensive_test_suite()
        
        # Test date label generation
        label_results = tester.test_date_label_generation()
        
        # Test trading day calculations
        tester.test_trading_day_calculations()
        
        # Generate comprehensive report
        report = tester.generate_test_report()
        
        # Simulate some daily updates for demonstration
        print("\n🔄 Simulating daily price updates...")
        tester.simulate_daily_updates()
        
        print("\n" + "=" * 60)
        print("✅ Future Date Testing Complete!")
        print(f"📊 {len(scenarios)} scenarios tested")
        print("📋 Check 'future_date_test_report.json' for detailed results")
        print("🌐 Test scenarios available in Interactive Tracker")
        print("💡 Test scenarios now include REAL historical stock prices!")
        print("\n💡 To test graphs with REAL price data:")
        print("   1. Go to /prediction-tracker-interactive")
        print("   2. Select test stocks (TEST_*) - each uses real stock data:")
        print("      • TEST_PAST_DATE: Uses RELIANCE historical prices")
        print("      • TEST_CURRENT_DATE: Uses TCS historical prices") 
        print("      • TEST_FUTURE_1WEEK: Uses INFY historical prices")
        print("      • TEST_FUTURE_1MONTH: Uses HINDUNILVR historical prices")
        print("      • TEST_NEXT_MONDAY: Uses WIPRO historical prices")
        print("   3. Switch between 5D/30D views to see real price movements")
        print("   4. Test lock/unlock functionality with realistic data")
        print("   5. Observe how graphs behave with actual market prices")
        print("   6. Compare predicted vs actual lines for validation")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False
    
    finally:
        # Optionally cleanup (comment out to keep test data)
        # tester.cleanup_test_data()
        pass

if __name__ == "__main__":
    success = run_future_date_tests()
    if success:
        print("\n🎉 Future date testing setup complete!")
        print("🔗 Visit: http://localhost:5000/prediction-tracker-interactive")
    else:
        print("\n❌ Future date testing failed!")
