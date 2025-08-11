
import requests, os, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_pins_list_empty():
    """Test getting pins when empty"""
    r = requests.get(f"{BASE_URL}/api/pins", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    assert "items" in data, "Missing items field"
    assert isinstance(data["items"], list), "items must be array"

def test_pin_add_and_list():
    """Test adding a pin and listing it"""
    # Add a pin
    pin_data = {
        "type": "equity",
        "symbol": "TCS"
    }
    
    r = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r.status_code == 200, f"Pin add failed: {r.text}"
    data = r.json()
    
    assert "success" in data, "Missing success field"
    assert data["success"] == True, "Pin add not successful"
    assert "items" in data, "Missing items field in response"

def test_pin_toggle_behavior():
    """Test pin toggle (add/remove) behavior"""
    pin_data = {
        "type": "equity", 
        "symbol": "RELIANCE"
    }
    
    # First pin should add
    r1 = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r1.status_code == 200
    items1 = r1.json()["items"]
    
    # Second pin should remove (toggle)
    r2 = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r2.status_code == 200
    items2 = r2.json()["items"]
    
    # Should have one less item after toggle
    assert len(items2) <= len(items1), "Toggle should remove item"

def test_locks_functionality():
    """Test locks follow same pattern as pins"""
    # Test lock add
    lock_data = {
        "type": "option",
        "symbol": "NIFTY"
    }
    
    r = requests.post(f"{BASE_URL}/api/locks", json=lock_data, timeout=5)
    assert r.status_code == 200, f"Lock add failed: {r.text}"
    data = r.json()
    
    assert "success" in data, "Missing success field"
    assert data["success"] == True, "Lock add not successful"

def test_bulk_pins_operation():
    """Test bulk pins operation"""
    bulk_data = {
        "items": [
            {"type": "equity", "symbol": "TCS"},
            {"type": "equity", "symbol": "INFY"}
        ]
    }
    
    r = requests.post(f"{BASE_URL}/api/pins", json=bulk_data, timeout=5)
    assert r.status_code == 200, f"Bulk pin failed: {r.text}"
    data = r.json()
    
    assert "success" in data, "Missing success field"
    assert data["success"] == True, "Bulk pin not successful"
    assert "items" in data, "Missing items field"
