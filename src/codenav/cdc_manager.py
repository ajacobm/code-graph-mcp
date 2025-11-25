"""
Change Data Capture (CDC) Manager via Redis Streams

Implements event-driven architecture where every graph mutation (node addition, edge creation, etc.)
is published to Redis Streams for:
1. Real-time frontend updates via WebSocket
2. Future Memgraph synchronization (Phase 2)
3. Audit trail and replay capability

Architecture:
- UniversalGraph mutations → CDC events → Redis Streams
- Redis Pub/Sub subscribers receive notifications
- Stream consumers (Memgraph sync worker) can replay/backfill
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from redis.asyncio import Redis

from .universal_graph import (
    NodeType,
    RelationshipType,
    UniversalNode,
    UniversalRelationship,
)

logger = logging.getLogger(__name__)


class CDCEventType(Enum):
    """Types of CDC events for graph mutations."""

    NODE_ADDED = "node_added"
    NODE_DELETED = "node_deleted"
    NODE_UPDATED = "node_updated"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_DELETED = "relationship_deleted"
    GRAPH_RESET = "graph_reset"
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_PROGRESS = "analysis_progress"


@dataclass
class CDCEvent:
    """A single CDC event representing a graph mutation."""

    event_type: CDCEventType
    timestamp: datetime
    entity_id: str  # node_id or relationship_id
    entity_type: str  # "node" or "relationship"
    data: Dict[str, Any]  # The actual node/relationship data or metadata
    event_id: Optional[str] = None  # Auto-generated if not provided

    def __post_init__(self):
        """Generate event_id if not provided."""
        if not self.event_id:
            self.event_id = str(uuid4())

    def to_redis_format(self) -> Dict[str, Any]:
        """Convert to format suitable for Redis Stream."""
        return {
            "event_id": self.event_id or "",
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "data": json.dumps(self._serialize_data()),
        }

    def _serialize_data(self) -> Dict[str, Any]:
        """Serialize data for JSON, handling Enums."""
        if not isinstance(self.data, dict):
            return self.data

        serialized = {}
        for key, value in self.data.items():
            if isinstance(value, Enum):
                serialized[key] = value.value
            elif isinstance(value, dict):
                serialized[key] = self._serialize_nested(value)
            else:
                serialized[key] = value
        return serialized

    def _serialize_nested(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively serialize nested dicts."""
        result = {}
        for key, value in obj.items():
            if isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, dict):
                result[key] = self._serialize_nested(value)
            else:
                result[key] = value
        return result

    @classmethod
    def from_redis_format(cls, data: Dict[str, Any]) -> "CDCEvent":
        """Parse a CDC event from Redis Stream format."""
        return cls(
            event_id=data["event_id"],
            event_type=CDCEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            data=json.loads(data["data"]),
        )


