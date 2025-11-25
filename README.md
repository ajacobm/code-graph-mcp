# CodeNavigator (codenav)

Model Context Protocol server providing comprehensive code analysis, navigation, and quality assessment capabilities **across 25+ programming languages**.

## Features

🎯 **Enhanced Tool Guidance & AI Optimization** ⭐ *NEW in v1.2.0*
- **Comprehensive Usage Guide** - Built-in `get_usage_guide` tool with workflows, best practices, and examples
- **Rich Tool Descriptions** - Visual hierarchy with 🎯 PURPOSE, 🔧 USAGE, ⚡ PERFORMANCE, 🔄 WORKFLOW, 💡 TIP sections
- **Performance-Aware Design** - Clear expectations for Fast (<3s), Moderate (3-15s), and Expensive (10-60s) operations
- **Workflow Orchestration** - Optimal tool sequences for Code Exploration, Refactoring Analysis, and Architecture Analysis
- **AI Model Optimization** - Reduces trial-and-error, improves tool orchestration, enables strategic usage patterns

🌍 **Multi-Language Support**
- **25+ Programming Languages**: JavaScript, TypeScript, Python, Java, C#, C++, C, Rust, Go, Kotlin, Scala, Swift, Dart, Ruby, PHP, Elixir, Elm, Lua, HTML, CSS, SQL, YAML, JSON, XML, Markdown, Haskell, OCaml, F#
- **Intelligent Language Detection**: Extension-based, MIME type, shebang, and content signature analysis
- **Framework Recognition**: React, Angular, Vue, Django, Flask, Spring, and 15+ more
- **Universal AST Abstraction**: Language-agnostic code analysis and graph structures

🔍 **Advanced Code Analysis**
- Complete codebase structure analysis with metrics across all languages
- Universal AST parsing with ast-grep backend and intelligent caching
- Cyclomatic complexity calculation with language-specific patterns
- Project health scoring and maintainability indexing
- Code smell detection: long functions, complex logic, duplicate patterns
- Cross-language similarity analysis and pattern matching

🧭 **Navigation & Search**
- Symbol definition lookup across mixed-language codebases
- Reference tracking across files and languages
- Function caller/callee analysis with cross-language calls
- Dependency mapping and circular dependency detection
- Call graph generation across entire project

⚡ **Performance Optimized**
- **Debounced File Watcher** - Automatic re-analysis when files change with 2-second intelligent debouncing
- **Real-time Updates** - Code graph automatically updates during active development
- Aggressive LRU caching with 50-90% speed improvements on repeated operations
- Cache sizes optimized for 500+ file codebases (up to 300K entries)
- Sub-microsecond response times on cache hits
- Memory-efficient universal graph building

🏢 **Enterprise Ready**
- Production-quality error handling across all languages
- Comprehensive logging and monitoring with language context
- UV package management with ast-grep integration

## Installation

### Quick Start (PyPI)

```bash
pip install codenav ast-grep-py rustworkx
```

## MCP Host Integration

### Claude Desktop

#### Method 1: Using Claude CLI (Recommended)

**For PyPI installation:**
```bash
# Project-specific installation
claude mcp add --scope project codenav codenav

# User-wide installation  
claude mcp add --scope user codenav codenav
```

**For development installation:**
```bash
# Project-specific installation
claude mcp add --scope project codenav uv run codenav

# User-wide installation  
claude mcp add --scope user codenav uv run codenav
```

**Verify installation:**
```bash
claude mcp list
```

