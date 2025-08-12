
import os
import requests
import time
import json
import pytest

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def _json(r):
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text}

class TestAgentsSurface:
    """Test complete agents API surface"""
    
    def test_list_agents_endpoint(self):
        """Test /api/agents/ endpoint"""
        r = requests.get(f"{BASE_URL}/api/agents/", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "agents" in data, "Missing agents list"
        assert "total" in data, "Missing total count"
        assert "timestamp" in data, "Missing timestamp"
        assert isinstance(data["agents"], list), "Agents should be a list"
        
        # Check required agents are present
        agent_keys = [a.get("key") for a in data["agents"]]
        assert "new_ai_analyzer" in agent_keys, "Missing new_ai_analyzer"
        assert "sentiment_analyzer" in agent_keys, "Missing sentiment_analyzer"

    def test_run_specific_agent(self):
        """Test /api/agents/<key>/run endpoint"""
        agent_key = "new_ai_analyzer"
        r = requests.post(f"{BASE_URL}/api/agents/{agent_key}/run", 
                         json={}, timeout=30)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "result" in data, "Missing result"
        assert "agent" in data, "Missing agent key"
        assert "timestamp" in data, "Missing timestamp"
        assert data["agent"] == agent_key, "Agent key mismatch"

    def test_run_nonexistent_agent(self):
        """Test running non-existent agent returns 404"""
        r = requests.post(f"{BASE_URL}/api/agents/nonexistent/run", 
                         json={}, timeout=5)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}"
        data = _json(r)
        assert data.get("success") is False, "Should return success=false"
        assert "error" in data, "Missing error message"
        assert "timestamp" in data, "Missing timestamp"

    def test_run_all_agents(self):
        """Test /api/agents/run_all endpoint"""
        r = requests.post(f"{BASE_URL}/api/agents/run_all", 
                         json={}, timeout=60)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "results" in data, "Missing results"
        assert "total_agents" in data, "Missing total_agents"
        assert "timestamp" in data, "Missing timestamp"
        assert isinstance(data["results"], dict), "Results should be a dict"

    def test_enable_disable_agent(self):
        """Test enable/disable agent endpoints"""
        agent_key = "sentiment_analyzer"
        
        # Test disable
        r = requests.post(f"{BASE_URL}/api/agents/{agent_key}/disable", timeout=5)
        assert r.status_code == 200, f"Disable HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert data["status"] == "disabled", "Status should be disabled"
        assert data["agent"] == agent_key, "Agent key mismatch"
        assert "timestamp" in data, "Missing timestamp"
        
        # Test enable
        r = requests.post(f"{BASE_URL}/api/agents/{agent_key}/enable", timeout=5)
        assert r.status_code == 200, f"Enable HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert data["status"] == "enabled", "Status should be enabled"
        assert data["agent"] == agent_key, "Agent key mismatch"
        assert "timestamp" in data, "Missing timestamp"

    def test_enable_disable_nonexistent_agent(self):
        """Test enable/disable non-existent agent returns 404"""
        # Test disable non-existent
        r = requests.post(f"{BASE_URL}/api/agents/nonexistent/disable", timeout=5)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}"
        data = _json(r)
        assert data.get("success") is False, "Should return success=false"
        
        # Test enable non-existent
        r = requests.post(f"{BASE_URL}/api/agents/nonexistent/enable", timeout=5)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}"
        data = _json(r)
        assert data.get("success") is False, "Should return success=false"

    def test_get_config(self):
        """Test /api/agents/config GET endpoint"""
        r = requests.get(f"{BASE_URL}/api/agents/config", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "config" in data, "Missing config"
        assert "timestamp" in data, "Missing timestamp"
        assert isinstance(data["config"], dict), "Config should be a dict"

    def test_set_config(self):
        """Test /api/agents/config POST endpoint"""
        test_config = {"test_setting": True, "max_runtime_sec": 45}
        r = requests.post(f"{BASE_URL}/api/agents/config", 
                         json=test_config, timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "config" in data, "Missing config"
        assert "timestamp" in data, "Missing timestamp"
        
        # Verify config was set
        config = data["config"]
        assert config.get("test_setting") is True, "Test setting not set"
        assert config.get("max_runtime_sec") == 45, "Runtime setting not updated"

    def test_set_config_invalid_json(self):
        """Test setting config with invalid JSON returns 400"""
        r = requests.post(f"{BASE_URL}/api/agents/config", 
                         data="invalid json", 
                         headers={"Content-Type": "application/json"},
                         timeout=5)
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        data = _json(r)
        assert data.get("success") is False, "Should return success=false"
        assert "error" in data, "Missing error message"

    def test_get_agent_history(self):
        """Test /api/agents/<key>/history endpoint"""
        agent_key = "new_ai_analyzer"
        
        # First run the agent to create some history
        requests.post(f"{BASE_URL}/api/agents/{agent_key}/run", 
                     json={}, timeout=30)
        time.sleep(1)  # Allow history to be written
        
        r = requests.get(f"{BASE_URL}/api/agents/{agent_key}/history", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "agent" in data, "Missing agent key"
        assert "history" in data, "Missing history"
        assert "registry_history" in data, "Missing registry history"
        assert "total_runs" in data, "Missing total_runs"
        assert "timestamp" in data, "Missing timestamp"
        assert data["agent"] == agent_key, "Agent key mismatch"
        
        # Check history structure
        history = data["history"]
        if history:  # If there's history
            entry = history[-1]  # Get latest entry
            assert "agent" in entry, "Missing agent in history entry"
            assert "started_at" in entry, "Missing started_at in history entry"
            assert "finished_at" in entry, "Missing finished_at in history entry"
            assert "success" in entry, "Missing success in history entry"
            assert "items" in entry, "Missing items in history entry"
            assert "summary" in entry, "Missing summary in history entry"
            assert "duration_ms" in entry, "Missing duration_ms in history entry"

    def test_get_all_history(self):
        """Test /api/agents/history endpoint"""
        r = requests.get(f"{BASE_URL}/api/agents/history", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "history" in data, "Missing history"
        assert "timestamp" in data, "Missing timestamp"
        assert isinstance(data["history"], dict), "History should be a dict"

    def test_get_agent_kpis(self):
        """Test /api/agents/kpis endpoint"""
        r = requests.get(f"{BASE_URL}/api/agents/kpis", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "kpis" in data, "Missing kpis"
        assert "timestamp" in data, "Missing timestamp"
        
        kpis = data["kpis"]
        required_kpis = [
            "total_agents", "active_agents", "total_runs", 
            "successful_runs", "success_rate", "avg_duration_ms",
            "predictions_today", "accuracy_rate", "avg_confidence"
        ]
        for kpi in required_kpis:
            assert kpi in kpis, f"Missing KPI: {kpi}"
            assert isinstance(kpis[kpi], (int, float)), f"KPI {kpi} should be numeric"

    def test_get_agents_status(self):
        """Test /api/agents/status endpoint"""
        r = requests.get(f"{BASE_URL}/api/agents/status", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        assert data.get("success") is True, data
        assert "agents" in data, "Missing agents"
        assert "timestamp" in data, "Missing timestamp"
        
        agents = data["agents"]
        assert isinstance(agents, list), "Agents should be a list"
        if agents:  # If there are agents
            agent = agents[0]
            required_fields = ["name", "key", "status", "last_run", "performance"]
            for field in required_fields:
                assert field in agent, f"Missing field in agent status: {field}"

    def test_error_format_consistency(self):
        """Test that all error responses follow consistent JSON format"""
        error_endpoints = [
            ("POST", "/api/agents/nonexistent/run"),
            ("POST", "/api/agents/nonexistent/enable"),
            ("POST", "/api/agents/nonexistent/disable"),
            ("GET", "/api/agents/nonexistent/history")
        ]
        
        for method, endpoint in error_endpoints:
            if method == "POST":
                r = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=5)
            else:
                r = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            
            assert r.status_code in [400, 404, 500], f"Unexpected status for {endpoint}"
            data = _json(r)
            assert data.get("success") is False, f"Error response should have success=false for {endpoint}"
            assert "error" in data, f"Error response should have error field for {endpoint}"
            assert "timestamp" in data, f"Error response should have timestamp for {endpoint}"

    def test_json_error_format(self):
        """Test JSON error format for 500 errors"""
        # This test might need to be adjusted based on how you can trigger a 500 error
        # For now, we'll test with malformed config
        r = requests.post(f"{BASE_URL}/api/agents/config", 
                         data="not json", 
                         headers={"Content-Type": "application/json"},
                         timeout=5)
        
        data = _json(r)
        assert data.get("success") is False, "Should return success=false"
        assert "error" in data, "Should have error field"
        assert "timestamp" in data, "Should have timestamp field"
        
        # Check timestamp format
        timestamp = data["timestamp"]
        assert timestamp.endswith("Z"), "Timestamp should end with Z"

    def test_persistence_after_agent_run(self):
        """Test that agent runs are properly persisted"""
        agent_key = "sentiment_analyzer"
        
        # Clear any existing history first by getting baseline
        r = requests.get(f"{BASE_URL}/api/agents/{agent_key}/history", timeout=5)
        baseline_count = len(_json(r).get("history", []))
        
        # Run the agent
        r = requests.post(f"{BASE_URL}/api/agents/{agent_key}/run", 
                         json={}, timeout=30)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        
        # Wait a moment for persistence
        time.sleep(2)
        
        # Check that history increased
        r = requests.get(f"{BASE_URL}/api/agents/{agent_key}/history", timeout=5)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
        data = _json(r)
        new_count = len(data.get("history", []))
        assert new_count > baseline_count, "History should have increased after agent run"

if __name__ == "__main__":
    # Run tests manually
    test_class = TestAgentsSurface()
    
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    print(f"Running {len(test_methods)} tests...")
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            print(f"\n🧪 {test_method}")
            getattr(test_class, test_method)()
            print(f"✅ {test_method} PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_method} FAILED: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed!")
