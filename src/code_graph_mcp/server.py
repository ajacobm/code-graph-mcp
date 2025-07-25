#!/usr/bin/env python3
# pylint: disable=too-many-lines,broad-exception-caught
"""
Code Graph Intelligence MCP Server

A Model Context Protocol server providing comprehensive
code analysis, navigation, and quality assessment capabilities.
"""

import ast
import asyncio
import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceRequest,
    ReadResourceResult,
    Resource,
    TextContent,
    Tool,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============================================================================
# Caching Infrastructure
# ============================================================================


class CacheManager:
    """Centralized cache management with statistics and invalidation."""

    def __init__(self):
        self.stats = {
            "ast_hits": 0,
            "ast_misses": 0,
            "graph_hits": 0,
            "graph_misses": 0,
            "file_hits": 0,
            "file_misses": 0,
        }

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        total_requests = sum(self.stats.values())
        if total_requests == 0:
            return {"hit_rate": 0.0, "requests": 0, "details": self.stats}

        hits = self.stats["ast_hits"] + self.stats["graph_hits"] + self.stats["file_hits"]
        hit_rate = hits / total_requests

        return {"hit_rate": hit_rate, "requests": total_requests, "details": self.stats}

    def record_hit(self, cache_type: str):
        """Record cache hit."""
        self.stats[f"{cache_type}_hits"] += 1

    def record_miss(self, cache_type: str):
        """Record cache miss."""
        self.stats[f"{cache_type}_misses"] += 1


# Global cache manager
cache_manager = CacheManager()


@lru_cache(maxsize=256)
def _parse_file_cached(
    file_path: str, _mtime: float
) -> Optional[ast.AST]:
    """Cache AST parsing with file modification time invalidation.

    Args:
        file_path: Path to the Python file to parse
        mtime: File modification time for cache invalidation
    """
    # _mtime parameter used for cache invalidation when file changes
    try:
        cache_manager.record_hit("ast")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ast.parse(content, filename=file_path)
    except (OSError, SyntaxError) as e:
        logger.debug("Failed to parse %s: %s", file_path, e)
        return None


@lru_cache(maxsize=128)
def _get_python_files_cached(
    _root_path: str, _ignore_patterns_hash: str
) -> Tuple[str, ...]:
    """Cache Python file discovery with gitignore pattern invalidation.

    Args:
        root_path: Root directory path for file discovery
        ignore_patterns_hash: Hash of ignore patterns for cache invalidation
    """
    # Parameters used for cache key generation and invalidation
    cache_manager.record_hit("file")
    # Implementation will be added in the file traversal section
    return tuple()


# ============================================================================
# Core Graph Data Structures
# ============================================================================


class NodeType(str, Enum):
    """Types of nodes in the code graph."""

    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    PARAMETER = "parameter"
    ATTRIBUTE = "attribute"


class EdgeType(str, Enum):
    """Types of edges in the code graph."""

    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    DEFINES = "defines"
    REFERENCES = "references"
    CONTAINS = "contains"
    ASSIGNS = "assigns"


@dataclass
class CodeLocation:
    """Represents a location in source code."""

    file_path: str
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0


@dataclass
class CodeNode:
    """Represents a node in the code graph."""

    id: str
    name: str
    node_type: NodeType
    location: CodeLocation
    metadata: Dict[str, Any] = field(default_factory=dict)
    docstring: Optional[str] = None
    complexity: int = 0


