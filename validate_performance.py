
#!/usr/bin/env python3
"""
Performance Validation Script
Tests performance budgets and metrics
"""

import sys
import time
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List
import statistics

# Add src to path
sys.path.insert(0, './src')

from src.common_repository.utils.telemetry import telemetry
from src.common_repository.cache.cache_manager import cache_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceValidator:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.results = {}
        
    async def test_endpoint_performance(self, endpoint: str, num_requests: int = 50, 
                                      concurrency: int = 10) -> Dict[str, float]:
        """Test endpoint performance with concurrent requests"""
        logger.info(f"Testing {endpoint} with {num_requests} requests, concurrency {concurrency}")
        
        async def make_request(session: aiohttp.ClientSession) -> float:
            start_time = time.time()
            try:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    await response.text()
                    return time.time() - start_time
            except Exception as e:
                logger.error(f"Request failed: {e}")
                return 0.0
                
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_request(session: aiohttp.ClientSession) -> float:
            async with semaphore:
                return await make_request(session)
                
        # Run concurrent requests
        connector = aiohttp.TCPConnector(limit=concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [limited_request(session) for _ in range(num_requests)]
            response_times = await asyncio.gather(*tasks)
            
        # Filter out failed requests (0.0 times)
        valid_times = [t for t in response_times if t > 0]
        
        if not valid_times:
            return {"p50": 0, "p95": 0, "avg": 0, "success_rate": 0}
            
        return {
            "p50": statistics.median(valid_times),
            "p95": statistics.quantiles(valid_times, n=20)[18],  # 95th percentile
            "avg": statistics.mean(valid_times),
            "success_rate": len(valid_times) / num_requests * 100
        }
        
    async def test_cache_performance(self) -> Dict[str, float]:
        """Test cache hit rate"""
        logger.info("Testing cache performance")
        
        # Make initial requests to populate cache
        connector = aiohttp.TCPConnector(limit=5)
        async with aiohttp.ClientSession(connector=connector) as session:
            # First round - populate cache
            endpoints = ["/api/stocks", "/api/options-strategies?timeframe=5D"]
            for endpoint in endpoints:
                for _ in range(3):
                    try:
                        async with session.get(f"{self.base_url}{endpoint}") as response:
                            await response.text()
                    except Exception:
                        pass
                        
        # Get cache stats
        cache_stats = cache_manager.get_stats()
        io_stats = telemetry.get_io_stats()
        
        return {
            "cache_hit_rate": io_stats.get("cache_hit_rate", 0),
            "cache_entries": cache_stats.get("memory_entries", 0),
            "cache_hits": io_stats.get("cache_hits", 0),
            "cache_misses": io_stats.get("cache_misses", 0)
        }
        
    async def check_memory_usage(self) -> Dict[str, float]:
        """Check memory usage"""
        logger.info("Checking memory usage")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health") as response:
                    health_data = await response.json()
                    
            memory_stats = telemetry.get_memory_stats()
            
            return {
                "rss_mb": memory_stats.get("memory_rss_mb", 0),
                "vms_mb": memory_stats.get("memory_vms_mb", 0),
                "gc_collections": memory_stats.get("gc_collections", 0)
            }
        except Exception as e:
            logger.error(f"Error checking memory: {e}")
            return {"rss_mb": 0, "vms_mb": 0, "gc_collections": 0}
            
    async def check_api_call_limits(self) -> Dict[str, float]:
        """Check API call rate limits"""
        logger.info("Checking API call limits")
        
        io_stats = telemetry.get_io_stats()
        
        return {
            "api_calls_per_min": io_stats.get("api_calls_per_min", 0),
            "failures_per_min": io_stats.get("failures_per_min", 0),
            "total_api_calls": io_stats.get("api_calls", 0)
        }
        
    def evaluate_budgets(self) -> Dict[str, bool]:
        """Evaluate if metrics meet budget requirements"""
        budgets = {}
        
        # Memory budget: < 250 MB steady-state
        memory_stats = self.results.get("memory", {})
        budgets["memory_under_budget"] = memory_stats.get("rss_mb", 0) < 250
        
        # API latency budget: P95 < 100ms for lightweight endpoints
        health_perf = self.results.get("performance", {}).get("/api/health", {})
        budgets["latency_under_budget"] = health_perf.get("p95", 0) < 0.1  # 100ms
        
        # Cache hit rate budget: >= 80%
        cache_stats = self.results.get("cache", {})
        budgets["cache_hit_rate_ok"] = cache_stats.get("cache_hit_rate", 0) >= 80
        
        # API call budget: <= 30/min
        api_stats = self.results.get("api_limits", {})
        budgets["api_calls_under_limit"] = api_stats.get("api_calls_per_min", 0) <= 30
        
        return budgets
        
    async def run_validation(self) -> bool:
        """Run full performance validation"""
        logger.info("Starting performance validation")
        
        try:
            # Test endpoint performance
            endpoints = ["/api/health", "/api/stocks", "/api/options-strategies?timeframe=5D"]
            performance_results = {}
            
            for endpoint in endpoints:
                perf_result = await self.test_endpoint_performance(endpoint)
                performance_results[endpoint] = perf_result
                
            self.results["performance"] = performance_results
            
            # Test cache performance
            self.results["cache"] = await self.test_cache_performance()
            
            # Check memory usage
            self.results["memory"] = await self.check_memory_usage()
            
            # Check API call limits
            self.results["api_limits"] = await self.check_api_call_limits()
            
            # Evaluate budgets
            budgets = self.evaluate_budgets()
            self.results["budgets"] = budgets
            
            # Print results
            self.print_results()
            
            # Return overall pass/fail
            return all(budgets.values())
            
        except Exception as e:
            logger.error(f"Validation failed with error: {e}")
            return False
            
    def print_results(self):
        """Print validation results"""
        print("\n" + "="*60)
        print("PERFORMANCE VALIDATION RESULTS")
        print("="*60)
        
        # Performance results
        print("\n📊 ENDPOINT PERFORMANCE:")
        for endpoint, stats in self.results.get("performance", {}).items():
            print(f"  {endpoint}:")
            print(f"    P50: {stats['p50']*1000:.1f}ms")
            print(f"    P95: {stats['p95']*1000:.1f}ms")
            print(f"    Success Rate: {stats['success_rate']:.1f}%")
            
        # Cache results
        print("\n🗂️ CACHE PERFORMANCE:")
        cache_stats = self.results.get("cache", {})
        print(f"  Hit Rate: {cache_stats.get('cache_hit_rate', 0):.1f}%")
        print(f"  Cache Entries: {cache_stats.get('cache_entries', 0)}")
        print(f"  Hits: {cache_stats.get('cache_hits', 0)}")
        print(f"  Misses: {cache_stats.get('cache_misses', 0)}")
        
        # Memory results
        print("\n💾 MEMORY USAGE:")
        memory_stats = self.results.get("memory", {})
        print(f"  RSS: {memory_stats.get('rss_mb', 0):.1f} MB")
        print(f"  VMS: {memory_stats.get('vms_mb', 0):.1f} MB")
        print(f"  GC Collections: {memory_stats.get('gc_collections', 0)}")
        
        # API limits
        print("\n🌐 API CALL LIMITS:")
        api_stats = self.results.get("api_limits", {})
        print(f"  Calls per minute: {api_stats.get('api_calls_per_min', 0):.1f}")
        print(f"  Failures per minute: {api_stats.get('failures_per_min', 0):.1f}")
        
        # Budget evaluation
        print("\n✅ BUDGET EVALUATION:")
        budgets = self.results.get("budgets", {})
        for budget_name, passed in budgets.items():
            status = "PASS" if passed else "FAIL"
            emoji = "✅" if passed else "❌"
            print(f"  {emoji} {budget_name}: {status}")
            
        # Overall result
        all_passed = all(budgets.values())
        overall_status = "PASS" if all_passed else "FAIL"
        overall_emoji = "🎉" if all_passed else "⚠️"
        
        print(f"\n{overall_emoji} OVERALL RESULT: {overall_status}")
        print("="*60)

async def main():
    """Main validation function"""
    validator = PerformanceValidator()
    
    try:
        success = await validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
