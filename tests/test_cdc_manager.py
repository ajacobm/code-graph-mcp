"""
Tests for Change Data Capture (CDC) Manager.

Tests covering:
- CDC event creation and serialization
- Redis Stream publishing
- Pub/Sub notifications
- Event handlers
- Stream reading and replay
"""

import asyncio
import json
from datetime import datetime
from typing import List

import pytest
import pytest_asyncio
from redis.asyncio import Redis, from_url

from src.codenav.cdc_manager import CDCEvent, CDCEventType, CDCManager
from src.codenav.universal_graph import (
    NodeType,
    RelationshipType,
    UniversalGraph,
    UniversalLocation,
    UniversalNode,
    UniversalRelationship,
)


@pytest_asyncio.fixture
async def redis_client():
    """Create and yield a Redis client for testing."""
    try:
        client = await from_url("redis://localhost:6379")
        # Test connection
        await client.ping()
        # Clear test data
        await client.flushdb()
        yield client
        await client.flushdb()
        await client.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest_asyncio.fixture
async def cdc_manager(redis_client):
    """Create a CDC manager with Redis client."""
    manager = CDCManager(redis_client)
    await manager.initialize()
    yield manager
    await manager.close()


class TestCDCEvent:
    """Test CDC event creation and serialization."""

    def test_event_creation(self):
        """Test creating a basic CDC event."""
        event = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime.utcnow(),
            entity_id="node_123",
            entity_type="node",
            data={"name": "test_func", "language": "python"},
        )

        assert event.event_type == CDCEventType.NODE_ADDED
        assert event.entity_id == "node_123"
        assert event.entity_type == "node"
        assert event.event_id is not None

    def test_event_auto_generated_id(self):
        """Test that event_id is auto-generated."""
        event1 = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime.utcnow(),
            entity_id="node_123",
            entity_type="node",
            data={},
        )

        event2 = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime.utcnow(),
            entity_id="node_456",
            entity_type="node",
            data={},
        )

        assert event1.event_id != event2.event_id

    def test_event_to_redis_format(self):
        """Test converting event to Redis format."""
        event = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime(2025, 11, 8, 12, 0, 0),
            entity_id="node_123",
            entity_type="node",
            data={"name": "test_func"},
            event_id="evt_001",
        )

        redis_data = event.to_redis_format()

        assert redis_data["event_id"] == "evt_001"
        assert redis_data["event_type"] == "node_added"
        assert redis_data["entity_id"] == "node_123"
        assert redis_data["entity_type"] == "node"
        assert "data" in redis_data
        assert json.loads(redis_data["data"])["name"] == "test_func"

    def test_event_enum_serialization(self):
        """Test that Enums are serialized to strings."""
        event = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime.utcnow(),
            entity_id="node_123",
            entity_type="node",
            data={"node_type": NodeType.FUNCTION, "rel_type": RelationshipType.CALLS},
        )

        redis_data = event.to_redis_format()
        data = json.loads(redis_data["data"])

        assert data["node_type"] == "function"
        assert data["rel_type"] == "calls"

    def test_event_roundtrip(self):
        """Test converting event to Redis format and back."""
        original = CDCEvent(
            event_type=CDCEventType.RELATIONSHIP_ADDED,
            timestamp=datetime(2025, 11, 8, 12, 0, 0),
            entity_id="rel_001",
            entity_type="relationship",
            data={"source": "node1", "target": "node2"},
            event_id="evt_001",
        )

        redis_data = original.to_redis_format()
        restored = CDCEvent.from_redis_format(redis_data)

        assert restored.event_type == original.event_type
        assert restored.entity_id == original.entity_id
        assert restored.data == original.data


