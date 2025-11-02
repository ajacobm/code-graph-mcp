#!/usr/bin/env python3
"""
Tests for SSE (Server-Sent Events) server functionality
Tests sse_server.py and streaming capabilities
"""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from code_graph_mcp.sse_server import SSECodeGraphServer, create_sse_app


class TestSSEServer:
    """Test suite for SSE Server functionality"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create test files
            (project_path / "main.py").write_text("""
def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
            """)
            
            (project_path / "utils.py").write_text("""
def helper_function():
    return "helper"

class UtilityClass:
    def method(self):
        return "utility"
            """)
            
            (project_path / "subdir").mkdir()
            (project_path / "subdir" / "module.py").write_text("""
import os
from typing import List

def process_data(data: List[str]) -> str:
    return "\n".join(data)
            """)
            
            yield project_path

    @pytest.fixture
    def sse_server(self, temp_project_dir):
        """Create SSE server instance for testing"""
        server = SSECodeGraphServer(temp_project_dir, enable_file_watcher=False)
        yield server

    @pytest.fixture
    def test_app(self, temp_project_dir):
        """Create FastAPI test application"""
        app = create_sse_app(temp_project_dir, enable_file_watcher=False)
        return app

    def test_sse_server_initialization(self, temp_project_dir):
        """Test SSE server initialization"""
        server = SSECodeGraphServer(temp_project_dir, enable_file_watcher=False)
        
        assert server.project_root == temp_project_dir
        assert server.app is not None
        assert server.analysis_engine is not None

    def test_fastapi_app_creation(self, test_app):
        """Test FastAPI application creation"""
        assert test_app is not None
        
        # Check that routes are registered
        routes = [route.path for route in test_app.routes]
        expected_routes = [
            "/",
            "/tools",
            "/tools/{tool_name}/execute",
            "/tools/{tool_name}/stream", 
            "/cache/stats",
            "/cache/clear"
        ]
        
        for expected in expected_routes:
            assert any(expected in route for route in routes), f"Route {expected} not found"

    @pytest.mark.asyncio
    async def test_tools_listing_endpoint(self, test_app):
        """Test tools listing endpoint"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.get("/tools")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "tools" in data
            tool_names = [tool["name"] for tool in data["tools"]]
            
            expected_tools = [
                "analyze_codebase",
                "find_definition", 
                "find_references",
                "find_callers",
                "find_callees",
                "complexity_analysis",
                "dependency_analysis", 
                "project_statistics"
            ]
            
            for tool in expected_tools:
                assert tool in tool_names, f"Tool {tool} not found in {tool_names}"

    @pytest.mark.asyncio 
    async def test_tool_execution_endpoint(self, test_app):
        """Test synchronous tool execution endpoint"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Test project statistics tool
            response = await client.post(
                "/tools/project_statistics/execute",
                json={}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "result" in data
            assert "execution_time" in data
            assert data["execution_time"] > 0

    @pytest.mark.asyncio
    async def test_tool_streaming_endpoint(self, test_app):
        """Test streaming tool execution endpoint"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Test streaming response
            async with client.stream(
                "POST",
                "/tools/project_statistics/stream", 
                json={}
            ) as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream"
                
                events = []
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])  # Remove "data: " prefix
                            events.append(event_data)
                        except json.JSONDecodeError:
                            pass  # Skip malformed JSON
                
                # Verify we got start, progress, result, and complete events
                event_types = [event.get("status") for event in events if "status" in event]
                assert "starting" in event_types
                assert "executing" in event_types  
                assert "completed" in event_types

    @pytest.mark.asyncio
    async def test_cache_stats_endpoint(self, test_app):
        """Test cache statistics endpoint"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.get("/cache/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            # Should return cache disabled status or actual stats
            if "status" in data:
                assert data["status"] == "cache_disabled"
            else:
                # If cache is enabled, check for expected fields
                assert "memory" in data or "redis" in data

    @pytest.mark.asyncio
    async def test_cache_clear_endpoint(self, test_app):
        """Test cache clear endpoint"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post("/cache/clear")
            
            # Might return 400 if cache not enabled or 200 if successful
            assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    async def test_invalid_tool_execution(self, test_app):
        """Test execution of non-existent tool"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            response = await client.post(
                "/tools/nonexistent_tool/execute",
                json={}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "error" in data

    @pytest.mark.asyncio
    async def test_tool_execution_with_invalid_arguments(self, test_app):
        """Test tool execution with invalid arguments"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Test find_definition with missing symbol argument
            response = await client.post(
                "/tools/find_definition/execute",
                json={}  # Missing required 'symbol' argument
            )
            
            # Should handle the error gracefully
            assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self, test_app):
        """Test concurrent tool executions"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Start multiple tool executions concurrently
            tasks = [
                client.post("/tools/project_statistics/execute", json={}),
                client.post("/tools/analyze_codebase/execute", json={}),
                client.get("/tools"),
            ]
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All requests should complete (might succeed or fail, but not hang)
            assert len(responses) == 3
            for response in responses:
                assert not isinstance(response, Exception)
                assert response.status_code == 200

    @pytest.mark.asyncio 
    async def test_sse_event_stream_format(self, test_app):
        """Test SSE event stream formatting"""
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            async with client.stream(
                "POST",
                "/tools/project_statistics/stream",
                json={}
            ) as response:
                
                raw_content = b""
                async for chunk in response.aiter_bytes():
                    raw_content += chunk
                
                content = raw_content.decode('utf-8')
                
                # Verify SSE format
                assert "event: start" in content
                assert "event: result" in content or "event: error" in content
                assert "event: complete" in content or "event: error" in content
                assert "data: " in content

    def test_sync_test_client_basic_endpoints(self, test_app):
        """Test basic endpoints using synchronous test client"""
        with TestClient(test_app) as client:
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200
            assert "Code Graph MCP SSE Server" in response.json()["message"]
            
            # Test tools listing  
            response = client.get("/tools")
            assert response.status_code == 200
            assert "tools" in response.json()


class TestSSEServerWithCache:
    """Test SSE server with Redis cache enabled"""

    @pytest.fixture
    def temp_project_with_cache(self):
        """Create project with cache configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create test files
            (project_path / "cached_test.py").write_text("""
def cached_function():
    \"\"\"A function that should be cached\"\"\"
    return True
            """)
            
            yield project_path

    @pytest.mark.asyncio
    async def test_sse_server_with_redis_cache(self, temp_project_with_cache):
        """Test SSE server with Redis cache integration"""
        # Mock Redis to avoid requiring actual Redis instance
        with patch('code_graph_mcp.redis_cache.RedisCache') as MockRedisCache:
            mock_cache = AsyncMock()
            mock_cache.available = True
            mock_cache.get_stats.return_value = {
                'hits': 10,
                'misses': 5,
                'memory_usage': '1MB'
            }
            MockRedisCache.return_value = mock_cache
            
            redis_config = {
                'url': 'redis://localhost:6379/0',
                'prefix': 'test_sse'
            }
            
            server = SSECodeGraphServer(
                temp_project_with_cache, 
                enable_file_watcher=False,
                redis_config=redis_config
            )
            
            # Test that cache stats endpoint works
            test_app = server.app
            async with AsyncClient(app=test_app, base_url="http://test") as client:
                response = await client.get("/cache/stats")
                assert response.status_code == 200
                
                # Should get actual stats, not disabled status
                data = response.json()
                assert "hits" in data or "memory" in data

    @pytest.mark.asyncio
    async def test_cache_performance_impact(self, temp_project_with_cache):
        """Test performance impact of cache on tool execution"""
        server = SSECodeGraphServer(temp_project_with_cache, enable_file_watcher=False)
        test_app = server.app
        
        async with AsyncClient(app=test_app, base_url="http://test") as client:
            # Execute same tool multiple times to test caching
            execution_times = []
            
            for i in range(3):
                start_time = time.time()
                response = await client.post(
                    "/tools/analyze_codebase/execute",
                    json={}
                )
                end_time = time.time()
                
                assert response.status_code == 200
                execution_times.append(end_time - start_time)
            
            # Later executions might be faster due to caching
            # (though this depends on implementation details)
            assert all(t > 0 for t in execution_times)


