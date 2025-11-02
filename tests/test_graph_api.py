"""
Tests for Graph Query API Endpoints

Tests for REST API endpoints including traversal, search, and seam detection.
"""

import pytest
import time
from pathlib import Path

from src.code_graph_mcp.graph.query_response import (
    NodeResponse,
    RelationshipResponse,
    TraversalResponse,
)
from src.code_graph_mcp.graph.rustworkx_unified import RustworkxCodeGraph
from src.code_graph_mcp.universal_graph import (
    UniversalLocation,
    UniversalNode,
    UniversalRelationship,
    NodeType,
    RelationshipType,
)


class TestResponseModels:
    """Test query response model serialization."""

    def test_node_response_serialization(self):
        """Test NodeResponse serialization."""
        node_resp = NodeResponse(
            id="test_node",
            name="TestNode",
            type="function",
            language="python",
            file_path="/path/to/file.py",
            start_line=1,
            end_line=10,
            complexity=2
        )
        
        node_dict = node_resp.to_dict()
        assert node_dict["id"] == "test_node"
        assert node_dict["name"] == "TestNode"
        assert node_dict["type"] == "function"

    def test_traversal_response_serialization(self):
        """Test TraversalResponse serialization."""
        nodes = [
            NodeResponse(
                id="node1",
                name="Node1",
                type="function",
                language="python"
            ),
            NodeResponse(
                id="node2",
                name="Node2",
                type="class",
                language="python"
            )
        ]
        
        response = TraversalResponse(
            nodes=nodes,
            edges=[],
            stats={"nodes_traversed": 2},
            execution_time_ms=10.5,
            query_type="bfs",
            max_depth=5
        )
        
        response_dict = response.to_dict()
        assert len(response_dict["nodes"]) == 2
        assert response_dict["stats"]["nodes_traversed"] == 2


class TestTraversalAlgorithms:
    """Test traversal algorithm implementations."""

    def test_dfs_traversal_with_depth(self):
        """Test DFS traversal with depth tracking."""
        graph = RustworkxCodeGraph()
        
        # Add test nodes
        loc = UniversalLocation(file_path="test.py", start_line=1, end_line=10)
        n1 = UniversalNode("n1", "Node1", NodeType.FUNCTION, loc, language="python")
        n2 = UniversalNode("n2", "Node2", NodeType.FUNCTION, loc, language="python")
        n3 = UniversalNode("n3", "Node3", NodeType.FUNCTION, loc, language="python")
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        # Add relationships
        r1 = UniversalRelationship(
            id="r1", source_id="n1", target_id="n2", relationship_type=RelationshipType.CALLS
        )
        r2 = UniversalRelationship(
            id="r2", source_id="n2", target_id="n3", relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(r1)
        graph.add_relationship(r2)
        
        # Test DFS
        result = graph.dfs_traversal_with_depth("n1", max_depth=5)
        
        assert "nodes_by_depth" in result
        assert "total_nodes" in result
        assert result["total_nodes"] > 0

    def test_find_call_chain(self):
        """Test call chain finding."""
        graph = RustworkxCodeGraph()
        
        # Add test nodes
        loc = UniversalLocation(file_path="test.py", start_line=1, end_line=10)
        n1 = UniversalNode("n1", "Node1", NodeType.FUNCTION, loc, language="python")
        n2 = UniversalNode("n2", "Node2", NodeType.FUNCTION, loc, language="python")
        n3 = UniversalNode("n3", "Node3", NodeType.FUNCTION, loc, language="python")
        
        graph.add_node(n1)
        graph.add_node(n2)
        graph.add_node(n3)
        
        # Add relationships
        r1 = UniversalRelationship(
            id="r1", source_id="n1", target_id="n2", relationship_type=RelationshipType.CALLS
        )
        r2 = UniversalRelationship(
            id="r2", source_id="n2", target_id="n3", relationship_type=RelationshipType.CALLS
        )
        graph.add_relationship(r1)
        graph.add_relationship(r2)
        
        # Test call chain
        chain = graph.find_call_chain("n1", "n3")
        assert isinstance(chain, list)

    def test_trace_cross_language_flow(self):
        """Test cross-language flow tracing."""
        graph = RustworkxCodeGraph()
        
        # Add test nodes in different languages
        loc_py = UniversalLocation(file_path="test.py", start_line=1, end_line=10)
        loc_js = UniversalLocation(file_path="test.js", start_line=1, end_line=10)
        
        py_func = UniversalNode("py_func", "PythonFunc", NodeType.FUNCTION, loc_py, language="python")
        js_func = UniversalNode("js_func", "JavaScriptFunc", NodeType.FUNCTION, loc_js, language="javascript")
        
        graph.add_node(py_func)
        graph.add_node(js_func)
        
        # Add SEAM relationship
        seam_rel = UniversalRelationship(
            id="seam1", source_id="py_func", target_id="js_func", relationship_type=RelationshipType.SEAM
        )
        graph.add_relationship(seam_rel)
        
        # Test cross-language tracing
        result = graph.trace_cross_language_flow("py_func")
        
        assert "language_flow" in result
        assert "seam_bridges" in result


class TestPerformance:
    """Test performance characteristics."""

    def test_traversal_performance(self):
        """Test that graph traversal completes in reasonable time."""
        graph = RustworkxCodeGraph()
        loc = UniversalLocation(file_path="test.py", start_line=1, end_line=10)
        
        # Create a small test graph
        for i in range(100):
            node = UniversalNode(f"n{i}", f"Node{i}", NodeType.FUNCTION, loc, language="python")
            graph.add_node(node)
        
        for i in range(99):
            rel = UniversalRelationship(
                id=f"r{i}", source_id=f"n{i}", target_id=f"n{i+1}", relationship_type=RelationshipType.CALLS
            )
            graph.add_relationship(rel)
        
        start = time.time()
        result = graph.dfs_traversal_with_depth("n0", max_depth=20)
        elapsed_ms = (time.time() - start) * 1000
        
        assert elapsed_ms < 100, f"DFS took {elapsed_ms}ms (should be <100ms)"
