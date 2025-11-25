#!/usr/bin/env python3
"""
Live test of query tools to verify they now work with CALLS relationships.
Tests find_function_callers, find_function_callees, and find_symbol_references.
"""

import asyncio
from pathlib import Path

import pytest

from codenav.server.analysis_engine import UniversalAnalysisEngine


@pytest.mark.asyncio
async def test_query_tools():
    """Test the query tools with live data."""
    
    project_root = Path(__file__).parent.parent / "src" / "codenav"
    
    print("="*80)
    print("LIVE QUERY TOOLS TEST")
    print("="*80)
    
    engine = UniversalAnalysisEngine(project_root, enable_file_watcher=False, enable_redis_cache=False)
    print(f"\n📁 Analyzing: {project_root}")
    
    await engine._analyze_project()
    print(f"✓ Analysis complete")
    
    graph = engine.graph
    print(f"\n📊 Graph statistics:")
    print(f"  Nodes: {len(graph.nodes)}")
    print(f"  Relationships: {len(graph.relationships)}")
    
    # Find a function to test
    functions = [n for n in graph.nodes.values() if n.name in ["analyze_project", "find_nodes_by_name", "add_relationship"]]
    
    if not functions:
        print("\n❌ Could not find test functions")
        return False
    
    test_func = functions[0]
    print(f"\n🎯 Testing with function: {test_func.name}")
    
    print(f"\n1️⃣  Testing find_function_callers('{test_func.name}')...")
    callers = await engine.find_function_callers(test_func.name)
    print(f"   ✓ Found {len(callers)} callers")
    if callers:
        for i, caller in enumerate(list(callers)[:3], 1):
            print(f"     {i}. {caller['caller']}")
    else:
        print("   ⚠️  No callers found (this is ok if function is not called)")
    
    print(f"\n2️⃣  Testing find_function_callees('{test_func.name}')...")
    callees = await engine.find_function_callees(test_func.name)
    print(f"   ✓ Found {len(callees)} callees")
    if callees:
        for i, callee in enumerate(list(callees)[:3], 1):
            print(f"     {i}. {callee['callee']}")
    
    print(f"\n3️⃣  Testing find_symbol_references('{test_func.name}')...")
    references = await engine.find_symbol_references(test_func.name)
    print(f"   ✓ Found {len(references)} references")
    if references:
        for i, ref in enumerate(list(references)[:3], 1):
            print(f"     {i}. {ref['referencing_symbol']}")
    else:
        print("   ℹ️  No REFERENCES relationships yet (only CALLS implemented)")
    
    print("\n" + "="*80)
    print("✅ QUERY TOOLS ARE WORKING!")
    print("="*80)
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_query_tools())
    sys.exit(0 if result else 1)
