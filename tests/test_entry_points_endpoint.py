"""
Test cases for entry-points API endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.code_graph_mcp.server.graph_api import create_graph_api_router
from src.code_graph_mcp.server.analysis_engine import UniversalAnalysisEngine
from src.code_graph_mcp.universal_graph import UniversalGraph, UniversalNode, NodeType, UniversalRelationship, RelationshipType

class TestEntryPointsEndpoint:
    
    @pytest.fixture
    def mock_engine(self):
        """Create a mock analysis engine."""
        engine = Mock(spec=UniversalAnalysisEngine)
        engine.analyzer = Mock()
        engine.analyzer.graph = Mock(spec=UniversalGraph)
        
        # Mock graph data
        mock_node1 = Mock(spec=UniversalNode)
        mock_node1.node_id = "node1"
        mock_node1.name = "main"
        mock_node1.language = "python"
        mock_node1.complexity = 5
        mock_node1.location = Mock()
        mock_node1.location.file_path = "/test/main.py"
        mock_node1.location.start_line = 10
        mock_node1.node_type = NodeType.FUNCTION
        
        mock_node2 = Mock(spec=UniversalNode)
        mock_node2.node_id = "node2"
        mock_node2.name = "app"
        mock_node2.language = "javascript"
        mock_node2.complexity = 3
        mock_node2.location = Mock()
        mock_node2.location.file_path = "/test/server.js"
        mock_node2.location.start_line = 5
        mock_node2.node_type = NodeType.MODULE
        
        engine.analyzer.graph.nodes = {
            "node1": mock_node1,
            "node2": mock_node2
        }
        
        return engine
    
    @pytest.fixture
    def client(self, mock_engine):
        """Create test client with graph API router."""
        from fastapi import FastAPI
        app = FastAPI()
        router = create_graph_api_router(mock_engine)
        app.include_router(router)
        return TestClient(app)
    
    def test_get_entry_points_success(self, client, mock_engine):
        """Test successful entry points retrieval."""
        # Mock file reading
        with patch("builtins.open", mock_open(read_data="def main():\n    pass")):
            response = client.get("/api/graph/entry-points")
            
        assert response.status_code == 200
        data = response.json()
        
        assert "entry_points" in data
        assert "total_count" in data
        assert "execution_time_ms" in data
    
    def test_get_entry_points_with_params(self, client, mock_engine):
        """Test entry points retrieval with parameters."""
        with patch("builtins.open", mock_open(read_data="def main():\n    pass")):
            response = client.get("/api/graph/entry-points?limit=10&min_confidence=1.0")
            
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 0
    
    def test_get_entry_points_no_graph(self, client):
        """Test entry points retrieval when graph is not ready."""
        # Create engine with no analyzer
        broken_engine = Mock()
        broken_engine.analyzer = None
        
        from fastapi import FastAPI
        app = FastAPI()
        router = create_graph_api_router(broken_engine)
        app.include_router(router)
        broken_client = TestClient(app)
        
        response = broken_client.get("/api/graph/entry-points")
        assert response.status_code == 500
    
    def test_entry_point_response_structure(self, client, mock_engine):
        """Test that entry point response has correct structure."""
        with patch("builtins.open", mock_open(read_data="def main():\n    pass")):
            response = client.get("/api/graph/entry-points")
            
        assert response.status_code == 200
        data = response.json()
        
        if data["entry_points"]:  # If any entry points were detected
            entry_point = data["entry_points"][0]
            required_fields = [
                "id", "name", "file_path", "language", "line_number",
                "pattern_matched", "confidence_score", "complexity", "type"
            ]
            
            for field in required_fields:
                assert field in entry_point

if __name__ == "__main__":
    pytest.main([__file__])