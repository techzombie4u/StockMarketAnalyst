
# tests/frontend/test_dashboard_ui.py
import os, json, pathlib
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")
ARTIFACTS = pathlib.Path("logs/regression/frontend")
ARTIFACTS.mkdir(parents=True, exist_ok=True)

def test_dashboard_renders_and_populates():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Capture console errors/warnings
        console = []
        page.on("console", lambda msg: console.append({"type": msg.type, "text": msg.text()}))

        page.goto(f"{BASE_URL}/fusion-dashboard", wait_until="load")
        # Allow JS to fetch and render
        page.wait_for_timeout(1500)

        # Basic checks
        expect(page.get_by_text("Stock Market Analyst Dashboard")).to_be_visible()
        # resultsTbody exists and has at least one row
        tbody = page.locator("#resultsTbody tr")
        rows = tbody.count()
        assert rows >= 1, "No rows rendered in resultsTbody"

        # No red console errors
        errs = [c for c in console if c["type"] == "error"]
        if errs:
            (ARTIFACTS / "console_errors.json").write_text(json.dumps(errs, indent=2))
        assert not errs, f"Console errors found (saved to logs): {errs}"

        # Screenshot
        page.screenshot(path=str(ARTIFACTS / "dashboard.png"))
        browser.close()
