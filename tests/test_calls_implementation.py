#!/usr/bin/env python3
"""
Test that CALLS relationships are now being created by the parser.
This validates the fix for the zero results issue.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_graph_mcp.universal_parser import UniversalParser
from code_graph_mcp.universal_graph import RelationshipType, NodeType

@pytest.mark.asyncio
async def test_calls_extraction():
    """Test that function calls are being extracted and CALLS relationships created."""
    
    project_root = Path("/app/src/code_graph_mcp")
    if not project_root.exists():
        print(f"Project root not found: {project_root}")
        return False
    
    print("="*80)
    print("TESTING CALLS RELATIONSHIP EXTRACTION")
    print("="*80)
    
    parser = UniversalParser()
    print(f"\n📁 Parsing: {project_root}")
    
    files_parsed = await parser.parse_directory(project_root, recursive=True)
    print(f"✓ Parsed {files_parsed} files")
    
    graph = parser.graph
    
    print(f"\n📊 GRAPH STATISTICS:")
    print(f"  Total nodes: {len(graph.nodes)}")
    print(f"  Total relationships: {len(graph.relationships)}")
    
    if len(graph.nodes) == 0:
        print("\n❌ FAILED: No nodes extracted")
        return False
    
    print(f"\n✓ Graph has {len(graph.nodes)} nodes")
    
    rel_counts = {}
    for rel_type in RelationshipType:
        rels = graph.get_relationships_by_type(rel_type)
        count = len(rels)
        rel_counts[rel_type] = count
        print(f"  {rel_type.name:15}: {count:4} relationships")
    
    calls_count = rel_counts.get(RelationshipType.CALLS, 0)
    
    if calls_count == 0:
        print(f"\n⚠️  WARNING: No CALLS relationships created")
        print("   This means find_function_callers and find_function_callees will still return 0 results")
        return False
    
    print(f"\n✅ SUCCESS: Found {calls_count} CALLS relationships!")
    print("   find_function_callers and find_function_callees should now work")
    
    # Show some examples
    calls = graph.get_relationships_by_type(RelationshipType.CALLS)
    print(f"\n📋 First 5 CALLS relationships:")
    for i, rel in enumerate(list(calls)[:5], 1):
        source = graph.get_node(rel.source_id)
        target = graph.get_node(rel.target_id)
        if source and target:
            print(f"  {i}. {source.name} → {target.name}")
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_calls_extraction())
    sys.exit(0 if result else 1)
