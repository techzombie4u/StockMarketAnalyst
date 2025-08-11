
#!/usr/bin/env python3

import requests
import time
import json
from datetime import datetime

def test_endpoint(url, description, delay=1):
    """Test an endpoint with rate limiting protection"""
    print(f"Testing {description}...")
    try:
        time.sleep(delay)  # Rate limiting protection
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ {description}: SUCCESS")
                if isinstance(data, dict) and len(data) <= 5:
                    print(f"   Response: {json.dumps(data, indent=2)}")
                else:
                    print(f"   Status: {response.status_code}")
                return True
            except:
                print(f"✅ {description}: SUCCESS (non-JSON response)")
                return True
        else:
            print(f"❌ {description}: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {description}: Connection error - {e}")
        return False
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def main():
    """Test all endpoints with rate limiting"""
    print("🧪 Testing Server Endpoints (Rate-Limited)")
    print("=" * 50)
    
    base_url = "http://0.0.0.0:5000"
    
    # Core endpoints
    endpoints = [
        (f"{base_url}/health", "Health Check"),
        (f"{base_url}/", "Root Endpoint"),
        (f"{base_url}/api/test", "API Test"),
        (f"{base_url}/api/pins-locks/status", "Pins/Locks Status"),
        (f"{base_url}/api/kpi/current", "KPI Current"),
    ]
    
    # Test with delays
    success_count = 0
    total_count = len(endpoints)
    
    for url, description in endpoints:
        if test_endpoint(url, description, delay=2):  # 2 second delay
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{total_count} endpoints working")
    
    if success_count >= 3:  # At least basic endpoints work
        print("✅ Server is operational!")
        return True
    else:
        print("❌ Server has issues")
        return False

if __name__ == "__main__":
    main()
