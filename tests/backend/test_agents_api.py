
# tests/backend/test_agents_api.py
import os, requests, time, json

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

def _json(r):
    try:
        return r.json()
    except Exception:
        return {"_raw": r.text}

def test_agents_registry_health():
    r = requests.get(f"{BASE_URL}/api/agents", timeout=5)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    data = _json(r)
    assert data.get("success") is True, data
    assert "agents" in data, "Missing agents list"

def test_required_agents_present():
    r = requests.get(f"{BASE_URL}/api/agents", timeout=5)
    agents = {a["key"]: a for a in r.json().get("agents", [])}
    missing = [k for k in ["new_ai_analyzer","sentiment_analyzer"] if k not in agents]
    assert not missing, f"Missing required agents: {missing}"

def test_agent_execution_and_persistence():
    # run both agents
    for a in ["new_ai_analyzer","sentiment_analyzer"]:
        rr = requests.post(f"{BASE_URL}/api/agents/{a}/run", json={}, timeout=30)
        assert rr.status_code == 200, f"{a} HTTP {rr.status_code}: {rr.text}"
        payload = _json(rr)
        assert payload.get("success") is True, payload
        assert "result" in payload, payload

        # check persisted history
        hr = requests.get(f"{BASE_URL}/api/agents/history?agent={a}", timeout=5)
        assert hr.status_code == 200, f"history {a} HTTP {hr.status_code}: {hr.text}"
        hist = _json(hr).get("history", [])
        assert len(hist) >= 1, f"No history for {a}"

def test_enable_disable_flow():
    # disable, verify cannot run, enable back
    dr = requests.post(f"{BASE_URL}/api/agents/new_ai_analyzer/disable", timeout=5)
    assert dr.status_code == 200, dr.text
    rr = requests.post(f"{BASE_URL}/api/agents/new_ai_analyzer/run", json={}, timeout=10)
    assert rr.status_code == 400, "Disabled agent should not run"
    er = requests.post(f"{BASE_URL}/api/agents/new_ai_analyzer/enable", timeout=5)
    assert er.status_code == 200, er.text

def test_config_get_set():
    gr = requests.get(f"{BASE_URL}/api/agents/config", timeout=5)
    assert gr.status_code == 200, gr.text
    cfg = gr.json().get("config", {})
    sr = requests.post(f"{BASE_URL}/api/agents/config", json={"config": cfg}, timeout=5)
    assert sr.status_code == 200, sr.text