class TestCDCManager:
    """Test CDC Manager functionality."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self, cdc_manager):
        """Test CDC manager initializes properly."""
        assert cdc_manager.enabled
        assert cdc_manager.redis is not None
        assert cdc_manager.stream_key == "code_graph:cdc"

    @pytest.mark.asyncio
    async def test_publish_node_added(self, cdc_manager):
        """Test publishing node_added event."""
        node = UniversalNode(
            id="node_001",
            name="test_function",
            node_type=NodeType.FUNCTION,
            location=UniversalLocation(
                file_path="test.py",
                start_line=1,
                end_line=5,
            ),
            language="python",
        )

        await cdc_manager.publish_node_added(node)

        # Verify event is in stream
        stream_info = await cdc_manager.get_stream_info()
        assert stream_info["length"] == 1

    @pytest.mark.asyncio
    async def test_publish_relationship_added(self, cdc_manager):
        """Test publishing relationship_added event."""
        rel = UniversalRelationship(
            id="rel_001",
            source_id="node1",
            target_id="node2",
            relationship_type=RelationshipType.CALLS,
        )

        await cdc_manager.publish_relationship_added(rel)

        stream_info = await cdc_manager.get_stream_info()
        assert stream_info["length"] == 1

    @pytest.mark.asyncio
    async def test_read_stream_events(self, cdc_manager):
        """Test reading events from stream."""
        # Publish multiple events
        for i in range(3):
            node = UniversalNode(
                id=f"node_{i}",
                name=f"func_{i}",
                node_type=NodeType.FUNCTION,
                location=UniversalLocation(
                    file_path="test.py",
                    start_line=i + 1,
                    end_line=i + 6,
                ),
            )
            await cdc_manager.publish_node_added(node)

        # Read all events
        events = await cdc_manager.read_stream(start_id="0", count=100)

        assert len(events) == 3
        assert all(isinstance(e, CDCEvent) for e in events)
        assert all(e.event_type == CDCEventType.NODE_ADDED for e in events)

    @pytest.mark.asyncio
    async def test_event_handler_registration(self, cdc_manager):
        """Test registering and calling event handlers."""
        received_events: List[CDCEvent] = []

        @cdc_manager.on_event(CDCEventType.NODE_ADDED)
        async def handle_node_added(event: CDCEvent):
            received_events.append(event)

        # Publish event (will trigger handler)
        node = UniversalNode(
            id="node_test",
            name="test",
            node_type=NodeType.FUNCTION,
            location=UniversalLocation(
                file_path="test.py",
                start_line=1,
                end_line=5,
            ),
        )

        await cdc_manager.publish_node_added(node)
        await asyncio.sleep(0.1)  # Allow handler to complete

        assert len(received_events) == 1
        assert received_events[0].entity_id == "node_test"

    @pytest.mark.asyncio
    async def test_analysis_progress_event(self, cdc_manager):
        """Test publishing analysis progress events."""
        await cdc_manager.publish_analysis_progress(
            percentage=50,
            message="Analyzing files...",
            metadata={"files_processed": 10, "total_files": 20},
        )

        events = await cdc_manager.read_stream(start_id="0", count=1)
        assert len(events) == 1
        assert events[0].event_type == CDCEventType.ANALYSIS_PROGRESS
        assert events[0].data["percentage"] == 50

    @pytest.mark.asyncio
    async def test_analysis_completed_event(self, cdc_manager):
        """Test publishing analysis completed event."""
        await cdc_manager.publish_analysis_completed(
            node_count=100,
            edge_count=500,
            duration_ms=1234.5,
        )

        events = await cdc_manager.read_stream(start_id="0", count=1)
        assert len(events) == 1
        assert events[0].event_type == CDCEventType.ANALYSIS_COMPLETED
        assert events[0].data["node_count"] == 100

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_stream_info(self, cdc_manager):
        """Test retrieving stream information."""
        # Add events first (stream won't exist if empty)
        node = UniversalNode(
            id="node_1",
            name="func",
            node_type=NodeType.FUNCTION,
            location=UniversalLocation(
                file_path="test.py",
                start_line=1,
                end_line=6,
            ),
        )
        await cdc_manager.publish_node_added(node)

        info = await cdc_manager.get_stream_info()
        assert info["length"] == 1
        assert info["first_entry_id"] is not None

    @pytest.mark.asyncio
    async def test_graph_relationship_addition_triggers_cdc(self, redis_client):
        """Test that adding relationships triggers CDC events."""
        cdc_manager = CDCManager(redis_client)
        await cdc_manager.initialize()

        graph = UniversalGraph(cdc_manager=cdc_manager)

        rel = UniversalRelationship(
            id="rel_001",
            source_id="node1",
            target_id="node2",
            relationship_type=RelationshipType.CALLS,
        )

        graph.add_relationship(rel)
        await asyncio.sleep(0.1)

        # Verify event published
        events = await cdc_manager.read_stream(start_id="0", count=1)
        assert len(events) > 0

        await cdc_manager.close()


class TestCDCEdgeCases:
    """Test edge cases and error handling."""

    def test_event_with_complex_data(self):
        """Test event with nested data structures."""
        event = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime.utcnow(),
            entity_id="node_001",
            entity_type="node",
            data={
                "metadata": {
                    "complexity": 5,
                    "params": ["arg1", "arg2"],
                    "types": {"NodeType": NodeType.FUNCTION, "RelType": RelationshipType.CALLS},
                }
            },
        )

        redis_data = event.to_redis_format()
        data = json.loads(redis_data["data"])

        assert data["metadata"]["complexity"] == 5
        assert data["metadata"]["types"]["NodeType"] == "function"

    @pytest.mark.asyncio
    async def test_manager_without_redis(self):
        """Test CDC manager gracefully handles missing Redis."""
        manager = CDCManager(redis_client=None)

        # Should not crash, just skip publishing
        await manager.publish_analysis_progress(50, "test")

        # Disable manager
        manager.enabled = False
        await manager.publish_analysis_progress(75, "test")

    @pytest.mark.asyncio
    async def test_multiple_event_types(self, cdc_manager):
        """Test publishing multiple different event types."""
        node = UniversalNode(
            id="n1",
            name="func",
            node_type=NodeType.FUNCTION,
            location=UniversalLocation(
                file_path="test.py",
                start_line=1,
                end_line=5,
            ),
        )

        rel = UniversalRelationship(
            id="r1",
            source_id="n1",
            target_id="n2",
            relationship_type=RelationshipType.CALLS,
        )

        await cdc_manager.publish_node_added(node)
        await cdc_manager.publish_relationship_added(rel)
        await cdc_manager.publish_analysis_progress(100, "Complete")

        events = await cdc_manager.read_stream(start_id="0", count=100)

        types = {e.event_type for e in events}
        assert CDCEventType.NODE_ADDED in types
        assert CDCEventType.RELATIONSHIP_ADDED in types
        assert CDCEventType.ANALYSIS_PROGRESS in types