#### Method 2: Manual Configuration
Add to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codenav": {
      "command": "codenav"
    }
  }
}
```

### Cline (VS Code Extension)

Add to your Cline MCP settings in VS Code:

1. Open VS Code Settings (Ctrl/Cmd + ,)
2. Search for "Cline MCP"
3. Add server configuration:

```json
{
  "cline.mcp.servers": {
    "codenav": {
      "command": "codenav"
    }
  }
}
```

### Continue (VS Code Extension)

Add to your `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "codenav",
      "command": "codenav",
      "env": {}
    }
  ]
}
```

### Cursor

Add to Cursor's MCP configuration:

1. Open Cursor Settings
2. Navigate to Extensions → MCP
3. Add server:

```json
{
  "name": "codenav",
  "command": "codenav"
}
```

### Zed Editor

Add to your Zed `settings.json`:

```json
{
  "assistant": {
    "mcp_servers": {
      "codenav": {
        "command": "codenav"
      }
    }
  }
}
```

### Zencoder ⭐

**The best AI coding tool!** Add to your Zencoder MCP configuration:

```json
{
  "mcpServers": {
    "codenav": {
      "command": "codenav",
      "env": {},
      "description": "Multi-language code analysis with 25+ language support"
    }
  }
}
```

**Pro Tip**: Zencoder's advanced AI capabilities work exceptionally well with CodeNavigator's comprehensive multi-language analysis. Perfect combination for professional development! 🚀

### Windsurf

Add to Windsurf's MCP configuration:

```json
{
  "mcpServers": {
    "codenav": {
      "command": "codenav"
    }
  }
}
```

### Aider

Use with Aider AI coding assistant:

```bash
aider --mcp-server codenav
```

### Open WebUI

For Open WebUI integration, add to your MCP configuration:

```json
{
  "mcp_servers": {
    "codenav": {
      "command": "codenav",
      "env": {}
    }
  }
}
```

### Generic MCP Client

For any MCP-compatible client, use these connection details:

```json
{
  "name": "codenav",
  "command": "codenav",
  "env": {}
}
```

### Docker Integration

#### Using Pre-built Images from GHCR

Pull and run from GitHub Container Registry:

```bash
# Pull latest SSE server
docker pull ghcr.io/ajacobm/codenav:sse-latest

# Run SSE mode (HTTP streaming)
docker run -p 8000:8000 -v $(pwd):/workspace \
  ghcr.io/ajacobm/codenav:sse-latest

# Run stdio mode (MCP over stdio)
docker pull ghcr.io/ajacobm/codenav:stdio-latest
docker run -v $(pwd):/workspace \
  ghcr.io/ajacobm/codenav:stdio-latest
```

Available image tags:
- `ghcr.io/ajacobm/codenav:sse-latest` - SSE HTTP streaming server
- `ghcr.io/ajacobm/codenav:stdio-latest` - stdio MCP server
- `ghcr.io/ajacobm/codenav:http-latest` - REST API server
- `ghcr.io/ajacobm/codenav:production-latest` - Production optimized
- `ghcr.io/ajacobm/codenav:development-latest` - Development with hot reload

#### Using Docker Compose

```bash
# With Redis cache (recommended)
docker compose -f docker-compose-ghcr.yml up -d

# For Codespaces
docker compose -f docker-compose-codespaces.yml up -d
```

#### Building Your Own Image

```dockerfile
FROM python:3.12-slim
RUN pip install codenav ast-grep-py rustworkx
WORKDIR /workspace
CMD ["codenav"]
```

```bash
docker build -t codenav .
docker run -v $(pwd):/workspace codenav
```

#### GitHub Codespaces

For development in Codespaces, see the [Codespaces Infrastructure Guide](docs/CODESPACES_INFRASTRUCTURE.md).

Quick start in Codespaces:
```bash
# Start Redis
./scripts/codespaces-redis.sh

# Run development server
./scripts/dev-server.sh sse 8000

# Or use Docker Compose
docker compose -f docker-compose-codespaces.yml up -d
```

### Development Installation

For contributing or custom builds:

```bash
git clone <repository-url>
cd codenav
uv sync --dev
uv build
```

**Add to Claude Code (development):**
```bash
# Project-specific
claude mcp add --scope project codenav uv run codenav

