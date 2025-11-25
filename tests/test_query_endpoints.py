"""Integration tests for graph query endpoints."""

import pytest
import pytest_asyncio
from pathlib import Path
from src.codenav.server.analysis_engine import UniversalAnalysisEngine
from src.codenav.server.graph_api import create_graph_api_router


@pytest_asyncio.fixture
async def engine():
    """Create analysis engine with test data."""
    project_root = Path(__file__).parent.parent / "src" / "codenav"
    engine = UniversalAnalysisEngine(str(project_root))
    await engine._ensure_analyzed()
    yield engine


@pytest.mark.asyncio
class TestQueryEndpoints:
    """Test new query endpoints."""

    async def test_find_callers_endpoint_exists(self):
        """Verify find_callers endpoint is properly defined."""
        project_root = Path(__file__).parent.parent / "src" / "codenav"
        engine = UniversalAnalysisEngine(str(project_root))
        router = create_graph_api_router(engine)
        
        routes = [route.path for route in router.routes]
        assert "/api/graph/query/callers" in routes

    async def test_find_callees_endpoint_exists(self):
        """Verify find_callees endpoint is properly defined."""
        project_root = Path(__file__).parent.parent / "src" / "codenav"
        engine = UniversalAnalysisEngine(str(project_root))
        router = create_graph_api_router(engine)
        
        routes = [route.path for route in router.routes]
        assert "/api/graph/query/callees" in routes

    async def test_find_references_endpoint_exists(self):
        """Verify find_references endpoint is properly defined."""
        project_root = Path(__file__).parent.parent / "src" / "codenav"
        engine = UniversalAnalysisEngine(str(project_root))
        router = create_graph_api_router(engine)
        
        routes = [route.path for route in router.routes]
        assert "/api/graph/query/references" in routes

    async def test_find_callers_with_data(self, engine):
        """Test find_callers with actual data."""
        callers = await engine.find_function_callers("__init__")
        assert isinstance(callers, list)

    async def test_find_callees_with_data(self, engine):
        """Test find_callees with actual data."""
        callees = await engine.find_function_callees("__init__")
        assert isinstance(callees, list)

    async def test_find_references_with_data(self, engine):
        """Test find_references with actual data."""
        refs = await engine.find_symbol_references("analyze_project")
        assert isinstance(refs, list)

    async def test_query_response_structure(self, engine):
        """Verify query response has expected structure."""
        callers = await engine.find_function_callers("analyze_project")
        
        if callers:
            caller = callers[0]
            assert "caller" in caller or "callee" in caller or "referencing_symbol" in caller
            assert "file" in caller
            assert "line" in caller

    async def test_router_has_all_graph_endpoints(self):
        """Verify all expected endpoints are registered."""
        project_root = Path(__file__).parent.parent / "src" / "codenav"
        engine = UniversalAnalysisEngine(str(project_root))
        router = create_graph_api_router(engine)
        
        routes = [route.path for route in router.routes]
        expected_endpoints = [
            "/api/graph/stats",
            "/api/graph/nodes/{node_id}",
            "/api/graph/traverse",
            "/api/graph/nodes/search",
            "/api/graph/seams",
            "/api/graph/call-chain/{start_node}",
            "/api/graph/query/callers",
            "/api/graph/query/callees",
            "/api/graph/query/references",
        ]
        
        for endpoint in expected_endpoints:
            assert endpoint in routes, f"Missing endpoint: {endpoint}"
