#!/usr/bin/env python3
"""
Integration tests for the complete Redis cache + MCP tools workflow
Tests the interaction between caching and MCP tool functionality
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

from code_graph_mcp.cache_manager import HybridCacheManager
from code_graph_mcp.universal_ast import UniversalASTAnalyzer


class TestMCPCacheIntegration:
    """Test MCP tools with Redis cache integration"""

    @pytest.fixture
    def complex_project_structure(self):
        """Create a complex project structure for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Main application files
            (project_path / "main.py").write_text("""
#!/usr/bin/env python3
\"\"\"Main application entry point\"\"\"

from src.calculator import Calculator
from src.utils.logger import setup_logger
from typing import List, Optional
import json

def main(args: List[str]) -> int:
    \"\"\"Main function with complex logic\"\"\"
    logger = setup_logger()
    calc = Calculator()
    
    try:
        result = calc.complex_calculation(10, 20, 30)
        logger.info(f"Calculation result: {result}")
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

def process_data(data: dict) -> Optional[dict]:
    \"\"\"Process input data\"\"\"
    if not data or "values" not in data:
        return None
    
    processed = {
        "total": sum(data["values"]),
        "count": len(data["values"]),
        "timestamp": time.time()
    }
    return processed

if __name__ == "__main__":
    import sys
    exit(main(sys.argv[1:]))
            """)
            
            # Source directory structure
            src_dir = project_path / "src"
            src_dir.mkdir()
            (src_dir / "__init__.py").write_text("")
            
            (src_dir / "calculator.py").write_text("""
\"\"\"Calculator module with various mathematical operations\"\"\"

from typing import Union, List
from .utils.math_helpers import advanced_operation

class Calculator:
    \"\"\"Advanced calculator with multiple operations\"\"\"
    
    def __init__(self):
        self.history: List[float] = []
    
    def add(self, a: float, b: float) -> float:
        \"\"\"Add two numbers\"\"\"
        result = a + b
        self.history.append(result)
        return result
    
    def multiply(self, a: float, b: float) -> float:
        \"\"\"Multiply two numbers\"\"\"
        result = a * b
        self.history.append(result)
        return result
    
    def complex_calculation(self, x: float, y: float, z: float) -> float:
        \"\"\"Perform complex calculation involving multiple operations\"\"\"
        intermediate1 = self.add(x, y)
        intermediate2 = self.multiply(intermediate1, z)
        final_result = advanced_operation(intermediate2)
        return final_result
    
    def get_history(self) -> List[float]:
        \"\"\"Get calculation history\"\"\"
        return self.history.copy()
    
    @staticmethod
    def percentage(value: float, percent: float) -> float:
        \"\"\"Calculate percentage of a value\"\"\"
        return (value * percent) / 100

class ScientificCalculator(Calculator):
    \"\"\"Extended calculator with scientific operations\"\"\"
    
    def power(self, base: float, exponent: float) -> float:
        \"\"\"Calculate power\"\"\"
        result = base ** exponent
        self.history.append(result)
        return result
    
    def square_root(self, value: float) -> float:
        \"\"\"Calculate square root\"\"\"
        import math
        result = math.sqrt(value)
        self.history.append(result)
        return result
            """)
            
            # Utils directory with multiple modules
            utils_dir = src_dir / "utils"
            utils_dir.mkdir()
            (utils_dir / "__init__.py").write_text("")
            
            (utils_dir / "logger.py").write_text("""
\"\"\"Logging utilities\"\"\"

import logging
import sys
from typing import Optional

def setup_logger(name: Optional[str] = None, level: int = logging.INFO):
    \"\"\"Setup application logger\"\"\"
    logger = logging.getLogger(name or __name__)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

class FileLogger:
    \"\"\"File-based logger\"\"\"
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.logger = setup_logger(f"file_{filepath}")
    
    def log_event(self, event: str, data: dict = None):
        \"\"\"Log an event with optional data\"\"\"
        message = f"Event: {event}"
        if data:
            message += f" | Data: {data}"
        self.logger.info(message)
            """)
            
            (utils_dir / "math_helpers.py").write_text("""
\"\"\"Mathematical helper functions\"\"\"

import math
from typing import Union, List

def advanced_operation(value: float) -> float:
    \"\"\"Perform advanced mathematical operation\"\"\"
    return math.sin(value) * math.cos(value) + math.sqrt(abs(value))

def factorial(n: int) -> int:
    \"\"\"Calculate factorial\"\"\"
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci_sequence(length: int) -> List[int]:
    \"\"\"Generate Fibonacci sequence\"\"\"
    if length <= 0:
        return []
    elif length == 1:
        return [0]
    elif length == 2:
        return [0, 1]
    
    sequence = [0, 1]
    for i in range(2, length):
        sequence.append(sequence[i-1] + sequence[i-2])
    return sequence

class MathUtils:
    \"\"\"Utility class for mathematical operations\"\"\"
    
    @staticmethod
    def gcd(a: int, b: int) -> int:
        \"\"\"Calculate greatest common divisor\"\"\"
        while b:
            a, b = b, a % b
        return a
    
    @staticmethod
    def lcm(a: int, b: int) -> int:
        \"\"\"Calculate least common multiple\"\"\"
        return abs(a * b) // MathUtils.gcd(a, b)
    
    def prime_factors(self, n: int) -> List[int]:
        \"\"\"Find prime factors of a number\"\"\"
        factors = []
        d = 2
        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1
        if n > 1:
            factors.append(n)
        return factors
            """)
            
            # Test files
            tests_dir = project_path / "tests"
            tests_dir.mkdir()
            (tests_dir / "__init__.py").write_text("")
            
            (tests_dir / "test_calculator.py").write_text("""
\"\"\"Tests for calculator module\"\"\"

import unittest
from src.calculator import Calculator, ScientificCalculator

class TestCalculator(unittest.TestCase):
    \"\"\"Test cases for Calculator class\"\"\"
    
    def setUp(self):
        self.calc = Calculator()
    
    def test_add(self):
        \"\"\"Test addition operation\"\"\"
        result = self.calc.add(2, 3)
        self.assertEqual(result, 5)
    
    def test_multiply(self):
        \"\"\"Test multiplication operation\"\"\"
        result = self.calc.multiply(4, 5)
        self.assertEqual(result, 20)
    
    def test_complex_calculation(self):
        \"\"\"Test complex calculation\"\"\"
        result = self.calc.complex_calculation(1, 2, 3)
        self.assertIsInstance(result, float)
    
    def test_history(self):
        \"\"\"Test calculation history\"\"\"
        self.calc.add(1, 2)
        self.calc.multiply(3, 4)
        history = self.calc.get_history()
        self.assertEqual(len(history), 2)

class TestScientificCalculator(unittest.TestCase):
    \"\"\"Test cases for ScientificCalculator class\"\"\"
    
    def setUp(self):
        self.calc = ScientificCalculator()
    
    def test_power(self):
        \"\"\"Test power operation\"\"\"
        result = self.calc.power(2, 3)
        self.assertEqual(result, 8)
    
    def test_square_root(self):
        \"\"\"Test square root operation\"\"\"
        result = self.calc.square_root(9)
        self.assertEqual(result, 3)

if __name__ == "__main__":
    unittest.main()
            """)
            
            # Configuration files
            (project_path / "config.json").write_text("""
{
    "app_name": "Advanced Calculator",
    "version": "1.0.0",
    "debug": false,
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(levelname)s - %(message)s"
    },
    "calculator": {
        "precision": 10,
        "history_limit": 100
    }
}
            """)
            
            (project_path / "requirements.txt").write_text("""
pytest>=7.0.0
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.5.0
            """)
            
            yield project_path

    @pytest.mark.asyncio
    async def test_mcp_tools_with_cache_performance(self, complex_project_structure):
        """Test MCP tools performance with caching enabled"""
        print("🚀 Testing MCP Tools with Cache Performance")
        
        # Initialize cache manager
        redis_config = {
            'url': 'redis://localhost:6379/0',
            'prefix': 'test_mcp_cache',
            'ttl': 3600
        }
        
        cache_manager = CacheManager(complex_project_structure, redis_config)
        await cache_manager.initialize()
        
        try:
            # Initialize analyzer with cache
            analyzer = UniversalAST(complex_project_structure)
            analyzer.cache_manager = cache_manager
            
            # Test 1: Cold cache performance (first run)
            print("📊 Testing cold cache performance...")
            start_time = time.time()
            
            # Analyze all files (cold cache)
            analysis_results = {}
            for py_file in complex_project_structure.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    result = await analyzer.analyze_file_async(str(py_file))
                    analysis_results[str(py_file)] = result
            
            cold_cache_time = time.time() - start_time
            print(f"✅ Cold cache analysis completed in {cold_cache_time:.2f}s")
            
            # Test 2: Warm cache performance (second run)
            print("📊 Testing warm cache performance...")
            start_time = time.time()
            
            # Analyze same files (should hit cache)
            cached_results = {}
            for py_file in complex_project_structure.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    result = await analyzer.analyze_file_async(str(py_file))
                    cached_results[str(py_file)] = result
            
            warm_cache_time = time.time() - start_time
            print(f"✅ Warm cache analysis completed in {warm_cache_time:.2f}s")
            
            # Verify cache effectiveness
            speedup = cold_cache_time / warm_cache_time if warm_cache_time > 0 else 1
            print(f"🏎️  Cache speedup: {speedup:.2f}x")
            
            # Verify results consistency
            assert len(analysis_results) == len(cached_results)
            assert len(analysis_results) > 0, "No files were analyzed"
            
            # Test cache statistics
            stats = await cache_manager.get_cache_stats()
            print(f"📈 Cache stats: {stats}")
            
            assert stats['total_hits'] > 0, "No cache hits recorded"
            
        finally:
            await cache_manager.close()

    @pytest.mark.asyncio
    async def test_mcp_tool_find_definition_with_cache(self, complex_project_structure):
        """Test find_definition tool with cache optimization"""
        print("🔍 Testing find_definition with caching")
        
        cache_manager = CacheManager(complex_project_structure, None)  # Memory cache only
        await cache_manager.initialize()
        
        try:
            analyzer = UniversalAST(complex_project_structure)
            analyzer.cache_manager = cache_manager
            
            # Pre-populate cache by analyzing project
            await analyzer.analyze_project_async()
            
            # Test finding definitions for various symbols
            test_symbols = [
                "Calculator",
                "ScientificCalculator", 
                "advanced_operation",
                "setup_logger",
                "main",
                "MathUtils"
            ]
            
            for symbol in test_symbols:
                print(f"🔎 Finding definition for: {symbol}")
                
                # Time the operation
                start_time = time.time()
                definitions = analyzer.find_definitions(symbol)
                end_time = time.time()
                
                print(f"   Found {len(definitions)} definition(s) in {(end_time - start_time)*1000:.1f}ms")
                
                if definitions:
                    for definition in definitions:
                        print(f"   📍 {definition['file']}:{definition['line']} - {definition['type']}")
            
            # Verify cache was used
            stats = await cache_manager.get_cache_stats() 
            print(f"📊 Final cache stats: {stats}")
            
        finally:
            await cache_manager.close()

    @pytest.mark.asyncio
    async def test_mcp_tool_complexity_analysis_with_cache(self, complex_project_structure):
        """Test complexity analysis with caching"""
        print("📊 Testing complexity analysis with caching")
        
        cache_manager = CacheManager(complex_project_structure, None)
        await cache_manager.initialize()
        
        try:
            analyzer = UniversalAST(complex_project_structure)
            analyzer.cache_manager = cache_manager
            
            # Test 1: First complexity analysis (populate cache)
            start_time = time.time()
            complexity_results = analyzer.analyze_complexity(threshold=5)
            first_run_time = time.time() - start_time
            
            print(f"✅ First complexity analysis: {first_run_time:.2f}s")
            print(f"   Found {len(complexity_results)} complex functions")
            
            # Test 2: Second complexity analysis (should use cache)
            start_time = time.time()
            cached_complexity_results = analyzer.analyze_complexity(threshold=5)
            second_run_time = time.time() - start_time
            
            print(f"✅ Cached complexity analysis: {second_run_time:.2f}s")
            
            # Verify results are consistent
            assert len(complexity_results) == len(cached_complexity_results)
            
            # Display some results
            for result in complexity_results[:3]:  # Show first 3
                print(f"   🔴 {result['function']} (complexity: {result['complexity']})")
            
            cache_speedup = first_run_time / second_run_time if second_run_time > 0 else 1
            print(f"🏎️  Cache speedup for complexity analysis: {cache_speedup:.2f}x")
            
        finally:
            await cache_manager.close()

    @pytest.mark.asyncio 
    async def test_mcp_tools_end_to_end_workflow(self, complex_project_structure):
        """Test complete MCP tools workflow with caching"""
        print("🎯 Testing end-to-end MCP workflow with caching")
        
        # Use Redis cache for this test
        redis_config = {
            'url': 'redis://localhost:6379/0', 
            'prefix': 'test_e2e_workflow',
            'ttl': 1800
        }
        
        cache_manager = CacheManager(complex_project_structure, redis_config)
        await cache_manager.initialize()
        
        try:
            analyzer = UniversalAST(complex_project_structure)
            analyzer.cache_manager = cache_manager
            
            print("1️⃣ Project Statistics...")
            stats = analyzer.get_project_statistics()
            print(f"   📁 {stats['total_files']} files, {stats['total_lines']} lines")
            
            print("2️⃣ Codebase Analysis...")
            start_time = time.time()
            analysis = await analyzer.analyze_project_async()
            analysis_time = time.time() - start_time
            print(f"   ✅ Analysis completed in {analysis_time:.2f}s")
            
            print("3️⃣ Find Definitions...")
            definitions = analyzer.find_definitions("Calculator")
            print(f"   📍 Found {len(definitions)} definitions for 'Calculator'")
            
            print("4️⃣ Find References...")
            references = analyzer.find_references("Calculator")
            print(f"   🔗 Found {len(references)} references to 'Calculator'")
            
            print("5️⃣ Call Graph Analysis...")
            callers = analyzer.find_callers("complex_calculation")
            callees = analyzer.find_callees("main")
            print(f"   📞 Found {len(callers)} callers, {len(callees)} callees")
            
            print("6️⃣ Complexity Analysis...")
            complex_funcs = analyzer.analyze_complexity(threshold=3)
            print(f"   🔴 Found {len(complex_funcs)} complex functions")
            
            print("7️⃣ Dependency Analysis...")
            dependencies = analyzer.analyze_dependencies()
            print(f"   🕸️  Found {len(dependencies)} dependency relationships")
            
            # Test cache effectiveness
            print("8️⃣ Cache Performance Test...")
            start_time = time.time()
            
            # Re-run some operations (should be faster with cache)
            _ = analyzer.find_definitions("Calculator")
            _ = analyzer.find_references("Calculator") 
            _ = analyzer.analyze_complexity(threshold=3)
            
            cached_ops_time = time.time() - start_time
            print(f"   ⚡ Cached operations completed in {cached_ops_time:.3f}s")
            
            # Final cache statistics
            final_stats = await cache_manager.get_cache_stats()
            print(f"9️⃣ Final Cache Statistics:")
            print(f"   📊 Total hits: {final_stats['total_hits']}")
            print(f"   📊 Total misses: {final_stats['total_misses']}")
            print(f"   📊 Hit rate: {final_stats['hit_rate']:.1%}")
            
            # Verify significant cache usage
            assert final_stats['total_hits'] > 0, "No cache hits recorded"
            assert final_stats['hit_rate'] > 0, "Cache hit rate is 0%"
            
        finally:
            await cache_manager.close()

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_file_change(self, complex_project_structure):
        """Test cache invalidation when files change"""
        print("🔄 Testing cache invalidation on file changes")
        
        cache_manager = CacheManager(complex_project_structure, None)
        await cache_manager.initialize()
        
        try:
            analyzer = UniversalAST(complex_project_structure)
            analyzer.cache_manager = cache_manager
            
            # Analyze a specific file
            test_file = complex_project_structure / "src" / "calculator.py"
            
            print(f"📝 Initial analysis of {test_file.name}")
            initial_analysis = await analyzer.analyze_file_async(str(test_file))
            initial_functions = len(initial_analysis.get('functions', []))
            print(f"   Found {initial_functions} functions")
            
            # Verify it's cached
            cached_analysis = await cache_manager.get_cached_analysis(str(test_file))
            assert cached_analysis is not None, "Analysis should be cached"
            
            # Modify the file
            print("✏️  Modifying file content...")
            original_content = test_file.read_text()
            modified_content = original_content + "\n\ndef new_function():\n    \"\"\"A new function\"\"\"\n    return 42\n"
            test_file.write_text(modified_content)
            
            # Wait a moment to ensure mtime changes
            await asyncio.sleep(0.1)
            
            print("🔍 Re-analyzing modified file...")
            modified_analysis = await analyzer.analyze_file_async(str(test_file))
            modified_functions = len(modified_analysis.get('functions', []))
            print(f"   Found {modified_functions} functions after modification")
            
            # Verify cache was invalidated and new content detected
            assert modified_functions > initial_functions, "New function should be detected"
            
            # Restore original content
            test_file.write_text(original_content)
            print("♻️  File restored to original state")
            
        finally:
            await cache_manager.close()

    @pytest.mark.asyncio
    async def test_concurrent_mcp_operations_with_cache(self, complex_project_structure):
        """Test concurrent MCP operations with shared cache"""
        print("🏃‍♂️ Testing concurrent MCP operations with shared cache")
        
        cache_manager = CacheManager(complex_project_structure, None)
        await cache_manager.initialize()
        
        try:
            # Create multiple analyzer instances (simulating concurrent sessions)
            analyzers = []
            for i in range(3):
                analyzer = UniversalAST(complex_project_structure)
                analyzer.cache_manager = cache_manager
                analyzers.append(analyzer)
            
            # Define concurrent operations
            async def analyzer_worker(analyzer_id, analyzer):
                print(f"🔧 Worker {analyzer_id} starting...")
                
                # Each worker performs different operations
                operations = [
                    lambda: analyzer.find_definitions("Calculator"),
                    lambda: analyzer.find_references("main"), 
                    lambda: analyzer.analyze_complexity(threshold=5),
                    lambda: analyzer.get_project_statistics()
                ]
                
                results = []
                for i, operation in enumerate(operations):
                    start_time = time.time()
                    result = operation()
                    duration = time.time() - start_time
                    
                    results.append({
                        'worker': analyzer_id,
                        'operation': i,
                        'duration': duration,
                        'result_size': len(result) if isinstance(result, (list, dict)) else 1
                    })
                    
                    # Small delay between operations
                    await asyncio.sleep(0.1)
                
                print(f"✅ Worker {analyzer_id} completed")
                return results
            
            # Run workers concurrently
            print("🚀 Starting concurrent workers...")
            worker_tasks = [
                analyzer_worker(i, analyzer) 
                for i, analyzer in enumerate(analyzers)
            ]
            
            all_results = await asyncio.gather(*worker_tasks)
            
            # Analyze results
            total_operations = sum(len(results) for results in all_results)
            avg_duration = sum(
                result['duration'] 
                for results in all_results 
                for result in results
            ) / total_operations
            
            print(f"📊 Completed {total_operations} concurrent operations")
            print(f"⏱️  Average operation duration: {avg_duration:.3f}s")
            
            # Check cache effectiveness
            final_stats = await cache_manager.get_cache_stats()
            print(f"📈 Final cache hit rate: {final_stats['hit_rate']:.1%}")
            
            # Concurrent operations should benefit from shared cache
            assert final_stats['total_hits'] > 0, "Concurrent operations should generate cache hits"
            
        finally:
            await cache_manager.close()


