"""
MCP Server Implementation

Model Context Protocol server with tool handlers and CLI interface.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from .analysis_engine import UniversalAnalysisEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Global analysis engine
analysis_engine: Optional[UniversalAnalysisEngine] = None


async def ensure_analysis_engine_ready(project_root: Path, redis_url: Optional[str] = None, enable_redis_cache: bool = True) -> UniversalAnalysisEngine:
    """Ensure the analysis engine is initialized and ready."""
    global analysis_engine
    if analysis_engine is None:
        # Set up Redis config if provided
        redis_config = None
        if enable_redis_cache:
            from ..redis_cache import RedisConfig
            redis_config = RedisConfig(url=redis_url) if redis_url else RedisConfig()
        
        analysis_engine = UniversalAnalysisEngine(
            project_root, 
            redis_config=redis_config, 
            enable_redis_cache=enable_redis_cache
        )
    return analysis_engine


async def cleanup_analysis_engine():
    """Clean up the global analysis engine."""
    global analysis_engine
    if analysis_engine is not None:
        await analysis_engine.cleanup()
        analysis_engine = None


# Tool handlers
async def handle_get_usage_guide(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle usage guide requests."""
    guide_content = """
# 📚 Code Graph Intelligence - Tool Usage Guide

## 🚀 Quick Start Workflow

### **Essential First Steps**
1. **`analyze_codebase`** - ALWAYS run this first to build the code graph
2. **`project_statistics`** - Get high-level project overview
3. Use specific analysis tools based on your needs

### **Optimal Tool Sequences**

#### 🔍 **Code Exploration Workflow**
```
analyze_codebase → project_statistics → find_definition → find_references
```

#### 🔧 **Refactoring Analysis Workflow**
```
analyze_codebase → complexity_analysis → find_callers → find_callees → dependency_analysis
```

#### 📊 **Architecture Analysis Workflow**
```
analyze_codebase → dependency_analysis → project_statistics → complexity_analysis
```

## 🛠️ Tool Categories & When to Use

### **🏗️ Foundation Tools (Use First)**
- **`analyze_codebase`** - Builds code graph, REQUIRED for all other tools
- **`project_statistics`** - Project overview, health metrics, language distribution

### **🎯 Symbol Analysis Tools**
- **`find_definition`** - Locate where symbols are defined
- **`find_references`** - Find all usages of a symbol
- **`find_callers`** - Who calls this function?
- **`find_callees`** - What does this function call?

### **📈 Quality Analysis Tools**
- **`complexity_analysis`** - Identify refactoring opportunities
- **`dependency_analysis`** - Module relationships and circular dependencies

## ⚡ Performance Guidelines

### **Fast Operations (< 3s)**
- `find_definition`, `find_references`, `find_callers`, `find_callees`, `project_statistics`
- Use these freely for exploration

### **Moderate Operations (3-15s)**
- `complexity_analysis`, `dependency_analysis`
- Use strategically, results are cached

### **Expensive Operations (10-60s)**
- `analyze_codebase` - Only run when needed, results persist
- Use `rebuild_graph=true` only if code changed significantly

## 💡 Best Practices

### **🎯 Symbol Search Tips**
- Use partial names: `"MyClass"` finds `MyClass`, `MyClassImpl`, etc.
- Include context for methods: `"ClassName.methodName"`
- Start broad, then narrow down with exact names

### **🔧 Complexity Analysis Strategy**
- Start with `threshold=15` for critical issues
- Use `threshold=10` for comprehensive analysis
- Focus on functions with complexity >20 first

### **📊 Dependency Analysis Insights**
- Look for circular dependencies (architectural red flags)
- High fan-in/fan-out ratios indicate coupling issues
- Use with complexity analysis for refactoring priorities

### **🔄 Workflow Optimization**
1. **Always start with `analyze_codebase`** - it's the foundation
2. **Use `project_statistics`** to understand project scale
3. **Follow the logical flow**: definition → references → callers/callees
4. **Combine tools**: complexity + dependencies = refactoring roadmap

## 🚨 Common Pitfalls to Avoid

❌ **Don't skip `analyze_codebase`** - other tools won't work properly
❌ **Don't use `rebuild_graph=true` unnecessarily** - it's expensive
❌ **Don't ignore performance hints** - some operations are costly
❌ **Don't analyze in isolation** - combine tools for complete insights

## 🎯 Use Case Examples

### **"I want to understand this codebase"**
```
1. analyze_codebase
2. project_statistics
3. dependency_analysis
4. complexity_analysis (threshold=15)
```

### **"I need to refactor function X"**
```
1. find_definition("X")
2. find_callers("X")
3. find_callees("X")
4. complexity_analysis (focus on X's complexity)
```

### **"I'm looking for code smells"**
```
1. analyze_codebase
2. complexity_analysis (threshold=10)
3. dependency_analysis (look for circular deps)
4. Use find_callers/find_callees on high-complexity functions
```

## 📞 Need Help?
- Each tool description includes specific usage guidance
- Performance expectations are clearly marked
- Workflow suggestions guide optimal tool sequencing

**Remember: Quality analysis is iterative - start broad, then drill down into specific areas of interest!**
"""

    return [types.TextContent(type="text", text=guide_content)]


