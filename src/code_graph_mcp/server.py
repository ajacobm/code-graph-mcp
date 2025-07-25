#!/usr/bin/env python3
"""
Code Graph Intelligence MCP Server

A Model Context Protocol server providing comprehensive
code analysis, navigation, and quality assessment capabilities.
"""

import ast
import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import the existing classes from the original server
# We'll keep all the existing analysis logic and just change the server part

# ============================================================================
# Copy all the existing classes here (CacheManager, NodeType, etc.)
# ============================================================================


class CacheManager:
    """Centralized cache management with statistics and invalidation."""

    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0
        self.file_mtimes: Dict[str, float] = {}

    def get(self, key: str, file_path: Optional[Path] = None) -> Optional[Any]:
        """Get cached value with optional file modification time check."""
        if file_path and self._is_file_modified(file_path):
            self.invalidate_file(file_path)
            return None

        if key in self.cache:
            self.hits += 1
            return self.cache[key]

        self.misses += 1
        return None

    def set(self, key: str, value: Any, file_path: Optional[Path] = None) -> None:
        """Set cached value with optional file tracking."""
        self.cache[key] = value
        if file_path and file_path.exists():
            self.file_mtimes[str(file_path)] = file_path.stat().st_mtime

    def _is_file_modified(self, file_path: Path) -> bool:
        """Check if file has been modified since last cache."""
        if not file_path.exists():
            return True

        path_str = str(file_path)
        if path_str not in self.file_mtimes:
            return True

        return file_path.stat().st_mtime > self.file_mtimes[path_str]

    def invalidate_file(self, file_path: Path) -> None:
        """Invalidate all cache entries related to a file."""
        path_str = str(file_path)
        keys_to_remove = [k for k in self.cache.keys() if path_str in k]
        for key in keys_to_remove:
            del self.cache[key]
        self.file_mtimes.pop(path_str, None)

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Get cache performance statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "total_entries": len(self.cache),
        }


class NodeType(Enum):
    """Types of nodes in the code graph."""

    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"
    PARAMETER = "parameter"
    IMPORT = "import"


class EdgeType(Enum):
    """Types of edges in the code graph."""

    CONTAINS = "contains"
    INHERITS = "inherits"
    CALLS = "calls"
    IMPORTS = "imports"
    REFERENCES = "references"


@dataclass
class Location:
    """Code location information."""

    file_path: str
    start_line: int
    end_line: int
    start_column: int = 0
    end_column: int = 0


