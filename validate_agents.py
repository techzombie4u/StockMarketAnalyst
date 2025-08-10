
#!/usr/bin/env python3
"""
Agent Orchestration Validation Script
Tests agent registry, API endpoints, and UI integration
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

class AgentOrchestrationValidator:
    """Validates agent orchestration implementation"""

    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.test_results = []

    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 Starting Agent Orchestration Validation")
        print("="*60)

        # Run all validation tests
        tests = [
            ("Agent Registry Health", self.test_agent_registry_health),
            ("Agent List API", self.test_agent_list_api),
            ("Agent Execution", self.test_agent_execution),
            ("Agent Enable/Disable", self.test_agent_enable_disable),
            ("Run All Agents", self.test_run_all_agents),
            ("Agent Results Persistence", self.test_agent_results_persistence),
            ("Config Management", self.test_config_management),
            ("UI Integration", self.test_ui_integration)
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

    def test_agent_registry_health(self) -> Dict[str, Any]:
        """Test basic agent registry health"""
        try:
            response = requests.get(f"{self.base_url}/api/agents", timeout=10)

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: {response.text}',
                    'suggestion': 'Check if the agents API blueprint is registered and server is running'
                }

            data = response.json()

            # Check response structure
            if not data.get('success'):
                return {
                    'success': False,
                    'error': 'API returned success=false',
                    'suggestion': 'Check agent registry initialization'
                }

            if 'agents' not in data or 'config' not in data:
                return {
                    'success': False,
                    'error': 'Missing agents or config in response',
                    'suggestion': 'Ensure agents API returns both agents list and config'
                }

            return {
                'success': True,
                'details': f'Agent registry healthy, {len(data["agents"])} agents registered'
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
                'suggestion': 'Check agents API for JSON serialization issues'
            }

    def test_agent_list_api(self) -> Dict[str, Any]:
        """Test agent list contains required agents"""
        try:
            response = requests.get(f"{self.base_url}/api/agents")
            data = response.json()

            agents = data.get('agents', [])
            agent_ids = [agent.get('id') for agent in agents]

            required_agents = ['new_ai_analyzer', 'sentiment_analyzer']
            missing_agents = [agent_id for agent_id in required_agents if agent_id not in agent_ids]

            if missing_agents:
                return {
                    'success': False,
                    'error': f'Missing required agents: {missing_agents}',
                    'suggestion': 'Check that both new_ai_agent.py and sentiment_agent.py are properly registered'
                }

            # Check agent structure
            for agent in agents:
                required_fields = ['id', 'name', 'enabled', 'description']
                missing_fields = [field for field in required_fields if field not in agent]

                if missing_fields:
                    return {
                        'success': False,
                        'error': f'Agent {agent.get("id")} missing fields: {missing_fields}',
                        'suggestion': 'Ensure agent registration includes all required fields'
                    }

            return {
                'success': True,
                'details': f'All required agents present: {required_agents}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_agent_execution(self) -> Dict[str, Any]:
        """Test individual agent execution"""
        try:
            # Test new AI analyzer
            response1 = requests.post(f"{self.base_url}/api/agents/new_ai_analyzer/run")
            if response1.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to run new_ai_analyzer: HTTP {response1.status_code}'
                }

            data1 = response1.json()
            if not data1.get('success'):
                return {
                    'success': False,
                    'error': f'new_ai_analyzer execution failed: {data1.get("error")}'
                }

            result1 = data1.get('result', {})
            required_fields1 = ['status', 'analysis', 'verdict', 'confidence']
            missing_fields1 = [field for field in required_fields1 if field not in result1]

            if missing_fields1:
                return {
                    'success': False,
                    'error': f'new_ai_analyzer result missing fields: {missing_fields1}'
                }

            # Test sentiment analyzer
            response2 = requests.post(f"{self.base_url}/api/agents/sentiment_analyzer/run")
            if response2.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to run sentiment_analyzer: HTTP {response2.status_code}'
                }

            data2 = response2.json()
            if not data2.get('success'):
                return {
                    'success': False,
                    'error': f'sentiment_analyzer execution failed: {data2.get("error")}'
                }

            result2 = data2.get('result', {})
            required_fields2 = ['status', 'sentiment_score', 'summary', 'verdict', 'confidence']
            missing_fields2 = [field for field in required_fields2 if field not in result2]

            if missing_fields2:
                return {
                    'success': False,
                    'error': f'sentiment_analyzer result missing fields: {missing_fields2}'
                }

            return {
                'success': True,
                'details': f'Both agents executed successfully with complete results'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_agent_enable_disable(self) -> Dict[str, Any]:
        """Test agent enable/disable functionality"""
        try:
            agent_id = 'new_ai_analyzer'

            # Disable agent
            response1 = requests.post(f"{self.base_url}/api/agents/{agent_id}/disable")
            if response1.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to disable agent: HTTP {response1.status_code}'
                }

            # Check agent list shows disabled
            response2 = requests.get(f"{self.base_url}/api/agents")
            data2 = response2.json()
            agents = data2.get('agents', [])
            
            target_agent = next((a for a in agents if a['id'] == agent_id), None)
            if not target_agent:
                return {
                    'success': False,
                    'error': f'Agent {agent_id} not found in list'
                }

            if target_agent.get('enabled', True):
                return {
                    'success': False,
                    'error': f'Agent {agent_id} still shows as enabled after disable'
                }

            # Re-enable agent
            response3 = requests.post(f"{self.base_url}/api/agents/{agent_id}/enable")
            if response3.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to re-enable agent: HTTP {response3.status_code}'
                }

            # Check agent list shows enabled
            response4 = requests.get(f"{self.base_url}/api/agents")
            data4 = response4.json()
            agents4 = data4.get('agents', [])
            
            target_agent4 = next((a for a in agents4 if a['id'] == agent_id), None)
            if not target_agent4 or not target_agent4.get('enabled', False):
                return {
                    'success': False,
                    'error': f'Agent {agent_id} not properly re-enabled'
                }

            return {
                'success': True,
                'details': f'Agent enable/disable functionality working correctly'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_run_all_agents(self) -> Dict[str, Any]:
        """Test running all agents at once"""
        try:
            response = requests.post(f"{self.base_url}/api/agents/run_all")
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to run all agents: HTTP {response.status_code}'
                }

            data = response.json()
            if not data.get('success'):
                return {
                    'success': False,
                    'error': f'Run all agents failed: {data.get("error")}'
                }

            results = data.get('results', {})
            expected_agents = ['new_ai_analyzer', 'sentiment_analyzer']
            
            for agent_id in expected_agents:
                if agent_id not in results:
                    return {
                        'success': False,
                        'error': f'Agent {agent_id} not in run_all results'
                    }

                agent_result = results[agent_id]
                if agent_result.get('status') != 'ok':
                    return {
                        'success': False,
                        'error': f'Agent {agent_id} failed in run_all: {agent_result}'
                    }

            return {
                'success': True,
                'details': f'All {len(results)} agents executed successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_agent_results_persistence(self) -> Dict[str, Any]:
        """Test that agent results are persisted"""
        try:
            agent_id = 'sentiment_analyzer'

            # Run agent
            response1 = requests.post(f"{self.base_url}/api/agents/{agent_id}/run")
            if response1.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to run agent for persistence test'
                }

            # Get agent result
            response2 = requests.get(f"{self.base_url}/api/agents/{agent_id}/result")
            if response2.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to get agent result: HTTP {response2.status_code}'
                }

            data2 = response2.json()
            if not data2.get('success'):
                return {
                    'success': False,
                    'error': f'Get agent result failed: {data2.get("error")}'
                }

            result = data2.get('result', {})
            if not result or result.get('status') != 'ok':
                return {
                    'success': False,
                    'error': f'Agent result not properly persisted or invalid'
                }

            return {
                'success': True,
                'details': f'Agent results properly persisted and retrievable'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_config_management(self) -> Dict[str, Any]:
        """Test configuration management"""
        try:
            # Get current config
            response1 = requests.get(f"{self.base_url}/api/agents/config")
            if response1.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to get config: HTTP {response1.status_code}'
                }

            data1 = response1.json()
            if not data1.get('success'):
                return {
                    'success': False,
                    'error': f'Get config failed: {data1.get("error")}'
                }

            # Check show_ai_verdict_columns exists
            config = data1.get('config', {})
            if 'show_ai_verdict_columns' not in config:
                return {
                    'success': False,
                    'error': 'show_ai_verdict_columns not in config'
                }

            # Toggle the setting
            original_value = config['show_ai_verdict_columns']
            new_value = not original_value

            response2 = requests.post(
                f"{self.base_url}/api/agents/config/show_ai_verdict_columns",
                json={"value": new_value}
            )
            if response2.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to set config: HTTP {response2.status_code}'
                }

            # Verify change
            response3 = requests.get(f"{self.base_url}/api/agents/config")
            data3 = response3.json()
            updated_config = data3.get('config', {})
            
            if updated_config.get('show_ai_verdict_columns') != new_value:
                return {
                    'success': False,
                    'error': 'Config change not persisted'
                }

            # Restore original value
            requests.post(
                f"{self.base_url}/api/agents/config/show_ai_verdict_columns",
                json={"value": original_value}
            )

            return {
                'success': True,
                'details': f'Config management working correctly'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def test_ui_integration(self) -> Dict[str, Any]:
        """Test UI integration for AI verdict columns"""
        try:
            # Test that fusion dashboard page loads
            response = requests.get(f"{self.base_url}/fusion-dashboard")

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Fusion dashboard page failed to load: {response.status_code}',
                    'suggestion': 'Check if /fusion-dashboard route is working'
                }

            html_content = response.text

            # Check for AI verdict column elements
            required_elements = [
                'ai-verdict-column',
                'ai-verdict-cell'
            ]

            missing_elements = [elem for elem in required_elements if elem not in html_content]
            if missing_elements:
                return {
                    'success': False,
                    'error': f'Missing AI verdict UI elements: {missing_elements}',
                    'suggestion': 'Check fusion_dashboard.html template for AI verdict column integration'
                }

            return {
                'success': True,
                'details': 'UI integration elements present in dashboard'
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
            print("\n🎉 All validation checks passed! Agent Orchestration is ready.")
        else:
            print(f"\n⚠️  Fix {total - passed} issues before deploying Agent Orchestration.")

    def all_tests_passed(self) -> bool:
        """Check if all tests passed"""
        return all(result['success'] for result in self.test_results)

def main():
    """Run validation"""
    validator = AgentOrchestrationValidator()

    try:
        success = validator.run_validation()

        if success:
            print("\n" + "="*60)
            print("🚀 VALIDATION COMPLETE - AGENT ORCHESTRATION READY!")
            print("="*60)
            print("✅ All systems operational")
            print("🌐 Agents API: http://localhost:5000/api/agents")
            print("📊 Dashboard: http://localhost:5000/fusion-dashboard")

            # Try to get agent stats
            try:
                import requests
                response = requests.get("http://localhost:5000/api/agents")
                if response.status_code == 200:
                    data = response.json()
                    agents = data.get('agents', [])
                    enabled_count = sum(1 for a in agents if a.get('enabled', False))
                    print(f"\n📈 Current Statistics:")
                    print(f"   • Total Agents: {len(agents)}")
                    print(f"   • Enabled Agents: {enabled_count}")
                    print(f"   • AI Verdict Columns: {'Enabled' if data.get('config', {}).get('show_ai_verdict_columns') else 'Disabled'}")
            except:
                pass

            return True
        else:
            print("\n❌ VALIDATION FAILED")
            print("Fix the issues above before proceeding to Prompt 11.")
            return False

    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    main()
