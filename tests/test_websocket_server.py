"""
Tests for WebSocket real-time event streaming.

Tests covering:
- WebSocket connection management
- Message broadcasting
- Event filtering
- Connection lifecycle
"""

import asyncio
import json
from typing import AsyncGenerator, Dict, List

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.codenav.websocket_server import (
    create_websocket_router,
    WebSocketConnectionManager,
)


@pytest_asyncio.fixture
async def connection_manager() -> WebSocketConnectionManager:
    """Create a WebSocket connection manager."""
    return WebSocketConnectionManager()


@pytest_asyncio.fixture
def app_with_websocket(connection_manager) -> FastAPI:
    """Create FastAPI app with WebSocket router."""
    app = FastAPI()
    router = create_websocket_router()
    # Override the manager in router with our test manager
    router.ws_manager = connection_manager  # type: ignore
    app.include_router(router)
    return app


@pytest_asyncio.fixture
def client(app_with_websocket):
    """Create test client."""
    return TestClient(app_with_websocket)


class TestWebSocketConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, connection_manager):
        """Test connection manager initializes properly."""
        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast_empty_connections(self, connection_manager):
        """Test broadcasting with no connections doesn't crash."""
        await connection_manager.broadcast({"type": "test"})
        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connection_manager):
        """Test connecting and disconnecting."""
        # Create a mock websocket
        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                pass

        ws = MockWebSocket()  # type: ignore
        await connection_manager.connect(ws)
        assert connection_manager.get_connection_count() == 1

        await connection_manager.disconnect(ws)
        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_multiple_connections(self, connection_manager):
        """Test managing multiple concurrent connections."""

        class MockWebSocket:
            def __init__(self, name):
                self.name = name

            async def accept(self):
                pass

            async def send_json(self, data):
                pass

        # Connect multiple
        sockets = [MockWebSocket(f"ws_{i}") for i in range(5)]  # type: ignore
        for ws in sockets:
            await connection_manager.connect(ws)

        assert connection_manager.get_connection_count() == 5

        # Disconnect some
        await connection_manager.disconnect(sockets[0])
        await connection_manager.disconnect(sockets[2])

        assert connection_manager.get_connection_count() == 3

    @pytest.mark.asyncio
    async def test_broadcast_to_all_connections(self, connection_manager):
        """Test broadcasting message to all connected clients."""
        received_messages: List[Dict] = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                received_messages.append(data)

        # Connect multiple clients
        sockets = [MockWebSocket() for _ in range(3)]  # type: ignore
        for ws in sockets:
            await connection_manager.connect(ws)

        # Broadcast message
        test_message = {"type": "event", "data": "test"}
        await connection_manager.broadcast(test_message)

        assert len(received_messages) == 3
        assert all(msg == test_message for msg in received_messages)

    @pytest.mark.asyncio
    async def test_send_to_specific_client(self, connection_manager):
        """Test sending message to specific client."""

        class MockWebSocket:
            def __init__(self):
                self.received_messages = []

            async def accept(self):
                pass

            async def send_json(self, data):
                self.received_messages.append(data)

        ws1 = MockWebSocket()  # type: ignore
        ws2 = MockWebSocket()  # type: ignore

        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)

        # Send to specific client
        test_message = {"type": "personal"}
        await connection_manager.send_to_client(ws1, test_message)

        assert len(ws1.received_messages) == 1
        assert len(ws2.received_messages) == 0

    @pytest.mark.asyncio
    async def test_handle_dead_connections(self, connection_manager):
        """Test that dead connections are cleaned up."""

        class MockWebSocket:
            def __init__(self, should_fail=False):
                self.should_fail = should_fail

            async def accept(self):
                pass

            async def send_json(self, data):
                if self.should_fail:
                    raise Exception("Connection dead")

        # Connect multiple including dead one
        ws_good = MockWebSocket()  # type: ignore
        ws_dead = MockWebSocket(should_fail=True)  # type: ignore

        await connection_manager.connect(ws_good)
        await connection_manager.connect(ws_dead)

        assert connection_manager.get_connection_count() == 2

        # Broadcast will fail on dead connection and remove it
        await connection_manager.broadcast({"type": "test"})

        # Dead connection should be removed
        assert connection_manager.get_connection_count() == 1