@dataclass
class Node:
    """Node in the code graph."""

    id: str
    name: str
    node_type: NodeType
    location: Location
    complexity: int = 0
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    """Edge in the code graph."""

    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeGraph:
    """In-memory representation of code structure and relationships."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self._edges_from: Dict[str, Set[str]] = defaultdict(set)
        self._edges_to: Dict[str, Set[str]] = defaultdict(set)

    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges[edge.id] = edge
        self._edges_from[edge.source_id].add(edge.id)
        self._edges_to[edge.target_id].add(edge.id)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edges_from(self, node_id: str) -> List[Edge]:
        """Get all edges originating from a node."""
        edge_ids = self._edges_from.get(node_id, set())
        return [self.edges[edge_id] for edge_id in edge_ids if edge_id in self.edges]

    def get_edges_to(self, node_id: str) -> List[Edge]:
        """Get all edges pointing to a node."""
        edge_ids = self._edges_to.get(node_id, set())
        return [self.edges[edge_id] for edge_id in edge_ids if edge_id in self.edges]


# Global cache manager
cache_manager = CacheManager()

# ============================================================================
# Analysis Engine (simplified version)
# ============================================================================


class CodeAnalysisEngine:
    """Core analysis engine for code graph intelligence."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.graph = CodeGraph()
        self.last_build_time: Optional[float] = None

    @lru_cache(maxsize=256)
    def _parse_python_file(self, file_path: str) -> Optional[ast.AST]:
        """Parse Python file with caching."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return ast.parse(f.read(), filename=file_path)
        except Exception as e:
            logger.debug("Failed to parse %s: %s", file_path, e)
            return None

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, (ast.ExceptHandler, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        for root, dirs, files in os.walk(self.project_root):
            # Skip common build/cache directories
            dirs[:] = [d for d in dirs if not d.startswith((".", "__pycache__"))]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    async def build_graph(self) -> None:
        """Build the code graph from project files."""
        logger.info("Building code graph for %s", self.project_root)
        start_time = time.time()

        # Reset graph
        self.graph = CodeGraph()

        # Find Python files
        python_files = self._find_python_files()
        logger.info("Found %d Python files to analyze", len(python_files))

        # Process each file
        for file_path in python_files:
            await self._process_python_file(file_path)

        self.last_build_time = time.time()
        elapsed = self.last_build_time - start_time

        logger.info(
            "Graph build complete: %d nodes, %d edges in %.2fs",
            len(self.graph.nodes),
            len(self.graph.edges),
            elapsed,
        )

    async def _process_python_file(self, file_path: Path) -> None:
        """Process a single Python file."""
        try:
            tree = self._parse_python_file(str(file_path))
            if not tree:
                return

            # Create file node
            file_id = f"file:{file_path}"
            file_node = Node(
                id=file_id,
                name=file_path.name,
                node_type=NodeType.FILE,
                location=Location(str(file_path), 1, len(open(file_path).readlines())),
            )
            self.graph.add_node(file_node)

            # Process AST nodes
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    await self._process_function(node, file_path, file_id)
                elif isinstance(node, ast.ClassDef):
                    await self._process_class(node, file_path, file_id)

        except Exception as e:
            logger.debug("Error processing %s: %s", file_path, e)

    async def _process_function(self, node: ast.FunctionDef, file_path: Path, file_id: str) -> None:
        """Process a function definition."""
        func_id = f"function:{file_path}:{node.name}:{node.lineno}"

        # Get docstring
        docstring = ast.get_docstring(node)

        func_node = Node(
            id=func_id,
            name=node.name,
            node_type=NodeType.FUNCTION,
            location=Location(str(file_path), node.lineno, node.end_lineno or node.lineno),
            complexity=self._calculate_complexity(node),
            docstring=docstring,
        )

        self.graph.add_node(func_node)

        # Add contains edge from file
        edge = Edge(
            id=f"contains:{file_id}:{func_id}",
            source_id=file_id,
            target_id=func_id,
            edge_type=EdgeType.CONTAINS,
        )
        self.graph.add_edge(edge)

    async def _process_class(self, node: ast.ClassDef, file_path: Path, file_id: str) -> None:
        """Process a class definition."""
        class_id = f"class:{file_path}:{node.name}:{node.lineno}"

        docstring = ast.get_docstring(node)

        class_node = Node(
            id=class_id,
            name=node.name,
            node_type=NodeType.CLASS,
            location=Location(str(file_path), node.lineno, node.end_lineno or node.lineno),
            docstring=docstring,
        )

        self.graph.add_node(class_node)

        # Add contains edge from file
        edge = Edge(
            id=f"contains:{file_id}:{class_id}",
            source_id=file_id,
            target_id=class_id,
            edge_type=EdgeType.CONTAINS,
        )
        self.graph.add_edge(edge)

        # Process methods
        for method in node.body:
            if isinstance(method, ast.FunctionDef):
                await self._process_method(method, file_path, class_id)

    async def _process_method(self, node: ast.FunctionDef, file_path: Path, class_id: str) -> None:
        """Process a method definition."""
        method_id = f"method:{file_path}:{node.name}:{node.lineno}"

        docstring = ast.get_docstring(node)

        method_node = Node(
            id=method_id,
            name=node.name,
            node_type=NodeType.METHOD,
            location=Location(str(file_path), node.lineno, node.end_lineno or node.lineno),
            complexity=self._calculate_complexity(node),
            docstring=docstring,
        )

        self.graph.add_node(method_node)

        # Add contains edge from class
        edge = Edge(
            id=f"contains:{class_id}:{method_id}",
            source_id=class_id,
            target_id=method_id,
            edge_type=EdgeType.CONTAINS,
        )
        self.graph.add_edge(edge)

    def get_project_stats(self) -> Dict[str, Any]:
        """Get comprehensive project statistics."""
        nodes_by_type = defaultdict(int)
        edges_by_type = defaultdict(int)
        complexities = []

        for node in self.graph.nodes.values():
            nodes_by_type[node.node_type.value] += 1
            if node.complexity > 0:
                complexities.append(node.complexity)

        for edge in self.graph.edges.values():
            edges_by_type[edge.edge_type.value] += 1

        return {
            "project_root": str(self.project_root),
            "last_build_time": self.last_build_time or 0,
            "files_analyzed": nodes_by_type.get("file", 0),
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "nodes_by_type": dict(nodes_by_type),
            "edges_by_type": dict(edges_by_type),
            "average_complexity": sum(complexities) / len(complexities) if complexities else 0,
            "max_complexity": max(complexities) if complexities else 0,
        }

    def find_symbol_definition(self, symbol: str) -> List[Dict[str, Any]]:
        """Find the definition of a symbol."""
        results = []

        for node in self.graph.nodes.values():
            if node.name == symbol and node.node_type in {
                NodeType.FUNCTION,
                NodeType.CLASS,
                NodeType.METHOD,
            }:
                results.append(
                    {
                        "name": node.name,
                        "type": node.node_type.value,
                        "file": node.location.file_path,
                        "line": node.location.start_line,
                        "complexity": node.complexity,
                        "docstring": node.docstring or "",
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

    def find_symbol_references(self, symbol: str) -> List[Dict[str, Any]]:
        """Find all references to a symbol throughout the codebase."""
        results = []

        for edge in self.graph.edges.values():
            if edge.edge_type == EdgeType.REFERENCES and symbol in edge.target_id:
                source_node = self.graph.get_node(edge.source_id)
                if source_node:
                    results.append(
                        {
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
# MCP Server Implementation
# ============================================================================

# Global analysis engine
analysis_engine: Optional[CodeAnalysisEngine] = None


async def ensure_analysis_engine_ready(project_root: Path) -> CodeAnalysisEngine:
    """Ensure the analysis engine is initialized and ready."""
    global analysis_engine
    if analysis_engine is None:
        analysis_engine = CodeAnalysisEngine(project_root)
        await analysis_engine.build_graph()
    elif not analysis_engine.last_build_time:
        await analysis_engine.build_graph()
    return analysis_engine


async def handle_analyze_codebase(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle analyze_codebase tool."""
    rebuild_graph = arguments.get("rebuild_graph", False)
    if rebuild_graph:
        await engine.build_graph()

    stats = engine.get_project_stats()
    result = f"""# Comprehensive Codebase Analysis

## Project Overview
- **Root Directory**: `{stats["project_root"]}`
- **Last Analysis**: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats["last_build_time"]))}

## Structure Metrics
- **Total Files**: {stats["files_analyzed"]:,}
- **Classes**: {stats["nodes_by_type"].get("class", 0):,}
- **Functions**: {stats["nodes_by_type"].get("function", 0):,}
- **Methods**: {stats["nodes_by_type"].get("method", 0):,}
- **Total Nodes**: {stats["total_nodes"]:,}
- **Total Relationships**: {stats["total_edges"]:,}

## Code Quality Metrics
- **Average Complexity**: {stats["average_complexity"]:.2f}
- **Maximum Complexity**: {stats["max_complexity"]}

✅ **Analysis Complete** - {stats["total_nodes"]:,} nodes analyzed across {stats["files_analyzed"]} files"""

    return [types.TextContent(type="text", text=result)]