@dataclass
class CodeEdge:
    """Represents an edge in the code graph."""

    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeGraph:
    """In-memory representation of code relationships."""

    def __init__(self):
        self.nodes: Dict[str, CodeNode] = {}
        self.edges: Dict[str, CodeEdge] = {}
        self.node_edges: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node: CodeNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: CodeEdge) -> None:
        """Add an edge to the graph."""
        self.edges[edge.id] = edge
        self.node_edges[edge.source_id].add(edge.id)
        self.reverse_edges[edge.target_id].add(edge.id)

    def get_node(self, node_id: str) -> Optional[CodeNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[CodeEdge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)

    def get_edges_from(self, node_id: str) -> List[CodeEdge]:
        """Get all edges originating from a node."""
        return [self.edges[edge_id] for edge_id in self.node_edges.get(node_id, set())]

    def get_edges_to(self, node_id: str) -> List[CodeEdge]:
        """Get all edges targeting a node."""
        return [self.edges[edge_id] for edge_id in self.reverse_edges.get(node_id, set())]

    def find_nodes_by_name(self, name: str) -> List[CodeNode]:
        """Find nodes by name."""
        return [node for node in self.nodes.values() if node.name == name]

    def find_nodes_by_type(self, node_type: NodeType) -> List[CodeNode]:
        """Find nodes by type."""
        return [node for node in self.nodes.values() if node.node_type == node_type]


# ============================================================================
# Graph Builder and Analysis
# ============================================================================


class PythonGraphBuilder:  # pylint: disable=too-few-public-methods
    """Builds code graphs from Python source files."""

    def __init__(self):
        self.current_file: Optional[str] = None
        self.current_module: Optional[str] = None

    def build_from_file(self, file_path: Path) -> Tuple[List[CodeNode], List[CodeEdge]]:
        """Build graph nodes and edges from a Python file."""
        nodes = []
        edges = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source, filename=str(file_path))

            # Set context
            self.current_file = str(file_path)
            self.current_module = file_path.stem

            # Create file node
            file_node = CodeNode(
                id=f"file:{file_path}",
                name=str(file_path),
                node_type=NodeType.FILE,
                location=CodeLocation(str(file_path), 1, len(source.splitlines())),
                metadata={"lines_of_code": len(source.splitlines())},
            )
            nodes.append(file_node)

            # Visit AST nodes
            visitor = GraphBuildingVisitor(self.current_file, nodes, edges)
            visitor.visit(tree)

        except (OSError, SyntaxError) as e:
            logger.error("Failed to parse %s: %s", file_path, e)

        return nodes, edges


class GraphBuildingVisitor(ast.NodeVisitor):
    """AST visitor that builds graph nodes and edges."""

    def __init__(self, file_path: str, nodes: List[CodeNode], edges: List[CodeEdge]):
        self.file_path = file_path
        self.nodes = nodes
        self.edges = edges
        self.scope_stack = []
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # pylint: disable=invalid-name
        """Visit class definition."""
        class_id = f"class:{self.file_path}:{node.name}:{node.lineno}"

        class_node = CodeNode(
            id=class_id,
            name=node.name,
            node_type=NodeType.CLASS,
            location=CodeLocation(
                self.file_path, node.lineno, getattr(node, "end_lineno", node.lineno)
            ),
            docstring=ast.get_docstring(node),
            complexity=self._calculate_complexity(node),
        )
        self.nodes.append(class_node)

        # Add inheritance edges
        for base in node.bases:
            if isinstance(base, ast.Name):
                inheritance_edge = CodeEdge(
                    id=f"inherits:{class_id}:{base.id}",
                    source_id=class_id,
                    target_id=f"class:{base.id}",
                    edge_type=EdgeType.INHERITS,
                )
                self.edges.append(inheritance_edge)

        # Visit class body
        old_class = self.current_class
        self.current_class = class_id
        self.scope_stack.append(class_id)

        for child in node.body:
            self.visit(child)

        self.scope_stack.pop()
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # pylint: disable=invalid-name
        """Visit function definition."""
        node_type = NodeType.METHOD if self.current_class else NodeType.FUNCTION
        func_id = f"func:{self.file_path}:{node.name}:{node.lineno}"

        func_node = CodeNode(
            id=func_id,
            name=node.name,
            node_type=node_type,
            location=CodeLocation(
                self.file_path, node.lineno, getattr(node, "end_lineno", node.lineno)
            ),
            docstring=ast.get_docstring(node),
            complexity=self._calculate_complexity(node),
            metadata={
                "parameters": [arg.arg for arg in node.args.args],
                "is_async": isinstance(node, ast.AsyncFunctionDef),
            },
        )
        self.nodes.append(func_node)

        # Add parameters as nodes
        for arg in node.args.args:
            param_id = f"param:{func_id}:{arg.arg}"
            param_node = CodeNode(
                id=param_id,
                name=arg.arg,
                node_type=NodeType.PARAMETER,
                location=CodeLocation(self.file_path, node.lineno, node.lineno),
            )
            self.nodes.append(param_node)

            # Add contains edge
            param_edge = CodeEdge(
                id=f"contains:{func_id}:{param_id}",
                source_id=func_id,
                target_id=param_id,
                edge_type=EdgeType.CONTAINS,
            )
            self.edges.append(param_edge)

        # Visit function body for calls
        self.scope_stack.append(func_id)
        for child in node.body:
            self.visit(child)
        self.scope_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:  # pylint: disable=invalid-name
        """Visit function call."""
        if self.scope_stack:
            caller_id = self.scope_stack[-1]

            # Extract function name
            func_name = None
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr

            if func_name:
                call_edge = CodeEdge(
                    id=f"calls:{caller_id}:{func_name}:{node.lineno}",
                    source_id=caller_id,
                    target_id=f"func:{func_name}",
                    edge_type=EdgeType.CALLS,
                    metadata={"line": node.lineno},
                )
                self.edges.append(call_edge)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # pylint: disable=invalid-name
        """Visit import statement."""
        for alias in node.names:
            import_id = f"import:{self.file_path}:{alias.name}:{node.lineno}"
            import_node = CodeNode(
                id=import_id,
                name=alias.name,
                node_type=NodeType.IMPORT,
                location=CodeLocation(self.file_path, node.lineno, node.lineno),
                metadata={"alias": alias.asname},
            )
            self.nodes.append(import_node)

            # Add import edge
            import_edge = CodeEdge(
                id=f"imports:{self.file_path}:{alias.name}",
                source_id=f"file:{self.file_path}",
                target_id=f"module:{alias.name}",
                edge_type=EdgeType.IMPORTS,
            )
            self.edges.append(import_edge)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # pylint: disable=invalid-name
        """Visit from import statement."""
        module = node.module or ""
        for alias in node.names:
            import_id = f"import:{self.file_path}:{module}.{alias.name}:{node.lineno}"
            import_node = CodeNode(
                id=import_id,
                name=f"{module}.{alias.name}",
                node_type=NodeType.IMPORT,
                location=CodeLocation(self.file_path, node.lineno, node.lineno),
                metadata={"module": module, "alias": alias.asname},
            )
            self.nodes.append(import_node)

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1

        return complexity


