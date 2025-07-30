#!/usr/bin/env python3
"""
Test client for MCP over HTTP server
Demonstrates proper JSON-RPC 2.0 usage for MCP protocol.
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any


async def test_mcp_over_http(base_url: str = "http://localhost:8000"):
    """Test the MCP over HTTP server."""
    
    print(f"🧪 Testing MCP over HTTP server at {base_url}")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: List tools
        print("📋 Test 1: List Tools")
        list_tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list", 
            "id": 1
        }
        
        try:
            async with session.post(f"{base_url}/mcp", json=list_tools_request) as resp:
                result = await resp.json()
                
                if resp.status == 200 and "result" in result:
                    tools = result["result"]["tools"]
                    print(f"✅ Found {len(tools)} tools:")
                    for tool in tools[:3]:  # Show first 3
                        print(f"   - {tool['name']}: {tool['description'][:60]}...")
                else:
                    print(f"❌ List tools failed: {result}")
                    
        except Exception as e:
            print(f"❌ List tools error: {e}")
        
        print()
        
        # Test 2: Call a tool
        print("🔧 Test 2: Call Tool (get_usage_guide)")
        call_tool_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_usage_guide",
                "arguments": {}
            },
            "id": 2
        }
        
        try:
            async with session.post(f"{base_url}/mcp", json=call_tool_request) as resp:
                result = await resp.json()
                
                if resp.status == 200 and "result" in result:
                    content = result["result"]["content"]
                    if content and len(content) > 0:
                        text = content[0]["text"]
                        print(f"✅ Tool executed successfully")
                        print(f"📄 Response length: {len(text)} characters")
                        print(f"📝 Preview: {text[:200]}...")
                    else:
                        print("❌ Empty response from tool")
                else:
                    print(f"❌ Tool call failed: {result}")
                    
        except Exception as e:
            print(f"❌ Tool call error: {e}")
        
        print()
        
        # Test 3: Test /sse endpoint (should work identically)
        print("🌊 Test 3: Test /sse endpoint")
        try:
            async with session.post(f"{base_url}/sse", json=list_tools_request) as resp:
                result = await resp.json()
                
                if resp.status == 200 and "result" in result:
                    tools = result["result"]["tools"]
                    print(f"✅ SSE endpoint works: {len(tools)} tools found")
                else:
                    print(f"❌ SSE endpoint failed: {result}")
                    
        except Exception as e:
            print(f"❌ SSE endpoint error: {e}")
        
        # Test 4: Invalid JSON-RPC
        print("\n🚫 Test 4: Invalid JSON-RPC (should fail gracefully)")
        invalid_request = {
            "method": "tools/list",  # Missing jsonrpc and id
        }
        
        try:
            async with session.post(f"{base_url}/mcp", json=invalid_request) as resp:
                result = await resp.json()
                
                if resp.status == 400 and "error" in result:
                    print(f"✅ Proper error handling: {result['error']['message']}")
                else:
                    print(f"❌ Expected error response, got: {result}")
                    
        except Exception as e:
            print(f"❌ Error test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Testing complete!")

if __name__ == "__main__":
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    asyncio.run(test_mcp_over_http(base_url))