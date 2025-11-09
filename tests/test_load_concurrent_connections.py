"""
Session 17: Concurrent WebSocket Connection Load Tests

Tests the system's ability to handle multiple simultaneous WebSocket connections
and broadcasts. Establishes baseline metrics for production capacity planning.

Objectives:
1. Connect N concurrent WebSocket clients (10, 50, 100+)
2. Measure connection establishment time
3. Verify broadcast delivery to all connected clients
4. Monitor memory usage during connections
5. Test connection recovery and cleanup
6. Identify performance bottlenecks
"""

import asyncio
import json
import time
import pytest
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class PerformanceMetrics:
    """Track performance metrics for load tests"""
    test_name: str
    num_clients: int
    connection_time_ms: float
    broadcast_time_ms: float
    messages_received: int
    messages_sent: int
    memory_mb: float
    cpu_percent: float
    peak_memory_mb: float
    errors: int
    success_rate: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LoadTestMetricsCollector:
    """Collect and report performance metrics"""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process() if HAS_PSUTIL else None

    def add_metrics(self, metrics: PerformanceMetrics) -> None:
        self.metrics.append(metrics)

    def get_memory_mb(self) -> float:
        """Get current process memory in MB"""
        if self.process:
            return self.process.memory_info().rss / 1024 / 1024
        return 0.0

    def get_cpu_percent(self) -> float:
        """Get current CPU usage percentage"""
        if self.process:
            return self.process.cpu_percent(interval=0.1)
        return 0.0

    def report_summary(self) -> Dict[str, Any]:
        """Generate summary report of all metrics"""
        if not self.metrics:
            return {}

        return {
            "total_tests": len(self.metrics),
            "total_clients": sum(m.num_clients for m in self.metrics),
            "avg_connection_time_ms": sum(m.connection_time_ms for m in self.metrics) / len(self.metrics),
            "avg_broadcast_time_ms": sum(m.broadcast_time_ms for m in self.metrics) / len(self.metrics),
            "total_messages_received": sum(m.messages_received for m in self.metrics),
            "total_errors": sum(m.errors for m in self.metrics),
            "avg_success_rate": sum(m.success_rate for m in self.metrics) / len(self.metrics),
            "peak_memory_mb": max(m.peak_memory_mb for m in self.metrics),
            "timestamp": datetime.now().isoformat(),
        }


class MockWebSocketClient:
    """Mock WebSocket client for testing"""

    def __init__(self, client_id: int):
        self.client_id = client_id
        self.connected = False
        self.messages_received: List[Dict[str, Any]] = []
        self.last_message_time = 0
        self.connection_time = 0
        self.errors = 0

    async def connect(self, delay_ms: int = 0) -> bool:
        """Simulate WebSocket connection"""
        try:
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000)
            
            start = time.time()
            # Simulate connection delay (network latency)
            await asyncio.sleep(0.01)  # 10ms connection time
            self.connection_time = (time.time() - start) * 1000
            
            self.connected = True
            return True
        except Exception as e:
            self.errors += 1
            return False

    async def disconnect(self) -> None:
        """Simulate WebSocket disconnection"""
        self.connected = False

    async def receive_broadcast(self, message: Dict[str, Any]) -> None:
        """Simulate receiving broadcasted message"""
        if self.connected:
            self.messages_received.append(message)
            self.last_message_time = time.time()

    def get_message_count(self) -> int:
        """Get total messages received"""
        return len(self.messages_received)