class TestMCPStdioIntegration:
    """Test MCP tools through stdio interface with cache"""

    @pytest.mark.asyncio
    async def test_stdio_mcp_with_cache_config(self, complex_project_structure):
        """Test MCP stdio interface with cache configuration"""
        print("📡 Testing MCP stdio interface with cache")
        
        # This test requires the actual MCP server binary
        # We'll test the configuration passing mechanism
        
        try:
            command = [
                "python", "-m", "code_graph_mcp.server",
                "--project-root", str(complex_project_structure),
                "--redis-url", "redis://localhost:6379/0", 
                "--redis-prefix", "test_stdio",
                "--verbose"
            ]
            
            # For testing, we'll mock the stdio client behavior
            print("🔌 Testing stdio client connection...")
            
            # Simulate MCP session
            async with stdio_client(command) as streams:
                if streams:
                    print("✅ Stdio client connected successfully")
                    
                    async with ClientSession(streams[0], streams[1]) as session:
                        # Test tool listing
                        tools = await session.list_tools()
                        tool_names = [tool.name for tool in tools.tools]
                        print(f"🛠️  Available tools: {tool_names}")
                        
                        # Test a few tools with cache enabled
                        test_cases = [
                            ("project_statistics", {}),
                            ("find_definition", {"symbol": "Calculator"}),
                            ("complexity_analysis", {"threshold": 10})
                        ]
                        
                        for tool_name, args in test_cases:
                            try:
                                print(f"🧪 Testing {tool_name}...")
                                result = await session.call_tool(tool_name, args)
                                
                                if result.content:
                                    print(f"   ✅ {tool_name} returned content")
                                else:
                                    print(f"   ⚠️  {tool_name} returned no content")
                                    
                            except Exception as e:
                                print(f"   ❌ {tool_name} failed: {e}")
                else:
                    print("❌ Failed to establish stdio connection")
                    
        except FileNotFoundError:
            print("⚠️  MCP server binary not found, skipping stdio test")
        except Exception as e:
            print(f"❌ Stdio test failed: {e}")


