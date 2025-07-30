#!/usr/bin/env python3
"""
MCP Server for Code Graph Analysis

Proper MCP implementation using official Python SDK patterns.
Provides code analysis tools through MCP protocol.
"""

import contextlib
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Optional

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# Import our existing MCP infrastructure
from code_graph_mcp.server.mcp_server import (
    get_tool_definitions, 
    get_tool_handlers,
    ensure_analysis_engine_ready,
    cleanup_analysis_engine
)

logger = logging.getLogger(__name__)


class CodeGraphMCPServer:
    """MCP Server for Code Graph Analysis using official Python SDK patterns."""
    
    def __init__(
        self, 
        project_root: Path, 
        redis_url: Optional[str] = None,
        json_response: bool = False
    ):
        self.project_root = project_root
        self.redis_url = redis_url
        self.json_response = json_response
        self.app = Server("code-graph-mcp")
        self.analysis_engine = None
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up MCP tool handlers using decorators."""
        
        @self.app.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
            """Handle tool calls using our existing MCP infrastructure."""
            try:
                # Ensure analysis engine is ready
                self.analysis_engine = await ensure_analysis_engine_ready(
                    self.project_root, self.redis_url
                )
                
                # Get our existing tool handlers
                handlers = get_tool_handlers()
                
                if name not in handlers:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Execute the tool using existing infrastructure
                logger.info(f"Executing tool: {name}")
                result = await handlers[name](self.analysis_engine, arguments)
                
                # Convert result to proper MCP ContentBlock format
                if isinstance(result, list):
                    content_blocks = []
                    for item in result:
                        if hasattr(item, 'text'):
                            content_blocks.append(
                                types.TextContent(type="text", text=item.text)
                            )
                        else:
                            content_blocks.append(
                                types.TextContent(type="text", text=str(item))
                            )
                    return content_blocks
                else:
                    text = result.text if hasattr(result, 'text') else str(result)
                    return [types.TextContent(type="text", text=text)]
                    
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [types.TextContent(
                    type="text", 
                    text=f"Error executing tool {name}: {str(e)}"
                )]
        
        @self.app.list_tools()
        async def list_tools() -> list[types.Tool]:
            """List available tools using our existing infrastructure."""
            try:
                # Get tool definitions from existing infrastructure  
                tool_definitions = get_tool_definitions()
                
                # Convert to MCP types.Tool format
                mcp_tools = []
                for tool_def in tool_definitions:
                    mcp_tools.append(types.Tool(
                        name=tool_def.name,
                        description=tool_def.description,
                        inputSchema=tool_def.inputSchema
                    ))
                
                return mcp_tools
                
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return []
    
    def create_starlette_app(self) -> Starlette:
        """Create Starlette ASGI application with proper MCP transport."""
        
        # Create session manager using official SDK pattern
        session_manager = StreamableHTTPSessionManager(
            app=self.app,
            event_store=None,  # Stateless for now
            json_response=self.json_response,
            stateless=True
        )

        async def handle_mcp_request(scope: Scope, receive: Receive, send: Send) -> None:
            """Handle MCP requests through StreamableHTTP transport."""
            await session_manager.handle_request(scope, receive, send)

        @contextlib.asynccontextmanager
        async def lifespan(starlette_app: Starlette) -> AsyncIterator[None]:
            """Manage application lifecycle."""
            async with session_manager.run():
                logger.info(f"Code Graph MCP Server started for: {self.project_root}")
                try:
                    yield
                finally:
                    logger.info("Shutting down Code Graph MCP Server...")
                    if self.analysis_engine:
                        await cleanup_analysis_engine()

        # Create Starlette app following official pattern
        starlette_app = Starlette(
            debug=True,
            routes=[
                Mount("/mcp", app=handle_mcp_request),
            ],
            lifespan=lifespan,
        )
        
        return starlette_app
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the MCP server."""
        starlette_app = self.create_starlette_app()
        
        import uvicorn
        uvicorn.run(starlette_app, host=host, port=port)


@click.command()
@click.option("--project-root", default=".", help="Project root directory")
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--redis-url", help="Redis URL for caching")
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
def main(
    project_root: str,
    host: str,
    port: int,
    redis_url: Optional[str],
    json_response: bool,
    log_level: str,
) -> int:
    """Run Code Graph MCP Server."""
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    root_path = Path(project_root).resolve()
    server = CodeGraphMCPServer(
        project_root=root_path,
        redis_url=redis_url,
        json_response=json_response
    )
    
    try:
        server.run(host=host, port=port)
        return 0
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1


if __name__ == "__main__":
    main()