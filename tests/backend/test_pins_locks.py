
<old_str>
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

</old_str>
<new_str>
import requests, os, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def test_pins_structured_schema():
    """Test pins returns structured schema"""
    r = requests.get(f"{BASE_URL}/api/pins", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    assert "pins" in data, "Missing pins field"
    assert isinstance(data["pins"], dict), "pins must be object"

def test_pin_add_structured():
    """Test adding a pin with structured schema"""
    # Add a pin
    pin_data = {
        "type": "EQUITY",
        "symbol": "TCS"
    }
    
    r = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r.status_code == 200, f"Pin add failed: {r.text}"
    data = r.json()
    
    assert "success" in data, "Missing success field"
    assert data["success"] == True, "Pin add not successful"
    assert "pins" in data, "Missing pins field in response"
    assert "EQUITY" in data["pins"], "Missing EQUITY category"
    assert "TCS" in data["pins"]["EQUITY"], "TCS not found in EQUITY pins"

def test_pin_toggle_behavior():
    """Test pin toggle (add/remove) behavior"""
    pin_data = {
        "type": "EQUITY", 
        "symbol": "RELIANCE"
    }
    
    # First pin should add
    r1 = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r1.status_code == 200
    pins1 = r1.json()["pins"]
    
    # Second pin should remove (toggle)
    r2 = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r2.status_code == 200
    pins2 = r2.json()["pins"]
    
    # Should be unpinned now
    equity_pins = pins2.get("EQUITY", [])
    assert "RELIANCE" not in equity_pins, "Toggle should remove item"

def test_pin_relist_unpin_sequence():
    """Test pin, relist, unpin sequence"""
    pin_data = {"type": "EQUITY", "symbol": "INFY"}
    
    # Pin
    r1 = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r1.status_code == 200
    assert "INFY" in r1.json()["pins"].get("EQUITY", [])
    
    # Relist (get current pins)
    r2 = requests.get(f"{BASE_URL}/api/pins", timeout=5)
    assert r2.status_code == 200
    assert "INFY" in r2.json()["pins"].get("EQUITY", [])
    
    # Unpin
    r3 = requests.post(f"{BASE_URL}/api/pins", json=pin_data, timeout=5)
    assert r3.status_code == 200
    assert "INFY" not in r3.json()["pins"].get("EQUITY", [])

def test_locks_structured_schema():
    """Test locks returns structured schema"""
    r = requests.get(f"{BASE_URL}/api/locks", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = r.json()
    
    assert "locks" in data, "Missing locks field"
    assert isinstance(data["locks"], dict), "locks must be object"

def test_lock_position_blocking():
    """Test lock position then verify POST update is 423/blocked"""
    # Lock a position
    lock_data = {
        "type": "OPTIONS",
        "id": "POS123"
    }
    
    r1 = requests.post(f"{BASE_URL}/api/locks", json=lock_data, timeout=5)
    assert r1.status_code == 200, f"Lock add failed: {r1.text}"
    data = r1.json()
    
    assert "success" in data, "Missing success field"
    assert data["success"] == True, "Lock add not successful"
    assert "locks" in data, "Missing locks field"
    assert "OPTIONS" in data["locks"], "Missing OPTIONS category"
    assert "POS123" in data["locks"]["OPTIONS"], "POS123 not found in OPTIONS locks"
    
    # Test that locked position blocks actions
    check_data = {
        "type": "OPTIONS",
        "id": "POS123"
    }
    
    r2 = requests.post(f"{BASE_URL}/api/locks/check", json=check_data, timeout=5)
    assert r2.status_code == 423, f"Expected 423 for locked item, got {r2.status_code}: {r2.text}"
    data2 = r2.json()
    assert data2["locked"] == True, "Item should be locked"
    assert "Action blocked" in data2["error"], "Missing blocked action error message"

def test_multi_product_pins():
    """Test pins across multiple product types"""
    pins = [
        {"type": "EQUITY", "symbol": "TCS"},
        {"type": "EQUITY", "symbol": "RELIANCE"},
        {"type": "OPTIONS", "symbol": "TCS-STRANGLE"},
        {"type": "COMMODITY", "symbol": "GOLD"}
    ]
    
    # Add pins
    for pin in pins:
        r = requests.post(f"{BASE_URL}/api/pins", json=pin, timeout=5)
        assert r.status_code == 200, f"Failed to pin {pin}"
    
    # Verify structured schema
    r = requests.get(f"{BASE_URL}/api/pins", timeout=5)
    assert r.status_code == 200
    data = r.json()
    
    # Should match expected schema structure
    expected_structure = {
        "EQUITY": ["TCS", "RELIANCE"],
        "OPTIONS": ["TCS-STRANGLE"],
        "COMMODITY": ["GOLD"]
    }
    
    for product_type, symbols in expected_structure.items():
        assert product_type in data["pins"], f"Missing {product_type} in pins"
        for symbol in symbols:
            assert symbol in data["pins"][product_type], f"{symbol} not found in {product_type} pins"

def test_locks_with_different_ids():
    """Test locks with position IDs and symbols"""
    locks = [
        {"type": "OPTIONS", "id": "POS123"},
        {"type": "OPTIONS", "id": "POS124"},
        {"type": "EQUITY", "symbol": "LOCKEDSTOCK"}
    ]
    
    # Add locks
    for lock in locks:
        r = requests.post(f"{BASE_URL}/api/locks", json=lock, timeout=5)
        assert r.status_code == 200, f"Failed to lock {lock}"
    
    # Verify locks
    r = requests.get(f"{BASE_URL}/api/locks", timeout=5)
    assert r.status_code == 200
    data = r.json()
    
    assert "POS123" in data["locks"].get("OPTIONS", [])
    assert "POS124" in data["locks"].get("OPTIONS", [])
    assert "LOCKEDSTOCK" in data["locks"].get("EQUITY", [])

</new_str>