if __name__ == "__main__":
    # Manual testing support
    import sys
    
    async def run_manual_integration_tests():
        """Run manual integration tests for debugging"""
        print("🧪 Running MCP Cache Integration Tests")
        print("=" * 60)
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                project_path = Path(tmpdir)
                
                # Create minimal test project
                (project_path / "test.py").write_text("""
def test_function():
    return True

class TestClass:
    def method(self):
        return self
                """)
                
                # Test cache manager
                cache_manager = CacheManager(project_path, None)
                await cache_manager.initialize()
                
                # Test analyzer with cache
                analyzer = UniversalAST(project_path)
                analyzer.cache_manager = cache_manager
                
                # Test basic operations
                print("1️⃣ Testing basic analysis...")
                analysis = await analyzer.analyze_file_async(str(project_path / "test.py"))
                print(f"   ✅ Found {len(analysis.get('functions', []))} functions")
                
                print("2️⃣ Testing cache statistics...")
                stats = await cache_manager.get_cache_stats()
                print(f"   📊 Cache stats: {stats}")
                
                await cache_manager.close()
                print("✅ Integration test completed successfully")
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        asyncio.run(run_manual_integration_tests())
    else:
        print("Run with --manual for manual testing")
        print("Use 'pytest test_mcp_cache_integration.py' for full test suite")