# ============================================================================
# File Management and Filtering
# ============================================================================


class FileManager:
    """Manages file discovery and filtering for code analysis."""

    DEFAULT_EXCLUDE_DIRS = {
        ".git",
        ".svn",
        ".hg",
        ".bzr",
        "node_modules",
        "venv",
        "env",
        ".env",
        "virtualenv",
        "__pycache__",
        ".pytest_cache",
        ".tox",
        ".mypy_cache",
        "build",
        "dist",
        "target",
        "bin",
        "obj",
        "out",
        ".vscode",
        ".idea",
        ".vs",
        ".cache",
        ".tmp",
        "tmp",
        "temp",
    }

    DEFAULT_EXCLUDE_PATTERNS = [
        r".*\.pyc$",
        r".*\.pyo$",
        r".*\.pyd$",
        r".*\.(jpg|jpeg|png|gif|svg|ico|bmp)$",
        r".*\.log$",
        r".*\.db$",
        r".*\.sqlite.*$",
        r".*\.lock$",
        r".*\.DS_Store$",
        r"Thumbs\.db$",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.exclude_dirs = self.DEFAULT_EXCLUDE_DIRS.copy()
        self.exclude_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.DEFAULT_EXCLUDE_PATTERNS
        ]
        self.gitignore_patterns = []

        self._load_gitignore()

    def _load_gitignore(self):
        """Load .gitignore patterns."""
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pattern = self._gitignore_to_regex(line)
                            if pattern:
                                self.gitignore_patterns.append(re.compile(pattern, re.IGNORECASE))
            except OSError as e:
                logger.warning("Failed to load .gitignore: %s", e)

    def _gitignore_to_regex(self, pattern: str) -> Optional[str]:
        """Convert gitignore pattern to regex."""
        if not pattern or pattern.startswith("!"):
            return None

        pattern = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
        if pattern.endswith("/"):
            pattern = pattern[:-1] + "$"
        if pattern.startswith(r"\/"):
            pattern = "^" + pattern[2:]
        else:
            pattern = ".*" + pattern

        return pattern

    def should_include_file(self, file_path: Path) -> bool:
        """Determine if a file should be included in analysis."""
        try:
            rel_path = file_path.relative_to(self.project_root)
            rel_path_str = str(rel_path)

            # Check directory exclusions
            for part in rel_path.parts:
                if part in self.exclude_dirs:
                    return False

            # Check file patterns
            for pattern in self.exclude_patterns:
                if pattern.match(rel_path_str):
                    return False

            # Check gitignore patterns
            for pattern in self.gitignore_patterns:
                if pattern.match(rel_path_str):
                    return False

            # Only include Python files
            return file_path.suffix in {".py", ".pyi"}

        except ValueError:
            return False

    def discover_files(self) -> List[Path]:
        """Discover all analyzable files in the project."""
        files = []
        for root, dirs, filenames in os.walk(self.project_root):
            # Filter directories in-place
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for filename in filenames:
                file_path = Path(root) / filename
                if self.should_include_file(file_path):
                    files.append(file_path)

        return files


