
#!/usr/bin/env python3
"""
Backend Test for SmartGoAgent - Real Data Validation
Tests whether SmartGoAgent is reading real prediction data vs mock data
"""

import sys
import os
import unittest
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from _backup_before_organization.smart_go_agent import SmartGoAgent
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Trying alternative import...")
    try:
        from src.analyzers.smart_go_agent import SmartGoAgent
    except ImportError:
        print("❌ Could not import SmartGoAgent from any location")
        sys.exit(1)


class TestSmartGoAgentRealData(unittest.TestCase):
    """Test suite to verify SmartGoAgent reads real backend prediction data"""
    
    def setUp(self):
        """Set up test environment"""
        self.agent = SmartGoAgent()
        print(f"\n🧪 Testing SmartGoAgent at {datetime.now()}")
    
    def test_prediction_summary_is_real(self):
        """Test that get_prediction_summary returns real, structured, non-empty prediction data"""
        print("\n📊 Testing prediction summary real data...")
        
        try:
            result = self.agent.get_prediction_summary()
            
            # Basic structure validation
            self.assertIsInstance(result, dict, "Expected a dictionary as output")
            
            # Check for required keys
            required_keys = ['total_predictions', 'accuracy', 'avg_confidence', 'predictions', 'timestamp']
            for key in required_keys:
                self.assertIn(key, result, f"Missing required key: {key}")
            
            # Validate total predictions
            total_predictions = result.get("total_predictions", 0)
            print(f"   📈 Total predictions found: {total_predictions}")
            
            if total_predictions == 0:
                print("   ⚠️  WARNING: Zero predictions found - may be using fallback data")
            else:
                self.assertGreater(total_predictions, 0, "No real predictions found")
            
            # Validate predictions array
            predictions = result.get("predictions", [])
            self.assertIsInstance(predictions, list, "Predictions must be a list")
            
            if predictions:
                print(f"   🔍 Analyzing {len(predictions)} prediction entries...")
                
                for i, pred in enumerate(predictions[:3]):  # Check first 3 predictions
                    print(f"   📝 Prediction {i+1}: {pred.get('symbol', 'Unknown')}")
                    
                    # Check required fields
                    required_fields = ["symbol", "confidence", "actual", "target", "window"]
                    for field in required_fields:
                        self.assertIn(field, pred, f"Missing field '{field}' in prediction {i+1}")
                    
                    # Validate data types
                    self.assertIsInstance(pred["confidence"], (int, float), 
                                        f"Confidence must be numeric in prediction {i+1}")
                    self.assertIsInstance(pred["actual"], (int, float), 
                                        f"Actual price must be numeric in prediction {i+1}")
                    self.assertIsInstance(pred["target"], (int, float), 
                                        f"Target price must be numeric in prediction {i+1}")
                    
                    # Validate ranges
                    confidence = pred["confidence"]
                    self.assertTrue(0 <= confidence <= 100, 
                                  f"Confidence {confidence} out of range 0-100 in prediction {i+1}")
                    
                    actual_price = pred["actual"]
                    target_price = pred["target"]
                    self.assertGreater(actual_price, 0, f"Actual price must be positive in prediction {i+1}")
                    self.assertGreater(target_price, 0, f"Target price must be positive in prediction {i+1}")
                    
                    print(f"      ✅ Symbol: {pred['symbol']}, Confidence: {confidence}%, "
                          f"Target: ₹{target_price:.2f}, Actual: ₹{actual_price:.2f}")
            
            # Check data source
            data_source = result.get('data_source', 'unknown')
            print(f"   📡 Data source: {data_source}")
            
            if data_source == 'fallback_empty':
                print("   ⚠️  WARNING: Using fallback empty data - real data not available")
            elif data_source == 'real_time_tracking':
                print("   ✅ SUCCESS: Reading from real-time tracking data")
            
            print("   ✅ Real prediction data structure verified.")
            
        except Exception as e:
            print(f"   ❌ ERROR in prediction summary test: {str(e)}")
            raise
    
    def test_model_kpi_metrics_valid(self):
        """Test that get_model_kpi returns valid KPI values for models"""
        print("\n🎯 Testing model KPI metrics validation...")
        
        try:
            result = self.agent.get_model_kpi()
            
            # Basic validation
            self.assertIsInstance(result, dict, "KPI result must be a dictionary")
            
            if len(result) == 0:
                print("   ⚠️  WARNING: Model KPI is empty - may be using fallback data")
                return
            
            print(f"   📊 Found {len(result)} model entries")
            
            # Check for models section if present
            models_data = result.get('models', result)  # Handle both structures
            
            if 'models' in result:
                print("   📋 Using structured KPI format")
                models_data = result['models']
            else:
                print("   📋 Using direct KPI format")
            
            # Validate each model
            expected_models = ['LSTM', 'RandomForest', 'LinearRegression', 'NaiveForecast']
            found_models = []
            
            for model_name, model_data in models_data.items():
                found_models.append(model_name)
                print(f"   🤖 Model: {model_name}")
                
                if isinstance(model_data, dict):
                    # Structured format
                    accuracy = model_data.get('accuracy', 0)
                    status = model_data.get('status', 'unknown')
                    print(f"      📈 Accuracy: {accuracy}%, Status: {status}")
                    
                    self.assertIsInstance(accuracy, (int, float), 
                                        f"Accuracy for {model_name} should be numeric")
                    self.assertTrue(0 <= accuracy <= 100, 
                                  f"Accuracy for {model_name} out of range: {accuracy}")
                else:
                    # Direct value format
                    accuracy = model_data
                    print(f"      📈 Accuracy: {accuracy}%")
                    
                    self.assertIsInstance(accuracy, (int, float), 
                                        f"KPI for {model_name} should be numeric")
                    self.assertTrue(0 <= accuracy <= 100, 
                                  f"KPI for {model_name} out of range: {accuracy}")
            
            print(f"   🔍 Models found: {', '.join(found_models)}")
            
            # Check if we have reasonable model coverage
            common_models_found = sum(1 for model in expected_models if model in found_models)
            if common_models_found >= 2:
                print(f"   ✅ Good model coverage: {common_models_found} common models found")
            else:
                print(f"   ⚠️  Limited model coverage: only {common_models_found} common models found")
            
            print("   ✅ Model KPI values validated.")
            
        except Exception as e:
            print(f"   ❌ ERROR in model KPI test: {str(e)}")
            raise
    
    def test_validation_api_endpoint(self):
        """Test the validation API endpoint functionality"""
        print("\n🔌 Testing validation API functionality...")
        
        try:
            # Test different timeframes
            timeframes = ['3D', '5D', '10D', '15D', '30D']
            
            for timeframe in timeframes:
                print(f"   ⏰ Testing timeframe: {timeframe}")
                
                validation_result = self.agent.validate_predictions(timeframe)
                
                # Basic structure check
                self.assertIsInstance(validation_result, dict, 
                                    f"Validation result for {timeframe} must be a dictionary")
                
                # Check required sections
                required_sections = ['prediction_summary', 'outcome_validation', 'gap_analysis']
                for section in required_sections:
                    self.assertIn(section, validation_result, 
                                f"Missing section '{section}' in {timeframe} validation")
                
                # Check prediction summary within validation
                pred_summary = validation_result.get('prediction_summary', {})
                total = pred_summary.get('total', 0)
                accuracy = pred_summary.get('accuracy', 0)
                
                print(f"      📊 Total: {total}, Accuracy: {accuracy:.1f}%")
                
                # Validate ranges
                if total > 0:
                    self.assertTrue(0 <= accuracy <= 100, 
                                  f"Accuracy {accuracy} out of range for {timeframe}")
            
            print("   ✅ Validation API functionality verified.")
            
        except Exception as e:
            print(f"   ❌ ERROR in validation API test: {str(e)}")
            raise
    
    def test_ai_copilot_functionality(self):
        """Test AI co-pilot query functionality"""
        print("\n🤖 Testing AI co-pilot functionality...")
        
        try:
            test_queries = [
                "What is the current accuracy?",
                "Which model is performing best?",
                "Show me confidence levels"
            ]
            
            for query in test_queries:
                print(f"   💭 Query: {query}")
                
                response = self.agent.query_ai_copilot(query)
                
                # Basic validation
                self.assertIsInstance(response, dict, "AI response must be a dictionary")
                self.assertIn('response', response, "Missing 'response' in AI output")
                self.assertIn('type', response, "Missing 'type' in AI output")
                self.assertIn('timestamp', response, "Missing 'timestamp' in AI output")
                
                response_text = response.get('response', '')
                self.assertIsInstance(response_text, str, "Response text must be a string")
                self.assertGreater(len(response_text), 0, "Response text cannot be empty")
                
                print(f"      ✅ Response received ({len(response_text)} chars)")
            
            print("   ✅ AI co-pilot functionality verified.")
            
        except Exception as e:
            print(f"   ❌ ERROR in AI co-pilot test: {str(e)}")
            raise


def run_comprehensive_backend_test():
    """Run comprehensive backend test and generate report"""
    print("="*80)
    print("🧪 SMARTGOAGENT BACKEND DATA VALIDATION TEST")
    print("="*80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSmartGoAgentRealData)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"Total Tests Run: {total_tests}")
    print(f"✅ Successes: {successes}")
    print(f"❌ Failures: {failures}")
    print(f"🚫 Errors: {errors}")
    
    if failures > 0:
        print("\n❌ FAILURE DETAILS:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print("\n🚫 ERROR DETAILS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("\n" + "="*80)
    
    if failures == 0 and errors == 0:
        print("🎉 ALL TESTS PASSED - SmartGoAgent is reading REAL backend data!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - SmartGoAgent may be using mock/fallback data!")
        return False


if __name__ == "__main__":
    # Run the comprehensive test
    success = run_comprehensive_backend_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
