#!/usr/bin/env python3
"""
Integration tests for MCP server with rustworkx backend.

Tests the complete integration of rustworkx functionality with the MCP server,
ensuring that all tools work correctly with the high-performance graph backend.
"""

import json
import pytest
import time
from unittest.mock import patch

from code_graph_mcp.server import UniversalAnalysisEngine
from code_graph_mcp.rustworkx_graph import RustworkxCodeGraph
from code_graph_mcp.universal_graph import (
    UniversalNode, UniversalRelationship, UniversalLocation,
    NodeType, RelationshipType
)


class TestMCPRustworkxIntegration:
    """Integration tests for MCP server with rustworkx backend."""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """Create a mock project root with sample Python files."""
        # Create sample Python files
        main_file = tmp_path / "main.py"
        main_file.write_text('''
def main():
    """Main function."""
    print("Hello, world!")
    helper_function()
    return 42

def helper_function():
    """Helper function."""
    data = process_data([1, 2, 3])
    return data

def process_data(items):
    """Process a list of items."""
    return [x * 2 for x in items]

class DataProcessor:
    """Class for processing data."""

    def __init__(self):
        self.data = []

    def add_data(self, item):
        """Add data item."""
        self.data.append(item)

    def process(self):
        """Process all data."""
        return process_data(self.data)
''')

        utils_file = tmp_path / "utils.py"
        utils_file.write_text('''
import json
from typing import List, Dict, Any

def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

def save_results(data: List[Any], filename: str) -> None:
    """Save results to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

class ConfigManager:
    """Manages application configuration."""

    def __init__(self, config_file: str):
        self.config_file = config_file
        self.config = load_config(config_file)

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)

    def update(self, key: str, value: Any):
        """Update configuration value."""
        self.config[key] = value
        save_results(self.config, self.config_file)
''')

        return tmp_path

    @pytest.fixture
    def analysis_engine(self, mock_project_root):
        """Create analysis engine with mock project."""
        with patch('code_graph_mcp.server.UniversalAnalysisEngine._ensure_analyzed'):
            engine = UniversalAnalysisEngine(mock_project_root)

            # Create a sample graph directly for testing
            graph = RustworkxCodeGraph()

            # Add sample nodes
            nodes = [
                UniversalNode(
                    id="file:main.py",
                    name="main.py",
                    node_type=NodeType.MODULE,
                    location=UniversalLocation(
                        file_path=str(mock_project_root / "main.py"),
                        start_line=1,
                        end_line=30,
                        language="Python"
                    ),
                    language="Python",
                    line_count=30
                ),
                UniversalNode(
                    id="function:main.py:main:2",
                    name="main",
                    node_type=NodeType.FUNCTION,
                    location=UniversalLocation(
                        file_path=str(mock_project_root / "main.py"),
                        start_line=2,
                        end_line=6,
                        language="Python"
                    ),
                    language="Python",
                    complexity=3,
                    docstring="Main function."
                ),
                UniversalNode(
                    id="function:main.py:helper_function:8",
                    name="helper_function",
                    node_type=NodeType.FUNCTION,
                    location=UniversalLocation(
                        file_path=str(mock_project_root / "main.py"),
                        start_line=8,
                        end_line=11,
                        language="Python"
                    ),
                    language="Python",
                    complexity=2,
                    docstring="Helper function."
                ),
                UniversalNode(
                    id="function:main.py:process_data:13",
                    name="process_data",
                    node_type=NodeType.FUNCTION,
                    location=UniversalLocation(
                        file_path=str(mock_project_root / "main.py"),
                        start_line=13,
                        end_line=15,
                        language="Python"
                    ),
                    language="Python",
                    complexity=1,
                    docstring="Process a list of items."
                ),
                UniversalNode(
                    id="class:main.py:DataProcessor:17",
                    name="DataProcessor",
                    node_type=NodeType.CLASS,
                    location=UniversalLocation(
                        file_path=str(mock_project_root / "main.py"),
                        start_line=17,
                        end_line=30,
                        language="Python"
                    ),
                    language="Python",
                    docstring="Class for processing data."
                )
            ]

            for node in nodes:
                graph.add_node(node)

            # Add sample relationships
            relationships = [
                UniversalRelationship(
                    id="contains:file:main:function:main",
                    source_id="file:main.py",
                    target_id="function:main.py:main:2",
                    relationship_type=RelationshipType.CONTAINS
                ),
                UniversalRelationship(
                    id="contains:file:main:function:helper",
                    source_id="file:main.py",
                    target_id="function:main.py:helper_function:8",
                    relationship_type=RelationshipType.CONTAINS
                ),
                UniversalRelationship(
                    id="calls:main:helper",
                    source_id="function:main.py:main:2",
                    target_id="function:main.py:helper_function:8",
                    relationship_type=RelationshipType.CALLS,
                    metadata={"call_line": 5}
                ),
                UniversalRelationship(
                    id="calls:helper:process_data",
                    source_id="function:main.py:helper_function:8",
                    target_id="function:main.py:process_data:13",
                    relationship_type=RelationshipType.CALLS,
                    metadata={"call_line": 10}
                )
            ]

            for rel in relationships:
                graph.add_relationship(rel)

            # Replace the engine's graph with our test graph
            engine.graph = graph
            engine._is_analyzed = True

            return engine

    def test_project_statistics_with_rustworkx(self, analysis_engine):
        """Test project statistics generation with rustworkx backend."""
        stats = analysis_engine.get_project_stats()

        # Verify basic statistics
        assert stats["total_nodes"] > 0
        assert stats["total_relationships"] > 0
        assert "node_types" in stats
        assert "last_analysis" in stats

        # Verify node types are present
        node_types = stats["node_types"]
        assert "module" in node_types
        assert "function" in node_types
        assert "class" in node_types

    def test_find_definition_with_rustworkx(self, analysis_engine):
        """Test symbol definition finding with rustworkx backend."""
        # Test finding a function
        main_defs = analysis_engine.find_symbol_definition("main")
        assert len(main_defs) > 0

        main_def = main_defs[0]
        assert main_def["name"] == "main"
        assert main_def["type"] == "function"
        assert main_def["complexity"] == 3
        assert "Main function" in main_def["documentation"]

        # Test finding a class
        class_defs = analysis_engine.find_symbol_definition("DataProcessor")
        assert len(class_defs) > 0

        class_def = class_defs[0]
        assert class_def["name"] == "DataProcessor"
        assert class_def["type"] == "class"

    def test_find_references_with_rustworkx(self, analysis_engine):
        """Test symbol reference finding with rustworkx backend."""
        # This would typically find references to symbols
        # For now, test that the method works without errors
        references = analysis_engine.find_symbol_references("process_data")
        assert isinstance(references, list)

    def test_find_callers_with_rustworkx(self, analysis_engine):
        """Test finding function callers with rustworkx backend."""
        # Test finding callers of helper_function
        callers = analysis_engine.find_function_callers("helper_function")

        # Should find that main() calls helper_function()
        assert len(callers) > 0
        caller = callers[0]
        assert caller["caller"] == "main"
        assert caller["target_function"] == "helper_function"
        assert caller["caller_type"] == "function"

    def test_find_callees_with_rustworkx(self, analysis_engine):
        """Test finding function callees with rustworkx backend."""
        # Test finding functions called by helper_function
        callees = analysis_engine.find_function_callees("helper_function")

        # Should find that helper_function() calls process_data()
        assert len(callees) > 0
        callee = callees[0]
        assert callee["callee"] == "process_data"
        assert callee["callee_type"] == "function"

    def test_complexity_analysis_with_rustworkx(self, analysis_engine):
        """Test complexity analysis with rustworkx backend."""
        # Test with low threshold to catch all functions
        complex_functions = analysis_engine.analyze_complexity(threshold=1)

        assert len(complex_functions) > 0

        # Check that functions have expected complexity data
        for func in complex_functions:
            assert "name" in func
            assert "complexity" in func
            assert "risk_level" in func
            assert "file" in func
            assert "line" in func
            assert func["complexity"] >= 1

    def test_dependency_analysis_with_rustworkx(self, analysis_engine):
        """Test dependency analysis with rustworkx enhanced features."""
        deps = analysis_engine.get_dependency_graph()

        # Verify basic structure
        assert "total_files" in deps
        assert "total_dependencies" in deps
        assert "dependencies" in deps

        # Verify rustworkx enhancements
        assert "circular_dependencies" in deps
        assert "is_directed_acyclic" in deps
        assert "strongly_connected_components" in deps
        assert "graph_density" in deps

        # Test that rustworkx analysis completed
        assert isinstance(deps["is_directed_acyclic"], bool)
        assert isinstance(deps["circular_dependencies"], list)
        assert isinstance(deps["graph_density"], (int, float))

    def test_code_insights_with_rustworkx(self, analysis_engine):
        """Test advanced code insights with rustworkx analytics."""
        insights = analysis_engine.get_code_insights()

        # Verify comprehensive analytics structure
        assert "centrality_analysis" in insights
        assert "structural_analysis" in insights
        assert "graph_statistics" in insights
        assert "topology_analysis" in insights

        # Test centrality analysis
        centrality = insights["centrality_analysis"]
        assert "betweenness_centrality" in centrality
        assert "pagerank" in centrality
        assert "closeness_centrality" in centrality
        assert "eigenvector_centrality" in centrality

        # Test structural analysis
        structural = insights["structural_analysis"]
        assert "articulation_points" in structural
        assert "bridges" in structural

        # Test topology analysis
        topology = insights["topology_analysis"]
        assert "is_directed_acyclic" in topology
        assert "num_cycles" in topology
        assert "strongly_connected_components" in topology

        # Verify that centrality calculations return results
        if centrality["betweenness_centrality"]:
            node_info = centrality["betweenness_centrality"][0]
            assert "node_id" in node_info
            assert "score" in node_info
            assert "node_name" in node_info
            assert "node_type" in node_info

    def test_graph_performance_metrics(self, analysis_engine):
        """Test performance characteristics of rustworkx backend."""
        import time

        # Test that basic operations are fast
        start_time = time.time()
        stats = analysis_engine.get_project_stats()
        stats_time = time.time() - start_time

        start_time = time.time()
        insights = analysis_engine.get_code_insights()
        insights_time = time.time() - start_time

        # Operations should complete quickly for small graphs
        assert stats_time < 1.0  # Less than 1 second
        assert insights_time < 5.0  # Less than 5 seconds

        # Verify we got meaningful results
        assert stats["total_nodes"] > 0
        assert len(insights["centrality_analysis"]["pagerank"]) > 0

    def test_rustworkx_serialization_integration(self, analysis_engine):
        """Test that rustworkx graph serialization works with MCP."""
        # Get the underlying rustworkx graph
        rustworkx_graph = analysis_engine.graph

        # Test JSON serialization
        json_output = rustworkx_graph.to_json()
        assert isinstance(json_output, str)
        assert len(json_output) > 100  # Should have substantial content

        # Verify it's valid JSON
        json_data = json.loads(json_output)
        assert isinstance(json_data, dict)

        # Test DOT serialization
        dot_output = rustworkx_graph.to_dot()
        assert isinstance(dot_output, str)
        assert "digraph" in dot_output.lower()

        # Test statistics
        graph_stats = rustworkx_graph.get_statistics()
        assert "total_nodes" in graph_stats
        assert "total_relationships" in graph_stats
        assert graph_stats["total_nodes"] > 0

    def test_error_handling_integration(self, analysis_engine):
        """Test error handling in MCP integration with rustworkx."""
        # Test non-existent symbol
        no_defs = analysis_engine.find_symbol_definition("nonexistent_symbol")
        assert len(no_defs) == 0

        no_callers = analysis_engine.find_function_callers("nonexistent_function")
        assert len(no_callers) == 0

        no_callees = analysis_engine.find_function_callees("nonexistent_function")
        assert len(no_callees) == 0

        # Operations should not crash and return empty results gracefully
        assert isinstance(no_defs, list)
        assert isinstance(no_callers, list)
        assert isinstance(no_callees, list)

    def test_large_graph_integration(self):
        """Test integration with a larger graph to verify scalability."""
        # Create a larger synthetic graph
        graph = RustworkxCodeGraph()

        # Add 100 nodes
        for i in range(100):
            node = UniversalNode(
                id=f"node_{i}",
                name=f"Function_{i}",
                node_type=NodeType.FUNCTION,
                location=UniversalLocation(
                    file_path=f"/test/file_{i//10}.py",
                    start_line=10 + i,
                    end_line=20 + i,
                    language="Python"
                ),
                language="Python",
                complexity=(i % 10) + 1
            )
            graph.add_node(node)

        # Add relationships
        for i in range(50):
            rel = UniversalRelationship(
                id=f"calls_{i}_{i+1}",
                source_id=f"node_{i}",
                target_id=f"node_{i+1}",
                relationship_type=RelationshipType.CALLS
            )
            graph.add_relationship(rel)

        # Test that rustworkx operations scale well
        start_time = time.time()

        centrality = graph.calculate_centrality()
        pagerank = graph.calculate_pagerank()
        stats = graph.get_statistics()

        total_time = time.time() - start_time

        # Should complete quickly even with 100 nodes
        assert total_time < 10.0
        assert len(centrality) == 100
        assert len(pagerank) == 100
        assert stats["total_nodes"] == 100

    @pytest.mark.asyncio
    async def test_mcp_tool_handlers_with_rustworkx(self, analysis_engine):
        """Test that MCP tool handlers work correctly with rustworkx backend."""
        from code_graph_mcp.server import (
            handle_analyze_codebase,
            handle_find_definition,
            handle_find_callers,
            handle_complexity_analysis,
            handle_project_statistics
        )

        # Test analyze_codebase handler
        result = await handle_analyze_codebase(analysis_engine, {})
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Analysis Complete" in result[0].text

        # Test find_definition handler
        result = await handle_find_definition(analysis_engine, {"symbol": "main"})
        assert len(result) == 1
        assert "Definition Analysis" in result[0].text

        # Test find_callers handler
        result = await handle_find_callers(analysis_engine, {"function": "helper_function"})
        assert len(result) == 1
        assert "Caller Analysis" in result[0].text

        # Test complexity_analysis handler
        result = await handle_complexity_analysis(analysis_engine, {"threshold": 1})
        assert len(result) == 1
        assert "Complexity Analysis" in result[0].text

        # Test project_statistics handler with rustworkx enhancements
        result = await handle_project_statistics(analysis_engine, {})
        assert len(result) == 1
        text_content = result[0].text
        assert "Advanced Project Statistics" in text_content
        assert "Powered by rustworkx" in text_content
        assert "Graph Analytics" in text_content
        assert "Most Central Code Elements" in text_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