class TestSSEErrorHandling:
    """Test error handling in SSE server"""

    @pytest.fixture
    def error_test_app(self):
        """Create app for error testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            app = create_sse_app(project_path, enable_file_watcher=False)
            yield app

    @pytest.mark.asyncio
    async def test_malformed_request_handling(self, error_test_app):
        """Test handling of malformed requests"""
        async with AsyncClient(app=error_test_app, base_url="http://test") as client:
            # Test with invalid JSON
            response = await client.post(
                "/tools/analyze_codebase/execute",
                data="invalid json",
                headers={"content-type": "application/json"}
            )
            assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_streaming_error_handling(self, error_test_app):
        """Test error handling in streaming responses"""
        async with AsyncClient(app=error_test_app, base_url="http://test") as client:
            # Force an error by using invalid tool
            async with client.stream(
                "POST",
                "/tools/invalid_tool/stream",
                json={}
            ) as response:
                
                content = ""
                async for line in response.aiter_lines():
                    content += line + "\n"
                
                # Should contain error event
                assert "event: error" in content

    @pytest.mark.asyncio
    async def test_server_shutdown_handling(self, error_test_app):
        """Test graceful server shutdown"""
        # This is more of a documentation test since actual shutdown
        # testing is complex in the test environment
        
        async with AsyncClient(app=error_test_app, base_url="http://test") as client:
            # Verify server is responsive
            response = await client.get("/")
            assert response.status_code == 200
        
        # In a real scenario, we would test:
        # 1. Server stops accepting new connections
        # 2. Existing connections complete gracefully  
        # 3. Resources are cleaned up properly


class TestSSEIntegration:
    """Integration tests for SSE server"""

    @pytest.mark.asyncio
    async def test_full_analysis_workflow_via_sse(self):
        """Test complete analysis workflow through SSE endpoints"""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            # Create a realistic project structure
            (project_path / "main.py").write_text("""