class CDCManager:
    """
    Manages Change Data Capture for graph mutations via Redis Streams.

    Collects mutations and publishes them to Redis Streams for:
    - Real-time frontend updates
    - Audit trail
    - Future Memgraph synchronization
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize CDC Manager.

        Args:
            redis_client: Async Redis client (optional, auto-created if needed)
        """
        self.redis = redis_client
        self.stream_key = "code_graph:cdc"  # Main CDC stream
        self.pubsub_key = "code_graph:events"  # Pub/Sub for real-time updates
        self.enabled = False
        self._event_handlers: Dict[str, List[Callable]] = {}

    async def initialize(self, redis_url: str = "redis://redis:6379") -> None:
        """Initialize Redis connection if not provided."""
        if not self.redis:
            from redis.asyncio import from_url

            self.redis = await from_url(redis_url)
        self.enabled = True
        logger.info("CDC Manager initialized")

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
        self.enabled = False

    def on_event(self, event_type: CDCEventType) -> Callable:
        """
        Decorator to register event handlers.

        Usage:
            @cdc.on_event(CDCEventType.NODE_ADDED)
            async def handle_node_added(event: CDCEvent):
                print(f"Node added: {event.entity_id}")
        """

        def decorator(func: Callable) -> Callable:
            key = event_type.value
            if key not in self._event_handlers:
                self._event_handlers[key] = []
            self._event_handlers[key].append(func)
            return func

        return decorator

    async def _call_handlers(self, event: CDCEvent) -> None:
        """Call all registered handlers for an event type."""
        key = event.event_type.value
        if key not in self._event_handlers:
            return

        for handler in self._event_handlers[key]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {key}: {e}", exc_info=True)

    async def publish_event(self, event: CDCEvent) -> None:
        """
        Publish a single CDC event to Redis Streams and Pub/Sub.

        Args:
            event: The CDC event to publish
        """
        if not self.enabled or not self.redis:
            return

        try:
            # Publish to Redis Stream (persistent, queryable)
            redis_data = event.to_redis_format()
            await self.redis.xadd(self.stream_key, {k: str(v) for k, v in redis_data.items()})

            # Publish to Pub/Sub (fast, real-time notifications)
            await self.redis.publish(
                self.pubsub_key,
                json.dumps(
                    {
                        "event_type": event.event_type.value,
                        "entity_id": event.entity_id,
                        "entity_type": event.entity_type,
                        "timestamp": event.timestamp.isoformat(),
                    }
                ),
            )

            logger.debug(f"CDC event published: {event.event_type.value}")

            # Call local handlers
            await self._call_handlers(event)

        except Exception as e:
            logger.error(f"Failed to publish CDC event: {e}", exc_info=True)

    async def publish_node_added(self, node: UniversalNode) -> None:
        """Publish a node_added event."""
        event = CDCEvent(
            event_type=CDCEventType.NODE_ADDED,
            timestamp=datetime.utcnow(),
            entity_id=node.id,
            entity_type="node",
            data=self._serialize_node(node),
        )
        await self.publish_event(event)

    async def publish_node_deleted(self, node_id: str) -> None:
        """Publish a node_deleted event."""
        event = CDCEvent(
            event_type=CDCEventType.NODE_DELETED,
            timestamp=datetime.utcnow(),
            entity_id=node_id,
            entity_type="node",
            data={"node_id": node_id},
        )
        await self.publish_event(event)

    async def publish_relationship_added(self, rel: UniversalRelationship) -> None:
        """Publish a relationship_added event."""
        event = CDCEvent(
            event_type=CDCEventType.RELATIONSHIP_ADDED,
            timestamp=datetime.utcnow(),
            entity_id=rel.id,
            entity_type="relationship",
            data=self._serialize_relationship(rel),
        )
        await self.publish_event(event)

    async def publish_relationship_deleted(self, rel_id: str) -> None:
        """Publish a relationship_deleted event."""
        event = CDCEvent(
            event_type=CDCEventType.RELATIONSHIP_DELETED,
            timestamp=datetime.utcnow(),
            entity_id=rel_id,
            entity_type="relationship",
            data={"relationship_id": rel_id},
        )
        await self.publish_event(event)

    async def publish_analysis_progress(
        self, percentage: int, message: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish analysis progress event."""
        event = CDCEvent(
            event_type=CDCEventType.ANALYSIS_PROGRESS,
            timestamp=datetime.utcnow(),
            entity_id="analysis",
            entity_type="metadata",
            data={
                "percentage": percentage,
                "message": message,
                **(metadata or {}),
            },
        )
        await self.publish_event(event)

    async def publish_analysis_completed(
        self, node_count: int, edge_count: int, duration_ms: float
    ) -> None:
        """Publish analysis completed event."""
        event = CDCEvent(
            event_type=CDCEventType.ANALYSIS_COMPLETED,
            timestamp=datetime.utcnow(),
            entity_id="analysis",
            entity_type="metadata",
            data={
                "node_count": node_count,
                "edge_count": edge_count,
                "duration_ms": duration_ms,
            },
        )
        await self.publish_event(event)

    async def get_stream_info(self) -> Dict[str, Any]:
        """Get Redis Stream information and statistics."""
        if not self.redis:
            return {}

        try:
            info = await self.redis.xinfo_stream(self.stream_key)
            return {
                "stream_key": self.stream_key,
                "length": info.get("length", 0),
                "first_entry_id": info.get("first-entry")[0] if info.get("first-entry") else None,
                "last_entry_id": info.get("last-entry")[0] if info.get("last-entry") else None,
                "consumer_groups": info.get("groups", []),
            }
        except Exception as e:
            logger.error(f"Failed to get stream info: {e}")
            return {"error": str(e)}

    async def read_stream(
        self, start_id: str = "0", count: int = 100
    ) -> List[CDCEvent]:
        """
        Read CDC events from stream.

        Args:
            start_id: Stream ID to start from (use "0" for beginning, "$" for end)
            count: Maximum number of events to read

        Returns:
            List of CDC events
        """
        if not self.redis:
            return []

        try:
            events = await self.redis.xrange(self.stream_key, min=start_id, count=count)
            result = []
            for stream_id, data in events:
                # Convert bytes to strings if needed
                if isinstance(stream_id, bytes):
                    stream_id = stream_id.decode()
                
                # Convert data dict values from bytes to strings
                cleaned_data = {}
                for k, v in data.items():
                    if isinstance(k, bytes):
                        k = k.decode()
                    if isinstance(v, bytes):
                        v = v.decode()
                    cleaned_data[k] = v
                
                # Use the actual event_id from data, or stream_id as fallback
                if "event_id" not in cleaned_data or not cleaned_data["event_id"]:
                    cleaned_data["event_id"] = stream_id
                
                result.append(CDCEvent.from_redis_format(cleaned_data))
            return result
        except Exception as e:
            logger.error(f"Failed to read stream: {e}", exc_info=True)
            return []

    async def subscribe_to_pubsub(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Subscribe to real-time Pub/Sub events.

        Args:
            callback: Async function to call for each event
        """
        if not self.redis:
            logger.error("Redis not initialized")
            return

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.pubsub_key)

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event_data)
                        else:
                            callback(event_data)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
        finally:
            await pubsub.close()

    @staticmethod
    def _serialize_node(node: UniversalNode) -> Dict[str, Any]:
        """Serialize node for CDC event."""
        data = asdict(node)
        # Convert enums to strings
        if "node_type" in data and isinstance(data["node_type"], NodeType):
            data["node_type"] = data["node_type"].value
        # Handle location object
        if "location" in data and isinstance(data["location"], dict):
            pass  # Already dict-like from asdict
        return data

    @staticmethod
    def _serialize_relationship(rel: UniversalRelationship) -> Dict[str, Any]:
        """Serialize relationship for CDC event."""
        data = asdict(rel)
        # Convert enums to strings
        if "relationship_type" in data and isinstance(data["relationship_type"], RelationshipType):
            data["relationship_type"] = data["relationship_type"].value
        return data
