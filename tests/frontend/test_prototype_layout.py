
import pytest
import os
from playwright.sync_api import sync_playwright, expect

BASE_URL = os.getenv("TEST_BASE_URL", "http://0.0.0.0:5000")

# Skip frontend tests if no browser available
SKIP_FRONTEND = os.getenv("SKIP_FRONTEND", "").lower() == "1"

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_dashboard_kpi_cards():
    """Test dashboard has 6 KPI cards and timeframe chips"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
            
            # Check for 6 KPI cards
            kpi_cards = page.locator(".kpi-card, .metric-card, [data-testid='kpi-card']")
            expect(kpi_cards).to_have_count(6)
            
            # Check for timeframe chips (6 timeframes: All, 3D, 5D, 10D, 15D, 30D)
            timeframe_chips = page.locator(".timeframe-chip, .chip, [data-testid='timeframe']")
            expect(timeframe_chips).to_have_count(6)
            
            # Check Top Signals table exists
            signals_table = page.locator(".signals-table, table[data-testid='top-signals'], .top-signals")
            expect(signals_table).to_be_visible()
            
            # Check Agent Insights card exists
            insights_card = page.locator(".agent-insights, [data-testid='agent-insights'], .insights-card")
            expect(insights_card).to_be_visible()
            
            # Check for console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
            page.wait_for_timeout(1000)  # Wait for any async errors
            
            if console_errors:
                error_messages = [f"{err.type}: {err.text}" for err in console_errors]
                pytest.fail(f"Console errors found: {error_messages}")
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_equities_page_layout():
    """Test equities page table headers match prototype"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/equities", wait_until="networkidle")
            
            # Check table headers
            expected_headers = ["Symbol", "Name", "Price", "Change%", "Volume", "Market Cap", "P/E", "Verdict"]
            
            for header in expected_headers:
                header_element = page.locator(f"th:has-text('{header}'), .header:has-text('{header}')")
                expect(header_element).to_be_visible()
            
            # Check pin/star buttons exist in rows
            pin_buttons = page.locator(".pin-btn, .star-btn, [data-testid='pin']")
            expect(pin_buttons.first).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_options_page_layout():
    """Test options page table headers match prototype"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/options", wait_until="networkidle")
            
            # Check for options-specific headers
            expected_headers = ["Symbol", "Strategy", "Strike", "Premium", "DTE", "Probability", "Verdict"]
            
            for header in expected_headers:
                header_element = page.locator(f"th:has-text('{header}'), .header:has-text('{header}')")
                expect(header_element).to_be_visible()
            
            # Check lock buttons exist
            lock_buttons = page.locator(".lock-btn, [data-testid='lock']")
            expect(lock_buttons.first).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_commodities_page_layout():
    """Test commodities page table headers match prototype"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/commodities", wait_until="networkidle")
            
            # Check commodities-specific headers
            expected_headers = ["Commodity", "Price", "Change%", "Volume", "Signal", "Strength", "Verdict"]
            
            for header in expected_headers:
                header_element = page.locator(f"th:has-text('{header}'), .header:has-text('{header}')")
                expect(header_element).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_kpi_page_layout():
    """Test KPI page layout matches prototype"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(f"{BASE_URL}/kpi", wait_until="networkidle")
            
            # Check for KPI sections
            sections = ["Prediction KPIs", "Financial KPIs", "Risk KPIs"]
            
            for section in sections:
                section_element = page.locator(f"h2:has-text('{section}'), .section-title:has-text('{section}')")
                expect(section_element).to_be_visible()
            
            # Check metric cards exist
            metric_cards = page.locator(".metric-card, .kpi-metric, [data-testid='metric']")
            expect(metric_cards.first).to_be_visible()
            
        finally:
            browser.close()

@pytest.mark.skipif(SKIP_FRONTEND, reason="Browser not available")
def test_navigation_between_pages():
    """Test navigation between all 4 main pages"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Start at dashboard
            page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
            expect(page).to_have_url(f"{BASE_URL}/dashboard")
            
            # Navigate to equities
            page.goto(f"{BASE_URL}/equities", wait_until="networkidle")
            expect(page).to_have_url(f"{BASE_URL}/equities")
            
            # Navigate to options
            page.goto(f"{BASE_URL}/options", wait_until="networkidle")
            expect(page).to_have_url(f"{BASE_URL}/options")
            
            # Navigate to commodities
            page.goto(f"{BASE_URL}/commodities", wait_until="networkidle")
            expect(page).to_have_url(f"{BASE_URL}/commodities")
            
            # Navigate to KPI
            page.goto(f"{BASE_URL}/kpi", wait_until="networkidle")
            expect(page).to_have_url(f"{BASE_URL}/kpi")
            
        finally:
            browser.close()
