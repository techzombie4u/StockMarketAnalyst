
import pytest
import os
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

# Skip frontend tests if no browser available
SKIP_FRONTEND = os.getenv("SKIP_FRONTEND", "").lower() == "1"

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_dashboard_page():
    """Test dashboard page has required elements"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
            
            # Check for key dashboard elements
            expect(page.get_by_text("Pinned Rollup")).to_be_visible()
            expect(page.get_by_text("Agent Insights")).to_be_visible()
            
            # Check for KPI cards
            kpi_cards = page.locator(".kpi-card, .metric-card, [data-testid='kpi-card']")
            expect(kpi_cards).to_have_count(6)
            
            # Check for timeframe chips
            timeframe_chips = page.locator(".timeframe-chip, .chip, [data-testid='timeframe']")
            expect(timeframe_chips).to_have_count(6)
            
            # Check Top Signals table
            signals_table = page.locator(".signals-table, table[data-testid='top-signals'], .top-signals")
            expect(signals_table).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_equities_page():
    """Test equities page has required table headings"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/equities", wait_until="networkidle")
            
            # Check required table headings
            required_headings = ["Symbol", "Name", "Price", "Change%", "Volume", "Market Cap", "P/E", "Verdict"]
            
            for heading in required_headings:
                heading_element = page.locator(f"th:has-text('{heading}'), .header:has-text('{heading}'), td:has-text('{heading}')")
                expect(heading_element).to_be_visible()
            
            # Check for pin/star buttons
            pin_buttons = page.locator(".pin-btn, .star-btn, [data-testid='pin'], .fas.fa-star")
            expect(pin_buttons.first).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_options_page():
    """Test options page has required table headings"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/options", wait_until="networkidle")
            
            # Check required table headings
            required_headings = ["Symbol", "Strategy", "Strike", "Premium", "DTE", "Probability", "Verdict"]
            
            for heading in required_headings:
                heading_element = page.locator(f"th:has-text('{heading}'), .header:has-text('{heading}'), td:has-text('{heading}')")
                expect(heading_element).to_be_visible()
            
            # Check for lock buttons
            lock_buttons = page.locator(".lock-btn, [data-testid='lock'], .fas.fa-lock")
            expect(lock_buttons.first).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_commodities_page():
    """Test commodities page has required table headings"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/commodities", wait_until="networkidle")
            
            # Check required table headings
            required_headings = ["Commodity", "Price", "Change%", "Volume", "Signal", "Strength", "Verdict"]
            
            for heading in required_headings:
                heading_element = page.locator(f"th:has-text('{heading}'), .header:has-text('{heading}'), td:has-text('{heading}')")
                expect(heading_element).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_all_pages_navigation():
    """Test that all required pages load successfully"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            pages_to_test = [
                ("/dashboard", "Dashboard"),
                ("/equities", "Equities"),
                ("/options", "Options"),
                ("/commodities", "Commodities")
            ]
            
            for url, page_name in pages_to_test:
                page.goto(f"{BASE_URL}{url}", wait_until="networkidle")
                
                # Check page loads without errors
                expect(page).to_have_url(f"{BASE_URL}{url}")
                
                # Check no critical JavaScript errors
                console_errors = []
                page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
                page.wait_for_timeout(1000)
                
                # Filter out non-critical errors
                critical_errors = [err for err in console_errors if "SyntaxError" not in str(err) or "Failed to load" not in str(err)]
                
                if critical_errors:
                    pytest.fail(f"Critical console errors on {page_name}: {[str(err) for err in critical_errors]}")
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_page_specific_content():
    """Test each page has its specific required content"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Dashboard specific content
            page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
            expect(page.get_by_text("Pinned Rollup")).to_be_visible()
            expect(page.get_by_text("Agent Insights")).to_be_visible()
            
            # Equities specific content
            page.goto(f"{BASE_URL}/equities", wait_until="networkidle")
            expect(page.locator("th:has-text('Symbol'), .header:has-text('Symbol')")).to_be_visible()
            expect(page.locator("th:has-text('Market Cap'), .header:has-text('Market Cap')")).to_be_visible()
            
            # Options specific content
            page.goto(f"{BASE_URL}/options", wait_until="networkidle")
            expect(page.locator("th:has-text('Strategy'), .header:has-text('Strategy')")).to_be_visible()
            expect(page.locator("th:has-text('DTE'), .header:has-text('DTE')")).to_be_visible()
            
            # Commodities specific content
            page.goto(f"{BASE_URL}/commodities", wait_until="networkidle")
            expect(page.locator("th:has-text('Commodity'), .header:has-text('Commodity')")).to_be_visible()
            expect(page.locator("th:has-text('Signal'), .header:has-text('Signal')")).to_be_visible()
            
        finally:
            browser.close()
