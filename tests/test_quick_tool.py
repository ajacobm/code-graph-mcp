#!/usr/bin/env python3
"""Quick test of a single MCP tool"""

import asyncio

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_single_tool():
    server_params = StdioServerParameters(
        command="code-graph-mcp",
        args=["--project-root", "."],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test project_statistics tool
            result = await session.call_tool("project_statistics", {})

            content = ""
            if result.content:
                for item in result.content:
                    if hasattr(item, 'text'):
                        content += item.text

            print("🎯 project_statistics result:")
            print(content[:500])
            print(f"\n✅ SUCCESS: {len(content)} characters returned")

if __name__ == "__main__":
    asyncio.run(test_single_tool())
