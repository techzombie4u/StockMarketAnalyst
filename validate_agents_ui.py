
#!/usr/bin/env python3
"""
Validation Script for AI Agents UI & Verdict Feeds (Prompt 6B)
Validates that AI verdicts are properly integrated into all prediction tables
"""

import requests
import time
import json
import os
from datetime import datetime

def log_test(message, status="INFO"):
    """Log test results with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{status}] {timestamp}: {message}")

def test_api_endpoints():
    """Test that required AI agent API endpoints are working"""
    log_test("Testing AI Agent API endpoints...")
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/api/agents/list",
        "/api/agents/latest?agent=equity&scope=product=equity&timeframe=5D&symbol=RELIANCE", 
        "/api/agents/history?agent=equity&limit=3"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                log_test(f"✅ {endpoint} - Response OK", "SUCCESS")
            else:
                log_test(f"❌ {endpoint} - Status: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            log_test(f"❌ {endpoint} - Error: {str(e)}", "ERROR")
            return False
    
    return True

def test_verdict_columns_exist():
    """Test that AI Verdict columns exist in HTML templates"""
    log_test("Testing AI Verdict column presence in templates...")
    
    templates = [
        "web/templates/index.html",
        "web/templates/options_strategy.html", 
        "web/templates/analysis.html",
        "web/templates/kpi_dashboard.html"
    ]
    
    for template in templates:
        if not os.path.exists(template):
            log_test(f"❌ Template not found: {template}", "ERROR")
            return False
            
        with open(template, 'r') as f:
            content = f.read()
            
        if "AI Verdict" not in content:
            log_test(f"❌ AI Verdict column missing in {template}", "ERROR")
            return False
        
        if "verdict-cell" not in content:
            log_test(f"❌ Verdict cell class missing in {template}", "ERROR")
            return False
            
        log_test(f"✅ AI Verdict column found in {template}", "SUCCESS")
    
    return True

def test_verdict_styling():
    """Test that verdict styling classes are present"""
    log_test("Testing verdict styling classes...")
    
    dashboard_template = "web/templates/index.html"
    if not os.path.exists(dashboard_template):
        log_test(f"❌ Dashboard template not found", "ERROR")
        return False
        
    with open(dashboard_template, 'r') as f:
        content = f.read()
    
    required_classes = [
        "verdict-positive",
        "verdict-cautious", 
        "verdict-negative",
        "verdict-unknown",
        "goahead-panel",
        "modal",
        "verdict-drawer"
    ]
    
    for css_class in required_classes:
        if css_class not in content:
            log_test(f"❌ CSS class missing: {css_class}", "ERROR")
            return False
    
    log_test("✅ All verdict styling classes found", "SUCCESS")
    return True

def test_javascript_functions():
    """Test that required JavaScript functions exist"""
    log_test("Testing JavaScript verdict functions...")
    
    js_file = "web/static/js/dashboard.js"
    if not os.path.exists(js_file):
        log_test(f"❌ Dashboard JS not found", "ERROR")
        return False
        
    with open(js_file, 'r') as f:
        content = f.read()
    
    required_functions = [
        "loadVerdicts",
        "fetchVerdict", 
        "updateVerdictCell",
        "loadGoAheadPanel",
        "openVerdictDrawer",
        "runVerdicts"
    ]
    
    for func in required_functions:
        if f"function {func}" not in content and f"{func} =" not in content:
            log_test(f"❌ JavaScript function missing: {func}", "ERROR")
            return False
    
    log_test("✅ All JavaScript verdict functions found", "SUCCESS")
    return True

def test_modal_and_drawer_html():
    """Test that modal and drawer HTML elements exist"""
    log_test("Testing modal and drawer HTML elements...")
    
    dashboard_template = "web/templates/index.html"
    with open(dashboard_template, 'r') as f:
        content = f.read()
    
    required_elements = [
        'id="verdictModal"',
        'id="verdictDrawer"', 
        'id="goaheadPanel"',
        'id="runVerdictBtn"'
    ]
    
    for element in required_elements:
        if element not in content:
            log_test(f"❌ HTML element missing: {element}", "ERROR")
            return False
    
    log_test("✅ All modal and drawer HTML elements found", "SUCCESS")
    return True

def test_goahead_panel_structure():
    """Test GoAhead panel structure"""
    log_test("Testing GoAhead panel structure...")
    
    dashboard_template = "web/templates/index.html"
    with open(dashboard_template, 'r') as f:
        content = f.read()
    
    required_elements = [
        "GoAhead Agent — Recommendations",
        "panel-tabs",
        "data-tab=\"all\"",
        "data-tab=\"product\"", 
        "data-tab=\"trainer\""
    ]
    
    for element in required_elements:
        if element not in content:
            log_test(f"❌ GoAhead panel element missing: {element}", "ERROR")
            return False
    
    log_test("✅ GoAhead panel structure is correct", "SUCCESS")
    return True

def test_run_verdict_api():
    """Test the run verdict API endpoint"""
    log_test("Testing run verdict API...")
    
    try:
        base_url = "http://localhost:5000"
        payload = {
            "agent_name": "equity",
            "scope": {
                "product": "equity",
                "timeframe": "5D",
                "symbol": "RELIANCE"
            }
        }
        
        response = requests.post(f"{base_url}/api/agents/run", 
                               json=payload, timeout=5)
        
        if response.status_code in [200, 202]:
            log_test("✅ Run verdict API responds correctly", "SUCCESS")
            return True
        else:
            log_test(f"❌ Run verdict API returned status: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log_test(f"❌ Run verdict API error: {str(e)}", "ERROR")
        return False

def run_comprehensive_validation():
    """Run all validation tests"""
    log_test("🚀 Starting AI Agents UI Validation (Prompt 6B)")
    log_test("=" * 60)
    
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Verdict Columns", test_verdict_columns_exist),
        ("Verdict Styling", test_verdict_styling),
        ("JavaScript Functions", test_javascript_functions),
        ("Modal & Drawer HTML", test_modal_and_drawer_html),
        ("GoAhead Panel", test_goahead_panel_structure),
        ("Run Verdict API", test_run_verdict_api)
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
    
    # Final results
    log_test("=" * 60)
    log_test(f"📊 VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        log_test("🎉 AI AGENTS UI VALIDATION PASSED!", "SUCCESS")
        log_test("✅ All AI verdict features are properly implemented")
        return True
    else:
        log_test(f"❌ VALIDATION FAILED: {total - passed} tests failed", "ERROR")
        return False

if __name__ == "__main__":
    success = run_comprehensive_validation()
    exit(0 if success else 1)
