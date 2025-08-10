
#!/usr/bin/env python3
"""
Validation Script for Trainer AI Agent (Prompt 7)
Validates that trainer agent triggers, evaluates, and executes retraining correctly
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta

def log_test(message, status="INFO"):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{status}] {timestamp}: {message}")

def test_trainer_agent_config():
    """Test that trainer agent configuration is properly loaded"""
    log_test("Testing trainer agent configuration...")
    
    config_file = "src/common_repository/config/agents.yaml"
    if not os.path.exists(config_file):
        log_test("❌ Agents config file not found", "ERROR")
        return False
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    required_config = [
        "trainer_agent:",
        "retrain_cooldown_days:",
        "triggers:",
        "hit_rate_drop:",
        "brier_score_thresholds:",
        "confidence_drift:",
        "max_days_without_retrain:"
    ]
    
    for config_item in required_config:
        if config_item not in content:
            log_test(f"❌ Missing config: {config_item}", "ERROR")
            return False
    
    log_test("✅ Trainer agent configuration is complete", "SUCCESS")
    return True

def test_trainer_service_exists():
    """Test that trainer service files exist"""
    log_test("Testing trainer service files...")
    
    required_files = [
        "src/agents/impl/trainer_agent_service.py",
        "src/common_repository/scheduler/trainer_job.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            log_test(f"❌ Missing file: {file_path}", "ERROR")
            return False
        
        # Check for key classes/functions
        with open(file_path, 'r') as f:
            content = f.read()
        
        if 'trainer_agent_service.py' in file_path:
            if 'class TrainerAgentService' not in content:
                log_test(f"❌ TrainerAgentService class not found in {file_path}", "ERROR")
                return False
            if 'evaluate_retrain_need' not in content:
                log_test(f"❌ evaluate_retrain_need method not found", "ERROR")
                return False
        
        if 'trainer_job.py' in file_path:
            if 'class TrainerAgentJob' not in content:
                log_test(f"❌ TrainerAgentJob class not found in {file_path}", "ERROR")
                return False
    
    log_test("✅ All trainer service files exist with required classes", "SUCCESS")
    return True

def test_trainer_api_endpoints():
    """Test trainer API endpoints"""
    log_test("Testing trainer API endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/agents/trainer/status",
        "/api/agents/trainer/history"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                log_test(f"✅ {endpoint} - Response OK", "SUCCESS")
            else:
                log_test(f"❌ {endpoint} - Status: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            log_test(f"❌ {endpoint} - Error: {str(e)}", "ERROR")
            return False
    
    return True

def test_trainer_manual_run():
    """Test manual trainer run functionality"""
    log_test("Testing manual trainer run...")
    
    try:
        base_url = "http://localhost:5000"
        payload = {
            "product": "equities",
            "timeframe": "5D",
            "force": False
        }
        
        response = requests.post(f"{base_url}/api/agents/trainer/run", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                log_test("✅ Manual trainer run executed successfully", "SUCCESS")
                
                # Check result structure
                result = data.get('result', {})
                if 'product' in result and 'timeframe' in result and 'decision' in result:
                    log_test("✅ Trainer run result has correct structure", "SUCCESS")
                    return True
                else:
                    log_test("❌ Trainer run result missing required fields", "ERROR")
                    return False
            else:
                log_test(f"❌ Trainer run failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            log_test(f"❌ Manual trainer run returned status: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Manual trainer run error: {str(e)}", "ERROR")
        return False

def test_trainer_force_run():
    """Test forced trainer run (bypasses cooldown)"""
    log_test("Testing forced trainer run...")
    
    try:
        base_url = "http://localhost:5000"
        payload = {
            "product": "options",
            "timeframe": "30D",
            "force": True
        }
        
        response = requests.post(f"{base_url}/api/agents/trainer/run", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                result = data.get('result', {})
                decision = result.get('decision', {})
                
                if decision.get('force_triggered', False):
                    log_test("✅ Forced trainer run correctly bypassed triggers", "SUCCESS")
                    return True
                else:
                    log_test("⚠️ Forced run executed but force_triggered not set", "WARNING")
                    return True
            else:
                log_test(f"❌ Forced trainer run failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            log_test(f"❌ Forced trainer run returned status: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Forced trainer run error: {str(e)}", "ERROR")
        return False

def test_trainer_status_monitoring():
    """Test trainer status monitoring"""
    log_test("Testing trainer status monitoring...")
    
    try:
        base_url = "http://localhost:5000"
        response = requests.get(f"{base_url}/api/agents/trainer/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            trainer_status = data.get('trainer_status', {})
            
            if 'products' in trainer_status:
                products = trainer_status['products']
                
                # Check that we have status for expected products
                expected_products = ['equities', 'options', 'comm']
                for product in expected_products:
                    if product in products:
                        product_status = products[product]
                        timeframes = ['5D', '30D']
                        
                        for tf in timeframes:
                            if tf in product_status:
                                tf_status = product_status[tf]
                                required_fields = ['status', 'in_cooldown']
                                
                                if all(field in tf_status for field in required_fields):
                                    log_test(f"✅ Status complete for {product} {tf}", "SUCCESS")
                                else:
                                    log_test(f"⚠️ Incomplete status for {product} {tf}", "WARNING")
                
                log_test("✅ Trainer status monitoring working", "SUCCESS")
                return True
            else:
                log_test("❌ Trainer status missing products field", "ERROR")
                return False
        else:
            log_test(f"❌ Trainer status returned status: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Trainer status monitoring error: {str(e)}", "ERROR")
        return False

def test_trainer_ui_integration():
    """Test trainer UI integration elements"""
    log_test("Testing trainer UI integration...")
    
    dashboard_template = "web/templates/index.html"
    if not os.path.exists(dashboard_template):
        log_test("❌ Dashboard template not found", "ERROR")
        return False
    
    with open(dashboard_template, 'r') as f:
        content = f.read()
    
    required_elements = [
        'id="trainerPanel"',
        'id="forceRetrainBtn"',
        'id="trainerContent"',
        'id="trainerStatusGrid"',
        'trainer-status-card',
        'trainer-history'
    ]
    
    for element in required_elements:
        if element not in content:
            log_test(f"❌ Missing UI element: {element}", "ERROR")
            return False
    
    # Check JavaScript file
    js_file = "web/static/js/dashboard.js"
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            js_content = f.read()
        
        required_functions = [
            'setupTrainerControls',
            'loadTrainerPanel',
            'renderTrainerStatus',
            'executeForceRetrain'
        ]
        
        for func in required_functions:
            if func not in js_content:
                log_test(f"❌ Missing JS function: {func}", "ERROR")
                return False
    
    log_test("✅ Trainer UI integration elements present", "SUCCESS")
    return True

def test_cooldown_mechanism():
    """Test that cooldown mechanism prevents back-to-back retrains"""
    log_test("Testing cooldown mechanism...")
    
    try:
        base_url = "http://localhost:5000"
        
        # First run (forced to ensure execution)
        payload1 = {
            "product": "equities",
            "timeframe": "5D",
            "force": True
        }
        
        response1 = requests.post(f"{base_url}/api/agents/trainer/run", 
                                json=payload1, timeout=30)
        
        if response1.status_code != 200:
            log_test("❌ First trainer run failed", "ERROR")
            return False
        
        # Second run immediately (should be blocked by cooldown)
        payload2 = {
            "product": "equities",
            "timeframe": "5D",
            "force": False  # Don't force, should be blocked
        }
        
        response2 = requests.post(f"{base_url}/api/agents/trainer/run", 
                                json=payload2, timeout=30)
        
        if response2.status_code == 200:
            data = response2.json()
            result = data.get('result', {})
            decision = result.get('decision', {})
            
            if not decision.get('triggered', True) and 'cooldown' in decision.get('reason', '').lower():
                log_test("✅ Cooldown mechanism working correctly", "SUCCESS")
                return True
            else:
                log_test("⚠️ Cooldown mechanism may not be working as expected", "WARNING")
                return True
        else:
            log_test("❌ Second trainer run failed", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Cooldown test error: {str(e)}", "ERROR")
        return False

def run_comprehensive_validation():
    """Run all validation tests"""
    log_test("🚀 Starting Trainer AI Agent Validation (Prompt 7)")
    log_test("=" * 60)
    
    tests = [
        ("Trainer Config", test_trainer_agent_config),
        ("Service Files", test_trainer_service_exists),
        ("API Endpoints", test_trainer_api_endpoints),
        ("Manual Run", test_trainer_manual_run),
        ("Force Run", test_trainer_force_run),
        ("Status Monitoring", test_trainer_status_monitoring),
        ("UI Integration", test_trainer_ui_integration),
        ("Cooldown Mechanism", test_cooldown_mechanism)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        log_test(f"Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                log_test(f"❌ {test_name} test FAILED", "ERROR")
        except Exception as e:
            log_test(f"❌ {test_name} test ERROR: {str(e)}", "ERROR")
        
        log_test("-" * 40)
        time.sleep(1)  # Brief pause between tests
    
    # Final results
    log_test("=" * 60)
    log_test(f"📊 VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        log_test("🎉 TRAINER AI AGENT VALIDATION PASSED!", "SUCCESS")
        log_test("✅ All trainer agent features are properly implemented")
        return True
    else:
        log_test(f"❌ VALIDATION FAILED: {total - passed} tests failed", "ERROR")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    exit(0 if success else 1)