# ============================================================================
# Analysis Engine
# ============================================================================


class CodeAnalysisEngine:
    """Core engine for code analysis and intelligence."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.graph = CodeGraph()
        self.file_manager = FileManager(project_root)
        self.builder = PythonGraphBuilder()
        self.last_build_time: Optional[float] = None

    async def build_graph(self) -> None:
        """Build the complete code graph."""
        logger.info("Building code graph for %s", self.project_root)
        start_time = time.time()

        # Clear existing graph
        self.graph = CodeGraph()

        # Discover files
        files = self.file_manager.discover_files()
        logger.info("Found %d Python files to analyze", len(files))

        # Build graph from each file
        for file_path in files:
            try:
                nodes, edges = self.builder.build_from_file(file_path)

                for node in nodes:
                    self.graph.add_node(node)
                for edge in edges:
                    self.graph.add_edge(edge)

            except (OSError, SyntaxError) as e:
                logger.error("Failed to analyze %s: %s", file_path, e)

        self.last_build_time = time.time()
        build_duration = self.last_build_time - start_time

        logger.info(
            "Graph build complete: %d nodes, %d edges in %.2fs",
            len(self.graph.nodes),
            len(self.graph.edges),
            build_duration,
        )

    def get_project_stats(self) -> Dict[str, Any]:
        """Get comprehensive project statistics."""
        nodes_by_type = defaultdict(int)
        edges_by_type = defaultdict(int)
        complexity_scores = []

        for node in self.graph.nodes.values():
            nodes_by_type[node.node_type.value] += 1
            if node.complexity > 0:
                complexity_scores.append(node.complexity)

        for edge in self.graph.edges.values():
            edges_by_type[edge.edge_type.value] += 1

        return {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "nodes_by_type": dict(nodes_by_type),
            "edges_by_type": dict(edges_by_type),
            "average_complexity": (
                sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
            ),
            "max_complexity": max(complexity_scores) if complexity_scores else 0,
            "files_analyzed": nodes_by_type["file"],
            "last_build_time": self.last_build_time,
            "project_root": str(self.project_root),
        }

    def find_symbol_definition(self, symbol: str) -> List[Dict[str, Any]]:
        """Find definitions of a symbol."""
        results = []

        for node in self.graph.nodes.values():
            if node.name == symbol and node.node_type in {
                NodeType.FUNCTION,
                NodeType.METHOD,
                NodeType.CLASS,
            }:
                results.append(
                    {
                        "symbol": symbol,
                        "type": node.node_type.value,
                        "file": node.location.file_path,
                        "line": node.location.start_line,
                        "docstring": node.docstring,
                        "complexity": node.complexity,
                    }
                )

        return results

    def find_symbol_references(self, symbol: str) -> List[Dict[str, Any]]:
        """Find references to a symbol."""
        results = []
        target_nodes = [node for node in self.graph.nodes.values() if node.name == symbol]

        for target_node in target_nodes:
            # Find edges pointing to this node
            edges_to_node = self.graph.get_edges_to(target_node.id)

            for edge in edges_to_node:
                source_node = self.graph.get_node(edge.source_id)
                if source_node:
                    results.append(
                        {
                            "symbol": symbol,
                            "reference_type": edge.edge_type.value,
                            "file": source_node.location.file_path,
                            "line": source_node.location.start_line,
                            "context": source_node.name,
                        }
                    )

        return results

    def find_function_callers(self, function_name: str) -> List[Dict[str, Any]]:
        """Find all functions that call the specified function."""
        results = []

        for edge in self.graph.edges.values():
            if edge.edge_type == EdgeType.CALLS and function_name in edge.target_id:
                source_node = self.graph.get_node(edge.source_id)
                if source_node:
                    results.append(
                        {
                            "caller": source_node.name,
                            "caller_type": source_node.node_type.value,
                            "file": source_node.location.file_path,
                            "line": source_node.location.start_line,
                            "target_function": function_name,
                        }
                    )

        return results

    def find_function_callees(self, function_name: str) -> List[Dict[str, Any]]:
        """Find all functions called by the specified function."""
        results = []

        # Find the function node
        func_nodes = [
            node
            for node in self.graph.nodes.values()
            if (
                node.name == function_name
                and node.node_type in {NodeType.FUNCTION, NodeType.METHOD}
            )
        ]

        for func_node in func_nodes:
            edges_from_func = self.graph.get_edges_from(func_node.id)

            for edge in edges_from_func:
                if edge.edge_type == EdgeType.CALLS:
                    results.append(
                        {
                            "caller": function_name,
                            "callee": edge.target_id.split(":")[-1],  # Extract function name
                            "call_line": edge.metadata.get("line", 0),
                        }
                    )

        return results

    def analyze_complexity(self, threshold: int = 10) -> List[Dict[str, Any]]:
        """Analyze code complexity and identify hotspots."""
        results = []

        for node in self.graph.nodes.values():
            if (
                node.node_type in {NodeType.FUNCTION, NodeType.METHOD}
                and node.complexity >= threshold
            ):
                results.append(
                    {
                        "name": node.name,
                        "type": node.node_type.value,
                        "complexity": node.complexity,
                        "file": node.location.file_path,
                        "line": node.location.start_line,
                        "risk_level": "high" if node.complexity > 20 else "moderate",
                    }
                )

        return sorted(results, key=lambda x: x["complexity"], reverse=True)

    def get_dependency_graph(self) -> Dict[str, Any]:
        """Generate dependency graph data."""
        dependencies = defaultdict(set)

        for edge in self.graph.edges.values():
            if edge.edge_type == EdgeType.IMPORTS:
                source_node = self.graph.get_node(edge.source_id)
                if source_node and source_node.node_type == NodeType.FILE:
                    target = edge.target_id.replace("module:", "")
                    dependencies[source_node.name].add(target)

        return {
            "dependencies": {k: list(v) for k, v in dependencies.items()},
            "total_files": len(dependencies),
            "total_dependencies": sum(len(v) for v in dependencies.values()),
        }


# ============================================================================
# MCP Server
# ============================================================================


class CodeGraphMCPServer:  # pylint: disable=too-few-public-methods
    """MCP server for code graph intelligence."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.server = Server("code-graph-intelligence")
        self.analysis_engine = CodeAnalysisEngine(self.project_root)
        self._register_handlers()

    def _get_tool_definitions(self) -> List[Tool]:
        """Get all tool definitions for the MCP server."""
        return [
                    Tool(
                        name="analyze_codebase",
                        description=(
                            "Perform comprehensive codebase analysis with "
                            "metrics and structure overview"
                        ),
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "rebuild_graph": {
                                    "type": "boolean",
                                    "description": "Force rebuild of code graph",
                                    "default": False,
                                }
                            },
                        },
                    ),
                    Tool(
                        name="find_definition",
                        description="Find the definition of a symbol (function, class, variable)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Symbol name to find definition for",
                                }
                            },
                            "required": ["symbol"],
                        },
                    ),
                    Tool(
                        name="find_references",
                        description="Find all references to a symbol throughout the codebase",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Symbol name to find references for",
                                }
                            },
                            "required": ["symbol"],
                        },
                    ),
                    Tool(
                        name="find_callers",
                        description="Find all functions that call the specified function",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "function": {
                                    "type": "string",
                                    "description": "Function name to find callers for",
                                }
                            },
                            "required": ["function"],
                        },
                    ),
                    Tool(
                        name="find_callees",
                        description="Find all functions called by the specified function",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "function": {
                                    "type": "string",
                                    "description": "Function name to find callees for",
                                }
                            },
                            "required": ["function"],
                        },
                    ),
                    Tool(
                        name="complexity_analysis",
                        description="Analyze code complexity and refactoring opportunities",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "threshold": {
                                    "type": "integer",
                                    "description": "Minimum complexity threshold to report",
                                    "default": 10,
                                }
                            },
                        },
                    ),
                    Tool(
                        name="dependency_analysis",
                        description="Analyze module dependencies and import relationships",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                    Tool(
                        name="project_statistics",
                        description="Get comprehensive project statistics and health metrics",
                        inputSchema={"type": "object", "properties": {}},
                    ),
                ]

    async def _handle_list_tools(self) -> ListToolsResult:
        """Handle list_tools request."""
        return ListToolsResult(tools=self._get_tool_definitions())

    async def _handle_call_tool(self, request: CallToolRequest) -> CallToolResult:
        """Handle call_tool request with routing."""
        try:
            # Ensure graph is built
            if not self.analysis_engine.last_build_time:
                await self.analysis_engine.build_graph()

            # Route to appropriate handler
            handlers = {
                "analyze_codebase": self._analyze_codebase,
                "find_definition": self._find_definition,
                "find_references": self._find_references,
                "find_callers": self._find_callers,
                "find_callees": self._find_callees,
                "complexity_analysis": self._complexity_analysis,
                "dependency_analysis": self._dependency_analysis,
                "project_statistics": self._project_statistics,
            }

            handler = handlers.get(request.params.name)
            if handler:
                return await handler(request.params.arguments or {})

            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ Unknown tool: {request.params.name}")
                ]
            )

        except Exception as e:
            logger.error("Error in tool %s: %s", request.params.name, e, exc_info=True)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"❌ Error executing {request.params.name}: {str(e)}"
                    )
                ]
            )

    def _register_handlers(self):
        """Register MCP protocol handlers."""

        @self.server.list_tools()  # type: ignore[misc]
        async def list_tools() -> ListToolsResult:
            return await self._handle_list_tools()

        @self.server.call_tool()  # type: ignore[misc]
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            return await self._handle_call_tool(request)

        @self.server.list_resources()  # type: ignore[misc]
        async def list_resources() -> ListResourcesResult:
            """List available resources."""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="graph://project/structure",  # type: ignore[arg-type]
                        name="Project Graph Structure",
                        description="Complete project code graph with nodes and edges",
                    ),
                    Resource(
                        uri="graph://metrics/complexity",  # type: ignore[arg-type]
                        name="Complexity Metrics",
                        description="Detailed complexity analysis and metrics",
                    ),
                    Resource(
                        uri="graph://dependencies/map",  # type: ignore[arg-type]
                        name="Dependency Map",
                        description="Module dependency relationships",
                    ),
                ]
            )

        @self.server.read_resource()  # type: ignore[misc]
        async def read_resource(request: ReadResourceRequest) -> ReadResourceResult:
            """Handle resource requests."""
            try:
                # Ensure graph is built
                if not self.analysis_engine.last_build_time:
                    await self.analysis_engine.build_graph()

                if request.params.uri == "graph://project/structure":
                    stats = self.analysis_engine.get_project_stats()
                    content = json.dumps(stats, indent=2)
                elif request.params.uri == "graph://metrics/complexity":
                    complexity_data = self.analysis_engine.analyze_complexity(threshold=1)
                    content = json.dumps(complexity_data, indent=2)
                elif request.params.uri == "graph://dependencies/map":
                    deps = self.analysis_engine.get_dependency_graph()
                    content = json.dumps(deps, indent=2)
                else:
                    content = f"Unknown resource: {request.params.uri}"

                return ReadResourceResult(
                    contents=[TextContent(type="text", text=content)]  # type: ignore[arg-type]
                )

            except Exception as e:
                logger.error("Error reading resource %s: %s", request.params.uri, e)
                return ReadResourceResult(
                    contents=[
                        TextContent(  # type: ignore[arg-type]
                            type="text", text=f"❌ Error reading resource: {str(e)}"
                        )
                    ]
                )

    async def _analyze_codebase(self, args: Dict[str, Any]) -> CallToolResult:
        """Perform comprehensive codebase analysis."""
        rebuild_graph = args.get("rebuild_graph", False)

        if rebuild_graph:
            await self.analysis_engine.build_graph()

        stats = self.analysis_engine.get_project_stats()

        result = f"""# Comprehensive Codebase Analysis

## Project Overview
- **Root Directory**: `{stats['project_root']}`
- **Last Analysis**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats['last_build_time']))}

## Structure Metrics
- **Total Files**: {stats['files_analyzed']:,}
- **Classes**: {stats['nodes_by_type'].get('class', 0):,}
- **Functions**: {stats['nodes_by_type'].get('function', 0):,}
- **Methods**: {stats['nodes_by_type'].get('method', 0):,}
- **Total Nodes**: {stats['total_nodes']:,}
- **Total Relationships**: {stats['total_edges']:,}

## Code Quality Metrics
- **Average Complexity**: {stats['average_complexity']:.2f}
- **Maximum Complexity**: {stats['max_complexity']}
- **Import Statements**: {stats['edges_by_type'].get('imports', 0):,}
- **Function Calls**: {stats['edges_by_type'].get('calls', 0):,}

## Relationship Analysis
"""
        for edge_type, count in stats["edges_by_type"].items():
            result += f"- **{edge_type.title()}**: {count:,}\n"

        # Add complexity analysis
        complex_functions = self.analysis_engine.analyze_complexity(threshold=15)
        if complex_functions:
            result += f"\n## High Complexity Functions ({len(complex_functions)} found)\n"
            for func in complex_functions[:5]:  # Show top 5
                result += (
                    f"- **{func['name']}** ({func['type']}): "
                    f"Complexity {func['complexity']} - "
                    f"`{Path(func['file']).name}:{func['line']}`\n"
                )

        result += (
            f"\n✅ **Analysis Complete** - {stats['total_nodes']:,} nodes "
            f"analyzed across {stats['files_analyzed']} files"
        )

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _find_definition(self, args: Dict[str, Any]) -> CallToolResult:
        """Find symbol definition with detailed information."""
        symbol = args["symbol"]
        definitions = self.analysis_engine.find_symbol_definition(symbol)

        if not definitions:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ No definition found for symbol: `{symbol}`")
                ]
            )

        result = f"# Definition Analysis: `{symbol}`\n\n"

        for i, defn in enumerate(definitions, 1):
            result += f"## Definition {i}: {defn['type'].title()}\n"
            result += f"- **Location**: `{Path(defn['file']).name}:{defn['line']}`\n"
            result += f"- **Type**: {defn['type']}\n"
            result += f"- **Complexity**: {defn['complexity']}\n"

            if defn["docstring"]:
                doc_preview = defn["docstring"][:200]
                doc_suffix = "..." if len(defn["docstring"]) > 200 else ""
                result += f"- **Documentation**: {doc_preview}{doc_suffix}\n"

            result += f"- **Full Path**: `{defn['file']}`\n\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _find_references(self, args: Dict[str, Any]) -> CallToolResult:
        """Find all references to a symbol."""
        symbol = args["symbol"]
        references = self.analysis_engine.find_symbol_references(symbol)

        if not references:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ No references found for symbol: `{symbol}`")
                ]
            )

        result = f"# Reference Analysis: `{symbol}` ({len(references)} found)\n\n"

        # Group by file
        refs_by_file = defaultdict(list)
        for ref in references:
            refs_by_file[ref["file"]].append(ref)

        for file_path, file_refs in refs_by_file.items():
            result += f"## {Path(file_path).name}\n"
            for ref in file_refs:
                result += f"- Line {ref['line']}: {ref['reference_type']} in `{ref['context']}`\n"
            result += "\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _find_callers(self, args: Dict[str, Any]) -> CallToolResult:
        """Find all callers of a function."""
        function = args["function"]
        callers = self.analysis_engine.find_function_callers(function)

        if not callers:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ No callers found for function: `{function}`")
                ]
            )

        result = f"# Caller Analysis: `{function}` ({len(callers)} callers)\n\n"

        for caller in callers:
            result += f"- **{caller['caller']}** ({caller['caller_type']})\n"
            result += f"  - File: `{Path(caller['file']).name}:{caller['line']}`\n"
            result += f"  - Full Path: `{caller['file']}`\n\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _find_callees(self, args: Dict[str, Any]) -> CallToolResult:
        """Find all functions called by a function."""
        function = args["function"]
        callees = self.analysis_engine.find_function_callees(function)

        if not callees:
            return CallToolResult(
                content=[
                    TextContent(type="text", text=f"❌ No callees found for function: `{function}`")
                ]
            )

        result = f"# Callee Analysis: `{function}` calls {len(callees)} functions\n\n"

        for callee in callees:
            result += f"- **{callee['callee']}**"
            if callee["call_line"]:
                result += f" (line {callee['call_line']})"
            result += "\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _complexity_analysis(self, args: Dict[str, Any]) -> CallToolResult:
        """Analyze code complexity and provide refactoring recommendations."""
        threshold = args.get("threshold", 10)
        complex_functions = self.analysis_engine.analyze_complexity(threshold)

        if not complex_functions:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"✅ No functions found with complexity >= {threshold}"
                    )
                ]
            )

        result = f"# Complexity Analysis (Threshold: {threshold})\n\n"
        result += f"Found **{len(complex_functions)}** functions requiring attention:\n\n"

        for func in complex_functions:
            risk_emoji = "🔴" if func["risk_level"] == "high" else "🟡"
            result += f"{risk_emoji} **{func['name']}** ({func['type']})\n"
            result += f"- **Complexity**: {func['complexity']}\n"
            result += f"- **Risk Level**: {func['risk_level']}\n"
            result += f"- **Location**: `{Path(func['file']).name}:{func['line']}`\n"
            result += "- **Recommendation**: "

            if func["complexity"] > 20:
                result += "Critical - Break into smaller functions immediately\n"
            elif func["complexity"] > 15:
                result += "High priority - Consider refactoring\n"
            else:
                result += "Monitor - May benefit from simplification\n"

            result += "\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _dependency_analysis(
        self, _args: Dict[str, Any]
    ) -> CallToolResult:
        """Analyze module dependencies."""
        deps = self.analysis_engine.get_dependency_graph()

        result = "# Dependency Analysis\n\n"
        result += f"- **Total Files**: {deps['total_files']}\n"
        result += f"- **Total Dependencies**: {deps['total_dependencies']}\n\n"

        result += "## Import Relationships\n\n"

        for file_path, dependencies in deps["dependencies"].items():
            if dependencies:
                result += f"**{Path(file_path).name}** imports:\n"
                for dep in dependencies:
                    result += f"- `{dep}`\n"
                result += "\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def _project_statistics(
        self, _args: Dict[str, Any]
    ) -> CallToolResult:
        """Get comprehensive project statistics."""
        stats = self.analysis_engine.get_project_stats()

        result = "# Project Statistics\n\n"
        result += "## Overview\n"
        result += f"- **Project Root**: `{stats['project_root']}`\n"
        result += f"- **Files Analyzed**: {stats['files_analyzed']}\n"
        result += f"- **Total Code Elements**: {stats['total_nodes']:,}\n"
        result += f"- **Relationships**: {stats['total_edges']:,}\n"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats["last_build_time"]))
        result += f"- **Last Analysis**: {timestamp}\n\n"

        result += "## Code Structure\n"
        for node_type, count in stats["nodes_by_type"].items():
            result += f"- **{node_type.title()}**: {count:,}\n"

        result += "\n## Quality Metrics\n"
        result += f"- **Average Complexity**: {stats['average_complexity']:.2f}\n"
        result += f"- **Maximum Complexity**: {stats['max_complexity']}\n"

        # Calculate health score
        files = stats["files_analyzed"]
        functions = stats["nodes_by_type"].get("function", 0) + stats["nodes_by_type"].get(
            "method", 0
        )
        classes = stats["nodes_by_type"].get("class", 0)

        if files > 0:
            functions_per_file = functions / files
            classes_per_file = classes / files
            health_score = min(10, (functions_per_file + classes_per_file) * 2)
            result += f"- **Health Score**: {health_score:.1f}/10\n"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    async def run(self):
        """Run the MCP server."""
        logger.info("🚀 Starting Code Graph Intelligence MCP Server")
        logger.info("📁 Project Root: %s", self.project_root)
        logger.info("🔧 Building initial code graph...")

        # Build initial graph
        await self.analysis_engine.build_graph()

        logger.info("✅ Server ready with %d nodes", len(self.analysis_engine.graph.nodes))

        # Run server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, initialization_options={}  # type: ignore[arg-type]
            )


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """Main entry point for the enterprise MCP server."""
    import argparse  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser(description="Code Graph Intelligence MCP Server")
    parser.add_argument("--project-root", type=str, help="Project root directory to analyze")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create and run server
    project_root = Path(args.project_root) if args.project_root else Path.cwd()
    server = CodeGraphMCPServer(project_root)

    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
