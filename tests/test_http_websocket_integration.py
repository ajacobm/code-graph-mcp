"""
Integration tests for HTTP server with WebSocket and CDC support.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from codenav.cdc_manager import CDCEventType, CDCManager
from codenav.http_server import GraphAPIServer


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory."""
    (tmp_path / "test.py").write_text("def foo(): pass")
    return tmp_path


@pytest.fixture
def server(temp_project_dir):
    """Create a GraphAPIServer instance."""
    return GraphAPIServer(
        temp_project_dir,
        host="127.0.0.1",
        port=8001,
        enable_redis_cache=False,
    )


class TestHTTPServerInitialization:
    """Test HTTP server initialization with CDC and WebSocket."""

    def test_server_has_cdc_manager_attribute(self, server):
        """Verify server has cdc_manager attribute."""
        assert hasattr(server, 'cdc_manager')
        assert server.cdc_manager is None

    def test_server_has_engine_attribute(self, server):
        """Verify server has engine attribute."""
        assert hasattr(server, 'engine')
        assert server.engine is None

    def test_health_check_endpoint_accessible(self, server):
        """Verify health check endpoint is accessible."""
        client = TestClient(server.app)
        response = client.get("/health")
        assert response.status_code in [200, 202]

    def test_root_endpoint_returns_api_info(self, server):
        """Verify root endpoint returns API information."""
        client = TestClient(server.app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Code Graph API"


class TestCDCManagerIntegration:
    """Test CDC manager integration."""

    def test_cdc_manager_without_redis(self):
        """Test CDCManager works without Redis."""
        manager = CDCManager(redis_client=None)
        assert not manager.enabled

    def test_cdc_manager_has_required_attributes(self):
        """Verify CDCManager has required attributes."""
        manager = CDCManager(redis_client=None)
        assert hasattr(manager, 'redis')
        assert hasattr(manager, 'stream_key')
        assert hasattr(manager, 'pubsub_key')
        assert hasattr(manager, 'enabled')


class TestWebSocketRouterIntegration:
    """Test WebSocket router integration."""

    def test_websocket_router_can_be_created(self):
        """Verify WebSocket router can be created."""
        from codenav.websocket_server import create_websocket_router
        
        router = create_websocket_router()
        assert router is not None
        assert hasattr(router, 'routes')

    def test_websocket_router_has_ws_manager(self):
        """Verify WebSocket router has manager."""
        from codenav.websocket_server import create_websocket_router
        
        router = create_websocket_router()
        assert hasattr(router, 'ws_manager')


class TestServerConfiguration:
    """Test server configuration."""

    def test_server_initialization(self, server):
        """Verify server initializes with correct config."""
        assert server.project_root is not None
        assert server.host == "127.0.0.1"
        assert server.port == 8001
        assert server.enable_redis_cache is False

    def test_server_app_is_fastapi(self, server):
        """Verify server.app is a FastAPI instance."""
        from fastapi import FastAPI
        assert isinstance(server.app, FastAPI)


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