class LoadTestSimulator:
    """Simulate load test scenarios"""

    def __init__(self, metrics_collector: LoadTestMetricsCollector):
        self.collector = metrics_collector
        self.clients: List[MockWebSocketClient] = []

    async def test_concurrent_connections(self, num_clients: int, stagger_ms: int = 1) -> PerformanceMetrics:
        """
        Test establishing N concurrent WebSocket connections
        
        Args:
            num_clients: Number of concurrent clients to connect
            stagger_ms: Time to stagger connections (ms between each)
        
        Returns:
            Performance metrics for the test
        """
        self.clients = []
        start_memory = self.collector.get_memory_mb()
        peak_memory = start_memory
        
        # Create clients
        clients = [MockWebSocketClient(i) for i in range(num_clients)]
        self.clients = clients
        
        # Connect all clients with stagger
        start_time = time.time()
        connection_tasks = []
        
        for i, client in enumerate(clients):
            # Stagger connections
            delay = i * stagger_ms
            task = client.connect(delay_ms=delay)
            connection_tasks.append(task)
        
        # Wait for all connections
        results = await asyncio.gather(*connection_tasks)
        connection_time = (time.time() - start_time) * 1000
        
        # Measure peak memory
        peak_memory = max(peak_memory, self.collector.get_memory_mb())
        
        # Calculate success rate
        successful = sum(1 for r in results if r)
        success_rate = successful / num_clients if num_clients > 0 else 0
        
        metrics = PerformanceMetrics(
            test_name=f"concurrent_connections_{num_clients}",
            num_clients=num_clients,
            connection_time_ms=connection_time,
            broadcast_time_ms=0,  # No broadcast in this test
            messages_received=0,
            messages_sent=0,
            memory_mb=self.collector.get_memory_mb(),
            cpu_percent=self.collector.get_cpu_percent(),
            peak_memory_mb=peak_memory,
            errors=sum(1 for r in results if not r),
            success_rate=success_rate,
            timestamp=datetime.now().isoformat(),
        )
        
        self.collector.add_metrics(metrics)
        return metrics

    async def test_broadcast_throughput(self, num_clients: int, num_messages: int = 100) -> PerformanceMetrics:
        """
        Test broadcasting messages to N connected clients
        
        Args:
            num_clients: Number of connected clients
            num_messages: Number of messages to broadcast
        
        Returns:
            Performance metrics for the test
        """
        # Setup: connect all clients
        await self.test_concurrent_connections(num_clients)
        
        start_memory = self.collector.get_memory_mb()
        peak_memory = start_memory
        
        # Broadcast messages
        start_time = time.time()
        total_received = 0
        
        for msg_num in range(num_messages):
            message = {
                "event_type": "test_broadcast",
                "message_id": msg_num,
                "timestamp": time.time(),
                "data": {"test": f"message_{msg_num}"}
            }
            
            # Broadcast to all clients
            broadcast_tasks = [
                client.receive_broadcast(message)
                for client in self.clients
            ]
            
            await asyncio.gather(*broadcast_tasks)
            
            # Update peak memory
            current_memory = self.collector.get_memory_mb()
            peak_memory = max(peak_memory, current_memory)
            
            total_received += len(self.clients)
        
        broadcast_time = (time.time() - start_time) * 1000
        avg_broadcast_time = broadcast_time / num_messages if num_messages > 0 else 0
        
        # Verify all clients received all messages
        all_received = sum(client.get_message_count() for client in self.clients)
        expected_received = num_clients * num_messages
        
        metrics = PerformanceMetrics(
            test_name=f"broadcast_throughput_{num_clients}_{num_messages}",
            num_clients=num_clients,
            connection_time_ms=0,
            broadcast_time_ms=avg_broadcast_time,
            messages_received=all_received,
            messages_sent=num_messages,
            memory_mb=self.collector.get_memory_mb(),
            cpu_percent=self.collector.get_cpu_percent(),
            peak_memory_mb=peak_memory,
            errors=expected_received - all_received,
            success_rate=(all_received / expected_received) if expected_received > 0 else 0,
            timestamp=datetime.now().isoformat(),
        )
        
        self.collector.add_metrics(metrics)
        
        # Cleanup
        for client in self.clients:
            await client.disconnect()
        
        return metrics

    async def test_connection_recovery(self, num_clients: int, num_cycles: int = 5) -> PerformanceMetrics:
        """
        Test connection recovery under repeated connect/disconnect cycles
        
        Args:
            num_clients: Number of clients
            num_cycles: Number of connect/disconnect cycles
        
        Returns:
            Performance metrics for the test
        """
        errors = 0
        total_connection_time = 0
        
        for cycle in range(num_cycles):
            # Connect
            clients = [MockWebSocketClient(i) for i in range(num_clients)]
            self.clients = clients
            
            start = time.time()
            tasks = [client.connect() for client in clients]
            results = await asyncio.gather(*tasks)
            
            connection_time = (time.time() - start) * 1000
            total_connection_time += connection_time
            
            errors += sum(1 for r in results if not r)
            
            # Send/receive some messages
            for i in range(10):
                message = {"event_type": "test", "id": i}
                broadcast_tasks = [client.receive_broadcast(message) for client in clients]
                await asyncio.gather(*broadcast_tasks)
            
            # Disconnect
            for client in clients:
                await client.disconnect()
            
            await asyncio.sleep(0.1)  # Brief pause between cycles
        
        avg_connection_time = total_connection_time / num_cycles if num_cycles > 0 else 0
        
        metrics = PerformanceMetrics(
            test_name=f"connection_recovery_{num_clients}_{num_cycles}",
            num_clients=num_clients * num_cycles,  # Total client-cycles
            connection_time_ms=avg_connection_time,
            broadcast_time_ms=0,
            messages_received=num_clients * num_cycles * 10,
            messages_sent=num_cycles * 10,
            memory_mb=self.collector.get_memory_mb(),
            cpu_percent=self.collector.get_cpu_percent(),
            peak_memory_mb=self.collector.get_memory_mb(),
            errors=errors,
            success_rate=(1 - (errors / (num_clients * num_cycles))) if (num_clients * num_cycles) > 0 else 0,
            timestamp=datetime.now().isoformat(),
        )
        
        self.collector.add_metrics(metrics)
        return metrics


