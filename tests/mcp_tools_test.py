#!/usr/bin/env python3
"""
Manual MCP Tools Test - Direct server communication
Tests all 8 MCP tools and generates a comprehensive report
"""

import pytest
import asyncio
import json
from pathlib import Path
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_all_mcp_tools():
    """Test all MCP tools and generate report"""

    results = {
        "test_timestamp": datetime.now().isoformat(),
        "project_path": str(Path.cwd()),
        "tool_results": {}
    }

    print("🧪 Testing Code Graph MCP Server Tools")
    print("=" * 60)

    try:
        server_params = StdioServerParameters(
            command="code-graph-mcp",
            args=["--project-root", "."],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List available tools first
                print("\n📋 Available Tools:")
                tools = await session.list_tools()
                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description}")

                # Test each tool
                test_cases = [
                    ("analyze_codebase", {}),
                    ("project_statistics", {}),
                    ("dependency_analysis", {}),
                    ("complexity_analysis", {"threshold": 10}),
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
                        results["tool_results"][tool_name] = {
                            "status": "SUCCESS" if success else "EMPTY",
                            "content_length": len(content),
                            "preview": content[:200] + "..." if len(content) > 200 else content,
                            "arguments": args
                        }

                        status = "✅" if success else "⚠️ "
                        print(f"  {status} {tool_name}: {len(content)} chars returned")

                    except Exception as e:
                        results["tool_results"][tool_name] = {
                            "status": "ERROR",
                            "error": str(e),
                            "arguments": args
                        }
                        print(f"  ❌ {tool_name}: {e}")

    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        results["server_error"] = str(e)

    # Generate summary
    successful_tools = sum(1 for r in results["tool_results"].values() if r["status"] == "SUCCESS")
    total_tools = len(results["tool_results"])

    if total_tools > 0:
        print(f"\n📊 SUMMARY: {successful_tools}/{total_tools} tools working ({successful_tools/total_tools*100:.1f}%)")
    else:
        print("\n📊 SUMMARY: No tools tested")

    return results


async def main():
    """Run tests and save report"""
    results = await test_all_mcp_tools()

    # Save detailed results
    with open("mcp_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n💾 Detailed results saved to mcp_test_results.json")
    return results


if __name__ == "__main__":
    asyncio.run(main())