async def handle_find_definition(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle find_definition tool."""
    symbol = arguments["symbol"]
    definitions = engine.find_symbol_definition(symbol)

    if not definitions:
        result = f"❌ No definition found for symbol: `{symbol}`"
    else:
        result = f"# Definition Analysis: `{symbol}`\n\n"
        for i, defn in enumerate(definitions, 1):
            result += f"## Definition {i}: {defn['type'].title()}\n"
            result += f"- **Location**: `{Path(defn['file']).name}:{defn['line']}`\n"
            result += f"- **Type**: {defn['type']}\n"
            result += f"- **Complexity**: {defn['complexity']}\n"
            if defn["docstring"]:
                result += f"- **Documentation**: {defn['docstring'][:200]}...\n"
            result += f"- **Full Path**: `{defn['file']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_complexity_analysis(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle complexity_analysis tool."""
    threshold = arguments.get("threshold", 10)
    complex_functions = engine.analyze_complexity(threshold)

    if not complex_functions:
        result = f"✅ No functions found with complexity >= {threshold}"
    else:
        result = f"# Complexity Analysis (Threshold: {threshold})\n\n"
        result += f"Found **{len(complex_functions)}** functions requiring attention:\n\n"

        for func in complex_functions:
            risk_emoji = "🔴" if func["risk_level"] == "high" else "🟡"
            result += f"{risk_emoji} **{func['name']}** ({func['type']})\n"
            result += f"- **Complexity**: {func['complexity']}\n"
            result += f"- **Risk Level**: {func['risk_level']}\n"
            result += f"- **Location**: `{Path(func['file']).name}:{func['line']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_find_references(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle find_references tool."""
    symbol = arguments["symbol"]
    references = engine.find_symbol_references(symbol)

    if not references:
        result = f"❌ No references found for symbol: `{symbol}`"
    else:
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

    return [types.TextContent(type="text", text=result)]


async def handle_find_callers(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle find_callers tool."""
    function = arguments["function"]
    callers = engine.find_function_callers(function)

    if not callers:
        result = f"❌ No callers found for function: `{function}`"
    else:
        result = f"# Caller Analysis: `{function}` ({len(callers)} callers)\n\n"

        for caller in callers:
            result += f"- **{caller['caller']}** ({caller['caller_type']})\n"
            result += f"  - File: `{Path(caller['file']).name}:{caller['line']}`\n"
            result += f"  - Full Path: `{caller['file']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_find_callees(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle find_callees tool."""
    function = arguments["function"]
    callees = engine.find_function_callees(function)

    if not callees:
        result = f"❌ No callees found for function: `{function}`"
    else:
        result = f"# Callee Analysis: `{function}` calls {len(callees)} functions\n\n"

        for callee in callees:
            result += f"- **{callee['callee']}**"
            if callee["call_line"]:
                result += f" (line {callee['call_line']})"
            result += "\n"

    return [types.TextContent(type="text", text=result)]


async def handle_dependency_analysis(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle dependency_analysis tool."""
    deps = engine.get_dependency_graph()

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

    return [types.TextContent(type="text", text=result)]


async def handle_project_statistics(engine: CodeAnalysisEngine, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle project_statistics tool."""
    stats = engine.get_project_stats()

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
    functions = stats["nodes_by_type"].get("function", 0) + stats["nodes_by_type"].get("method", 0)
    classes = stats["nodes_by_type"].get("class", 0)

    if files > 0:
        functions_per_file = functions / files
        classes_per_file = classes / files
        health_score = min(10, (functions_per_file + classes_per_file) * 2)
        result += f"- **Health Score**: {health_score:.1f}/10\n"

    return [types.TextContent(type="text", text=result)]


@click.command()
@click.option("--project-root", type=str, help="Project root directory to analyze")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(project_root: Optional[str], verbose: bool) -> int:
    """Main entry point for the MCP server."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create server
    app = Server("code-graph-intelligence")
    root_path = Path(project_root) if project_root else Path.cwd()

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="analyze_codebase",
                description="Perform comprehensive codebase analysis with metrics and structure overview",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "rebuild_graph": {
                            "type": "boolean",
                            "description": "Force rebuild of code graph",
                        }
                    },
                },
            ),
            types.Tool(
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
            types.Tool(
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
            types.Tool(
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
            types.Tool(
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
            types.Tool(
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
            types.Tool(
                name="dependency_analysis",
                description="Analyze module dependencies and import relationships",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="project_statistics",
                description="Get comprehensive project statistics and health metrics",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle tool calls."""
        try:
            engine = await ensure_analysis_engine_ready(root_path)

            handlers = {
                "analyze_codebase": handle_analyze_codebase,
                "find_definition": handle_find_definition,
                "find_references": handle_find_references,
                "find_callers": handle_find_callers,
                "find_callees": handle_find_callees,
                "complexity_analysis": handle_complexity_analysis,
                "dependency_analysis": handle_dependency_analysis,
                "project_statistics": handle_project_statistics,
            }

            handler = handlers.get(name)
            if handler:
                return await handler(engine, arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.exception("Error in tool %s", name)
            return [types.TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]

    # Run server
    logger.info("🚀 Starting Code Graph Intelligence MCP Server")
    logger.info("📁 Project Root: %s", root_path)

    async def arun():
        async with stdio_server() as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    anyio.run(arun)
    return 0


if __name__ == "__main__":
    main()

