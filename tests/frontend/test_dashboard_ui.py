
# tests/frontend/test_dashboard_ui.py
import os, json, pathlib, pytest

# Allow skipping from env (Replit system-deps often block browser install)
if os.getenv("SKIP_FRONTEND", "0") == "1":
    pytest.skip("Frontend tests skipped by SKIP_FRONTEND=1", allow_module_level=True)

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:5000")
ARTIFACTS = pathlib.Path("logs/regression/frontend")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def test_dashboard_renders_and_populates():
    with sync_playwright() as p:
        # If Chromium isn't installed, this will raise; mark as xfail instead of crashing the run
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as e:
            pytest.xfail(f"Chromium not available in this environment: {e}")

        context = browser.new_context()
        page = context.new_page()

        console = []
        page.on("console", lambda msg: console.append({"type": msg.type, "text": msg.text()}))

        page.goto(f"{BASE_URL}/fusion-dashboard", wait_until="load")
        page.wait_for_timeout(1500)

        expect(page.get_by_text("Stock Market Analyst Dashboard")).to_be_visible()

        tbody = page.locator("#resultsTbody tr")
        assert tbody.count() >= 1, "No rows rendered in resultsTbody"

        errs = [c for c in console if c["type"] == "error"]
        if errs:
            (ARTIFACTS / "console_errors.json").write_text(json.dumps(errs, indent=2))
        assert not errs, f"Console errors found (saved to logs): {errs}"

        page.screenshot(path=str(ARTIFACTS / "dashboard.png"))
        browser.close()