# User-wide
claude mcp add --scope user codenav uv run codenav
```

**For other MCP clients, use:**
```json
{
  "command": "uv",
  "args": ["run", "codenav"]
}
```

## Configuration Options

### Command Line Arguments

```bash
codenav --help
```

Available options:
- `--project-root PATH`: Root directory of your project (optional, defaults to current directory)
- `--verbose`: Enable detailed logging
- `--no-file-watcher`: Disable automatic file change detection

### Environment Variables

```bash
export CODENAV_LOG_LEVEL=DEBUG
export CODENAV_CACHE_SIZE=500000
export CODENAV_MAX_FILES=10000
export CODENAV_FILE_WATCHER=true
export CODENAV_DEBOUNCE_DELAY=2.0
```

### File Watcher (v1.1.0+)

The server includes an intelligent file watcher that automatically updates the code graph when files change:

- **Automatic Detection**: Monitors all supported file types in your project
- **Smart Debouncing**: 2-second delay prevents excessive re-analysis during rapid changes
- **Efficient Filtering**: Respects `.gitignore` patterns and only watches relevant files
- **Thread-Safe**: Runs in background without blocking analysis operations
- **Zero Configuration**: Starts automatically after first analysis

**File Watcher Features:**
- Real-time graph updates during development
- Batch processing of multiple rapid changes
- Duplicate change prevention
- Graceful error recovery
- Resource cleanup on shutdown

### Troubleshooting

#### Common Issues

1. **"Command not found"**: Ensure `codenav` is in your PATH
   ```bash
   pip install --upgrade codenav
   which codenav
   ```

2. **"ast-grep not found"**: Install the required dependency
   ```bash
   pip install ast-grep-py
   ```

3. **Permission errors**: Use virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   pip install codenav ast-grep-py rustworkx
   ```

4. **Large project performance**: Use verbose mode for debugging
   ```bash
   codenav --verbose
   ```

#### Debug Mode

Enable verbose logging for troubleshooting:

```bash
codenav --verbose
```

#### Supported File Types

The server automatically detects and analyzes these file extensions:
- **Web**: `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`
- **Backend**: `.py`, `.java`, `.cs`, `.cpp`, `.c`, `.rs`, `.go`
- **Mobile**: `.swift`, `.dart`, `.kt`
- **Scripting**: `.rb`, `.php`, `.lua`, `.pl`
- **Config**: `.json`, `.yaml`, `.yml`, `.toml`, `.xml`
- **Docs**: `.md`, `.rst`, `.txt`

## Available Tools

The MCP server provides **9 comprehensive analysis tools** with enhanced guidance that work across all 25+ supported languages:

### 🎯 **Enhanced Tool Experience** ⭐ *NEW in v1.2.0*

Each tool now includes **rich guidance** with visual hierarchy:
- **🎯 PURPOSE** - Clear explanation of what the tool does
- **🔧 USAGE** - When and how to use the tool effectively  
- **⚡ PERFORMANCE** - Speed expectations and caching information
- **🔄 WORKFLOW** - Optimal tool sequencing recommendations
- **💡 TIP** - Pro tips for maximum effectiveness

### 📚 **Usage Guide Tool**
| Tool | Description | Key Features |
|------|-------------|--------------|
| `get_usage_guide` | **NEW** - Comprehensive guidance with workflows, best practices, and examples | Complete documentation, workflow patterns, performance guidelines |

### 🛠️ **Analysis Tools**
| Tool | Description | Multi-Language Features | Performance |
|------|-------------|------------------------|-------------|
| `analyze_codebase` | Complete project analysis with structure metrics and complexity assessment | Language detection, framework identification, cross-language dependency mapping | ⚡ Expensive (10-60s) |
| `find_definition` | Locate symbol definitions with detailed metadata and documentation | Universal AST traversal, language-agnostic symbol resolution | ⚡ Fast (<3s) |
| `find_references` | Find all references to symbols throughout the codebase | Cross-file and cross-language reference tracking | ⚡ Fast (<3s) |
| `find_callers` | Identify all functions that call a specified function | Multi-language call graph analysis | ⚡ Fast (<3s) |
| `find_callees` | List all functions called by a specified function | Universal function call detection across languages | ⚡ Fast (<3s) |
| `complexity_analysis` | Analyze code complexity with refactoring recommendations | Language-specific complexity patterns, universal metrics | ⚡ Moderate (5-15s) |
| `dependency_analysis` | Generate module dependency graphs and import relationships | Cross-language dependency detection, circular dependency analysis | ⚡ Moderate (3-10s) |
| `project_statistics` | Comprehensive project health metrics and statistics | Multi-language project profiling, maintainability indexing | ⚡ Fast (<3s) |

