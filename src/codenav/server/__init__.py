"""
Code Graph Intelligence MCP Server Package

Provides comprehensive code analysis, navigation, and quality assessment capabilities
through Model Context Protocol (MCP) interface.
"""

from .analysis_engine import UniversalAnalysisEngine
from .mcp_server import (
    main, 
    cli,
    get_tool_definitions,
    get_tool_handlers,
    ensure_analysis_engine_ready,
    cleanup_analysis_engine
)

__all__ = [
    "UniversalAnalysisEngine", 
    "main", 
    "cli",
    "get_tool_definitions",
    "get_tool_handlers", 
    "ensure_analysis_engine_ready",
    "cleanup_analysis_engine"
]