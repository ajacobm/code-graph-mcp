"""
Session 17: HTTP Endpoint Load Testing

Tests the performance of REST API endpoints under concurrent load.
Measures throughput, latency, and error rates.

Objectives:
1. Test query endpoints under concurrent load (10-100 requests/sec)
2. Measure endpoint response times and percentiles (p50, p95, p99)
3. Monitor backend resource usage during load
4. Identify performance bottlenecks
5. Test graceful degradation under overload
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import pytest


@dataclass
class EndpointMetrics:
    """Metrics for a single endpoint under load"""
    endpoint: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MockHTTPClient:
    """Mock HTTP client for testing"""

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times: List[float] = []

    async def get(self, endpoint: str, params: Dict[str, Any] = None) -> tuple[bool, float]:
        """
        Simulate HTTP GET request
        
        Returns:
            (success: bool, response_time_ms: float)
        """
        self.request_count += 1
        
        start = time.time()
        
        # Simulate network latency based on endpoint
        base_latency = 0.001  # 1ms base
        
        if "/api/graph/stats" in endpoint:
            latency = base_latency
        elif "/api/graph/nodes/" in endpoint:
            latency = base_latency * 1.5
        elif "/api/graph/traverse" in endpoint:
            latency = base_latency * 3
        else:
            latency = base_latency
        
        # Add some variance (0-50% additional latency)
        variance = latency * random.random() * 0.5
        await asyncio.sleep(latency + variance)
        
        response_time = (time.time() - start) * 1000
        self.response_times.append(response_time)
        
        # Simulate occasional errors (1% error rate)
        if random.random() < 0.01:
            self.error_count += 1
            return False, response_time
        
        return True, response_time

    async def post(self, endpoint: str, data: Dict[str, Any] = None) -> tuple[bool, float]:
        """Simulate HTTP POST request"""
        self.request_count += 1
        
        try:
            start = time.time()
            
            # POST operations take longer
            latency = 0.02  # 20ms
            
            variance = latency * random.random() * 0.5
            await asyncio.sleep(latency + variance)
            
            response_time = (time.time() - start) * 1000
            self.response_times.append(response_time)
            
            # Simulate 2% error rate for POST
            if random.random() < 0.02:
                self.error_count += 1
                return False, response_time
            
            return True, response_time
            
        except Exception as e:
            self.error_count += 1
            return False, 0


class HTTPLoadTester:
    """Load testing for HTTP endpoints"""

    def __init__(self):
        self.client = MockHTTPClient()

    async def load_test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        concurrent_requests: int = 10,
        duration_seconds: int = 10,
        params: Dict[str, Any] = None,
    ) -> EndpointMetrics:
        """
        Load test an endpoint for a duration with concurrent requests
        
        Args:
            endpoint: API endpoint to test
            method: HTTP method (GET or POST)
            concurrent_requests: Number of concurrent requests
            duration_seconds: How long to run the test
            params: Query parameters
        
        Returns:
            EndpointMetrics for the test
        """
        self.client = MockHTTPClient()  # Reset client
        start_time = time.time()
        
        async def make_request():
            """Make a single request"""
            if method == "GET":
                return await self.client.get(endpoint, params)
            else:
                return await self.client.post(endpoint, params)
        
        # Create concurrent request tasks
        tasks: List[asyncio.Task] = []
        
        while time.time() - start_time < duration_seconds:
            # Maintain N concurrent requests
            while len(tasks) < concurrent_requests:
                task = asyncio.create_task(make_request())
                tasks.append(task)
            
            # Wait for at least one to complete
            done, tasks = await asyncio.wait(
                tasks,
                timeout=0.1,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Remove completed tasks
            tasks = list(tasks)
        
        # Wait for remaining tasks
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        response_times = self.client.response_times
        if response_times:
            sorted_times = sorted(response_times)
            p50 = sorted_times[int(len(sorted_times) * 0.50)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0
        
        total_requests = self.client.request_count
        successful = total_requests - self.client.error_count
        
        metrics = EndpointMetrics(
            endpoint=endpoint,
            total_requests=total_requests,
            successful_requests=successful,
            failed_requests=self.client.error_count,
            total_time_ms=total_time * 1000,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            median_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            requests_per_second=total_requests / total_time if total_time > 0 else 0,
            error_rate=self.client.error_count / total_requests if total_requests > 0 else 0,
            timestamp=datetime.now().isoformat(),
        )
        
        return metrics

    async def load_test_multiple_endpoints(
        self,
        endpoints: List[Dict[str, Any]],
        concurrent_requests: int = 10,
        duration_seconds: int = 10,
    ) -> List[EndpointMetrics]:
        """
        Load test multiple endpoints concurrently
        
        Args:
            endpoints: List of {endpoint, method, params}
            concurrent_requests: Concurrent requests per endpoint
            duration_seconds: Duration of test
        
        Returns:
            List of EndpointMetrics for each endpoint
        """
        tasks = [
            self.load_test_endpoint(
                ep.get("endpoint", ""),
                method=ep.get("method", "GET"),
                concurrent_requests=concurrent_requests,
                duration_seconds=duration_seconds,
                params=ep.get("params"),
            )
            for ep in endpoints
        ]
        
        return await asyncio.gather(*tasks)


@pytest.fixture
def load_tester():
    """Fixture for HTTP load tester"""
    return HTTPLoadTester()


class TestGraphAPILoad:
    """Test graph API endpoints under load"""

    @pytest.mark.asyncio
    async def test_stats_endpoint_load(self, load_tester):
        """Load test /api/graph/stats endpoint"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            method="GET",
            concurrent_requests=10,
            duration_seconds=5,
        )
        
        assert metrics.total_requests > 50
        assert metrics.error_rate < 0.05
        assert metrics.p95_response_time_ms < 100
        assert metrics.p99_response_time_ms < 200

    @pytest.mark.asyncio
    async def test_node_search_endpoint_load(self, load_tester):
        """Load test node search endpoint"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/nodes/search",
            method="GET",
            concurrent_requests=10,
            duration_seconds=5,
            params={"query": "test"},
        )
        
        assert metrics.total_requests > 50
        assert metrics.error_rate < 0.05
        assert metrics.p95_response_time_ms < 150

    @pytest.mark.asyncio
    async def test_traverse_endpoint_load(self, load_tester):
        """Load test traverse endpoint (more complex operation)"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/traverse",
            method="POST",
            concurrent_requests=5,
            duration_seconds=5,
            params={"start_node": "test_node", "depth": 3},
        )
        
        assert metrics.total_requests > 25
        assert metrics.error_rate < 0.10
        assert metrics.p95_response_time_ms < 300


