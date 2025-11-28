"""Memgraph CDC Sync Worker

Consumes CDC events from Redis Streams and syncs to Memgraph.
Supports both native stream transformations and Python-based worker.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

import redis.asyncio as redis
from neo4j import GraphDatabase, Driver

logger = logging.getLogger(__name__)


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
        self.driver: Optional[Driver] = None

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
