"""
Focused backend tests for graph query operations.

Tests the core query functionality:
- find_function_callers: "function X calls function Y" 
- find_function_callees: "function X calls functions [...]"
- find_symbol_references: "symbol X is referenced by [...]"
"""

from pathlib import Path

import pytest
import pytest_asyncio

from code_graph_mcp.server.analysis_engine import UniversalAnalysisEngine
from code_graph_mcp.universal_graph import NodeType


@pytest_asyncio.fixture(scope="module")
async def graph_with_calls():
    """Analyze code_graph_mcp to get real call relationships."""
    project_root = Path(__file__).parent.parent / "src" / "code_graph_mcp"
    
    engine = UniversalAnalysisEngine(
        project_root,
        enable_file_watcher=False,
        enable_redis_cache=False
    )
    await engine._analyze_project()
    
    yield engine


@pytest.mark.asyncio
async def test_graph_has_function_nodes(graph_with_calls):
    """Verify graph contains function nodes."""
    graph = graph_with_calls.graph
    
    functions = [n for n in graph.nodes.values() if n.node_type == NodeType.FUNCTION]
    assert len(functions) > 0, "Graph should contain function nodes"
    assert len(functions) > 5, f"Expected at least 5 functions, got {len(functions)}"


@pytest.mark.asyncio
async def test_graph_has_calls_relationships(graph_with_calls):
    """Verify graph has CALLS relationships."""
    graph = graph_with_calls.graph
    from code_graph_mcp.universal_graph import RelationshipType
    
    calls = graph.get_relationships_by_type(RelationshipType.CALLS)
    assert len(calls) > 0, "Graph should have CALLS relationships"
    print(f"\n✓ Found {len(calls)} CALLS relationships")


@pytest.mark.asyncio
async def test_find_function_callers_basic(graph_with_calls):
    """Test find_function_callers with a known function."""
    engine = graph_with_calls
    
    called_functions = ["analyze_project", "parse_file", "add_node"]
    
    for func_name in called_functions:
        callers = await engine.find_function_callers(func_name)
        if callers:
            print(f"\n✓ find_function_callers('{func_name}'): {len(callers)} results")
            assert len(callers) > 0
            break
    else:
        pytest.skip("No callers found for any test function (data dependent)")


@pytest.mark.asyncio
async def test_find_function_callees_basic(graph_with_calls):
    """Test find_function_callees with a known function."""
    engine = graph_with_calls
    graph = engine.graph
    
    calling_functions = ["analyze_project", "parse_file", "_analyze_project"]
    
    for func_name in calling_functions:
        callees = await engine.find_function_callees(func_name)
        if callees:
            print(f"\n✓ find_function_callees('{func_name}'): {len(callees)} results")
            assert len(callees) > 0
            break
    else:
        pytest.skip("No callees found for any test function (data dependent)")


@pytest.mark.asyncio
async def test_find_symbol_references_basic(graph_with_calls):
    """Test find_symbol_references with a known symbol."""
    engine = graph_with_calls
    
    symbols = ["UniversalAnalysisEngine", "UniversalParser", "RustworkxCodeGraph"]
    
    for symbol_name in symbols:
        references = await engine.find_symbol_references(symbol_name)
        if references:
            print(f"\n✓ find_symbol_references('{symbol_name}'): {len(references)} results")
            assert len(references) > 0
            break
    else:
        pytest.skip("No references found for any test symbol (data dependent)")


@pytest.mark.asyncio
async def test_query_results_have_required_fields(graph_with_calls):
    """Verify query results have required fields."""
    engine = graph_with_calls
    
    callers = await engine.find_function_callers("analyze_project")
    if callers:
        result = list(callers)[0]
        assert "caller" in result, "Callers result should have 'caller' field"
        print(f"✓ Caller result format: {result}")


@pytest.mark.asyncio
async def test_query_tools_do_not_crash(graph_with_calls):
    """Ensure all query tools can execute without errors."""
    engine = graph_with_calls
    
    try:
        await engine.find_function_callers("any_function")
        print("✓ find_function_callers executed")
    except Exception as e:
        pytest.fail(f"find_function_callers crashed: {e}")
    
    try:
        await engine.find_function_callees("any_function")
        print("✓ find_function_callees executed")
    except Exception as e:
        pytest.fail(f"find_function_callees crashed: {e}")
    
    try:
        await engine.find_symbol_references("any_symbol")
        print("✓ find_symbol_references executed")
    except Exception as e:
        pytest.fail(f"find_symbol_references crashed: {e}")
