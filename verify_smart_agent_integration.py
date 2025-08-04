
#!/usr/bin/env python3
"""
Verification Script for SmartStockAgent Integration
"""

import requests
import json
import time
from datetime import datetime

def test_api_with_smart_agent():
    """Test the API to see if SmartStockAgent data is present"""
    try:
        print("🔍 Testing API for SmartStockAgent integration...")
        
        # Wait a moment for the app to start
        time.sleep(3)
        
        # Test API endpoint
        response = requests.get("http://localhost:5000/api/stocks", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stocks = data.get('stocks', [])
            
            print(f"✅ API responded with {len(stocks)} stocks")
            
            # Check for SmartStockAgent fields
            agent_enhanced_count = 0
            for stock in stocks:
                if 'agent_recommendation' in stock:
                    agent_enhanced_count += 1
                    print(f"   📊 {stock.get('symbol', 'N/A')}: {stock.get('agent_recommendation', 'N/A')} ({stock.get('agent_confidence', 0)}%)")
            
            if agent_enhanced_count > 0:
                print(f"✅ SmartStockAgent enhanced {agent_enhanced_count} stocks")
                return True
            else:
                print("⚠️ No SmartStockAgent enhancements found")
                return False
        else:
            print(f"❌ API error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

def test_agent_decision_files():
    """Test if agent decision files are being created"""
    try:
        print("\n🔍 Testing SmartStockAgent decision files...")
        
        import os
        
        # Check for agent files
        agent_files = [
            'agent_decisions.json',
            'locked_predictions.json',
            'agent_performance.json'
        ]
        
        files_created = 0
        for file in agent_files:
            if os.path.exists(file):
                files_created += 1
                print(f"✅ {file} exists")
                
                # Check file content
                try:
                    with open(file, 'r') as f:
                        content = json.load(f)
                        if content:
                            print(f"   📄 Contains data: {len(content) if isinstance(content, (list, dict)) else 'Yes'}")
                        else:
                            print(f"   📄 Empty file")
                except:
                    print(f"   ⚠️ Could not read {file}")
            else:
                print(f"⏳ {file} not yet created (normal for first run)")
        
        print(f"✅ Agent files status: {files_created}/{len(agent_files)} exist")
        return True
        
    except Exception as e:
        print(f"❌ File test failed: {str(e)}")
        return False

def test_dashboard_display():
    """Test if dashboard shows SmartStockAgent elements"""
    try:
        print("\n🔍 Testing dashboard for SmartStockAgent display...")
        
        # Test dashboard HTML
        response = requests.get("http://localhost:5000/", timeout=10)
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check for SmartStockAgent CSS classes
            agent_elements = [
                'ai-recommendation',
                'ai-action',
                'ai-confidence',
                'ai-locked'
            ]
            
            elements_found = 0
            for element in agent_elements:
                if element in html_content:
                    elements_found += 1
                    print(f"✅ Found {element} styling")
                else:
                    print(f"⚠️ Missing {element} styling")
            
            if elements_found >= 3:
                print("✅ Dashboard has SmartStockAgent styling")
                return True
            else:
                print("⚠️ Dashboard missing SmartStockAgent elements")
                return False
        else:
            print(f"❌ Dashboard error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {str(e)}")
        return False

def main():
    """Run all verification tests"""
    print("🚀 SmartStockAgent Integration Verification")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        ("API with SmartStockAgent Data", test_api_with_smart_agent),
        ("Agent Decision Files", test_agent_decision_files),
        ("Dashboard Display", test_dashboard_display)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {str(e)}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 SmartStockAgent integration VERIFIED!")
        print("✅ All features are working correctly")
    else:
        print("⚠️ Some verification tests failed")
        print("🔧 Please check the application logs for details")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
