"""
Session 17: Live HTTP Endpoint Load Testing

Real load tests against the deployed backend at http://localhost:8000
Measures actual performance metrics from the running system.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import pytest
import aiohttp


@dataclass
class LiveEndpointMetrics:
    """Metrics from real endpoint testing"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    response_times_ms: List[float]
    min_ms: float
    max_ms: float
    median_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    rps: float
    error_rate: float
    timestamp: str


class LiveHTTPLoadTester:
    """Test real backend endpoints"""

    BASE_URL = "http://localhost:8000"
    HEALTH_CHECK_URL = f"{BASE_URL}/health"

    @staticmethod
    async def health_check() -> bool:
        """Verify backend is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(LiveHTTPLoadTester.HEALTH_CHECK_URL, timeout=5) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    @staticmethod
    async def load_test_endpoint(
        endpoint: str,
        method: str = "GET",
        params: Dict[str, Any] = None,
        duration_seconds: int = 10,
        concurrent_requests: int = 5,
    ) -> LiveEndpointMetrics:
        """
        Load test a single endpoint
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST)
            params: Query parameters or request body
            duration_seconds: How long to run test
            concurrent_requests: Number of concurrent requests
        """
        url = f"{LiveHTTPLoadTester.BASE_URL}{endpoint}"
        response_times = []
        successful = 0
        failed = 0
        start_time = time.time()

        async def make_request(session):
            nonlocal successful, failed
            try:
                req_start = time.time()
                if method == "GET":
                    async with session.get(url, params=params, timeout=30) as resp:
                        await resp.read()
                        if resp.status == 200:
                            successful += 1
                        else:
                            failed += 1
                else:  # POST
                    async with session.post(url, json=params, timeout=30) as resp:
                        await resp.read()
                        if resp.status == 200:
                            successful += 1
                        else:
                            failed += 1
                
                response_time = (time.time() - req_start) * 1000
                response_times.append(response_time)
            except Exception as e:
                failed += 1
                response_times.append(0)

        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration_seconds:
                tasks = [make_request(session) for _ in range(concurrent_requests)]
                await asyncio.gather(*tasks)

        total_time = time.time() - start_time
        total_requests = successful + failed
        
        if response_times:
            sorted_times = sorted(response_times)
            p95_idx = int(len(sorted_times) * 0.95)
            p99_idx = int(len(sorted_times) * 0.99)
        else:
            sorted_times = []
            p95_idx = 0
            p99_idx = 0

        return LiveEndpointMetrics(
            endpoint=endpoint,
            method=method,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=failed,
            response_times_ms=response_times,
            min_ms=min(response_times) if response_times else 0,
            max_ms=max(response_times) if response_times else 0,
            median_ms=statistics.median(response_times) if response_times else 0,
            p95_ms=sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0,
            p99_ms=sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0,
            mean_ms=statistics.mean(response_times) if response_times else 0,
            rps=total_requests / total_time,
            error_rate=failed / total_requests if total_requests > 0 else 0,
            timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def print_metrics(metrics: LiveEndpointMetrics):
        """Print formatted metrics"""
        print(f"\n{'='*70}")
        print(f"Endpoint: {metrics.method} {metrics.endpoint}")
        print(f"{'='*70}")
        print(f"Total requests:     {metrics.total_requests}")
        print(f"Successful:         {metrics.successful_requests}")
        print(f"Failed:             {metrics.failed_requests} ({metrics.error_rate*100:.1f}%)")
        print(f"Throughput:         {metrics.rps:.1f} req/sec")
        print(f"\nResponse Times:")
        print(f"  Min:              {metrics.min_ms:.2f}ms")
        print(f"  Median:           {metrics.median_ms:.2f}ms")
        print(f"  Mean:             {metrics.mean_ms:.2f}ms")
        print(f"  p95:              {metrics.p95_ms:.2f}ms")
        print(f"  p99:              {metrics.p99_ms:.2f}ms")
        print(f"  Max:              {metrics.max_ms:.2f}ms")
        print(f"{'='*70}\n")


class TestLiveHTTPLoad:
    """Test real backend performance"""

    @pytest.mark.asyncio
    async def test_backend_health(self):
        """Verify backend is running and healthy"""
        is_healthy = await LiveHTTPLoadTester.health_check()
        assert is_healthy, "Backend at http://localhost:8000 is not responding"

    @pytest.mark.asyncio
    async def test_stats_endpoint_performance(self):
        """Load test /api/graph/stats endpoint"""
        metrics = await LiveHTTPLoadTester.load_test_endpoint(
            "/api/graph/stats",
            method="GET",
            concurrent_requests=10,
            duration_seconds=10,
        )
        LiveHTTPLoadTester.print_metrics(metrics)
        
        assert metrics.error_rate < 0.05, f"Error rate {metrics.error_rate} too high"
        assert metrics.rps > 20, f"Throughput {metrics.rps} too low"
        assert metrics.p95_ms < 500, f"p95 latency {metrics.p95_ms} too high"

    @pytest.mark.asyncio
    async def test_category_hubs_performance(self):
        """Load test /api/graph/categories/hubs endpoint"""
        metrics = await LiveHTTPLoadTester.load_test_endpoint(
            "/api/graph/categories/hubs",
            method="GET",
            params={"limit": 20},
            concurrent_requests=10,
            duration_seconds=10,
        )
        LiveHTTPLoadTester.print_metrics(metrics)
        
        assert metrics.error_rate < 0.05
        assert metrics.rps > 10
        assert metrics.p95_ms < 1000

    @pytest.mark.asyncio
    async def test_concurrent_scaling(self):
        """Test performance under increasing load"""
        print("\n\nTesting Concurrent Load Scaling:")
        
        for concurrent in [5, 10, 20, 50]:
            metrics = await LiveHTTPLoadTester.load_test_endpoint(
                "/api/graph/stats",
                concurrent_requests=concurrent,
                duration_seconds=5,
            )
            print(f"\nConcurrent={concurrent:2d}: {metrics.rps:6.1f} req/s, p95={metrics.p95_ms:7.2f}ms, errors={metrics.failed_requests:3d}")
            
            assert metrics.error_rate < 0.10, f"Error rate too high at {concurrent} concurrent"

    @pytest.mark.asyncio
    async def test_endpoint_comparison(self):
        """Compare performance across different endpoints"""
        endpoints = [
            ("/api/graph/stats", "GET", None),
            ("/api/graph/categories/hubs", "GET", {"limit": 20}),
            ("/api/graph/categories/entry_points", "GET", {"limit": 20}),
        ]
        
        print("\n\nEndpoint Performance Comparison:")
        print(f"{'Endpoint':<40} {'RPS':>8} {'p95ms':>8} {'Errors':>8}")
        print("-" * 65)
        
        for endpoint, method, params in endpoints:
            metrics = await LiveHTTPLoadTester.load_test_endpoint(
                endpoint,
                method=method,
                params=params,
                concurrent_requests=5,
                duration_seconds=5,
            )
            print(f"{endpoint:<40} {metrics.rps:8.1f} {metrics.p95_ms:8.2f} {metrics.error_rate*100:7.1f}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
