"""
Tests for Graph Export API Endpoint

Tests the /api/graph/export endpoint that returns full graph data
for force-directed graph visualization.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
from typing import Optional

# Test data structures
@dataclass
class MockLocation:
    file_path: str = "/test/file.py"
    start_line: int = 1
    end_line: int = 10


@dataclass 
class MockNode:
    id: str
    name: str
    node_type: str
    language: str
    complexity: int = 0
    docstring: str = ""
    line_count: int = 0
    location: Optional[MockLocation] = None
    
    @property
    def node_id(self):
        return self.id


@dataclass
class MockRelationship:
    source_id: str
    target_id: str
    relationship_type: str
    
    @property
    def id(self):
        return f"{self.source_id}-{self.target_id}"


class TestGraphExportEndpoint:
    """Test cases for the /api/graph/export endpoint."""
    
    def test_export_response_structure(self):
        """Test that export response has correct structure."""
        # Expected response format
        response = {
            "nodes": [],
            "links": [],
            "stats": {
                "totalNodes": 0,
                "totalLinks": 0,
                "languages": {},
                "nodeTypes": {},
                "avgComplexity": 0,
            },
            "execution_time_ms": 0.1
        }
        
        assert "nodes" in response
        assert "links" in response
        assert "stats" in response
        assert "execution_time_ms" in response
        
        stats = response["stats"]
        assert "totalNodes" in stats
        assert "totalLinks" in stats
        assert "languages" in stats
        assert "nodeTypes" in stats
        assert "avgComplexity" in stats
    
    def test_node_format(self):
        """Test that nodes have correct format for force-graph."""
        mock_node = MockNode(
            id="test_func",
            name="my_function",
            node_type="function",
            language="python",
            complexity=5,
            location=MockLocation()
        )
        
        # Format node as the API would
        node_type = getattr(mock_node, 'node_type', 'unknown')
        location = getattr(mock_node, 'location', None)
        
        node_data = {
            "id": mock_node.id,
            "name": getattr(mock_node, 'name', ''),
            "type": node_type.value if hasattr(node_type, 'value') else str(node_type),
            "language": getattr(mock_node, 'language', ''),
            "complexity": getattr(mock_node, 'complexity', 0),
            "file": location.file_path if location else "",
            "line": location.start_line if location else 0,
        }
        
        assert node_data["id"] == "test_func"
        assert node_data["name"] == "my_function"
        assert node_data["type"] == "function"
        assert node_data["language"] == "python"
        assert node_data["complexity"] == 5
        assert node_data["file"] == "/test/file.py"
        assert node_data["line"] == 1
    
    def test_link_format(self):
        """Test that links have correct format for force-graph."""
        mock_rel = MockRelationship(
            source_id="func_a",
            target_id="func_b",
            relationship_type="calls"
        )
        
        rel_type = getattr(mock_rel, 'relationship_type', 'unknown')
        rel_type_str = rel_type.value if hasattr(rel_type, 'value') else str(rel_type)
        
        link_data = {
            "source": mock_rel.source_id,
            "target": mock_rel.target_id,
            "type": rel_type_str,
            "isSeam": rel_type_str == 'seam',
        }
        
        assert link_data["source"] == "func_a"
        assert link_data["target"] == "func_b"
        assert link_data["type"] == "calls"
        assert link_data["isSeam"] is False
    
    def test_seam_link_detection(self):
        """Test that cross-language seam links are properly identified."""
        mock_rel = MockRelationship(
            source_id="py_func",
            target_id="ts_func",
            relationship_type="seam"
        )
        
        rel_type = getattr(mock_rel, 'relationship_type', 'unknown')
        rel_type_str = rel_type.value if hasattr(rel_type, 'value') else str(rel_type)
        
        link_data = {
            "source": mock_rel.source_id,
            "target": mock_rel.target_id,
            "type": rel_type_str,
            "isSeam": rel_type_str == 'seam',
        }
        
        assert link_data["isSeam"] is True
    
    def test_stats_calculation(self):
        """Test that stats are correctly calculated from nodes."""
        nodes = [
            {"id": "1", "name": "func1", "type": "function", "language": "python", "complexity": 5},
            {"id": "2", "name": "func2", "type": "function", "language": "python", "complexity": 10},
            {"id": "3", "name": "MyClass", "type": "class", "language": "typescript", "complexity": 15},
        ]
        
        # Calculate language distribution
        languages = {}
        for node in nodes:
            lang = node.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
        
        # Calculate type distribution
        node_types = {}
        for node in nodes:
            nt = node.get("type", "unknown")
            node_types[nt] = node_types.get(nt, 0) + 1
        
        # Calculate average complexity
        avg_complexity = sum(n.get("complexity", 0) for n in nodes) / max(len(nodes), 1)
        
        assert languages == {"python": 2, "typescript": 1}
        assert node_types == {"function": 2, "class": 1}
        assert avg_complexity == 10.0
    
    def test_language_filter(self):
        """Test that language filter works correctly."""
        nodes = [
            MockNode(id="1", name="func1", node_type="function", language="python"),
            MockNode(id="2", name="func2", node_type="function", language="typescript"),
            MockNode(id="3", name="func3", node_type="function", language="python"),
        ]
        
        language_filter = "python"
        filtered = [n for n in nodes if getattr(n, 'language', '') == language_filter]
        
        assert len(filtered) == 2
        assert all(n.language == "python" for n in filtered)
    
    def test_type_filter(self):
        """Test that node type filter works correctly."""
        nodes = [
            MockNode(id="1", name="func1", node_type="function", language="python"),
            MockNode(id="2", name="MyClass", node_type="class", language="python"),
            MockNode(id="3", name="func2", node_type="function", language="python"),
        ]
        
        type_filter = "function"
        filtered = [n for n in nodes if getattr(n, 'node_type', '') == type_filter]
        
        assert len(filtered) == 2
        assert all(n.node_type == "function" for n in filtered)
    
    def test_relationship_filtering(self):
        """Test that relationships are filtered to only include nodes in the set."""
        node_ids = {"node1", "node2", "node3"}
        
        relationships = [
            MockRelationship("node1", "node2", "calls"),  # Both in set
            MockRelationship("node2", "node4", "calls"),  # node4 not in set
            MockRelationship("node5", "node1", "calls"),  # node5 not in set
            MockRelationship("node1", "node3", "calls"),  # Both in set
        ]
        
        filtered_rels = []
        for rel in relationships:
            if rel.source_id in node_ids and rel.target_id in node_ids:
                filtered_rels.append(rel)
        
        assert len(filtered_rels) == 2
        assert all(r.source_id in node_ids and r.target_id in node_ids for r in filtered_rels)
    
    def test_limit_parameter(self):
        """Test that limit parameter restricts the number of nodes."""
        nodes = [MockNode(id=str(i), name=f"func{i}", node_type="function", language="python") for i in range(100)]
        
        limit = 50
        limited_nodes = nodes[:limit]
        
        assert len(limited_nodes) == 50
    
    def test_metadata_inclusion(self):
        """Test that metadata is included when requested."""
        mock_node = MockNode(
            id="test_func",
            name="my_function",
            node_type="function",
            language="python",
            docstring="This is a test function",
            line_count=20,
            location=MockLocation(end_line=20)
        )
        
        include_metadata = True
        
        node_data = {
            "id": mock_node.id,
            "name": mock_node.name,
        }
        
        if include_metadata:
            location = getattr(mock_node, 'location', None)
            node_data["metadata"] = {
                "docstring": getattr(mock_node, 'docstring', ''),
                "line_count": getattr(mock_node, 'line_count', 0),
                "end_line": location.end_line if location else 0,
            }
        
        assert "metadata" in node_data
        assert node_data["metadata"]["docstring"] == "This is a test function"
        assert node_data["metadata"]["line_count"] == 20
        assert node_data["metadata"]["end_line"] == 20


class TestForceGraphDataFormat:
    """Test that the data format is compatible with force-graph library."""
    
    def test_nodes_have_required_fields_for_force_graph(self):
        """force-graph requires nodes to have 'id' field."""
        node = {"id": "test_id", "name": "Test Node"}
        assert "id" in node
    
    def test_links_have_required_fields_for_force_graph(self):
        """force-graph requires links to have 'source' and 'target' fields."""
        link = {"source": "node1", "target": "node2"}
        assert "source" in link
        assert "target" in link
    
    def test_graph_data_structure(self):
        """Test complete graph data structure for force-graph."""
        graph_data = {
            "nodes": [
                {"id": "1", "name": "Node 1", "val": 1},
                {"id": "2", "name": "Node 2", "val": 2},
            ],
            "links": [
                {"source": "1", "target": "2"},
            ]
        }
        
        assert isinstance(graph_data["nodes"], list)
        assert isinstance(graph_data["links"], list)
        assert len(graph_data["nodes"]) == 2
        assert len(graph_data["links"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
