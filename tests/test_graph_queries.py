#!/usr/bin/env python3
"""
Comprehensive tests for graph query tools:
- find_references
- find_callers
- find_callees

These tests diagnose why these tools return zero results despite having data in Redis.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_graph_mcp.server.analysis_engine import UniversalAnalysisEngine
from code_graph_mcp.universal_graph import RelationshipType, NodeType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
async def analysis_engine():
    """Initialize analysis engine for testing."""
    project_root = Path("/app/workspace")
    if not project_root.exists():
        pytest.skip("Test workspace not available")
    
    engine = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine.analyze()
    yield engine


@pytest.mark.asyncio
async def test_graph_contains_nodes(analysis_engine):
    """Verify that graph has nodes after analysis."""
    graph = analysis_engine.graph
    total_nodes = len(graph.nodes)
    logger.info(f"Total nodes in graph: {total_nodes}")
    
    assert total_nodes > 0, "Graph should contain nodes after analysis"


@pytest.mark.asyncio
async def test_relationship_types_exist(analysis_engine):
    """Check that all relationship types are represented."""
    graph = analysis_engine.graph
    
    relationship_counts = {}
    for rel_type in RelationshipType:
        rels = graph.get_relationships_by_type(rel_type)
        relationship_counts[rel_type.name] = len(rels)
        logger.info(f"{rel_type.name}: {len(rels)} relationships")
    
    # At least CALLS should exist
    assert relationship_counts.get("CALLS", 0) > 0 or \
           relationship_counts.get("REFERENCES", 0) > 0, \
           "Graph should have either CALLS or REFERENCES relationships"


@pytest.mark.asyncio
async def test_relationship_indexing(analysis_engine):
    """Verify relationship indexing is working correctly."""
    graph = analysis_engine.graph
    
    # Sample a relationship and verify indexing
    if not graph.relationships:
        pytest.skip("No relationships to test")
    
    first_rel = next(iter(graph.relationships.values()))
    source_id = first_rel.source_id
    target_id = first_rel.target_id
    
    # Check if relationships are properly indexed
    rels_from = graph.get_relationships_from(source_id)
    rels_to = graph.get_relationships_to(target_id)
    
    logger.info(f"Sample relationship: {first_rel.source_id} -> {first_rel.target_id}")
    logger.info(f"Relationships from source: {len(rels_from)}")
    logger.info(f"Relationships to target: {len(rels_to)}")
    
    assert len(rels_from) > 0, "Should find relationships from source"
    assert len(rels_to) > 0, "Should find relationships to target"
    assert first_rel in rels_from, "Sampled relationship should be in rels_from"
    assert first_rel in rels_to, "Sampled relationship should be in rels_to"


@pytest.mark.asyncio
async def test_find_nodes_by_name(analysis_engine):
    """Test finding nodes by name."""
    graph = analysis_engine.graph
    
    # Find some nodes
    if graph.nodes:
        first_node = next(iter(graph.nodes.values()))
        logger.info(f"Testing with node: {first_node.name}")
        
        # Search for exact match
        results = graph.find_nodes_by_name(first_node.name, exact_match=True)
        logger.info(f"Exact match results: {len(results)}")
        assert len(results) > 0
        assert first_node in results
        
        # Search for fuzzy match
        if len(first_node.name) > 2:
            partial = first_node.name[:2]
            fuzzy_results = graph.find_nodes_by_name(partial, exact_match=False)
            logger.info(f"Fuzzy match for '{partial}': {len(fuzzy_results)}")


@pytest.mark.asyncio
async def test_find_symbol_references(analysis_engine):
    """Test find_symbol_references engine method."""
    graph = analysis_engine.graph
    
    # Find a node with relationships
    nodes_with_incoming = []
    for node_id, node in graph.nodes.items():
        rels_to = graph.get_relationships_to(node_id)
        if rels_to:
            nodes_with_incoming.append((node, rels_to))
    
    if not nodes_with_incoming:
        logger.warning("No nodes with incoming relationships found")
        pytest.skip("No reference relationships to test")
    
    test_node, rels = nodes_with_incoming[0]
    logger.info(f"Testing references for node: {test_node.name}")
    logger.info(f"Node has {len(rels)} incoming relationships")
    
    # Call find_symbol_references
    references = await analysis_engine.find_symbol_references(test_node.name)
    logger.info(f"find_symbol_references returned: {len(references)} results")
    logger.info(f"Expected at least: {len(rels)} results")
    
    for ref in references[:3]:
        logger.info(f"  - {ref}")


@pytest.mark.asyncio
async def test_find_callers(analysis_engine):
    """Test find_function_callers engine method."""
    graph = analysis_engine.graph
    
    # Find a function/method node
    function_nodes = [
        node for node in graph.nodes.values()
        if node.node_type == NodeType.FUNCTION
    ]
    
    if not function_nodes:
        pytest.skip("No function nodes found in graph")
    
    test_func = function_nodes[0]
    logger.info(f"Testing callers for: {test_func.name}")
    
    callers = await analysis_engine.find_function_callers(test_func.name)
    logger.info(f"find_function_callers returned: {len(callers)} results")
    
    for caller in callers[:3]:
        logger.info(f"  - {caller}")


@pytest.mark.asyncio
async def test_find_callees(analysis_engine):
    """Test find_function_callees engine method."""
    graph = analysis_engine.graph
    
    # Find a function/method node with outgoing calls
    function_nodes = [
        node for node in graph.nodes.values()
        if node.node_type == NodeType.FUNCTION
    ]
    
    if not function_nodes:
        pytest.skip("No function nodes found in graph")
    
    test_func = function_nodes[0]
    logger.info(f"Testing callees for: {test_func.name}")
    
    callees = await analysis_engine.find_function_callees(test_func.name)
    logger.info(f"find_function_callees returned: {len(callees)} results")
    
    for callee in callees[:3]:
        logger.info(f"  - {callee}")


@pytest.mark.asyncio
async def test_graph_relationship_type_mismatch():
    """
    Diagnose potential issue: find_symbol_references looks for REFERENCES type,
    but the parser might be creating CALLS relationships instead.
    """
    project_root = Path("/app/workspace")
    if not project_root.exists():
        pytest.skip("Test workspace not available")
    
    engine = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=True
    )
    await engine.analyze()
    graph = engine.graph
    
    # Count each relationship type
    logger.info("\n=== RELATIONSHIP TYPE ANALYSIS ===")
    for rel_type in RelationshipType:
        rels = graph.get_relationships_by_type(rel_type)
        logger.info(f"{rel_type.name}: {len(rels)}")
        if rels:
            sample = rels[0]
            logger.info(f"  Sample: {sample.source_id} -> {sample.target_id}")
    
    logger.info("\n=== POTENTIAL ISSUE ===")
    refs = graph.get_relationships_by_type(RelationshipType.REFERENCES)
    calls = graph.get_relationships_by_type(RelationshipType.CALLS)
    
    if len(refs) == 0 and len(calls) > 0:
        logger.warning(
            "⚠️  MISMATCH DETECTED: No REFERENCES relationships but "
            f"{len(calls)} CALLS relationships exist!"
        )
        logger.warning(
            "This explains why find_symbol_references returns 0 results - "
            "it's looking for REFERENCES but only CALLS exist."
        )


@pytest.mark.asyncio
async def test_engine_methods_exist(analysis_engine):
    """Verify all required methods exist on engine."""
    required_methods = [
        'find_symbol_references',
        'find_function_callers',
        'find_function_callees',
    ]
    
    for method_name in required_methods:
        assert hasattr(analysis_engine, method_name), \
            f"Engine missing method: {method_name}"
        
        method = getattr(analysis_engine, method_name)
        assert callable(method), f"{method_name} is not callable"
        logger.info(f"✓ {method_name} exists and is callable")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
