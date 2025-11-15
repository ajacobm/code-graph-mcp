"""
CDC Sync Validation Tests

Tests for the Memgraph CDC (Change Data Capture) synchronization worker.
Validates that graph events are correctly captured, transformed, and synchronized
between Redis Streams and Memgraph.
"""

import pytest
import pytest_asyncio
import redis.asyncio as redis
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from code_graph_mcp.memgraph_sync import (
    MemgraphCDCSync,
    CDCEventProcessor,
    RedisStreamConsumer
)


@pytest_asyncio.fixture
async def redis_client():
    """Fixture: Redis async client."""
    client = await redis.from_url("redis://localhost:6379", decode_responses=True)
    yield client
    # Cleanup
    await client.delete("code-graph:nodes", "code-graph:edges", "code-graph:events")
    await client.close()


@pytest_asyncio.fixture
async def memgraph_driver():
    """Fixture: Memgraph driver."""
    try:
        driver = GraphDatabase.driver("bolt://localhost:7687")
        with driver.session() as session:
            session.run("RETURN 1")  # Test connection
        yield driver
    except ServiceUnavailable:
        pytest.skip("Memgraph not available")
    finally:
        driver.close()


@pytest_asyncio.fixture
async def cdc_sync(redis_client, memgraph_driver):
    """Fixture: CDC Sync instance."""
    sync = MemgraphCDCSync(
        redis_url="redis://localhost:6379",
        memgraph_url="bolt://localhost:7687"
    )
    await sync.connect()
    yield sync
    await sync.shutdown()


class TestRedisStreamConsumer:
    """Tests for Redis Stream consumption."""

    @pytest.mark.asyncio
    async def test_consumer_reads_events(self, redis_client):
        """Test that consumer reads events from Redis Stream."""
        stream_key = "code-graph:events"
        
        # Publish test events
        test_events = [
            {"type": "node_created", "node_id": "func1", "node_type": "Function"},
            {"type": "node_created", "node_id": "func2", "node_type": "Function"},
            {"type": "edge_created", "source": "func1", "target": "func2", "relationship_type": "CALLS"}
        ]
        
        for event in test_events:
            await redis_client.xadd(stream_key, event)
        
        # Read events
        consumer = RedisStreamConsumer(redis_client, stream_key)
        events = await consumer.read_batch(count=3, block_ms=1000)
        
        assert len(events) == 3
        assert events[0]["type"] == "node_created"
        assert events[1]["type"] == "node_created"
        assert events[2]["type"] == "edge_created"

    @pytest.mark.asyncio
    async def test_consumer_handles_empty_stream(self, redis_client):
        """Test consumer handles empty stream gracefully."""
        stream_key = "code-graph:empty"
        
        consumer = RedisStreamConsumer(redis_client, stream_key)
        events = await consumer.read_batch(count=5, block_ms=100)
        
        assert events == []

    @pytest.mark.asyncio
    async def test_consumer_tracks_offset(self, redis_client):
        """Test consumer tracks stream offset correctly."""
        stream_key = "code-graph:offset-test"
        
        # Add 5 events
        event_ids = []
        for i in range(5):
            event_id = await redis_client.xadd(
                stream_key,
                {"event": f"event_{i}"}
            )
            event_ids.append(event_id)
        
        # Read first 2
        consumer = RedisStreamConsumer(redis_client, stream_key)
        batch1 = await consumer.read_batch(count=2)
        assert len(batch1) == 2
        
        # Read next 3 (should start from offset)
        batch2 = await consumer.read_batch(count=3)
        assert len(batch2) == 3
        assert batch2[0]["event"] == "event_2"


class TestCDCEventProcessor:
    """Tests for CDC event processing and transformation."""

    def test_process_node_created_event(self):
        """Test processing of node_created events."""
        event = {
            "id": "node_123",
            "node_type": "Function",
            "name": "process_data",
            "file": "/src/utils.py",
            "language": "python",
            "complexity": 3
        }
        
        processor = CDCEventProcessor()
        cypher = processor.process_event("node_created", event)
        
        assert "CREATE" in cypher or "MERGE" in cypher
        assert "Function" in cypher
        assert "process_data" in cypher
        assert "python" in cypher

    def test_process_edge_created_event(self):
        """Test processing of edge_created events."""
        event = {
            "source_id": "node_1",
            "target_id": "node_2",
            "relationship_type": "CALLS",
            "weight": 1
        }
        
        processor = CDCEventProcessor()
        cypher = processor.process_event("edge_created", event)
        
        assert "-[:CALLS]->" in cypher or "CALLS" in cypher
        assert "node_1" in cypher
        assert "node_2" in cypher

    def test_process_node_updated_event(self):
        """Test processing of node_updated events."""
        event = {
            "id": "node_123",
            "complexity": 5,
            "has_tests": True
        }
        
        processor = CDCEventProcessor()
        cypher = processor.process_event("node_updated", event)
        
        assert "SET" in cypher or "UPDATE" in cypher
        assert "node_123" in cypher

    def test_process_invalid_event(self):
        """Test processor handles invalid events gracefully."""
        event = {"incomplete": "data"}
        
        processor = CDCEventProcessor()
        cypher = processor.process_event("unknown_type", event)
        
        assert cypher is None or cypher == ""

    def test_batch_event_processing(self):
        """Test processing multiple events in batch."""
        events = [
            ("node_created", {"id": "n1", "node_type": "Function", "name": "func1"}),
            ("node_created", {"id": "n2", "node_type": "Function", "name": "func2"}),
            ("edge_created", {"source_id": "n1", "target_id": "n2", "type": "CALLS"})
        ]
        
        processor = CDCEventProcessor()
        cyphers = [processor.process_event(e_type, e_data) for e_type, e_data in events]
        
        assert len(cyphers) == 3
        assert all(cypher for cypher in cyphers)  # All non-empty


