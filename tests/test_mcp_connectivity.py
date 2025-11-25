#!/usr/bin/env python3
"""
Simple MCP Connectivity Test
Just tests that the server is reachable and tools are listed
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import pytest


@pytest.mark.asyncio
async def test_basic_connectivity():
    """Test basic MCP server connectivity"""

    print("🔗 Testing MCP Server Connectivity")
    print("=" * 40)

    try:
        server_params = StdioServerParameters(
            command="codenav",
            args=["--project-root", ".", "--verbose"],
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                print("✅ Server connection established")

                # List available tools
                print("\n📋 Listing Tools...")
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")

                for tool in tools.tools:
                    print(f"  • {tool.name}: {tool.description}")

                print(f"\n🎯 SUCCESS: MCP server is properly exposing {len(tools.tools)} tools")
                return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def main():
    """Run connectivity test"""
    success = await test_basic_connectivity()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
