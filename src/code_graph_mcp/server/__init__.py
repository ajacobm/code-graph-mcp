"""
Code Graph Intelligence MCP Server Package

Provides comprehensive code analysis, navigation, and quality assessment capabilities
through Model Context Protocol (MCP) interface.
"""

from .analysis_engine import UniversalAnalysisEngine
from .mcp_server import main, cli

__all__ = ["UniversalAnalysisEngine", "main", "cli"]