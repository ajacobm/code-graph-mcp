"""
WebSocket Server for Real-Time CDC Events

Provides WebSocket endpoints for subscribing to real-time code graph updates
via Redis Pub/Sub. Clients connect and receive live notifications when:
- Nodes are added/modified to the graph
- Relationships are created/deleted
- Analysis completes or progresses

Usage:
    app.include_router(create_websocket_router(cdc_manager))
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from .cdc_manager import CDCManager

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection."""
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return

        async with self._lock:
            dead_connections = []

            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    dead_connections.append(connection)

            # Remove dead connections
            for connection in dead_connections:
                self.active_connections.discard(connection)

    async def send_to_client(self, websocket: WebSocket, message: dict) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            await self.disconnect(websocket)

    def get_connection_count(self) -> int:
        """Get current number of connected clients."""
        return len(self.active_connections)


def create_websocket_router(cdc_manager: Optional[CDCManager] = None) -> APIRouter:
    """
    Create WebSocket router with CDC event streaming.

    Args:
        cdc_manager: CDC manager for subscribing to events

    Returns:
        FastAPI router with WebSocket endpoints
    """
    router = APIRouter()
    manager = WebSocketConnectionManager()

    @router.websocket("/ws/events")
    async def websocket_events(websocket: WebSocket) -> None:
        """
        WebSocket endpoint for real-time CDC events.

        Broadcasts all CDC events to connected clients as they occur.

        Message format:
        {
            "type": "cdc_event",
            "event_type": "node_added",
            "entity_id": "node_001",
            "entity_type": "node",
            "timestamp": "2025-11-08T12:00:00.000Z",
            "data": {...}
        }
        """
        await manager.connect(websocket)

        try:
            # Keep connection alive and listen for client messages
            while True:
                # Receive any messages from client (keep-alive pings, etc)
                data = await websocket.receive_text()

                # Echo back a pong if client sends ping
                if data == "ping":
                    await manager.send_to_client(websocket, {"type": "pong"})

        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await manager.disconnect(websocket)

    @router.websocket("/ws/events/filtered")
    async def websocket_filtered_events(
        websocket: WebSocket,
    ) -> None:
        """
        WebSocket endpoint with event filtering.

        Client can send filter instructions to receive only specific event types.

        Client message format:
        {
            "action": "filter",
            "event_types": ["node_added", "relationship_added"],
            "entity_types": ["node", "relationship"]
        }
        """
        await manager.connect(websocket)
        filters: Dict[str, Set[Any]] = {
            "event_types": set(),
            "entity_types": set(),
        }

        try:
            while True:
                data = await websocket.receive_text()

                if data == "ping":
                    await manager.send_to_client(websocket, {"type": "pong"})
                    continue

                try:
                    message = json.loads(data)

                    if message.get("action") == "filter":
                        event_types = set(message.get("event_types", []))
                        entity_types = set(message.get("entity_types", []))
                        filters["event_types"] = event_types
                        filters["entity_types"] = entity_types
                        await manager.send_to_client(
                            websocket,
                            {
                                "type": "filter_updated",
                                "filters": {
                                    "event_types": list(event_types),
                                    "entity_types": list(entity_types),
                                },
                            },
                        )

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client: {data}")

        except WebSocketDisconnect:
            await manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket filtered error: {e}")
            await manager.disconnect(websocket)

    @router.get("/ws/status")
    async def websocket_status() -> JSONResponse:
        """Get current WebSocket connection status."""
        return JSONResponse(
            {
                "active_connections": manager.get_connection_count(),
                "status": "healthy",
            }
        )

    # Store manager in router for external access
    router.ws_manager = manager  # type: ignore

    return router


async def setup_cdc_broadcaster(cdc_manager: CDCManager, ws_manager: WebSocketConnectionManager) -> None:
    """
    Connect CDC events to WebSocket broadcasting.

    Call this during app startup to subscribe to CDC events and broadcast them
    to all connected WebSocket clients.

    Args:
        cdc_manager: CDC manager with Redis Pub/Sub
        ws_manager: WebSocket connection manager for broadcasting
    """

    async def broadcast_cdc_event(event_data: dict) -> None:
        """Broadcast incoming CDC event to all clients."""
        message = {
            "type": "cdc_event",
            **event_data,
        }
        await ws_manager.broadcast(message)

    # Subscribe to CDC events
    try:
        await cdc_manager.subscribe_to_pubsub(broadcast_cdc_event)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Failed to subscribe to CDC events: {e}")


__all__ = [
    "create_websocket_router",
    "setup_cdc_broadcaster",
    "WebSocketConnectionManager",
]
