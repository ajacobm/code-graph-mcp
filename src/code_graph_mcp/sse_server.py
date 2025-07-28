#!/usr/bin/env python3
"""
SSE (Server-Sent Events) Server for Code Graph MCP

Provides HTTP/SSE endpoints for code analysis tools, exposing only the
call_tool and list_tools methods as requested.
"""

import asyncio
import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import uvicorn

from .server import (
    UniversalAnalysisEngine,
    get_tool_definitions,
    get_tool_handlers,
    ensure_analysis_engine_ready,
    cleanup_analysis_engine
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Pydantic models for API
class ToolCallRequest(BaseModel):
    """Request model for tool calls."""
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")


class ToolResponse(BaseModel):
    """Response model for tool definitions."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class SSECodeGraphServer:
    """SSE server for code graph analysis tools."""
    
    def __init__(self, project_root: Path, enable_file_watcher: bool = True):
        self.project_root = project_root
        self.enable_file_watcher = enable_file_watcher
        self.app = FastAPI(
            title="Code Graph MCP SSE Server",
            description="Server-Sent Events API for code graph intelligence",
            version="1.2.3"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup routes
        self._setup_routes()
        
        # Initialize analysis engine
        self.analysis_engine: Optional[UniversalAnalysisEngine] = None
        
        # Add startup and shutdown handlers
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize analysis engine on server startup."""
            logger.info(f"Starting SSE server for project: {self.project_root}")
            try:
                self.analysis_engine = UniversalAnalysisEngine(
                    self.project_root, 
                    enable_file_watcher=self.enable_file_watcher
                )
                # Ensure initial analysis is complete
                await self.analysis_engine._ensure_analyzed()
                logger.info("Analysis engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize analysis engine: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Cleanup on server shutdown."""
            logger.info("Shutting down SSE server...")
            if self.analysis_engine:
                await self.analysis_engine.cleanup()
            logger.info("Server shutdown complete")
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            return {
                "name": "Code Graph MCP SSE Server",
                "version": "1.2.3",
                "description": "Server-Sent Events API for code graph intelligence",
                "project_root": str(self.project_root),
                "endpoints": {
                    "list_tools": "/list-tools",
                    "call_tool": "/call-tool"
                }
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": time.time(),
                "analysis_engine_ready": self.analysis_engine is not None
            }
        
        @self.app.get("/list-tools")
        async def list_tools() -> List[ToolResponse]:
            """List available analysis tools."""
            try:
                tools = get_tool_definitions()
                return [
                    ToolResponse(
                        name=tool.name,
                        description=tool.description,
                        inputSchema=tool.inputSchema
                    )
                    for tool in tools
                ]
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")
        
        @self.app.post("/call-tool")
        async def call_tool(request: ToolCallRequest):
            """Call a tool with Server-Sent Events response."""
            if not self.analysis_engine:
                raise HTTPException(status_code=503, detail="Analysis engine not initialized")
            
            return StreamingResponse(
                self._stream_tool_response(request.name, request.arguments),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "Cache-Control"
                }
            )
        
        @self.app.get("/cache/stats")
        async def cache_stats():
            """Get cache statistics."""
            if not self.analysis_engine or not self.analysis_engine.analyzer.cache_manager:
                return {"status": "cache_disabled"}
            
            try:
                stats = await self.analysis_engine.analyzer.cache_manager.get_cache_stats()
                return stats
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")
        
        @self.app.post("/cache/clear")
        async def clear_cache():
            """Clear all cache data."""
            if not self.analysis_engine or not self.analysis_engine.analyzer.cache_manager:
                raise HTTPException(status_code=400, detail="Cache not enabled")
            
            try:
                await self.analysis_engine.analyzer.cache_manager.clear_all()
                return {"status": "success", "message": "Cache cleared"}
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")
    
    async def _stream_tool_response(self, tool_name: str, arguments: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream tool execution results as SSE events."""
        try:
            # Send start event
            yield f"event: start\ndata: {json.dumps({'tool': tool_name, 'status': 'starting'})}\n\n"
            
            # Get tool handlers
            handlers = get_tool_handlers()
            handler = handlers.get(tool_name)
            
            if not handler:
                error_msg = f"Unknown tool: {tool_name}"
                yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"
                return
            
            # Send progress event
            yield f"event: progress\ndata: {json.dumps({'status': 'executing', 'tool': tool_name})}\n\n"
            
            start_time = time.time()
            
            # Execute the tool
            logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
            result = await handler(self.analysis_engine, arguments)
            
            execution_time = time.time() - start_time
            
            # Convert TextContent results to JSON serializable format
            if isinstance(result, list):
                # Assuming list of TextContent objects
                text_results = []
                for item in result:
                    if hasattr(item, 'text'):
                        text_results.append(item.text)
                    else:
                        text_results.append(str(item))
                
                # Send success event with results
                yield f"event: result\ndata: {json.dumps({'results': text_results, 'execution_time': execution_time})}\n\n"
            else:
                # Single result
                text_result = result.text if hasattr(result, 'text') else str(result)
                yield f"event: result\ndata: {json.dumps({'result': text_result, 'execution_time': execution_time})}\n\n"
            
            # Send completion event
            yield f"event: complete\ndata: {json.dumps({'tool': tool_name, 'status': 'completed', 'execution_time': execution_time})}\n\n"
            
            logger.info(f"Tool {tool_name} completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            logger.exception(f"Error executing tool {tool_name}")
            error_info = {
                'error': str(e),
                'tool': tool_name,
                'traceback': traceback.format_exc()
            }
            yield f"event: error\ndata: {json.dumps(error_info)}\n\n"
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the SSE server."""
        logger.info(f"Starting SSE server on {host}:{port}")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            access_log=debug,
            reload=debug
        )


def create_sse_app(project_root: Path, enable_file_watcher: bool = True) -> FastAPI:
    """Create FastAPI application for SSE server."""
    server = SSECodeGraphServer(project_root, enable_file_watcher)
    return server.app


async def run_sse_server(
    project_root: Path,
    host: str = "0.0.0.0",
    port: int = 8000,
    debug: bool = False,
    enable_file_watcher: bool = True
):
    """Run the SSE server asynchronously."""
    server = SSECodeGraphServer(project_root, enable_file_watcher)
    
    try:
        config = uvicorn.Config(
            server.app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            access_log=debug
        )
        server_instance = uvicorn.Server(config)
        await server_instance.serve()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    import click
    
    @click.command()
    @click.option("--project-root", type=str, help="Root directory of the project to analyze", default=".")
    @click.option("--host", default="0.0.0.0", help="Host to bind to")
    @click.option("--port", default=8000, type=int, help="Port to bind to")
    @click.option("--debug", is_flag=True, help="Enable debug mode")
    @click.option("--disable-file-watcher", is_flag=True, help="Disable file watcher")
    def main(project_root: str, host: str, port: int, debug: bool, disable_file_watcher: bool):
        """Run the Code Graph SSE Server."""
        root_path = Path(project_root).resolve()
        server = SSECodeGraphServer(root_path, enable_file_watcher=not disable_file_watcher)
        server.run(host=host, port=port, debug=debug)
    
    main()