## Usage Examples

### 🎯 **Getting Started with Enhanced Guidance** ⭐ *NEW in v1.2.0*

```
First, get comprehensive guidance on using the tools effectively:
get_usage_guide
```

### 🔍 **Multi-Language Analysis Workflows**

**Code Exploration Workflow:**
```
1. analyze_codebase (build the foundation)
2. project_statistics (get overview)  
3. find_definition("MyClass") (locate specific symbols)
4. find_references("MyClass") (understand usage patterns)
```

**Refactoring Analysis Workflow:**
```
1. analyze_codebase
2. complexity_analysis (threshold=15 for critical issues)
3. find_callers("complex_function") (impact analysis)
4. find_callees("complex_function") (dependency analysis)
```

**Architecture Analysis Workflow:**
```
1. analyze_codebase
2. dependency_analysis (identify circular dependencies)
3. project_statistics (health metrics)
4. complexity_analysis (quality assessment)
```

### 💬 **Natural Language Examples**

```
Analyze this React/TypeScript frontend with Python backend - show me the overall structure and complexity metrics
```

```
Find all references to the function "authenticate" across both the Java services and JavaScript frontend
```

```
Show me functions with complexity higher than 15 across all languages that need refactoring
```

```
Generate a dependency graph showing how the Python API connects to the React components
```

```
Detect code smells and duplicate patterns across the entire multi-language codebase
```

## Development

### Requirements
- Python 3.12+
- UV package manager
- MCP SDK
- ast-grep-py (for multi-language support)
- rustworkx (for high-performance graph operations)

### Running locally
```bash
# Install dependencies
uv sync

# Run the server directly (auto-detects current directory)
uv run codenav --verbose

# Test with help
uv run codenav --help
```

### Performance Features

- **LRU Caching**: 50-90% speed improvements with cache sizes up to 300K entries for large codebases
- **High-Performance Analytics**: PageRank at 4.9M nodes/second, Betweenness Centrality at 104K nodes/second
- **Sub-microsecond Response**: Cache hits deliver sub-microsecond response times for repeated operations
- **Memory Optimized**: Cache configurations optimized for 500+ file codebases with 500MB memory allocation
- **Comprehensive Benchmarks**: Performance monitoring with detailed cache effectiveness metrics

## Supported Languages

| Category | Languages | Count |
|----------|-----------|-------|
| **Web & Frontend** | JavaScript, TypeScript, HTML, CSS | 4 |
| **Backend & Systems** | Python, Java, C#, C++, C, Rust, Go | 7 |
| **JVM Languages** | Java, Kotlin, Scala | 3 |  
| **Functional** | Elixir, Elm | 2 |
| **Mobile** | Swift, Dart | 2 |
| **Scripting** | Ruby, PHP, Lua | 3 |
| **Data & Config** | SQL, YAML, JSON, TOML | 4 |
| **Markup & Docs** | XML, Markdown | 2 |
| **Additional** | Haskell, OCaml, F# | 3 |
| **Total** | | **25+** |

## Status

✅ **Multi-Language Support** - 25+ programming languages with ast-grep backend  
✅ **MCP SDK integrated** - Full protocol compliance across all languages  
✅ **Universal Architecture** - Language-agnostic graph structures and analysis  
✅ **Server architecture complete** - Enterprise-grade multi-language structure  
✅ **Core tools implemented** - 8 comprehensive analysis tools working across all languages  
✅ **Performance optimized** - Multi-language AST caching with intelligent routing  
✅ **Production ready** - comprehensive error handling, defensive security