class TestWebSocketEndpoints:
    """Test WebSocket HTTP endpoints."""

    def test_websocket_status_endpoint(self, client):
        """Test /ws/status endpoint returns connection count."""
        response = client.get("/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data
        assert "status" in data
        assert data["status"] == "healthy"


class TestWebSocketMessaging:
    """Test WebSocket message handling."""

    @pytest.mark.asyncio
    async def test_ping_pong(self, connection_manager):
        """Test ping/pong keep-alive mechanism."""

        class MockWebSocket:
            def __init__(self):
                self.received_messages = []

            async def accept(self):
                pass

            async def send_json(self, data):
                self.received_messages.append(data)

            async def receive_text(self):
                return "ping"

        ws = MockWebSocket()  # type: ignore
        await connection_manager.send_to_client(ws, {"type": "pong"})
        assert len(ws.received_messages) == 1
        assert ws.received_messages[0]["type"] == "pong"

    @pytest.mark.asyncio
    async def test_event_message_format(self, connection_manager):
        """Test CDC event is formatted correctly for WebSocket."""

        class MockWebSocket:
            def __init__(self):
                self.received_messages = []

            async def accept(self):
                pass

            async def send_json(self, data):
                self.received_messages.append(data)

        ws = MockWebSocket()  # type: ignore
        await connection_manager.connect(ws)

        # Broadcast CDC-like event
        event = {
            "type": "cdc_event",
            "event_type": "node_added",
            "entity_id": "node_001",
            "entity_type": "node",
            "timestamp": "2025-11-08T12:00:00Z",
        }

        await connection_manager.broadcast(event)

        assert len(ws.received_messages) == 1
        assert ws.received_messages[0]["type"] == "cdc_event"
        assert ws.received_messages[0]["event_type"] == "node_added"


class TestWebSocketEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(self, connection_manager):
        """Test concurrent connect/disconnect operations."""

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                pass

        async def connect_and_disconnect(name):
            ws = MockWebSocket()  # type: ignore
            await connection_manager.connect(ws)
            await asyncio.sleep(0.001)
            await connection_manager.disconnect(ws)

        # Run concurrent operations
        await asyncio.gather(*[connect_and_disconnect(f"ws_{i}") for i in range(10)])

        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_connection(self, connection_manager):
        """Test disconnecting connection that was never connected."""

        class MockWebSocket:
            pass

        ws = MockWebSocket()  # type: ignore
        # Should not raise error
        await connection_manager.disconnect(ws)
        assert connection_manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_send_to_disconnected_client(self, connection_manager):
        """Test sending to disconnected client removes it."""

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                raise Exception("Already disconnected")

        ws = MockWebSocket()  # type: ignore
        await connection_manager.connect(ws)
        assert connection_manager.get_connection_count() == 1

        # Try to send to disconnected client
        await connection_manager.send_to_client(ws, {"type": "test"})

        # Should be removed after error
        assert connection_manager.get_connection_count() == 0


class TestWebSocketEventFlows:
    """Test real-world event flow scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_event_broadcast(self, connection_manager):
        """Test broadcasting multiple events in sequence."""

        class MockWebSocket:
            def __init__(self):
                self.received_messages = []

            async def accept(self):
                pass

            async def send_json(self, data):
                self.received_messages.append(data)

        ws = MockWebSocket()  # type: ignore
        await connection_manager.connect(ws)

        # Simulate event stream
        events = [
            {"type": "cdc_event", "event_type": "node_added", "entity_id": "n1"},
            {"type": "cdc_event", "event_type": "relationship_added", "entity_id": "r1"},
            {"type": "cdc_event", "event_type": "analysis_progress", "percentage": 50},
        ]

        for event in events:
            await connection_manager.broadcast(event)

        assert len(ws.received_messages) == 3
        assert ws.received_messages[0]["event_type"] == "node_added"
        assert ws.received_messages[1]["event_type"] == "relationship_added"
        assert ws.received_messages[2]["percentage"] == 50

    @pytest.mark.asyncio
    async def test_client_joins_during_stream(self, connection_manager):
        """Test new client joining during active event stream."""

        class MockWebSocket:
            def __init__(self):
                self.received_messages = []

            async def accept(self):
                pass

            async def send_json(self, data):
                self.received_messages.append(data)

        # First client
        ws1 = MockWebSocket()  # type: ignore
        await connection_manager.connect(ws1)

        # Broadcast to first client
        await connection_manager.broadcast({"type": "event", "id": 1})

        # Second client joins
        ws2 = MockWebSocket()  # type: ignore
        await connection_manager.connect(ws2)

        # Broadcast to both
        await connection_manager.broadcast({"type": "event", "id": 2})

        # First client got both, second got only latest
        assert len(ws1.received_messages) == 2
        assert len(ws2.received_messages) == 1
