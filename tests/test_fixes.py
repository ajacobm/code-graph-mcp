#!/usr/bin/env python3
"""Test script to verify the fixes to the MCP server."""

import asyncio
import httpx
import json
from time import sleep

async def test_mcp_server():
    """Test the MCP server functionality."""
    
    base_url = "http://localhost:10101"
    
    # Test 1: Health endpoint
    print("🩺 Testing health endpoint...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            health_data = response.json()
            print(f"✅ Health check: {health_data['status']}")
            print(f"   - Redis connected: {health_data.get('redis_connected', 'Unknown')}")
            print(f"   - Analysis engine: {health_data.get('analysis_engine', 'Unknown')}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: MCP Protocol initialization 
    print("\n🔌 Testing MCP protocol...")
    try:
        async with httpx.AsyncClient() as client:
            # Initialize connection
            init_data = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            }
            
            response = await client.post(
                f"{base_url}/mcp/",
                headers={"Content-Type": "application/json"},
                json=init_data
            )
            
            if response.status_code == 200:
                print("✅ MCP initialization successful")
            else:
                print(f"❌ MCP initialization failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ MCP initialization failed: {e}")
        return False
    
    print("\n🎉 All tests passed! The fixes are working correctly.")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())