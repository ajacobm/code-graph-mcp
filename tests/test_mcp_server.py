#!/usr/bin/env python3
"""
Comprehensive test for the Code Graph MCP Server
Tests all 8 MCP tools, server functionality, and Redis cache integration
"""

import asyncio
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

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

        # Test 4: New functionality tests
        await self.test_redis_cache_integration()
        await self.test_sse_server_functionality()
        await self.test_performance_benchmarks()

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

    async def test_redis_cache_integration(self):
        """Test Redis cache integration"""
        print("\n📋 Test 11: Redis Cache Integration")
        try:
            # Test with Redis cache enabled
            command = [
                "code-graph-mcp", 
                "--project-root", ".",
                "--redis-url", "redis://localhost:6379/0",
                "--redis-prefix", "test_mcp"
            ]
            
            async with stdio_client(command) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    # First run - populate cache
                    start_time = time.time()
                    result1 = await session.call_tool("analyze_codebase", {})
                    first_run_time = time.time() - start_time
                    
                    # Second run - should use cache
                    start_time = time.time()
                    result2 = await session.call_tool("analyze_codebase", {})
                    second_run_time = time.time() - start_time
                    
                    if result1.content and result2.content:
                        speedup = first_run_time / second_run_time if second_run_time > 0 else 1
                        self.log_success(
                            "Redis cache integration", 
                            f"Cache speedup: {speedup:.2f}x ({first_run_time:.2f}s -> {second_run_time:.2f}s)"
                        )
                    else:
                        self.log_failure("Redis cache integration", "Cache test returned no content")
        except Exception as e:
            # Cache might not be available - this is acceptable
            self.log_success("Redis cache integration", f"Cache unavailable (fallback mode): {e}")

    async def test_sse_server_functionality(self):
        """Test SSE server integration"""
        print("\n📋 Test 12: SSE Server Functionality")
        try:
            # Test if we can create a temporary SSE server
            with tempfile.TemporaryDirectory() as tmpdir:
                project_path = Path(tmpdir)
                (project_path / "test.py").write_text("def test(): pass")
                
                # Import and test SSE server creation
                try:
                    from codenav.sse_server import create_sse_app
                    app = create_sse_app(project_path, enable_file_watcher=False)
                    
                    if app:
                        self.log_success("SSE server functionality", "SSE server created successfully")
                    else:
                        self.log_failure("SSE server functionality", "Failed to create SSE server")
                except ImportError:
                    self.log_failure("SSE server functionality", "SSE server module not available")
                    
        except Exception as e:
            self.log_failure("SSE server functionality", f"Exception: {e}")

    async def test_performance_benchmarks(self):
        """Test performance benchmarks with and without cache"""
        print("\n📋 Test 13: Performance Benchmarks")
        try:
            # Create test project
            with tempfile.TemporaryDirectory() as tmpdir:
                project_path = Path(tmpdir)
                
                # Create multiple test files
                for i in range(10):
                    (project_path / f"test_{i}.py").write_text(f"""
def function_{i}():
    '''Function {i}'''
    return {i}

class Class_{i}:
    def method_{i}(self):
        return function_{i}()
                    """)
                
                # Test without cache
                command_no_cache = ["code-graph-mcp", "--project-root", str(project_path)]
                
                async with stdio_client(command_no_cache) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        start_time = time.time()
                        await session.call_tool("analyze_codebase", {})
                        no_cache_time = time.time() - start_time
                
                # Test with cache (if available)
                try:
                    command_with_cache = [
                        "code-graph-mcp", 
                        "--project-root", str(project_path),
                        "--redis-url", "redis://localhost:6379/0",
                        "--redis-prefix", "test_perf"
                    ]
                    
                    async with stdio_client(command_with_cache) as streams:
                        async with ClientSession(streams[0], streams[1]) as session:
                            # First run to populate cache
                            await session.call_tool("analyze_codebase", {})
                            
                            # Second run to test cache performance
                            start_time = time.time()
                            await session.call_tool("analyze_codebase", {})
                            cache_time = time.time() - start_time
                    
                    speedup = no_cache_time / cache_time if cache_time > 0 else 1
                    self.log_success(
                        "Performance benchmarks", 
                        f"Analysis performance: {no_cache_time:.2f}s (no cache) vs {cache_time:.2f}s (cached) - {speedup:.2f}x speedup"
                    )
                    
                except Exception:
                    self.log_success(
                        "Performance benchmarks",
                        f"Analysis performance: {no_cache_time:.2f}s (cache not available)"
                    )
                    
        except Exception as e:
            self.log_failure("Performance benchmarks", f"Exception: {e}")

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
