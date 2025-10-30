#!/usr/bin/env python3
"""
HTTP Server with FastAPI for Graph Query API

Provides REST endpoints for code graph analysis and traversal.
"""

import logging
from pathlib import Path
from typing import Optional

import click
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .server.analysis_engine import UniversalAnalysisEngine
from .server.graph_api import create_graph_api_router

logger = logging.getLogger(__name__)


class GraphAPIServer:
    """HTTP server for graph query API."""
    
    def __init__(
        self,
        project_root: Path,
        host: str = "0.0.0.0",
        port: int = 8000,
        redis_url: Optional[str] = None,
        enable_redis_cache: bool = True
    ):
        self.project_root = project_root
        self.host = host
        self.port = port
        self.redis_url = redis_url
        self.enable_redis_cache = enable_redis_cache
        self.app = FastAPI(
            title="Code Graph API",
            description="REST API for code graph analysis and visualization",
            version="1.0.0"
        )
        self.engine: Optional[UniversalAnalysisEngine] = None
        self._setup_app()
    
    def _setup_app(self):
        """Set up FastAPI application."""
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @self.app.on_event("startup")
        async def startup_event():
            """Initialize analysis engine on startup."""
            try:
                logger.info(f"Initializing analysis engine for {self.project_root}")
                from code_graph_mcp.redis_cache import RedisConfig
                
                redis_config = None
                if self.enable_redis_cache:
                    redis_config = RedisConfig(url=self.redis_url) if self.redis_url else RedisConfig()
                
                self.engine = UniversalAnalysisEngine(
                    self.project_root,
                    redis_config=redis_config,
                    enable_redis_cache=self.enable_redis_cache
                )
                
                logger.info("Analysis engine initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize analysis engine: {e}")
                raise
        
        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Clean up analysis engine on shutdown."""
            try:
                if self.engine:
                    await self.engine.cleanup()
                logger.info("Analysis engine cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            try:
                if not self.engine:
                    return JSONResponse(
                        {"status": "initializing"},
                        status_code=202
                    )
                
                cache_manager = getattr(self.engine, 'cache_manager', None)
                redis_ok = True
                
                if cache_manager and self.enable_redis_cache:
                    try:
                        if hasattr(cache_manager, 'redis_client') and cache_manager.redis_client:
                            cache_manager.redis_client.ping()
                    except Exception as e:
                        logger.warning(f"Redis health check failed: {e}")
                        redis_ok = False
                
                return JSONResponse({
                    "status": "healthy",
                    "redis_enabled": self.enable_redis_cache,
                    "redis_ok": redis_ok
                })
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    {"status": "unhealthy", "error": str(e)},
                    status_code=500
                )
        
        @self.app.get("/")
        async def root():
            """Root endpoint with API documentation."""
            return JSONResponse({
                "name": "Code Graph API",
                "version": "1.0.0",
                "docs": "/docs",
                "endpoints": {
                    "health": "/health",
                    "graph_stats": "/api/graph/stats",
                    "get_node": "/api/graph/nodes/{node_id}",
                    "traverse": "/api/graph/traverse (POST)",
                    "search_nodes": "/api/graph/nodes/search",
                    "get_seams": "/api/graph/seams",
                    "call_chain": "/api/graph/call-chain/{start_node}"
                }
            })
        
        if self.engine:
            self.app.include_router(create_graph_api_router(self.engine))
    
    async def initialize(self):
        """Initialize the server."""
        try:
            logger.info(f"Initializing HTTP server on {self.host}:{self.port}")
            from code_graph_mcp.redis_cache import RedisConfig
            
            redis_config = None
            if self.enable_redis_cache:
                redis_config = RedisConfig(url=self.redis_url) if self.redis_url else RedisConfig()
            
            self.engine = UniversalAnalysisEngine(
                self.project_root,
                redis_config=redis_config,
                enable_redis_cache=self.enable_redis_cache
            )
            
            self.app.include_router(create_graph_api_router(self.engine))
            logger.info("Server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    
    def run(self):
        """Run the HTTP server."""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


@click.command()
@click.option(
    "--project-root",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Root directory of the project to analyze"
)
@click.option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="Host to bind to"
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to listen on"
)
@click.option(
    "--redis-url",
    type=str,
    default=None,
    help="Redis URL for caching (optional)"
)
@click.option(
    "--no-redis",
    is_flag=True,
    default=False,
    help="Disable Redis caching"
)
def main(project_root: str, host: str, port: int, redis_url: Optional[str], no_redis: bool):
    """Start the Code Graph API HTTP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    server = GraphAPIServer(
        Path(project_root),
        host=host,
        port=port,
        redis_url=redis_url,
        enable_redis_cache=not no_redis
    )
    
    logger.info(f"Starting Code Graph API server on {host}:{port}")
    logger.info(f"Analyzing project: {project_root}")
    server.run()


if __name__ == "__main__":
    main()