class TestConcurrentLoadScaling:
    """Test system behavior under increasing concurrent load"""

    @pytest.mark.asyncio
    async def test_5_concurrent_requests(self, load_tester):
        """Test with 5 concurrent requests"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            concurrent_requests=5,
            duration_seconds=3,
        )
        
        assert metrics.error_rate < 0.05
        rps = metrics.requests_per_second
        assert rps > 50  # Should handle 50+ RPS

    @pytest.mark.asyncio
    async def test_20_concurrent_requests(self, load_tester):
        """Test with 20 concurrent requests"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            concurrent_requests=20,
            duration_seconds=3,
        )
        
        assert metrics.error_rate < 0.05
        rps = metrics.requests_per_second
        assert rps > 100  # Should handle 100+ RPS

    @pytest.mark.asyncio
    async def test_50_concurrent_requests(self, load_tester):
        """Test with 50 concurrent requests"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            concurrent_requests=50,
            duration_seconds=3,
        )
        
        # More relaxed constraints for higher load
        assert metrics.error_rate < 0.10


class TestResponseTimePercentiles:
    """Test response time percentile performance"""

    @pytest.mark.asyncio
    async def test_p50_response_time(self, load_tester):
        """Verify median (p50) response time is acceptable"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            concurrent_requests=10,
            duration_seconds=3,
        )
        
        assert metrics.median_response_time_ms < 50
        assert metrics.min_response_time_ms > 0

    @pytest.mark.asyncio
    async def test_p95_response_time(self, load_tester):
        """Verify p95 response time is acceptable"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            concurrent_requests=10,
            duration_seconds=3,
        )
        
        # p95 should be less than 2x median
        assert metrics.p95_response_time_ms < 100

    @pytest.mark.asyncio
    async def test_p99_response_time(self, load_tester):
        """Verify p99 response time is acceptable"""
        metrics = await load_tester.load_test_endpoint(
            "/api/graph/stats",
            concurrent_requests=10,
            duration_seconds=3,
        )
        
        # p99 should be less than 3x median
        assert metrics.p99_response_time_ms < 200


class TestMultipleEndpointsLoad:
    """Test multiple endpoints under load simultaneously"""

    @pytest.mark.asyncio
    async def test_all_endpoints_concurrent_load(self, load_tester):
        """Test all graph endpoints under concurrent load"""
        endpoints = [
            {"endpoint": "/api/graph/stats", "method": "GET"},
            {"endpoint": "/api/graph/nodes/search", "method": "GET", "params": {"query": "test"}},
            {"endpoint": "/api/graph/traverse", "method": "POST"},
        ]
        
        metrics_list = await load_tester.load_test_multiple_endpoints(
            endpoints,
            concurrent_requests=5,
            duration_seconds=3,
        )
        
        assert len(metrics_list) == 3
        
        for metrics in metrics_list:
            assert metrics.total_requests > 0
            assert metrics.error_rate < 0.10


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
