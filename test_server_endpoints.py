
#!/usr/bin/env python3
"""
Rate-Limited Server Endpoint Testing
Tests all API endpoints with proper delays to avoid rate limiting
"""

import time
import requests
import json
import sys

def test_endpoint_with_delay(url, name, delay=2):
    """Test a single endpoint with delay"""
    print(f"\n🔍 Testing {name}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ {name}: SUCCESS")
                print(f"Response preview: {str(data)[:200]}...")
                return True
            except json.JSONDecodeError:
                print(f"⚠️  {name}: Non-JSON response")
                print(f"Content: {response.text[:200]}...")
                return False
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            print(f"Content: {response.text[:200]}...")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Connection error - {str(e)}")
        return False
    finally:
        # Always wait to avoid rate limiting
        print(f"⏳ Waiting {delay} seconds...")
        time.sleep(delay)

def main():
    """Test all endpoints with proper rate limiting"""
    print("🚀 RATE-LIMITED API ENDPOINT TESTING")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test endpoints with increased delays
    endpoints = [
        (f"{base_url}/api/equities/list", "Equities List"),
        (f"{base_url}/api/equities/kpis?timeframe=5D", "Equities KPIs"),
        (f"{base_url}/api/options/strangle/candidates?underlying=TCS&expiry=2024-02-29", "Options Strangle"),
        (f"{base_url}/api/commodities/signals?timeframe=10D", "Commodities Signals"),
        (f"{base_url}/api/commodities/kpis?timeframe=10D", "Commodities KPIs"), 
        (f"{base_url}/api/commodities/correlations?symbol=GOLD", "Commodities Correlations"),
        (f"{base_url}/api/pins", "Pins API"),
        (f"{base_url}/api/locks", "Locks API"),
    ]
    
    success_count = 0
    total_count = len(endpoints)
    
    for url, name in endpoints:
        if test_endpoint_with_delay(url, name, delay=3):
            success_count += 1
    
    print("\n" + "=" * 50)
    print("📊 TESTING SUMMARY")
    print("=" * 50)
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 ALL ENDPOINTS WORKING!")
        return True
    else:
        print(f"\n⚠️  {total_count - success_count} endpoints need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
