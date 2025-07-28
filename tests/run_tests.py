#!/usr/bin/env python3
"""
Test runner for Code Graph MCP comprehensive test suite
Runs all cache, SSE, and integration tests
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path


class TestRunner:
    """Comprehensive test runner for Code Graph MCP"""

    def __init__(self):
        self.results = []
        self.total_start_time = time.time()

    def run_pytest_suite(self, test_file: str, description: str) -> bool:
        """Run a pytest test suite and capture results"""
        print(f"\n🧪 Running {description}")
        print("=" * 60)
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, "-v", "--tb=short", "--color=yes"
            ], capture_output=True, text=True, timeout=300)
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ {description} - PASSED")
            else:
                print(f"❌ {description} - FAILED")
                if result.stdout:
                    print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                if result.stderr:
                    print("STDERR:", result.stderr[-500:])  # Last 500 chars
            
            self.results.append({
                "test": description,
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            })
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} - TIMEOUT")
            self.results.append({
                "test": description, 
                "success": False,
                "error": "Timeout after 300s"
            })
            return False
            
        except Exception as e:
            print(f"💥 {description} - ERROR: {e}")
            self.results.append({
                "test": description,
                "success": False, 
                "error": str(e)
            })
            return False

    def run_manual_test(self, test_file: str, description: str) -> bool:
        """Run a test file with manual flag"""
        print(f"\n🔧 Running {description}")
        print("=" * 60)
        
        try:
            result = subprocess.run([
                sys.executable, test_file, "--manual"
            ], capture_output=True, text=True, timeout=120)
            
            success = result.returncode == 0
            
            if success:
                print(f"✅ {description} - PASSED")
            else:
                print(f"❌ {description} - FAILED")
            
            # Always show output for manual tests
            if result.stdout:
                print("Output:")
                print(result.stdout[-1000:])  # Last 1000 chars
            
            self.results.append({
                "test": description,
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr
            })
            
            return success
            
        except Exception as e:
            print(f"💥 {description} - ERROR: {e}")
            self.results.append({
                "test": description,
                "success": False,
                "error": str(e)
            })
            return False

    async def run_async_test(self, test_file: str, description: str) -> bool:
        """Run an async test file"""
        print(f"\n🚀 Running {description}")
        print("=" * 60)
        
        try:
            # Import and run the test
            test_module_path = Path(test_file).stem
            
            if "test_mcp_server" in test_file:
                from tests.test_mcp_server import main as test_main
                await test_main()
                success = True
            elif "test_mcp_tools" in test_file:
                # This test has its own async runner
                result = subprocess.run([
                    sys.executable, test_file
                ], capture_output=True, text=True, timeout=180)
                success = result.returncode == 0
                
                if result.stdout:
                    print(result.stdout[-800:])
            else:
                success = False
                print(f"⚠️  Unknown async test file: {test_file}")
            
            if success:
                print(f"✅ {description} - PASSED")
            else:
                print(f"❌ {description} - FAILED")
                
            self.results.append({
                "test": description,
                "success": success
            })
                
            return success
            
        except Exception as e:
            print(f"💥 {description} - ERROR: {e}")
            self.results.append({
                "test": description,
                "success": False,
                "error": str(e)
            })
            return False

    def print_summary(self):
        """Print comprehensive test summary"""
        total_time = time.time() - self.total_start_time
        
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - passed
        
        print(f"📊 Results:")
        print(f"   Total Tests: {len(self.results)}")
        print(f"   Passed:      {passed} ✅")
        print(f"   Failed:      {failed} ❌")
        print(f"   Success Rate: {(passed/len(self.results)*100):.1f}%")
        print(f"   Total Time:  {total_time:.1f}s")
        
        if failed > 0:
            print(f"\n💥 Failed Tests:")
            for result in self.results:
                if not result["success"]:
                    print(f"   ❌ {result['test']}")
                    if "error" in result:
                        print(f"      Error: {result['error']}")
        
        print(f"\n🏁 Overall Result: {'PASS' if failed == 0 else 'FAIL'}")
        return failed == 0

    async def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Code Graph MCP Comprehensive Test Suite")
        print("=" * 80)
        
        tests_dir = Path("tests")
        
        # Test 1: Redis Cache Tests
        if (tests_dir / "test_redis_cache.py").exists():
            self.run_pytest_suite(
                "tests/test_redis_cache.py",
                "Redis Cache Integration Tests"
            )
            
            # Also run manual tests
            self.run_manual_test(
                "tests/test_redis_cache.py",
                "Redis Cache Manual Tests"
            )
        else:
            print("⚠️  Redis cache tests not found")
        
        # Test 2: SSE Server Tests  
        if (tests_dir / "test_sse_server.py").exists():
            self.run_pytest_suite(
                "tests/test_sse_server.py",
                "SSE Server Tests"
            )
            
            self.run_manual_test(
                "tests/test_sse_server.py", 
                "SSE Server Manual Tests"
            )
        else:
            print("⚠️  SSE server tests not found")
        
        # Test 3: MCP Cache Integration Tests
        if (tests_dir / "test_mcp_cache_integration.py").exists():
            self.run_pytest_suite(
                "tests/test_mcp_cache_integration.py",
                "MCP Cache Integration Tests"
            )
            
            self.run_manual_test(
                "tests/test_mcp_cache_integration.py",
                "MCP Cache Integration Manual Tests"
            )
        else:
            print("⚠️  MCP cache integration tests not found")
        
        # Test 4: Enhanced MCP Server Tests
        if (tests_dir / "test_mcp_server.py").exists():
            await self.run_async_test(
                "tests/test_mcp_server.py",
                "Enhanced MCP Server Tests"
            )
        else:
            print("⚠️  Enhanced MCP server tests not found")
        
        # Test 5: Original MCP Tools Tests  
        if (tests_dir / "test_mcp_tools.py").exists():
            await self.run_async_test(
                "tests/test_mcp_tools.py",
                "Original MCP Tools Tests"
            )
        else:
            print("⚠️  Original MCP tools tests not found")
        
        # Test 6: Existing Test Suites (if they exist)
        existing_tests = [
            "test_ast_grep.py",
            "test_multi_language.py", 
            "test_rustworkx_graph.py",
            "test_tool_schema.py"
        ]
        
        for test_file in existing_tests:
            test_path = tests_dir / test_file
            if test_path.exists():
                self.run_pytest_suite(
                    str(test_path),
                    f"Existing Tests: {test_file}"
                )
        
        return self.print_summary()


async def main():
    """Main test runner entry point"""
    runner = TestRunner()
    success = await runner.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    # Check for specific test flags
    if len(sys.argv) > 1:
        if sys.argv[1] == "--redis-only":
            runner = TestRunner()
            runner.run_pytest_suite("tests/test_redis_cache.py", "Redis Cache Tests")
            runner.run_manual_test("tests/test_redis_cache.py", "Redis Manual Tests")
            success = runner.print_summary()
            sys.exit(0 if success else 1)
            
        elif sys.argv[1] == "--sse-only":
            runner = TestRunner()
            runner.run_pytest_suite("tests/test_sse_server.py", "SSE Server Tests")
            runner.run_manual_test("tests/test_sse_server.py", "SSE Manual Tests")
            success = runner.print_summary()
            sys.exit(0 if success else 1)
            
        elif sys.argv[1] == "--integration-only":
            runner = TestRunner()
            runner.run_pytest_suite("tests/test_mcp_cache_integration.py", "Integration Tests")
            runner.run_manual_test("tests/test_mcp_cache_integration.py", "Integration Manual")
            success = runner.print_summary()
            sys.exit(0 if success else 1)
            
        elif sys.argv[1] == "--help":
            print("""
Code Graph MCP Test Runner

Usage:
  python run_tests.py                  # Run all tests
  python run_tests.py --redis-only     # Run only Redis cache tests
  python run_tests.py --sse-only       # Run only SSE server tests  
  python run_tests.py --integration-only # Run only integration tests
  python run_tests.py --help           # Show this help
  
Test Files:
  tests/test_redis_cache.py            # Redis cache functionality
  tests/test_sse_server.py             # SSE server functionality
  tests/test_mcp_cache_integration.py  # End-to-end integration
  tests/test_mcp_server.py             # Enhanced MCP server tests
  tests/test_mcp_tools.py              # Original MCP tools tests
            """)
            sys.exit(0)
    
    # Run all tests
    asyncio.run(main())
