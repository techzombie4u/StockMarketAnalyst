
"""
Paper Trade API Tests - Real-time Integration
"""
import pytest
import json
from datetime import datetime
from tests.utils.server_manager import ServerManager

class TestPaperTradeAPI:
    """Test Paper Trade API with real-time data validation"""
    
    @pytest.fixture(autouse=True)
    def setup_server(self):
        """Setup test server"""
        self.server_manager = ServerManager()
        self.server_manager.start()
        self.base_url = self.server_manager.base_url
        yield
        self.server_manager.stop()

    def test_paper_trade_endpoints_exist(self):
        """Test that all Paper Trade endpoints are accessible"""
        endpoints = [
            '/api/papertrade/portfolio',
            '/api/papertrade/positions', 
            '/api/papertrade/orders',
        ]
        
        for endpoint in endpoints:
            response = self.server_manager.get(endpoint)
            assert response.status_code == 200, f"Endpoint {endpoint} not accessible"
            
            data = response.json()
            assert data.get("success") is True, f"Endpoint {endpoint} returned failure"

    def test_live_price_endpoint(self):
        """Test live price fetching with real data"""
        # Test with common stock symbol
        response = self.server_manager.get('/api/papertrade/live-price/RELIANCE')
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") is True
        assert "price" in data
        assert isinstance(data["price"], (int, float))
        assert data["price"] > 0, "Live price should be positive"
        assert "timestamp" in data

    def test_execute_trade_real_data(self):
        """Test trade execution with real-time prices"""
        # Execute buy order
        trade_data = {
            "symbol": "RELIANCE",
            "side": "BUY", 
            "quantity": 10
        }
        
        response = self.server_manager.post('/api/papertrade/execute', json=trade_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result.get("success") is True
        assert "order" in result
        assert "live_price" in result
        assert result["live_price"] > 0
        
        # Verify order structure
        order = result["order"]
        assert order["symbol"] == "RELIANCE"
        assert order["side"] == "BUY"
        assert order["quantity"] == 10
        assert order["status"] == "EXECUTED"
        assert "order_id" in order
        assert "timestamp" in order

    def test_position_management_flow(self):
        """Test complete position management flow"""
        # 1. Execute buy order
        buy_data = {"symbol": "SBIN", "side": "BUY", "quantity": 50}
        buy_response = self.server_manager.post('/api/papertrade/execute', json=buy_data)
        assert buy_response.status_code == 200
        assert buy_response.json()["success"] is True
        
        # 2. Check positions
        positions_response = self.server_manager.get('/api/papertrade/positions')
        assert positions_response.status_code == 200
        
        positions_data = positions_response.json()
        assert positions_data["success"] is True
        assert len(positions_data["positions"]) > 0
        
        # Find SBIN position
        sbin_position = None
        for pos in positions_data["positions"]:
            if pos["symbol"] == "SBIN":
                sbin_position = pos
                break
        
        assert sbin_position is not None, "SBIN position not found"
        assert sbin_position["quantity"] == 50
        assert "current_price" in sbin_position
        assert "pnl" in sbin_position
        
        # 3. Close position
        close_response = self.server_manager.post('/api/papertrade/close', json={"symbol": "SBIN"})
        assert close_response.status_code == 200
        assert close_response.json()["success"] is True
        
        # 4. Verify position is closed
        final_positions = self.server_manager.get('/api/papertrade/positions')
        final_data = final_positions.json()
        
        # SBIN position should be gone or have 0 quantity
        sbin_final = None
        for pos in final_data["positions"]:
            if pos["symbol"] == "SBIN":
                sbin_final = pos
                break
        
        assert sbin_final is None or sbin_final["quantity"] == 0

    def test_portfolio_metrics_real_time(self):
        """Test portfolio metrics calculation with real data"""
        response = self.server_manager.get('/api/papertrade/portfolio')
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        portfolio_data = data["data"]
        assert "portfolio" in portfolio_data
        assert "positions_count" in portfolio_data
        assert "total_trades" in portfolio_data
        
        portfolio = portfolio_data["portfolio"]
        required_fields = [
            "initial_capital", "current_capital", "total_pnl", 
            "realized_pnl", "unrealized_pnl", "last_updated"
        ]
        
        for field in required_fields:
            assert field in portfolio, f"Portfolio missing required field: {field}"

    def test_order_history_persistence(self):
        """Test order history persistence and retrieval"""
        # Execute a trade
        trade_data = {"symbol": "ITC", "side": "BUY", "quantity": 25}
        execute_response = self.server_manager.post('/api/papertrade/execute', json=trade_data)
        assert execute_response.status_code == 200
        
        # Get order history
        orders_response = self.server_manager.get('/api/papertrade/orders')
        assert orders_response.status_code == 200
        
        orders_data = orders_response.json()
        assert orders_data["success"] is True
        assert len(orders_data["orders"]) > 0
        
        # Find the ITC order
        itc_order = None
        for order in orders_data["orders"]:
            if order["symbol"] == "ITC" and order["side"] == "BUY":
                itc_order = order
                break
        
        assert itc_order is not None, "ITC order not found in history"
        assert itc_order["quantity"] == 25
        assert itc_order["status"] == "EXECUTED"

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid symbol
        invalid_price = self.server_manager.get('/api/papertrade/live-price/INVALID123')
        assert invalid_price.status_code == 404
        
        # Test invalid trade data
        invalid_trade = self.server_manager.post('/api/papertrade/execute', json={
            "symbol": "",
            "side": "INVALID",
            "quantity": -1
        })
        assert invalid_trade.status_code == 400
        
        # Test close non-existent position
        invalid_close = self.server_manager.post('/api/papertrade/close', json={
            "symbol": "NONEXISTENT"
        })
        assert invalid_close.status_code == 400

    def test_real_time_price_updates(self):
        """Test that prices are actually real-time (not cached stale data)"""
        # Get price twice with small delay
        import time
        
        response1 = self.server_manager.get('/api/papertrade/live-price/RELIANCE')
        time.sleep(2)
        response2 = self.server_manager.get('/api/papertrade/live-price/RELIANCE')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        price1 = response1.json()["price"]
        price2 = response2.json()["price"]
        
        # Prices should be real numbers from live feed
        assert isinstance(price1, (int, float))
        assert isinstance(price2, (int, float))
        assert price1 > 0
        assert price2 > 0
        
        # Timestamps should be different (real-time)
        time1 = response1.json()["timestamp"]
        time2 = response2.json()["timestamp"]
        assert time1 != time2, "Timestamps should be different for real-time data"

    def test_integration_with_kpi_dashboard(self):
        """Test that Paper Trade data integrates with KPI dashboard"""
        # Execute some trades first
        trades = [
            {"symbol": "HDFCBANK", "side": "BUY", "quantity": 5},
            {"symbol": "ICICIBANK", "side": "BUY", "quantity": 10}
        ]
        
        for trade in trades:
            response = self.server_manager.post('/api/papertrade/execute', json=trade)
            assert response.status_code == 200
        
        # Check fusion dashboard includes Paper Trade data
        fusion_response = self.server_manager.get('/api/fusion/dashboard?timeframe=5D')
        assert fusion_response.status_code == 200
        
        fusion_data = fusion_response.json()
        assert "papertrade_summary" in fusion_data
        
        pt_summary = fusion_data["papertrade_summary"]
        if pt_summary.get("enabled"):
            assert "portfolio_value" in pt_summary
            assert "total_pnl" in pt_summary
            assert "open_positions" in pt_summary
            assert pt_summary["open_positions"] > 0  # Should have positions from our trades

    def test_concurrent_trade_execution(self):
        """Test concurrent trade execution doesn't cause data corruption"""
        import threading
        import time
        
        results = []
        
        def execute_trade(symbol, side, quantity):
            try:
                response = self.server_manager.post('/api/papertrade/execute', json={
                    "symbol": symbol,
                    "side": side, 
                    "quantity": quantity
                })
                results.append({
                    "symbol": symbol,
                    "success": response.status_code == 200,
                    "data": response.json()
                })
            except Exception as e:
                results.append({
                    "symbol": symbol,
                    "success": False,
                    "error": str(e)
                })
        
        # Execute multiple trades concurrently
        threads = []
        trade_symbols = ["RELIANCE", "TCS", "INFY", "SBIN", "BHARTIARTL"]
        
        for i, symbol in enumerate(trade_symbols):
            thread = threading.Thread(
                target=execute_trade, 
                args=(symbol, "BUY", 10 + i)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all trades to complete
        for thread in threads:
            thread.join()
        
        # Verify all trades succeeded
        assert len(results) == len(trade_symbols)
        for result in results:
            assert result["success"] is True, f"Concurrent trade failed: {result}"
        
        # Verify data consistency
        positions_response = self.server_manager.get('/api/papertrade/positions')
        assert positions_response.status_code == 200
        
        positions = positions_response.json()["positions"]
        assert len(positions) == len(trade_symbols), "Position count doesn't match executed trades"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
