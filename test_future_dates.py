
#!/usr/bin/env python3
"""
Future Date Testing for Interactive Prediction Tracker
Test how graphs behave with different date scenarios
"""

import json
import os
from datetime import datetime, timedelta
import pytz
from interactive_tracker_manager import InteractiveTrackerManager

IST = pytz.timezone('Asia/Kolkata')

class FutureDateTester:
    def __init__(self):
        self.tracker = InteractiveTrackerManager()
        self.test_scenarios = []

    def create_test_scenario(self, scenario_name, start_date_offset_days=0, lock_5d=False, lock_30d=False):
        """Create a test scenario with specific date settings"""
        # Calculate test start date
        base_date = datetime.now(IST) + timedelta(days=start_date_offset_days)
        test_start_date = base_date.strftime('%Y-%m-%d')
        
        # Create test stock data
        test_symbol = f"TEST_{scenario_name.upper()}"
        test_data = {
            'symbol': test_symbol,
            'start_date': test_start_date,
            'current_price': 100.0,
            'confidence': 85,
            'score': 75,
            'predicted_5d': [100, 102, 104, 106, 108],
            'predicted_30d': [100 + i for i in range(30)],
            'actual_progress_5d': [100, None, None, None, None],
            'actual_progress_30d': [100] + [None] * 29,
            'updated_prediction_5d': [None] * 5,
            'updated_prediction_30d': [None] * 30,
            'locked_5d': lock_5d,
            'locked_30d': lock_30d,
            'lock_start_date_5d': test_start_date if lock_5d else None,
            'lock_start_date_30d': test_start_date if lock_30d else None,
            'persistent_lock_5d': lock_5d,
            'persistent_lock_30d': lock_30d,
            'last_updated': datetime.now(IST).isoformat(),
            'days_tracked': 0
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
        """Generate a comprehensive test report"""
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
                'locked_status': {
                    '5d': stock_data.get('locked_5d', False),
                    '30d': stock_data.get('locked_30d', False)
                },
                'lock_dates': {
                    '5d': stock_data.get('lock_start_date_5d'),
                    '30d': stock_data.get('lock_start_date_30d')
                },
                'date_labels_5d': self.tracker.generate_locked_date_labels(symbol, '5d'),
                'date_labels_30d': self.tracker.generate_locked_date_labels(symbol, '30d')
            }
            
            report['scenarios'].append(scenario_report)
        
        # Save report
        with open('future_date_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("✅ Test report saved to 'future_date_test_report.json'")
        return report

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
        
        print("\n" + "=" * 60)
        print("✅ Future Date Testing Complete!")
        print(f"📊 {len(scenarios)} scenarios tested")
        print("📋 Check 'future_date_test_report.json' for detailed results")
        print("🌐 Test scenarios available in Interactive Tracker")
        print("\n💡 To test graphs:")
        print("   1. Go to /prediction-tracker-interactive")
        print("   2. Select test stocks (TEST_*)")
        print("   3. Switch between 5D/30D views")
        print("   4. Test lock/unlock functionality")
        print("   5. Observe date behavior differences")
        
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
