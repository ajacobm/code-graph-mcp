#!/usr/bin/env python3
"""
Quick test of all 8 MCP tools with simple function calls
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_all_tools():
    """Test all 8 MCP tools with simple calls"""
    
    print("🧪 Testing All 8 MCP Tools")
    print("=" * 50)
    
    results = {}
    
    try:
        server_params = StdioServerParameters(
            command="code-graph-mcp",
            args=["--project-root", "."],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test cases for each tool
                test_cases = [
                    ("project_statistics", {}),
                    ("analyze_codebase", {}),
                    ("dependency_analysis", {}),
                    ("complexity_analysis", {"threshold": 5}),
                    ("find_definition", {"symbol": "main"}),
                    ("find_references", {"symbol": "main"}),
                    ("find_callers", {"function": "main"}),
                    ("find_callees", {"function": "main"}),
                ]
                
                for tool_name, args in test_cases:
                    print(f"\n🔧 Testing {tool_name}...")
                    try:
                        result = await session.call_tool(tool_name, args)
                        
                        # Extract content
                        content = ""
                        if result.content:
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    content += item.text
                        
                        success = bool(content.strip())
                        results[tool_name] = {
                            "status": "✅ SUCCESS" if success else "⚠️  EMPTY",
                            "content_length": len(content),
                            "preview": content[:100] + "..." if len(content) > 100 else content[:100]
                        }
                        
                        print(f"  {results[tool_name]['status']}: {len(content)} characters returned")
                        if content:
                            print(f"  Preview: {results[tool_name]['preview']}")
                        
                    except Exception as e:
                        results[tool_name] = {"status": "❌ ERROR", "error": str(e)}
                        print(f"  ❌ ERROR: {e}")
                
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
    
    # Summary
    successful = sum(1 for r in results.values() if "SUCCESS" in r.get("status", ""))
    total = len(results)
    
    print(f"\n📊 FINAL RESULTS: {successful}/{total} tools working")
    print("=" * 50)
    
    for tool, result in results.items():
        print(f"{result['status']} {tool}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_all_tools())