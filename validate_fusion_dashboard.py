
#!/usr/bin/env python3
"""
Fusion Dashboard Validation Script
Validates all components of the KPI + AI Verdict Fusion Dashboard
"""

import time
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FusionDashboardValidator:
    """Validates fusion dashboard implementation"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []
        
    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting Fusion Dashboard Validation")
        print("="*60)
        
        # Run all validation tests
        tests = [
            ("Endpoint Health Check", self.test_endpoint_health),
            ("Timeframes Coverage", self.test_timeframes_coverage),
            ("Verdict Normalization", self.test_verdict_normalization),
            ("Pinned Rollup", self.test_pinned_rollup),
            ("Caching Behavior", self.test_caching),
            ("Performance Check", self.test_performance),
            ("Frontend Smoke Test", self.test_frontend_smoke)
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 Running: {test_name}")
                result = test_func()
                if result['success']:
                    print(f"✅ {test_name}: PASSED")
                    if result.get('details'):
                        print(f"   {result['details']}")
                else:
                    print(f"❌ {test_name}: FAILED")
                    print(f"   Error: {result['error']}")
                    if result.get('suggestion'):
                        print(f"   💡 Suggestion: {result['suggestion']}")
                
                self.test_results.append({
                    'name': test_name,
                    'success': result['success'],
                    'error': result.get('error'),
                    'details': result.get('details')
                })
                
            except Exception as e:
                print(f"❌ {test_name}: EXCEPTION")
                print(f"   Error: {str(e)}")
                self.test_results.append({
                    'name': test_name,
                    'success': False,
                    'error': str(e)
                })
        
        self.print_summary()
        return self.all_tests_passed()
    
    def test_endpoint_health(self) -> Dict[str, Any]:
        """Test basic endpoint health and response structure"""
        try:
            response = requests.get(f"{self.base_url}/api/fusion/dashboard", timeout=10)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'suggestion': 'Check if the fusion API blueprint is registered and server is running'
                }
            
            data = response.json()
            
            # Check required keys
            required_keys = [
                'last_updated_utc', 'market_session', 'timeframes',
                'ai_verdict_summary', 'product_breakdown', 'pinned_summary',
                'top_signals', 'alerts'
            ]
            
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return {
                    'success': False,
                    'error': f'Missing required keys: {missing_keys}',
                    'suggestion': 'Ensure fusion_schema.py FusionDashboardPayload includes all required fields'
                }
            
            return {
                'success': True,
                'details': f'Endpoint healthy, {len(data.get("top_signals", []))} signals returned'
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'suggestion': 'Check if server is running on port 5000'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON response: {str(e)}',
                'suggestion': 'Check fusion API for JSON serialization issues'
            }
    
    def test_timeframes_coverage(self) -> Dict[str, Any]:
        """Test that timeframes include All and required buckets"""
        try:
            response = requests.get(f"{self.base_url}/api/fusion/dashboard")
            data = response.json()
            
            timeframes = data.get('timeframes', [])
            timeframe_names = [tf.get('timeframe') for tf in timeframes]
            
            required_timeframes = ['All', '3D', '5D', '10D', '15D', '30D']
            missing_timeframes = [tf for tf in required_timeframes if tf not in timeframe_names]
            
            if missing_timeframes:
                return {
                    'success': False,
                    'error': f'Missing timeframes: {missing_timeframes}',
                    'suggestion': 'Update kpi_mapper.py to include all required timeframes'
                }
            
            # Check KPI structure
            for tf in timeframes:
                required_kpi_groups = ['prediction_kpis', 'financial_kpis', 'risk_kpis']
                missing_groups = [group for group in required_kpi_groups if group not in tf]
                
                if missing_groups:
                    return {
                        'success': False,
                        'error': f'Timeframe {tf.get("timeframe")} missing KPI groups: {missing_groups}',
                        'suggestion': 'Ensure kpi_mapper creates all KPI groups for each timeframe'
                    }
            
            return {
                'success': True,
                'details': f'All {len(required_timeframes)} timeframes present with KPI structure'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_verdict_normalization(self) -> Dict[str, Any]:
        """Test AI verdict normalization"""
        try:
            response = requests.get(f"{self.base_url}/api/fusion/dashboard")
            data = response.json()
            
            top_signals = data.get('top_signals', [])
            valid_verdicts = {'STRONG_BUY', 'BUY', 'HOLD', 'CAUTIOUS', 'AVOID'}
            
            invalid_verdicts = []
            for signal in top_signals:
                verdict = signal.get('ai_verdict_normalized')
                if verdict not in valid_verdicts:
                    invalid_verdicts.append(verdict)
            
            if invalid_verdicts:
                return {
                    'success': False,
                    'error': f'Invalid normalized verdicts found: {set(invalid_verdicts)}',
                    'suggestion': 'Check verdict_normalizer.py and ensure all verdicts map to valid values'
                }
            
            return {
                'success': True,
                'details': f'All {len(top_signals)} signals have valid normalized verdicts'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_pinned_rollup(self) -> Dict[str, Any]:
        """Test pinned summary calculations"""
        try:
            response = requests.get(f"{self.base_url}/api/fusion/dashboard")
            data = response.json()
            
            pinned_summary = data.get('pinned_summary', {})
            
            # Check structure
            required_fields = ['total', 'met', 'not_met', 'in_progress']
            missing_fields = [field for field in required_fields if field not in pinned_summary]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Pinned summary missing fields: {missing_fields}',
                    'suggestion': 'Check pinned_rollup.py PinnedSummary structure'
                }
            
            # Check math
            total = pinned_summary['total']
            sum_outcomes = pinned_summary['met'] + pinned_summary['not_met'] + pinned_summary['in_progress']
            
            # Note: sum_outcomes might be less than total if some pinned stocks have no predictions
            if sum_outcomes > total:
                return {
                    'success': False,
                    'error': f'Pinned summary math error: sum({sum_outcomes}) > total({total})',
                    'suggestion': 'Check pinned_rollup.py calculation logic'
                }
            
            return {
                'success': True,
                'details': f'Pinned summary: {total} total, math checks out'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_caching(self) -> Dict[str, Any]:
        """Test caching behavior"""
        try:
            # First request
            start_time = time.time()
            response1 = requests.get(f"{self.base_url}/api/fusion/dashboard")
            first_duration = time.time() - start_time
            
            if response1.status_code != 200:
                return {'success': False, 'error': f'First request failed: {response1.status_code}'}
            
            data1 = response1.json()
            first_updated = data1.get('last_updated_utc')
            
            # Second request (should hit cache)
            time.sleep(0.1)  # Brief pause
            start_time = time.time()
            response2 = requests.get(f"{self.base_url}/api/fusion/dashboard")
            second_duration = time.time() - start_time
            
            if response2.status_code != 200:
                return {'success': False, 'error': f'Second request failed: {response2.status_code}'}
            
            data2 = response2.json()
            second_updated = data2.get('last_updated_utc')
            
            # Should be same timestamp if cached
            if first_updated != second_updated:
                return {
                    'success': False,
                    'error': 'Cache not working - timestamps differ between requests',
                    'suggestion': 'Check _is_cache_valid() function in fusion API'
                }
            
            # Test force refresh
            response3 = requests.get(f"{self.base_url}/api/fusion/dashboard?forceRefresh=true")
            if response3.status_code == 200:
                data3 = response3.json()
                third_updated = data3.get('last_updated_utc')
                
                if third_updated == first_updated:
                    return {
                        'success': False,
                        'error': 'Force refresh not working - timestamp unchanged',
                        'suggestion': 'Check forceRefresh parameter handling in fusion API'
                    }
            
            return {
                'success': True,
                'details': f'Caching works, force refresh works'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_performance(self) -> Dict[str, Any]:
        """Test performance requirements"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/fusion/dashboard")
            total_duration = (time.time() - start_time) * 1000  # Convert to ms
            
            if response.status_code != 200:
                return {'success': False, 'error': f'Request failed: {response.status_code}'}
            
            data = response.json()
            generation_time = data.get('generation_time_ms', 0)
            
            # Check against target (150ms for dev environment)
            target_ms = 150
            if generation_time > target_ms:
                return {
                    'success': False,
                    'error': f'Generation time {generation_time:.1f}ms exceeds target {target_ms}ms',
                    'suggestion': 'Optimize data loading in fusion API or increase cache TTL'
                }
            
            return {
                'success': True,
                'details': f'Generation time: {generation_time:.1f}ms (target: {target_ms}ms)'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_frontend_smoke(self) -> Dict[str, Any]:
        """Basic frontend smoke test"""
        try:
            # Test that the HTML page loads
            response = requests.get(f"{self.base_url}/fusion-dashboard")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Fusion dashboard page failed to load: {response.status_code}',
                    'suggestion': 'Check if /fusion-dashboard route is registered in app.py'
                }
            
            html_content = response.text
            
            # Check for key elements
            required_elements = [
                'Fusion Dashboard',  # Page title
                'topSignalsTable',   # Main table
                'timeframeFilter',   # Filter controls
                'refreshBtn'         # Refresh button
            ]
            
            missing_elements = [elem for elem in required_elements if elem not in html_content]
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing HTML elements: {missing_elements}',
                    'suggestion': 'Check fusion_dashboard.html template'
                }
            
            return {
                'success': True,
                'details': 'HTML page loads with required elements'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}/{total} tests")
        
        if passed < total:
            print(f"❌ Failed: {total - passed} tests")
            print("\n🔧 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['name']}: {result['error']}")
        
        print(f"\n🎯 Overall Result: {'✅ PASS' if passed == total else '❌ FAIL'}")
        
        if passed == total:
            print("\n🎉 All validation checks passed! Fusion Dashboard is ready.")
        else:
            print(f"\n⚠️  Fix {total - passed} issues before deploying Fusion Dashboard.")
    
    def all_tests_passed(self) -> bool:
        """Check if all tests passed"""
        return all(result['success'] for result in self.test_results)

def main():
    """Run validation"""
    validator = FusionDashboardValidator()
    
    try:
        success = validator.run_validation()
        
        if success:
            print("\n" + "="*60)
            print("🚀 VALIDATION COMPLETE - FUSION DASHBOARD READY!")
            print("="*60)
            print("✅ All systems operational")
            print("🌐 Access at: http://localhost:5000/fusion-dashboard")
            print("📊 API endpoint: http://localhost:5000/api/fusion/dashboard")
            
            # Try to get summary stats
            try:
                import requests
                response = requests.get("http://localhost:5000/api/fusion/dashboard")
                if response.status_code == 200:
                    data = response.json()
                    print(f"\n📈 Current Statistics:")
                    print(f"   • Top Signals: {len(data.get('top_signals', []))}")
                    print(f"   • Timeframes: {len(data.get('timeframes', []))}")
                    print(f"   • Alerts: {len(data.get('alerts', []))}")
                    print(f"   • Generation Time: {data.get('generation_time_ms', 0):.1f}ms")
            except:
                pass
            
            return True
        else:
            print("\n❌ VALIDATION FAILED")
            print("Fix the issues above before proceeding to Prompt 9.")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    main()
