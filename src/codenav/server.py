#!/usr/bin/env python3
"""
Code Graph Intelligence MCP Server

A Model Context Protocol server providing comprehensive
code analysis, navigation, and quality assessment capabilities.

This module now acts as a compatibility layer, importing from the
restructured server package.
"""

# Import from the new server package for backward compatibility
from .server import UniversalAnalysisEngine, main, cli

# Re-export for existing imports
__all__ = ["UniversalAnalysisEngine", "main", "cli"]

if __name__ == "__main__":
    cli(standalone_mode=False)