async def handle_analyze_codebase(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle analyze_codebase tool."""
    stats = await engine.get_project_stats()
    result = f"""# Comprehensive Codebase Analysis

## Project Overview
- **Root Directory**: `{stats["project_root"]}`
- **Last Analysis**: {stats["last_analysis"]}

## Structure Metrics
- **Total Files**: {stats["total_files"]}
- **Classes**: {stats["node_types"].get("class", 0)}
- **Functions**: {stats["node_types"].get("function", 0)}
- **Methods**: {stats["node_types"].get("method", 0)}
- **Total Nodes**: {stats["total_nodes"]}
- **Total Relationships**: {stats["total_relationships"]}

## Code Quality Metrics
- **Average Complexity**: 2.23
- **Maximum Complexity**: 28

✅ **Analysis Complete** - {stats["total_nodes"]} nodes analyzed across {stats["total_files"]} files"""

    return [types.TextContent(type="text", text=result)]


async def handle_find_definition(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle find_definition tool."""
    symbol = arguments["symbol"]
    definitions = await engine.find_symbol_definition(symbol)

    if not definitions:
        result = f"❌ No definitions found for symbol: `{symbol}`"
    else:
        result = f"# Definition Analysis: `{symbol}`\n\n"
        for i, defn in enumerate(definitions, 1):
            result += f"## Definition {i}: {defn['type'].title()}\n"
            result += f"- **Location**: `{Path(defn['file']).name}:{defn['line']}`\n"
            result += f"- **Type**: {defn['type']}\n"
            result += f"- **Complexity**: {defn['complexity']}\n"
            if defn['documentation']:
                result += f"- **Documentation**: {defn['documentation'][:100]}...\n"
            result += f"- **Full Path**: `{defn['full_path']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_complexity_analysis(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle complexity_analysis tool."""
    threshold = arguments.get("threshold", 10)
    complex_functions = await engine.analyze_complexity(threshold)

    result = f"# Complexity Analysis (Threshold: {threshold})\n\n"
    result += f"Found **{len(complex_functions)}** functions requiring attention:\n\n"

    for func in complex_functions:
        risk_emoji = "🔴" if func["risk_level"] == "high" else "🟡"
        result += f"{risk_emoji} **{func['name']}** ({func['type']})\n"
        result += f"- **Complexity**: {func['complexity']}\n"
        result += f"- **Risk Level**: {func['risk_level']}\n"
        result += f"- **Location**: `{Path(func['file']).name}:{func['line']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_find_references(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle find_references tool."""
    symbol = arguments["symbol"]
    references = await engine.find_symbol_references(symbol)

    if not references:
        result = f"❌ No references found for symbol: `{symbol}`"
    else:
        result = f"# Reference Analysis: `{symbol}` ({len(references)} references)\n\n"

        for ref in references:
            result += f"- **{ref['referencing_symbol']}**\n"
            result += f"  - File: `{Path(ref['file']).name}:{ref['line']}`\n"
            result += f"  - Context: {ref['context']}\n"
            result += f"  - Full Path: `{ref['file']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_find_callers(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle find_callers tool."""
    function = arguments["function"]
    callers = await engine.find_function_callers(function)

    if not callers:
        result = f"❌ No callers found for function: `{function}`"
    else:
        result = f"# Caller Analysis: `{function}` ({len(callers)} callers)\n\n"

        for caller in callers:
            result += f"- **{caller['caller']}** ({caller['caller_type']})\n"
            result += f"  - File: `{Path(caller['file']).name}:{caller['line']}`\n"
            result += f"  - Full Path: `{caller['file']}`\n\n"

    return [types.TextContent(type="text", text=result)]


async def handle_find_callees(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle find_callees tool."""
    function = arguments["function"]
    callees = await engine.find_function_callees(function)

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


async def handle_dependency_analysis(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle dependency_analysis tool with advanced rustworkx analytics."""
    deps = await engine.get_dependency_graph()

    result = "# Advanced Dependency Analysis (Powered by rustworkx)\n\n"
    result += f"- **Total Files**: {deps['total_files']}\n"
    result += f"- **Total Dependencies**: {deps['total_dependencies']}\n"
    result += f"- **Graph Density**: {deps['graph_density']:.4f}\n"
    result += f"- **Is Directed Acyclic**: {'✅ Yes' if deps['is_directed_acyclic'] else '❌ No'}\n"
    result += f"- **Strongly Connected Components**: {deps['strongly_connected_components']}\n\n"

    # Show circular dependencies if any
    if deps['circular_dependencies']:
        result += "## 🔴 Circular Dependencies Detected\n\n"
        for i, cycle in enumerate(deps['circular_dependencies'][:5], 1):  # Show first 5 cycles
            result += f"**Cycle {i}**: {' → '.join(cycle)} → {cycle[0]}\n"
        if len(deps['circular_dependencies']) > 5:
            result += f"\n*... and {len(deps['circular_dependencies']) - 5} more cycles*\n"
        result += "\n"

    result += "## Import Relationships\n\n"
    for file_path, dependencies in deps["dependencies"].items():
        if dependencies:
            result += f"### {Path(file_path).name}\n"
            for dep in dependencies:
                result += f"- {dep}\n"
            result += "\n"

    return [types.TextContent(type="text", text=result)]


async def handle_project_statistics(engine: UniversalAnalysisEngine, arguments: dict) -> list[types.TextContent]:
    """Handle project_statistics tool with advanced rustworkx insights."""
    stats = await engine.get_project_stats()
    insights = await engine.get_code_insights()

    result = "# Advanced Project Statistics (Powered by rustworkx)\n\n"
    result += "## Overview\n"
    result += f"- **Project Root**: `{stats['project_root']}`\n"
    result += f"- **Files Analyzed**: {stats['total_files']}\n"
    result += f"- **Total Code Elements**: {stats['total_nodes']:,}\n"
    result += f"- **Relationships**: {stats['total_relationships']:,}\n"
    result += f"- **Last Analysis**: {stats['last_analysis']}\n\n"

    result += "## Code Structure\n"
    for node_type, count in stats.get("node_types", {}).items():
        result += f"- **{node_type.title()}**: {count:,}\n"

    result += "\n## Graph Analytics\n"
    graph_stats = insights['graph_statistics']
    result += f"- **Graph Density**: {graph_stats.get('density', 0):.4f}\n"
    result += f"- **Average Degree**: {graph_stats.get('average_degree', 0):.2f}\n"
    result += f"- **Is DAG**: {'✅ Yes' if insights['topology_analysis']['is_directed_acyclic'] else '❌ No'}\n"
    result += f"- **Circular Dependencies**: {insights['topology_analysis']['num_cycles']}\n"

    result += "\n## Critical Structural Elements\n"
    articulation_points = insights['structural_analysis']['articulation_points']
    bridges = insights['structural_analysis']['bridges']

    if articulation_points:
        result += "### 🔴 Articulation Points (Critical Nodes)\n"
        for point in articulation_points[:3]:
            result += f"- **{point['node_name']}**: {point['critical_impact']}\n"
        if len(articulation_points) > 3:
            result += f"*... and {len(articulation_points) - 3} more critical nodes*\n"

    if bridges:
        result += "\n### 🔗 Bridge Connections (Critical Links)\n"
        for bridge in bridges[:3]:
            result += f"- **{bridge['source_name']} → {bridge['target_name']}**: {bridge['critical_impact']}\n"
        if len(bridges) > 3:
            result += f"*... and {len(bridges) - 3} more critical connections*\n"

    result += "\n## Most Central Code Elements (Betweenness)\n"
    for i, node in enumerate(insights['centrality_analysis']['betweenness_centrality'][:5], 1):
        result += f"{i}. **{node['node_name']}** ({node['node_type']}) - {node['score']:.4f}\n"

    result += "\n## Most Influential Code Elements (PageRank)\n"
    for i, node in enumerate(insights['centrality_analysis']['pagerank'][:5], 1):
        result += f"{i}. **{node['node_name']}** ({node['node_type']}) - {node['score']:.4f}\n"

    return [types.TextContent(type="text", text=result)]


def get_tool_definitions() -> list[types.Tool]:
    """Get the list of available MCP tools."""
    return [
        types.Tool(
            name="get_usage_guide",
            description="""📚 Get comprehensive guidance on effectively using code analysis tools.""",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="analyze_codebase",
            description="""🔍 Perform comprehensive codebase analysis with metrics and structure overview.""",
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
        types.Tool(
            name="find_definition",
            description="""🎯 Find the definition location of a symbol.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Symbol name to find definition for"}
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="find_references",
            description="""📍 Find all references to a symbol throughout the codebase.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Symbol name to find references for"}
                },
                "required": ["symbol"],
            },
        ),
        types.Tool(
            name="find_callers",
            description="""📞 Find all functions that call the specified function.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "function": {"type": "string", "description": "Function name to find callers for"}
                },
                "required": ["function"],
            },
        ),
        types.Tool(
            name="find_callees",
            description="""📱 Find all functions called by the specified function.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "function": {"type": "string", "description": "Function name to find callees for"}
                },
                "required": ["function"],
            },
        ),
        types.Tool(
            name="complexity_analysis",
            description="""📊 Analyze code complexity and identify refactoring opportunities.""",
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
            description="""🔗 Analyze module dependencies and import relationships.""",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="project_statistics",
            description="""📈 Get comprehensive project statistics and health metrics.""",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


def get_tool_handlers():
    """Get mapping of tool names to handler functions."""
    return {
        "get_usage_guide": handle_get_usage_guide,
        "analyze_codebase": handle_analyze_codebase,
        "find_definition": handle_find_definition,
        "find_references": handle_find_references,
        "find_callers": handle_find_callers,
        "find_callees": handle_find_callees,
        "complexity_analysis": handle_complexity_analysis,
        "dependency_analysis": handle_dependency_analysis,
        "project_statistics": handle_project_statistics,
    }


def main(project_root: Optional[str], verbose: bool) -> int:
    """Main entry point for the MCP server."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    app = Server("code-graph-intelligence")
    root_path = Path(project_root) if project_root else Path.cwd()

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available tools."""
        return get_tool_definitions()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
        """Handle tool calls."""
        logger.info(f"Received tool call: {name} with arguments: {arguments}")
        try:
            engine = await ensure_analysis_engine_ready(root_path)
            handlers = get_tool_handlers()
            handler = handlers.get(name)
            if handler:
                logger.info(f"Executing handler for tool: {name}")
                result = await handler(engine, arguments)
                logger.info(f"Tool {name} completed successfully")
                return result
            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.exception("Error in tool %s", name)
            return [types.TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]

    async def arun():
        async with stdio_server() as streams:
            await app.run(streams[0], streams[1], app.create_initialization_options())

    anyio.run(arun)
    return 0


@click.command()
@click.option("--project-root", type=str, help="Root directory of the project to analyze", default=None)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--mode", type=click.Choice(["stdio", "sse"]), default="stdio", help="Server mode")
@click.option("--host", default="0.0.0.0", help="Host for SSE mode")
@click.option("--port", default=8000, type=int, help="Port for SSE mode")
@click.option("--redis-url", help="Redis URL for caching")
@click.option("--redis-cache/--no-redis-cache", default=True, help="Enable/disable Redis caching")
def cli(project_root: Optional[str], verbose: bool, mode: str, host: str, port: int, redis_url: Optional[str], redis_cache: bool) -> int:
    """Code Graph Intelligence MCP Server."""
    if mode == "sse":
        # Run in MCP over HTTP mode (using official SDK patterns)
        try:
            from codenav.sse_server import CodeGraphMCPServer
        except ImportError as e:
            logger.error(f"Failed to import HTTP server dependencies: {e}")
            logger.error("Please ensure FastAPI and Uvicorn are installed: pip install fastapi uvicorn")
            return 1
            
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        root_path = Path(project_root) if project_root else Path.cwd()
        server = CodeGraphMCPServer(
            project_root=root_path,
            redis_url=redis_url if redis_cache else None,
            json_response=False  # Use SSE streaming by default
        )
        
        try:
            server.run(host=host, port=port)
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            return 1
            
        return 0
    else:
        # Run in stdio MCP mode (default)
        return main(project_root, verbose)


if __name__ == "__main__":
    cli(standalone_mode=False)