#!/usr/bin/env python3
"""Simple MCP server test"""

import asyncio
import subprocess

async def test_basic_functionality():
    """Test basic server functionality"""
    print("🚀 Testing Code Graph MCP Server")
    
    # Test 1: Can we start the server?
    print("\n1. Testing server startup...")
    try:
        result = subprocess.run([
            "code-graph-mcp", "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Server command works")
            print(f"   Output: {result.stdout[:100]}...")
        else:
            print(f"❌ Server command failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    # Test 2: Can we start with project root?
    print("\n2. Testing server with project root...")
    try:
        proc = subprocess.Popen([
            "code-graph-mcp", "--project-root", ".", "--verbose"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Let it run for 2 seconds then kill
        await asyncio.sleep(2)
        proc.terminate()
        stdout, stderr = proc.communicate()
        
        if "Initializing server" in stderr or "code-graph-intelligence" in stderr:
            print("✅ Server initializes correctly")
            print(f"   Debug output contains expected server initialization")
        else:
            print(f"❌ Unexpected output: {stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    print("\n🎯 Basic functionality test: PASSED")
    return True

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())