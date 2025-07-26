#!/usr/bin/env python3
"""
Comprehensive test for the Code Graph MCP Server
Tests all 8 MCP tools and server functionality
"""

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client


class MCPServerTest:
    """Test suite for the Code Graph MCP Server"""
    
    def __init__(self):
        self.results = []
        self.server_process = None
        
    async def run_all_tests(self):
        """Run all MCP server tests"""
        print("🚀 Starting Code Graph MCP Server Tests")
        print("=" * 50)
        
        # Test 1: Server startup
        await self.test_server_startup()
        
        # Test 2: Tool listing
        await self.test_tool_listing()
        
        # Test 3: Individual tool tests
        await self.test_analyze_codebase()
        await self.test_find_definition()
        await self.test_find_references()
        await self.test_find_callers()
        await self.test_find_callees()
        await self.test_complexity_analysis()
        await self.test_dependency_analysis()
        await self.test_project_statistics()
        
        # Summary
        self.print_summary()
        
    async def test_server_startup(self):
        """Test if the server starts correctly"""
        print("\n📋 Test 1: Server Startup")
        try:
            # Test direct command
            result = subprocess.run([
                "code-graph-mcp", "--project-root", ".", "--help"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "Code Graph Intelligence MCP Server" in result.stdout:
                self.log_success("Server startup", "Server starts and shows help")
            else:
                self.log_failure("Server startup", f"Command failed: {result.stderr}")
                
        except Exception as e:
            self.log_failure("Server startup", f"Exception: {e}")
    
    async def test_tool_listing(self):
        """Test MCP tool listing via stdio client"""
        print("\n📋 Test 2: Tool Listing")
        try:
            command = ["code-graph-mcp", "--project-root", "."]
            async with stdio_client(command) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    tools = await session.list_tools()
                    
                    expected_tools = {
                        "analyze_codebase", "find_definition", "find_references",
                        "find_callers", "find_callees", "complexity_analysis", 
                        "dependency_analysis", "project_statistics"
                    }
                    
                    actual_tools = {tool.name for tool in tools.tools}
                    
                    if expected_tools.issubset(actual_tools):
                        self.log_success("Tool listing", f"All 8 tools available: {actual_tools}")
                    else:
                        missing = expected_tools - actual_tools
                        self.log_failure("Tool listing", f"Missing tools: {missing}")
                        
        except Exception as e:
            self.log_failure("Tool listing", f"Exception: {e}")
    
    async def test_analyze_codebase(self):
        """Test analyze_codebase tool"""
        print("\n📋 Test 3: Analyze Codebase")
        await self.test_tool("analyze_codebase", {})
    
    async def test_find_definition(self):
        """Test find_definition tool"""
        print("\n📋 Test 4: Find Definition")
        await self.test_tool("find_definition", {"symbol": "main"})
    
    async def test_find_references(self):
        """Test find_references tool"""
        print("\n📋 Test 5: Find References")
        await self.test_tool("find_references", {"symbol": "main"})
    
    async def test_find_callers(self):
        """Test find_callers tool"""
        print("\n📋 Test 6: Find Callers")
        await self.test_tool("find_callers", {"function": "main"})
    
    async def test_find_callees(self):
        """Test find_callees tool"""
        print("\n📋 Test 7: Find Callees")
        await self.test_tool("find_callees", {"function": "main"})
    
    async def test_complexity_analysis(self):
        """Test complexity_analysis tool"""
        print("\n📋 Test 8: Complexity Analysis")
        await self.test_tool("complexity_analysis", {"threshold": 10})
    
    async def test_dependency_analysis(self):
        """Test dependency_analysis tool"""
        print("\n📋 Test 9: Dependency Analysis")
        await self.test_tool("dependency_analysis", {})
    
    async def test_project_statistics(self):
        """Test project_statistics tool"""
        print("\n📋 Test 10: Project Statistics")
        await self.test_tool("project_statistics", {})
    
    async def test_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Generic tool test"""
        try:
            command = ["code-graph-mcp", "--project-root", "."]
            async with stdio_client(command) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    result = await session.call_tool(tool_name, arguments)
                    
                    if result.content and len(result.content) > 0:
                        # Check if result contains meaningful content
                        content_text = ""
                        for content in result.content:
                            if hasattr(content, 'text'):
                                content_text += content.text
                        
                        if content_text.strip():
                            self.log_success(tool_name, f"Returned content ({len(content_text)} chars)")
                        else:
                            self.log_failure(tool_name, "Empty content returned")
                    else:
                        self.log_failure(tool_name, "No content returned")
                        
        except Exception as e:
            self.log_failure(tool_name, f"Exception: {e}")
    
    def log_success(self, test_name: str, message: str):
        """Log successful test"""
        self.results.append({"test": test_name, "status": "PASS", "message": message})
        print(f"✅ {test_name}: {message}")
    
    def log_failure(self, test_name: str, message: str):
        """Log failed test"""
        self.results.append({"test": test_name, "status": "FAIL", "message": message})
        print(f"❌ {test_name}: {message}")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n🎯 OVERALL RESULT:", "PASS" if failed == 0 else "FAIL")
        
        return failed == 0


async def main():
    """Main test runner"""
    test_suite = MCPServerTest()
    success = await test_suite.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())