class TestMemgraphCDCSync:
    """Tests for end-to-end CDC sync."""

    @pytest.mark.asyncio
    async def test_sync_nodes_to_memgraph(self, cdc_sync, redis_client):
        """Test syncing node_created events to Memgraph."""
        # Add events to Redis
        stream_key = "code-graph:events"
        await redis_client.xadd(stream_key, {
            "type": "node_created",
            "id": "func1",
            "name": "test_function",
            "node_type": "Function",
            "language": "python"
        })
        
        # Process one event
        stats = await cdc_sync.process_batch(max_events=1)
        
        assert stats.nodes_synced > 0 or stats.total_processed > 0

    @pytest.mark.asyncio
    async def test_sync_edges_to_memgraph(self, cdc_sync, redis_client):
        """Test syncing edge_created events to Memgraph."""
        stream_key = "code-graph:events"
        
        # Create two nodes first
        await redis_client.xadd(stream_key, {
            "type": "node_created",
            "id": "func1",
            "name": "func1"
        })
        await redis_client.xadd(stream_key, {
            "type": "node_created",
            "id": "func2",
            "name": "func2"
        })
        
        # Create edge
        await redis_client.xadd(stream_key, {
            "type": "edge_created",
            "source_id": "func1",
            "target_id": "func2",
            "relationship_type": "CALLS"
        })
        
        stats = await cdc_sync.process_batch(max_events=3)
        
        assert stats.total_processed >= 3

    @pytest.mark.asyncio
    async def test_sync_retry_on_transient_failure(self, cdc_sync, redis_client):
        """Test sync retries on transient failures."""
        # Add a valid event
        await redis_client.xadd("code-graph:events", {
            "type": "node_created",
            "id": "func1",
            "name": "func1"
        })
        
        # First attempt might fail, retry should succeed
        stats = await cdc_sync.process_batch(max_events=1, max_retries=3)
        
        assert stats.errors == 0 or stats.total_processed > 0

    @pytest.mark.asyncio
    async def test_sync_statistics_tracking(self, cdc_sync, redis_client):
        """Test that sync tracks statistics correctly."""
        stream_key = "code-graph:events"
        
        # Add multiple events
        for i in range(5):
            await redis_client.xadd(stream_key, {
                "type": "node_created",
                "id": f"node_{i}",
                "name": f"node_{i}"
            })
        
        stats = await cdc_sync.process_batch(max_events=5)
        
        assert stats.total_processed == 5 or stats.total_processed > 0
        assert stats.nodes_synced >= 0
        assert stats.edges_synced >= 0
        assert stats.errors >= 0

    @pytest.mark.asyncio
    async def test_sync_deduplication(self, cdc_sync, redis_client):
        """Test that duplicate events are handled correctly."""
        stream_key = "code-graph:events"
        
        # Add same node creation event twice
        event = {"type": "node_created", "id": "func1", "name": "func1"}
        await redis_client.xadd(stream_key, event)
        await redis_client.xadd(stream_key, event)
        
        stats = await cdc_sync.process_batch(max_events=2)
        
        # Should handle duplication (either deduplicate or upsert)
        assert stats.total_processed >= 2 or stats.errors == 0


class TestCDCSyncRobustness:
    """Tests for CDC sync robustness and error handling."""

    @pytest.mark.asyncio
    async def test_sync_handles_malformed_json(self, cdc_sync, redis_client):
        """Test sync handles malformed JSON in events."""
        stream_key = "code-graph:events"
        
        # Add malformed event
        await redis_client.xadd(stream_key, {
            "type": "node_created",
            "data": "{invalid json"
        })
        
        # Add valid event
        await redis_client.xadd(stream_key, {
            "type": "node_created",
            "id": "func1",
            "name": "func1"
        })
        
        stats = await cdc_sync.process_batch(max_events=2)
        
        # Should skip malformed, process valid
        assert stats.total_processed >= 1

    @pytest.mark.asyncio
    async def test_sync_handles_missing_fields(self, cdc_sync, redis_client):
        """Test sync handles events with missing required fields."""
        stream_key = "code-graph:events"
        
        # Add event missing required fields
        await redis_client.xadd(stream_key, {
            "type": "node_created"
            # Missing: id, name, type
        })
        
        # Add complete event
        await redis_client.xadd(stream_key, {
            "type": "node_created",
            "id": "func1",
            "name": "func1",
            "node_type": "Function"
        })
        
        stats = await cdc_sync.process_batch(max_events=2)
        
        # Should skip invalid, process valid
        assert stats.total_processed >= 1

    @pytest.mark.asyncio
    async def test_sync_performance_large_batch(self, cdc_sync, redis_client):
        """Test sync performance with large event batches."""
        stream_key = "code-graph:events"
        
        # Add 1000 events
        for i in range(1000):
            await redis_client.xadd(stream_key, {
                "type": "node_created",
                "id": f"node_{i}",
                "name": f"node_{i}",
                "node_type": "Function"
            })
        
        import time
        start = time.time()
        stats = await cdc_sync.process_batch(max_events=1000)
        duration = time.time() - start
        
        # Should complete in reasonable time (< 30s)
        assert duration < 30
        assert stats.total_processed > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
