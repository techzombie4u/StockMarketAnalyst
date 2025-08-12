
import pytest
import time
import psutil
from unittest.mock import patch, MagicMock
from src.core.guardrails import PerformanceGuardrails, guardrails

class TestPerformanceGuardrails:
    
    def setup_method(self):
        """Setup for each test"""
        self.guardrails = PerformanceGuardrails()

    def test_record_request_latency(self):
        """Test recording request latency"""
        endpoint = "/api/test"
        latency = 150.0
        
        self.guardrails.record_request_latency(endpoint, latency)
        
        assert len(self.guardrails.latency_data[endpoint]) == 1
        assert self.guardrails.latency_data[endpoint][0]['latency_ms'] == latency

    def test_record_cache_operations(self):
        """Test recording cache hits and misses"""
        endpoint = "/api/test"
        
        self.guardrails.record_cache_hit(endpoint)
        self.guardrails.record_cache_miss(endpoint)
        
        assert self.guardrails.cache_hits[endpoint] == 1
        assert self.guardrails.cache_misses[endpoint] == 1

    def test_p95_latency_calculation(self):
        """Test p95 latency calculation"""
        endpoint = "/api/test"
        latencies = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        
        for latency in latencies:
            self.guardrails.record_request_latency(endpoint, latency)
        
        p95 = self.guardrails.get_p95_latency(endpoint)
        assert p95 == 950.0  # 95th percentile of the data

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation"""
        endpoint = "/api/test"
        
        # Record 7 hits and 3 misses (70% hit rate)
        for _ in range(7):
            self.guardrails.record_cache_hit(endpoint)
        for _ in range(3):
            self.guardrails.record_cache_miss(endpoint)
        
        hit_rate = self.guardrails.get_cache_hit_rate(endpoint)
        assert hit_rate == 0.7

    @patch('psutil.Process')
    def test_memory_usage_mb(self, mock_process_class):
        """Test memory usage calculation"""
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 262144000  # 250MB in bytes
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process
        
        memory_mb = self.guardrails.get_memory_usage_mb()
        assert memory_mb == 250.0

    def test_budget_violations_trigger_degraded_mode(self):
        """Test that budget violations trigger degraded mode"""
        endpoint = "/api/test"
        
        # Simulate high latency violations
        for _ in range(10):
            self.guardrails.record_request_latency(endpoint, 800)  # > 600ms budget
        
        # Mock time to simulate violation duration
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 0, 130]  # 130 seconds = > 120 second threshold
            
            # First check establishes violation
            budgets = self.guardrails.check_budgets()
            self.guardrails.enforce_guardrails()
            
            # Second check triggers degraded mode
            budgets = self.guardrails.check_budgets()
            self.guardrails.enforce_guardrails()
            
            degraded = self.guardrails.is_degraded_mode()
            assert degraded['degraded'] == True
            assert 'latency' in degraded['reason'].lower()

    @patch('psutil.Process')
    def test_memory_budget_violation(self, mock_process_class):
        """Test memory budget violation triggers degraded mode"""
        mock_process = MagicMock()
        mock_memory_info = MagicMock()
        mock_memory_info.rss = 314572800  # 300MB > 250MB budget
        mock_process.memory_info.return_value = mock_memory_info
        mock_process_class.return_value = mock_process
        
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 0, 130]  # Simulate violation duration
            
            # Check budgets twice to trigger degraded mode
            budgets = self.guardrails.check_budgets()
            self.guardrails.enforce_guardrails()
            
            budgets = self.guardrails.check_budgets()
            self.guardrails.enforce_guardrails()
            
            degraded = self.guardrails.is_degraded_mode()
            assert degraded['degraded'] == True
            assert 'memory' in degraded['reason'].lower()

    def test_feature_flags_disabled_in_degraded_mode(self):
        """Test that features are disabled in degraded mode"""
        # Force degraded mode
        self.guardrails._enable_degraded_mode("Test degradation")
        
        # Check that features are disabled
        assert not self.guardrails.is_feature_enabled('charts_enabled')
        assert not self.guardrails.is_feature_enabled('agents_run_enabled')
        assert not self.guardrails.is_feature_enabled('enable_ai_agents')

    def test_degraded_mode_recovery(self):
        """Test recovery from degraded mode when budgets are met"""
        # Start in degraded mode
        self.guardrails._enable_degraded_mode("Test degradation")
        assert self.guardrails.is_degraded_mode()['degraded'] == True
        
        # Simulate good performance (empty violations)
        with patch.object(self.guardrails, 'check_budgets', return_value={'memory_ok': True, 'latency_ok': True, 'cache_ok': True}):
            self.guardrails.enforce_guardrails()
            
            degraded = self.guardrails.is_degraded_mode()
            assert degraded['degraded'] == False

    def test_performance_status_response(self):
        """Test performance status response structure"""
        status = self.guardrails.get_performance_status()
        
        assert 'budgets' in status
        assert 'degraded_mode' in status
        assert 'memory_mb' in status
        assert 'violations' in status
        assert 'timestamp' in status
        
        # Check degraded_mode structure
        degraded = status['degraded_mode']
        assert 'degraded' in degraded
        assert 'reason' in degraded

    def test_banner_flag_simulation(self):
        """Test that banner flag is properly set based on degraded mode"""
        # Normal mode - banner should not show
        degraded_status = self.guardrails.is_degraded_mode()
        assert degraded_status['degraded'] == False
        
        # Degraded mode - banner should show
        self.guardrails._enable_degraded_mode("High memory usage")
        degraded_status = self.guardrails.is_degraded_mode()
        assert degraded_status['degraded'] == True
        assert degraded_status['reason'] == "High memory usage"


# Integration tests for the guardrails system
class TestGuardrailsIntegration:
    
    def test_guardrails_api_endpoint_response(self):
        """Test the guardrails API endpoint returns proper structure"""
        from src.run_server import app
        
        with app.test_client() as client:
            response = client.get('/api/metrics/guardrails')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'degraded' in data
            assert 'reason' in data
            assert 'memory_mb' in data
            assert 'budgets' in data
            assert 'violations' in data
            assert 'timestamp' in data

    def test_metrics_collection_works(self):
        """Test that metrics are properly collected"""
        from src.core.metrics import metrics
        
        # Record some test metrics
        metrics.increment('requests_total_/api/test')
        metrics.increment('errors_total_/api/test')
        metrics.record_latency('/api/test', 250.0)
        
        collected_metrics = metrics.get_metrics()
        
        assert 'requests_total' in collected_metrics
        assert 'errors_total' in collected_metrics
        assert 'latency_p95_ms' in collected_metrics
        assert '/api/test' in collected_metrics['requests_total']
        assert collected_metrics['requests_total']['/api/test'] == 1