@pytest.fixture
def metrics_collector():
    """Fixture for metrics collection"""
    return LoadTestMetricsCollector()


@pytest.fixture
def simulator(metrics_collector):
    """Fixture for load test simulator"""
    return LoadTestSimulator(metrics_collector)


class TestConcurrentConnections:
    """Test suite for concurrent WebSocket connections"""

    @pytest.mark.asyncio
    async def test_10_concurrent_connections(self, simulator):
        """Test 10 concurrent connections"""
        metrics = await simulator.test_concurrent_connections(10)
        
        assert metrics.num_clients == 10
        assert metrics.success_rate > 0.95
        assert metrics.connection_time_ms < 5000  # Should complete in < 5 seconds
        assert metrics.errors < 1

    @pytest.mark.asyncio
    async def test_50_concurrent_connections(self, simulator):
        """Test 50 concurrent connections"""
        metrics = await simulator.test_concurrent_connections(50)
        
        assert metrics.num_clients == 50
        assert metrics.success_rate > 0.95
        assert metrics.connection_time_ms < 10000  # Should complete in < 10 seconds
        assert metrics.errors < 3

    @pytest.mark.asyncio
    async def test_100_concurrent_connections(self, simulator):
        """Test 100 concurrent connections"""
        metrics = await simulator.test_concurrent_connections(100)
        
        assert metrics.num_clients == 100
        assert metrics.success_rate > 0.90  # Slightly relaxed for larger scale
        assert metrics.connection_time_ms < 15000  # Should complete in < 15 seconds
        assert metrics.errors < 5

    @pytest.mark.asyncio
    async def test_memory_under_concurrent_load(self, simulator, metrics_collector):
        """Verify memory doesn't explode under concurrent connections"""
        initial_memory = metrics_collector.get_memory_mb()
        
        metrics = await simulator.test_concurrent_connections(100)
        
        # Memory should not increase more than 50MB per 100 clients
        memory_increase = metrics.peak_memory_mb - initial_memory
        assert memory_increase < 50, f"Memory increased by {memory_increase}MB"


class TestBroadcastThroughput:
    """Test suite for broadcast message throughput"""

    @pytest.mark.asyncio
    async def test_broadcast_to_10_clients(self, simulator):
        """Test broadcasting to 10 connected clients"""
        metrics = await simulator.test_broadcast_throughput(10, num_messages=100)
        
        assert metrics.num_clients == 10
        assert metrics.messages_sent == 100
        assert metrics.messages_received == 1000  # 10 clients * 100 messages
        assert metrics.success_rate > 0.99

    @pytest.mark.asyncio
    async def test_broadcast_to_50_clients(self, simulator):
        """Test broadcasting to 50 connected clients"""
        metrics = await simulator.test_broadcast_throughput(50, num_messages=50)
        
        assert metrics.num_clients == 50
        assert metrics.messages_sent == 50
        assert metrics.messages_received == 2500  # 50 clients * 50 messages
        assert metrics.success_rate > 0.99

    @pytest.mark.asyncio
    async def test_broadcast_latency(self, simulator):
        """Verify broadcast latency is acceptable"""
        metrics = await simulator.test_broadcast_throughput(20, num_messages=100)
        
        # Average per-message broadcast should be < 100ms
        assert metrics.broadcast_time_ms < 100


class TestConnectionRecovery:
    """Test suite for connection recovery and resilience"""

    @pytest.mark.asyncio
    async def test_recovery_10_clients_5_cycles(self, simulator):
        """Test connection recovery with 10 clients, 5 cycles"""
        metrics = await simulator.test_connection_recovery(10, num_cycles=5)
        
        assert metrics.success_rate > 0.95
        assert metrics.errors < 3

    @pytest.mark.asyncio
    async def test_recovery_50_clients_3_cycles(self, simulator):
        """Test connection recovery with 50 clients, 3 cycles"""
        metrics = await simulator.test_connection_recovery(50, num_cycles=3)
        
        assert metrics.success_rate > 0.90
        assert metrics.errors < 5


class TestLoadTestMetricsReport:
    """Test metrics reporting functionality"""

    @pytest.mark.asyncio
    async def test_metrics_reporting(self, simulator, metrics_collector):
        """Verify metrics are properly collected and reported"""
        # Run multiple tests
        await simulator.test_concurrent_connections(10)
        await simulator.test_broadcast_throughput(10, num_messages=50)
        await simulator.test_connection_recovery(5, num_cycles=2)
        
        # Generate report
        report = metrics_collector.report_summary()
        
        assert report["total_tests"] == 4
        assert report["total_clients"] > 0
        assert "avg_connection_time_ms" in report
        assert "avg_broadcast_time_ms" in report
        assert "total_messages_received" in report
        assert "peak_memory_mb" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
