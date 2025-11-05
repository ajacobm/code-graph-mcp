#!/usr/bin/env python3
"""
MCP Client for testing code-graph-mcp server.
Tests the graph query tools via MCP protocol.
"""

import asyncio
import sys
import pytest

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Error: mcp package not installed")
    print("Install with: pip install mcp")
    sys.exit(1)


@pytest.mark.asyncio
async def test_mcp_tools():
    """Test MCP tools via stdio connection."""
    
    print("="*80)
    print("MCP CLIENT - LIVE TOOL TESTING")
    print("="*80)
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "code-graph-mcp", "--project-root", "/app/src/code_graph_mcp", "--verbose"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                print("\n✓ MCP session initialized")
                
                # List tools
                tools = await session.list_tools()
                print(f"✓ Available tools: {len(tools.tools)} tools")
                for tool in tools.tools:
                    print(f"  - {tool.name}")
                
                # Test find_callers
                print("\n" + "="*80)
                print("TEST 1: find_callers('analyze_project')")
                print("="*80)
                result = await session.call_tool(
                    "find_callers",
                    {"function": "analyze_project"}
                )
                if result.content:
                    text = result.content[0].text
                    lines = text.split('\n')
                    print(f"Response length: {len(text)} chars")
                    print(f"First 500 chars:")
                    print(text[:500])
                    if "caller" in text.lower() or "get_tool_definitions" in text:
                        print("\n✅ find_callers WORKING - returns actual results")
                    else:
                        print("\n⚠️ find_callers returned but no obvious callers")
                
                # Test find_callees
                print("\n" + "="*80)
                print("TEST 2: find_callees('analyze_project')")
                print("="*80)
                result = await session.call_tool(
                    "find_callees",
                    {"function": "analyze_project"}
                )
                if result.content:
                    text = result.content[0].text
                    print(f"Response length: {len(text)} chars")
                    print(f"First 500 chars:")
                    print(text[:500])
                    if "callee" in text.lower() or "_analyze" in text:
                        print("\n✅ find_callees WORKING - returns actual results")
                    else:
                        print("\n⚠️ find_callees returned but no obvious callees")
                
                # Test find_references
                print("\n" + "="*80)
                print("TEST 3: find_references('analyze_project')")
                print("="*80)
                result = await session.call_tool(
                    "find_references",
                    {"symbol": "analyze_project"}
                )
                if result.content:
                    text = result.content[0].text
                    print(f"Response: {text}")
                
                # Test analyze_codebase
                print("\n" + "="*80)
                print("TEST 4: analyze_codebase()")
                print("="*80)
                result = await session.call_tool("analyze_codebase", {})
                if result.content:
                    text = result.content[0].text
                    print(f"Response: {text}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*80)
    print("✅ MCP CLIENT TEST COMPLETE")
    print("="*80)
    return True


if __name__ == "__main__":
    result = asyncio.run(test_mcp_tools())
    sys.exit(0 if result else 1)
