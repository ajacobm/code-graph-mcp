"""Memgraph CDC Sync Worker

Consumes CDC events from Redis Streams and syncs to Memgraph.
Supports both native stream transformations and Python-based worker.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

import redis.asyncio as redis
from neo4j import GraphDatabase, driver

logger = logging.getLogger(__name__)


@dataclass
class SyncStatistics:
    """Statistics for sync operations."""

    total_processed: int = 0
    nodes_synced: int = 0
    edges_synced: int = 0
    errors: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class SyncMode(str, Enum):
    """Memgraph sync modes."""

    NATIVE = "native"  # Native Memgraph stream transformations
    WORKER = "worker"  # Python-based consumer
    DISABLED = "disabled"


class MemgraphClient:
    """Wrapper around Neo4j driver for Memgraph (Bolt protocol)."""

    def __init__(self, url: str = "bolt://memgraph:7687"):
        """Initialize Memgraph connection."""
        self.url = url
        self.driver: Optional[driver.Driver] = None

    async def connect(self) -> None:
        """Establish connection to Memgraph."""
        try:
            self.driver = GraphDatabase.driver(self.url)
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Connected to Memgraph")
        except Exception as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise

    async def close(self) -> None:
        """Close Memgraph connection."""
        if self.driver:
            self.driver.close()

    async def execute(self, query: str, **params) -> list:
        """Execute Cypher query."""
        if not self.driver:
            raise RuntimeError("Memgraph not connected")

        with self.driver.session() as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    async def create_node(self, node_data: Dict[str, Any]) -> None:
        """Create or merge a node."""
        query = """
        MERGE (n:Function {id: $id})
        SET n.name = $name,
            n.node_type = $node_type,
            n.language = $language,
            n.file = $file,
            n.line = $line,
            n.complexity = $complexity,
            n.is_entry_point = $is_entry_point
        """
        await self.execute(query, **node_data)

    async def create_relationship(self, rel_data: Dict[str, Any]) -> None:
        """Create or merge a relationship."""
        query = """
        MATCH (source {id: $source_id})
        MATCH (target {id: $target_id})
        MERGE (source)-[r:CALLS {id: $id}]->(target)
        SET r.type = $rel_type
        """
        await self.execute(query, **rel_data)

    async def health_check(self) -> Dict[str, Any]:
        """Get Memgraph health status."""
        try:
            await self.execute("RETURN 1")
            return {"status": "healthy", "connected": True}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "connected": False}


class RedisStreamConsumer:
    """Consumes events from Redis Streams."""

    def __init__(self, redis_client: redis.Redis, stream_key: str = "code-graph:events"):
        self.redis = redis_client
        self.stream_key = stream_key
        self.last_id = "0-0"

    async def read_batch(self, count: int = 100, block_ms: int = 1000) -> List[Dict[str, Any]]:
        """Read a batch of events from the stream."""
        try:
            messages = await self.redis.xread(
                {self.stream_key: self.last_id},
                count=count,
                block=block_ms
            )

            events = []
            if messages:
                for stream_key, message_list in messages:
                    for msg_id, msg_data in message_list:
                        # Decode message data
                        event = {}
                        for key, value in msg_data.items():
                            if isinstance(key, bytes):
                                key = key.decode()
                            if isinstance(value, bytes):
                                value = value.decode()
                            event[key] = value

                        events.append(event)
                        self.last_id = msg_id.decode() if isinstance(msg_id, bytes) else msg_id

            return events

        except Exception as e:
            logger.error(f"Failed to read stream batch: {e}")
            return []


class CDCEventProcessor:
    """Processes CDC events and generates Cypher queries."""

    def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Optional[str]:
        """Transform event to Cypher query."""
        try:
            if event_type == "node_created":
                return self._process_node_created(event_data)
            elif event_type == "edge_created":
                return self._process_edge_created(event_data)
            elif event_type == "node_updated":
                return self._process_node_updated(event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                return None

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return None

    def _process_node_created(self, data: Dict[str, Any]) -> str:
        """Generate MERGE query for node creation."""
        node_id = data.get("id", "unknown")
        node_type = data.get("node_type", "Unknown")
        name = data.get("name", "")

        # Build property assignments
        props = []
        for key, value in data.items():
            if key not in ["id", "node_type"]:
                if isinstance(value, str):
                    props.append(f'n.{key} = "{value}"')
                else:
                    props.append(f'n.{key} = {value}')

        set_clause = ", ".join(props) if props else ""
        cypher = f"MERGE (n:{node_type} {{id: '{node_id}'}}"
        if set_clause:
            cypher += f"\nSET {set_clause}"

        return cypher

    def _process_edge_created(self, data: Dict[str, Any]) -> str:
        """Generate MERGE query for relationship creation."""
        source_id = data.get("source_id", "unknown")
        target_id = data.get("target_id", "unknown")
        rel_type = data.get("relationship_type", "CALLS")

        cypher = (
            f"MATCH (source {{id: '{source_id}'}})\n"
            f"MATCH (target {{id: '{target_id}'}})\n"
            f"MERGE (source)-[:{rel_type}]->(target)"
        )

        return cypher

    def _process_node_updated(self, data: Dict[str, Any]) -> str:
        """Generate SET query for node update."""
        node_id = data.get("id", "unknown")

        # Build property assignments
        props = []
        for key, value in data.items():
            if key != "id":
                if isinstance(value, str):
                    props.append(f'n.{key} = "{value}"')
                else:
                    props.append(f'n.{key} = {value}')

        set_clause = ", ".join(props) if props else ""
        cypher = f"MATCH (n {{id: '{node_id}'}})"
        if set_clause:
            cypher += f"\nSET {set_clause}"

        return cypher


class MemgraphCDCSync:
    """Main CDC synchronization worker."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        memgraph_url: str = "bolt://localhost:7687",
    ):
        self.redis_url = redis_url
        self.memgraph_url = memgraph_url
        self.redis: Optional[redis.Redis] = None
        self.memgraph_driver: Optional[driver.Driver] = None
        self.stream_consumer = None
        self.event_processor = CDCEventProcessor()
        self.stats = SyncStatistics()

    async def connect(self) -> None:
        """Initialize connections."""
        try:
            self.redis = await redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            logger.info("✓ Redis connected")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        try:
            self.memgraph_driver = GraphDatabase.driver(self.memgraph_url)
            with self.memgraph_driver.session() as session:
                session.run("RETURN 1")
            logger.info("✓ Memgraph connected")
        except Exception as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise

    async def disconnect(self) -> None:
        """Close connections."""
        if self.redis:
            await self.redis.close()
        if self.memgraph_driver:
            self.memgraph_driver.close()

    async def process_batch(self, max_events: int = 100, max_retries: int = 3) -> SyncStatistics:
        """Process a batch of events from Redis stream."""
        if not self.stream_consumer:
            self.stream_consumer = RedisStreamConsumer(self.redis)

        retry_count = 0
        while retry_count < max_retries:
            try:
                events = await self.stream_consumer.read_batch(count=max_events)

                for event in events:
                    try:
                        event_type = event.get("type", "unknown")
                        cypher = self.event_processor.process_event(event_type, event)

                        if cypher:
                            # Execute in Memgraph
                            with self.memgraph_driver.session() as session:
                                session.run(cypher)

                            # Update statistics
                            if "node" in event_type.lower():
                                self.stats.nodes_synced += 1
                            elif "edge" in event_type.lower():
                                self.stats.edges_synced += 1

                            self.stats.total_processed += 1

                    except Exception as e:
                        logger.error(f"Failed to process event: {e}")
                        self.stats.errors += 1
                        continue

                return self.stats

            except Exception as e:
                retry_count += 1
                logger.warning(f"Retry {retry_count}/{max_retries}: {e}")
                await asyncio.sleep(0.5 * retry_count)

        self.stats.errors += 1
        return self.stats

    async def shutdown(self) -> None:
        """Shutdown the sync worker."""
        await self.disconnect()


