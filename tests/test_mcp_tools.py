#!/usr/bin/env python3
"""Test script for code-graph-mcp MCP tools."""

import asyncio
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def run_mcp_tool_test(session, tool_name, arguments=None):
    """Test a specific MCP tool and return results."""
    if arguments is None:
        arguments = {}

    try:
        logger.info(f"Testing tool: {tool_name} with args: {arguments}")
        result = await session.call_tool(tool_name, arguments)

        return {
            'tool': tool_name,
            'success': True,
            'content': result.content,
            'error': None
        }
    except Exception as e:
        logger.error(f"Error testing {tool_name}: {str(e)}")
        return {
            'tool': tool_name,
            'success': False,
            'content': None,
            'error': str(e)
        }

async def run_all_tests():
    """Run all MCP tool tests."""
    project_root = '/home/adam/GitHub/code-graph-mcp/src/codenav'

    server_params = StdioServerParameters(
        command='uv',
        args=['run', 'code-graph-mcp', '--project-root', project_root, '--verbose']
    )

    # Define test cases for each tool
    test_cases = [
        ('analyze_codebase', {}),
        ('find_definition', {'symbol': 'main'}),
        ('find_references', {'symbol': 'main'}),
        ('find_callers', {'function': 'main'}),
        ('find_callees', {'function': 'main'}),
        ('complexity_analysis', {'threshold': 10}),
        ('dependency_analysis', {}),
        ('project_statistics', {})
    ]

    results = []

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.info("MCP session initialized successfully")

                # List available tools first
                try:
                    tools = await session.list_tools()
                    logger.info(f"Available tools: {[tool.name for tool in tools.tools]}")
                except Exception as e:
                    logger.error(f"Failed to list tools: {e}")
                    return []

                # Test each tool
                for tool_name, args in test_cases:
                    result = await run_mcp_tool_test(session, tool_name, args)
                    results.append(result)

                    # Add a small delay between tests
                    await asyncio.sleep(0.5)

    except Exception as e:
        logger.error(f"Failed to create MCP session: {e}")
        return []

    return results

def print_results(results):
    """Print formatted test results."""
    print("\n" + "="*80)
    print("MCP TOOL TEST RESULTS")
    print("="*80)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. Tool: {result['tool']}")
        print(f"   Status: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")

        if result['success'] and result['content']:
            # Try to format content nicely
            content = result['content']
            if isinstance(content, list) and len(content) > 0:
                first_item = content[0]
                if hasattr(first_item, 'text'):
                    text_content = first_item.text
                    # Truncate very long content
                    if len(text_content) > 500:
                        print(f"   Content: {text_content[:500]}... [truncated]")
                    else:
                        print(f"   Content: {text_content}")
                else:
                    print(f"   Content: {str(content)[:300]}...")
            else:
                print(f"   Content: {str(content)[:300]}...")
        elif not result['success']:
            print(f"   Error: {result['error']}")
        else:
            print("   Content: No content returned")

    print("\n" + "="*80)

    # Summary
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"SUMMARY: {successful}/{total} tools tested successfully")
    print("="*80)

if __name__ == "__main__":
    results = asyncio.run(run_all_tests())
    print_results(results)
