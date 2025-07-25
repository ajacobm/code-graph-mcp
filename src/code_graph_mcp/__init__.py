"""
Code Graph MCP Server

Enterprise-ready Model Context Protocol server providing comprehensive
code analysis, navigation, and quality assessment capabilities.
"""

import asyncio
from .server import CodeGraphMCPServer


def main() -> None:
    """Entry point for the code-graph-mcp command."""
    from .server import main as async_main  # pylint: disable=import-outside-toplevel

    asyncio.run(async_main())


__version__ = "0.1.0"
__all__ = ["CodeGraphMCPServer", "main"]