class NativeStreamTransform:
    """Setup Memgraph native stream transformations (low latency)."""

    def __init__(self, memgraph_client: MemgraphClient):
        self.memgraph = memgraph_client

    async def setup(self) -> None:
        """Configure Memgraph to consume Redis Streams directly."""
        try:
            # Create stream transformation
            setup_queries = [
                # Drop existing stream if present
                "DROP STREAM IF EXISTS code_graph_events",
                # Create new stream
                """
                CREATE STREAM code_graph_events
                TOPICS graph:cdc
                TRANSFORM memgraph_stream.parse_json
                BATCH_SIZE 100
                """,
                # Create trigger for NODE_ADDED events
                """
                CREATE TRIGGER on_node_added
                ON STREAM code_graph_events
                WHEN data['event_type'] = 'node_added'
                EXECUTE
                MERGE (n:Function {id: data['entity_id']})
                SET n.name = data['data'].name,
                    n.node_type = data['data'].node_type,
                    n.language = data['data'].language,
                    n.file = data['data'].file,
                    n.line = data['data'].line,
                    n.complexity = data['data'].complexity,
                    n.is_entry_point = data['data'].is_entry_point
                """,
                # Create trigger for RELATIONSHIP_ADDED events
                """
                CREATE TRIGGER on_relationship_added
                ON STREAM code_graph_events
                WHEN data['event_type'] = 'relationship_added'
                EXECUTE
                MATCH (source {id: data['data'].source_id})
                MATCH (target {id: data['data'].target_id})
                MERGE (source)-[r:CALLS {id: data['entity_id']}]->(target)
                SET r.type = data['data'].rel_type
                """,
            ]

            for query in setup_queries:
                try:
                    await self.memgraph.execute(query)
                    logger.debug(f"Executed: {query[:50]}...")
                except Exception as e:
                    logger.warning(f"Query may have failed (might be normal): {e}")

            logger.info("✓ Native stream transformations configured")

        except Exception as e:
            logger.error(f"Failed to setup native stream transforms: {e}")
            raise