from utils import Calculator
from typing import Optional

def main() -> int:
    calc = Calculator()
    result = calc.add(5, 3)
    print(f"Result: {result}")
    return 0

if __name__ == "__main__":
    main()
            """)
            
            (project_path / "utils.py").write_text("""
class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
    
    def multiply(self, a: int, b: int) -> int:
        return a * b

def helper() -> str:
    return "helper function"
            """)
            
            app = create_sse_app(project_path, enable_file_watcher=False)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                # Step 1: Get project statistics
                stats_response = await client.post(
                    "/tools/project_statistics/execute",
                    json={}
                )
                assert stats_response.status_code == 200
                stats = stats_response.json()
                assert "result" in stats
                
                # Step 2: Analyze codebase
                analysis_response = await client.post(
                    "/tools/analyze_codebase/execute",
                    json={}
                )
                assert analysis_response.status_code == 200
                
                # Step 3: Find definitions
                definition_response = await client.post(
                    "/tools/find_definition/execute",
                    json={"symbol": "Calculator"}
                )
                assert definition_response.status_code == 200
                
                # Step 4: Find references
                references_response = await client.post(
                    "/tools/find_references/execute", 
                    json={"symbol": "Calculator"}
                )
                assert references_response.status_code == 200
                
                # All operations should complete successfully
                assert all(r.status_code == 200 for r in [
                    stats_response, analysis_response, 
                    definition_response, references_response
                ])


if __name__ == "__main__":
    # Manual testing support
    import sys
    
    async def run_manual_sse_tests():
        """Run manual SSE tests for debugging"""
        print("🌊 Running SSE Server Tests")
        print("=" * 50)
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                project_path = Path(tmpdir)
                (project_path / "test.py").write_text("def test(): pass")
                
                # Test server creation
                server = SSECodeGraphServer(project_path, enable_file_watcher=False)
                print("✅ SSE Server created successfully")
                
                # Test app creation
                app = create_sse_app(project_path, enable_file_watcher=False)
                print("✅ FastAPI app created successfully")
                
                # Test with sync client
                with TestClient(app) as client:
                    response = client.get("/")
                    if response.status_code == 200:
                        print("✅ Root endpoint working")
                    else:
                        print(f"❌ Root endpoint failed: {response.status_code}")
                    
                    response = client.get("/tools")
                    if response.status_code == 200:
                        tools = response.json()["tools"]
                        print(f"✅ Tools endpoint working ({len(tools)} tools)")
                    else:
                        print(f"❌ Tools endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            
        print("\n🎯 Manual SSE tests completed")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        asyncio.run(run_manual_sse_tests())
    else:
        print("Run with --manual for manual testing")
        print("Use 'pytest test_sse_server.py' for full test suite")
