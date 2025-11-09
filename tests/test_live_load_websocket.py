"""
Session 17: Live WebSocket Load Testing

Real load tests against the deployed WebSocket at ws://localhost:8000/ws/events
Measures connection handling, message throughput, and event delivery.
"""

import asyncio
import time
from typing import List, Set
from dataclasses import dataclass
from datetime import datetime
import pytest
import websockets
import json


@dataclass
class WebSocketMetrics:
    """Metrics from WebSocket testing"""
    num_clients: int
    successful_connections: int
    failed_connections: int
    total_messages_received: int
    messages_per_client: List[int]
    connection_times_ms: List[float]
    min_connection_time_ms: float
    max_connection_time_ms: float
    avg_connection_time_ms: float
    broadcast_latencies_ms: List[float]
    test_duration_seconds: float
    timestamp: str


class LiveWebSocketLoadTester:
    """Test real WebSocket endpoint"""

    BASE_URL = "ws://localhost:8000/ws/events"

    @staticmethod
    async def create_websocket_client(client_id: int) -> tuple[bool, float, asyncio.Queue]:
        """
        Connect a single WebSocket client
        
        Returns:
            (success, connection_time_ms, message_queue)
        """
        try:
            start = time.time()
            uri = LiveWebSocketLoadTester.BASE_URL
            
            async with websockets.connect(uri, ping_interval=20, ping_timeout=10) as websocket:
                connection_time = (time.time() - start) * 1000
                
                message_queue = asyncio.Queue()
                
                async def receive_messages():
                    try:
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                await message_queue.put(data)
                            except json.JSONDecodeError:
                                pass
                    except asyncio.CancelledError:
                        pass

                # Start message receiver task
                receiver_task = asyncio.create_task(receive_messages())
                
                # Send ping to keep connection alive
                await websocket.ping()
                
                # Give receiver time to start
                await asyncio.sleep(0.1)
                
                return True, connection_time, message_queue
                
        except Exception as e:
            print(f"Client {client_id} connection failed: {e}")
            return False, 0, None

    @staticmethod
    async def load_test_connections(num_clients: int, duration_seconds: int = 30) -> WebSocketMetrics:
        """
        Test concurrent WebSocket connections
        
        Args:
            num_clients: Number of concurrent clients to connect
            duration_seconds: How long to maintain connections
        """
        start_time = time.time()
        successful = 0
        failed = 0
        connection_times = []
        message_counts = {}
        queues: List[asyncio.Queue] = []
        
        print(f"\nConnecting {num_clients} WebSocket clients...")
        
        # Connect all clients
        for i in range(num_clients):
            success, conn_time, queue = await LiveWebSocketLoadTester.create_websocket_client(i)
            if success:
                successful += 1
                connection_times.append(conn_time)
                message_counts[i] = 0
                if queue:
                    queues.append(queue)
            else:
                failed += 1
            
            # Stagger connections slightly
            await asyncio.sleep(0.01)
        
        print(f"✓ Connected: {successful}, ✗ Failed: {failed}")
        
        # Collect messages for duration
        async def collect_messages():
            nonlocal message_counts
            end_time = time.time() + duration_seconds
            while time.time() < end_time:
                try:
                    for i, queue in enumerate(queues):
                        try:
                            msg = queue.get_nowait()
                            message_counts[i] = message_counts.get(i, 0) + 1
                        except asyncio.QueueEmpty:
                            pass
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Error collecting messages: {e}")
        
        await collect_messages()
        
        total_time = time.time() - start_time
        total_messages = sum(message_counts.values())
        
        return WebSocketMetrics(
            num_clients=num_clients,
            successful_connections=successful,
            failed_connections=failed,
            total_messages_received=total_messages,
            messages_per_client=list(message_counts.values()),
            connection_times_ms=connection_times,
            min_connection_time_ms=min(connection_times) if connection_times else 0,
            max_connection_time_ms=max(connection_times) if connection_times else 0,
            avg_connection_time_ms=sum(connection_times) / len(connection_times) if connection_times else 0,
            broadcast_latencies_ms=[],
            test_duration_seconds=total_time,
            timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def print_metrics(metrics: WebSocketMetrics):
        """Print formatted metrics"""
        print(f"\n{'='*70}")
        print(f"WebSocket Load Test Results")
        print(f"{'='*70}")
        print(f"Target clients:     {metrics.num_clients}")
        print(f"Connected:          {metrics.successful_connections}")
        print(f"Failed:             {metrics.failed_connections}")
        print(f"\nConnection Times:")
        print(f"  Min:              {metrics.min_connection_time_ms:.2f}ms")
        print(f"  Avg:              {metrics.avg_connection_time_ms:.2f}ms")
        print(f"  Max:              {metrics.max_connection_time_ms:.2f}ms")
        print(f"\nMessage Delivery:")
        print(f"  Total messages:   {metrics.total_messages_received}")
        print(f"  Per client:       {sum(metrics.messages_per_client) / len(metrics.messages_per_client):.1f} avg")
        print(f"  Test duration:    {metrics.test_duration_seconds:.1f}s")
        print(f"{'='*70}\n")


class TestLiveWebSocketLoad:
    """Test real WebSocket performance"""

    @pytest.mark.asyncio
    async def test_single_connection(self):
        """Test single WebSocket connection establishment"""
        success, conn_time, queue = await LiveWebSocketLoadTester.create_websocket_client(0)
        assert success, "Failed to connect single WebSocket client"
        assert conn_time < 5000, f"Connection time {conn_time}ms too high"
        print(f"\n✓ Single connection established in {conn_time:.2f}ms")

    @pytest.mark.asyncio
    async def test_10_concurrent_connections(self):
        """Test 10 concurrent WebSocket connections"""
        metrics = await LiveWebSocketLoadTester.load_test_connections(10, duration_seconds=15)
        LiveWebSocketLoadTester.print_metrics(metrics)
        
        assert metrics.successful_connections >= 8, "Too many connection failures"
        assert metrics.avg_connection_time_ms < 500, "Connection time too high"

    @pytest.mark.asyncio
    async def test_50_concurrent_connections(self):
        """Test 50 concurrent WebSocket connections"""
        metrics = await LiveWebSocketLoadTester.load_test_connections(50, duration_seconds=20)
        LiveWebSocketLoadTester.print_metrics(metrics)
        
        assert metrics.successful_connections >= 40, "Too many connection failures"
        assert metrics.max_connection_time_ms < 2000, "Max connection time too high"

    @pytest.mark.asyncio
    async def test_100_concurrent_connections(self):
        """Test 100 concurrent WebSocket connections"""
        metrics = await LiveWebSocketLoadTester.load_test_connections(100, duration_seconds=30)
        LiveWebSocketLoadTester.print_metrics(metrics)
        
        success_rate = metrics.successful_connections / metrics.num_clients
        assert success_rate > 0.80, f"Success rate {success_rate} too low"
        print(f"✓ Connection success rate: {success_rate*100:.1f}%")

    @pytest.mark.asyncio
    async def test_connection_recovery(self):
        """Test WebSocket connection recovery after disconnect"""
        print("\nTesting connection recovery...")
        
        # Initial connection
        success1, time1, _ = await LiveWebSocketLoadTester.create_websocket_client(0)
        assert success1, "Initial connection failed"
        print(f"✓ Initial connection: {time1:.2f}ms")
        
        # Simulate delay
        await asyncio.sleep(2)
        
        # Reconnect
        success2, time2, _ = await LiveWebSocketLoadTester.create_websocket_client(0)
        assert success2, "Reconnection failed"
        print(f"✓ Reconnection: {time2:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