class PythonSyncWorker:
    """Python-based CDC consumer (fallback/debugging)."""

    def __init__(
        self,
        redis_client: redis.Redis,
        memgraph_client: MemgraphClient,
        stream_key: str = "graph:cdc",
    ):
        self.redis = redis_client
        self.memgraph = memgraph_client
        self.stream_key = stream_key
        self.last_id = "0-0"
        self.running = False

    async def start(self) -> None:
        """Start consuming CDC stream."""
        self.running = True
        logger.info(f"Starting CDC consumer from {self.stream_key}")

        try:
            while self.running:
                # Read new messages
                messages = await self.redis.xread({self.stream_key: self.last_id}, block=1000)

                if not messages:
                    continue

                for stream_key, message_list in messages:
                    for msg_id, msg_data in message_list:
                        await self._process_message(msg_data)
                        self.last_id = msg_id.decode() if isinstance(msg_id, bytes) else msg_id

        except asyncio.CancelledError:
            logger.info("CDC consumer stopped")
            self.running = False
        except Exception as e:
            logger.error(f"CDC consumer error: {e}")
            self.running = False

    async def stop(self) -> None:
        """Stop consuming CDC stream."""
        self.running = False

    async def _process_message(self, msg_data: Dict[str, bytes]) -> None:
        """Process a single CDC message."""
        try:
            # Decode message
            event_type = msg_data.get(b"event_type", b"").decode()
            entity_id = msg_data.get(b"entity_id", b"").decode()
            data_json = msg_data.get(b"data", b"{}").decode()
            data = json.loads(data_json)

            if event_type == "node_added":
                await self.memgraph.create_node({**data, "id": entity_id})
                logger.debug(f"Synced NODE: {entity_id}")

            elif event_type == "relationship_added":
                await self.memgraph.create_relationship({**data, "id": entity_id})
                logger.debug(f"Synced RELATIONSHIP: {entity_id}")

        except Exception as e:
            logger.error(f"Failed to process message: {e}")


class MemgraphSyncManager:
    """Orchestrates Memgraph sync with configurable strategy."""

    def __init__(
        self,
        redis_url: str = "redis://redis:6379",
        memgraph_url: str = "bolt://memgraph:7687",
        sync_mode: SyncMode = SyncMode.NATIVE,
    ):
        self.redis_url = redis_url
        self.memgraph_url = memgraph_url
        self.sync_mode = sync_mode

        self.redis: Optional[redis.Redis] = None
        self.memgraph = MemgraphClient(memgraph_url)
        self.worker: Optional[PythonSyncWorker] = None
        self.worker_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Initialize connections."""
        try:
            self.redis = await redis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("✓ Redis connected")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        try:
            await self.memgraph.connect()
        except Exception as e:
            logger.error(f"Failed to connect to Memgraph: {e}")
            raise

    async def start(self) -> None:
        """Start Memgraph sync based on configured mode."""
        if self.sync_mode == SyncMode.DISABLED:
            logger.info("Memgraph sync disabled")
            return

        await self.connect()

        if self.sync_mode == SyncMode.NATIVE:
            logger.info("Using native Memgraph stream transformations")
            transformer = NativeStreamTransform(self.memgraph)
            await transformer.setup()

        elif self.sync_mode == SyncMode.WORKER:
            logger.info("Starting Python CDC worker")
            self.worker = PythonSyncWorker(self.redis, self.memgraph)
            self.worker_task = asyncio.create_task(self.worker.start())

    async def stop(self) -> None:
        """Stop sync and cleanup."""
        if self.worker:
            await self.worker.stop()
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        if self.memgraph:
            await self.memgraph.close()
        if self.redis:
            await self.redis.close()

        logger.info("Memgraph sync manager stopped")

    async def get_status(self) -> Dict[str, Any]:
        """Get sync status."""
        status = {
            "mode": self.sync_mode.value,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            memgraph_health = await self.memgraph.health_check()
            status["memgraph"] = memgraph_health

            # Get sync lag if using worker
            if self.sync_mode == SyncMode.WORKER and self.worker:
                # Query Redis stream length
                stream_len = await self.redis.xlen("graph:cdc")
                status["pending_events"] = stream_len
                status["worker_running"] = self.worker.running

        except Exception as e:
            status["error"] = str(e)

        return status


# Standalone main for testing
async def main():
    """Test the sync worker."""
    manager = MemgraphSyncManager(sync_mode=SyncMode.WORKER)

    try:
        await manager.start()
        logger.info("Sync manager started successfully")

        # Check status
        status = await manager.get_status()
        logger.info(f"Status: {status}")

        # Keep running for a bit
        await asyncio.sleep(5)

    finally:
        await manager.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
