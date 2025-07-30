"""
Code Graph Package

High-performance graph operations and algorithms for code analysis.
Uses Rust-backed rustworkx for optimal performance with large codebases.
"""

from .rustworkx_unified import RustworkxCodeGraph

__all__ = ["RustworkxCodeGraph"]