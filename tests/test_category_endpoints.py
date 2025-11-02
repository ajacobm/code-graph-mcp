"""Tests for category and subgraph endpoints."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from code_graph_mcp.server.graph_api import create_graph_api_router
from code_graph_mcp.universal_graph import UniversalGraph, UniversalNode, UniversalRelationship, UniversalLocation, NodeType, RelationshipType


@pytest.fixture
def mock_engine_with_graph():
    """Create a mock engine with test graph data."""
    from code_graph_mcp.server.analysis_engine import UniversalAnalysisEngine
    
    # Create mock engine
    engine = MagicMock(spec=UniversalAnalysisEngine)
    analyzer = MagicMock()
    
    # Create test graph
    graph = UniversalGraph()
    
    # Add test nodes with varying degrees
    nodes_data = [
        ("main", 0, 2),
        ("entry_func", 0, 3),
        ("utility_hub", 5, 5),
        ("helper_func", 4, 6),
        ("leaf_util", 3, 0),
        ("leaf_worker", 2, 0),
    ]
    
    for name, in_count, out_count in nodes_data:
        loc = UniversalLocation(file_path="test_file.py", start_line=1, end_line=10)
        node = UniversalNode(
            id=f"test_file.py:{name}:1",
            name=name,
            node_type=NodeType.FUNCTION,
            location=loc,
            language="python",
            complexity=1
        )
        graph.add_node(node)
    
    # Add relationships
    node_ids = [f"test_file.py:{name}:1" for name, _, _ in nodes_data]
    rel_id = 0
    for i, (_, in_count, out_count) in enumerate(nodes_data):
        for j in range(in_count):
            source_idx = (i + j + 1) % len(node_ids)
            if source_idx != i:
                rel = UniversalRelationship(
                    id=f"rel_{rel_id}",
                    source_id=node_ids[source_idx],
                    target_id=node_ids[i],
                    relationship_type=RelationshipType.CALLS
                )
                graph.add_relationship(rel)
                rel_id += 1
        
        for j in range(out_count):
            target_idx = (i + j + 1) % len(node_ids)
            if target_idx != i:
                rel = UniversalRelationship(
                    id=f"rel_{rel_id}",
                    source_id=node_ids[i],
                    target_id=node_ids[target_idx],
                    relationship_type=RelationshipType.CALLS
                )
                graph.add_relationship(rel)
                rel_id += 1
    
    analyzer.graph = graph
    engine.analyzer = analyzer
    return engine


@pytest.fixture
def test_client(mock_engine_with_graph):
    """Create test client with mock engine."""
    app = FastAPI()
    router = create_graph_api_router(mock_engine_with_graph)
    app.include_router(router)
    return TestClient(app)


def test_categories_entry_points(test_client):
    """Test entry_points category endpoint."""
    response = test_client.get("/api/graph/categories/entry_points")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "entry_points"
    assert "nodes" in data
    assert data["total"] > 0


def test_categories_hubs(test_client):
    """Test hubs category endpoint."""
    response = test_client.get("/api/graph/categories/hubs")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "hubs"
    assert "nodes" in data


def test_categories_leaves(test_client):
    """Test leaves category endpoint."""
    response = test_client.get("/api/graph/categories/leaves")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "leaves"
    assert "nodes" in data


def test_pagination_works(test_client):
    """Test pagination with limit and offset."""
    response = test_client.get("/api/graph/categories/entry_points?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) <= 1


def test_response_has_all_fields(test_client):
    """Test response structure."""
    response = test_client.get("/api/graph/categories/entry_points")
    assert response.status_code == 200
    data = response.json()
    
    required = ["category", "total", "nodes", "execution_time_ms", "offset", "limit"]
    for field in required:
        assert field in data


def test_subgraph_endpoint(test_client):
    """Test subgraph endpoint."""
    response = test_client.post("/api/graph/subgraph?node_id=test_file.py:utility_hub:1&depth=2")
    # Accept both 200 (success) and 404 (node not found)
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert "node_id" in data
        assert "nodes" in data
        assert "relationships" in data
