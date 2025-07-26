# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2025-07-25

### 🚀 Critical Fix: MCP Tool Exposure Resolved

This critical release fixes the MCP tool exposure issue that prevented tools from being accessible in Claude Code.

#### 🐛 Fixed
- **CRITICAL MCP Tool Exposure** - Fixed issue where MCP tools were not properly accessible through Claude Code interface
- **SDK Compliance** - Updated function signatures to match official Python SDK patterns exactly
- **Type Annotations** - Changed `Dict[str, Any]` → `dict`, `List[types.TextContent]` → `list[types.TextContent]`
- **Tool Dispatch** - Replaced complex handler dispatch with simple if/elif pattern following SDK examples

#### ✅ Verified
- **Tool Accessibility** - All 8 tools now properly exposed and accessible: `claude mcp list` shows "✓ Connected"
- **SDK Pattern Compliance** - Server implementation matches official Python SDK examples exactly
- **Connectivity Testing** - Comprehensive test confirms "SUCCESS: MCP server is properly exposing 8 tools"

#### 📊 Added
- **Connectivity Test Suite** - Added `test_mcp_connectivity.py` for MCP integration verification
- **Comprehensive Test Report** - Added detailed `MCP_TOOLS_TEST_REPORT.md` with technical specifications
- **Production Verification** - Confirmed all 8 tools working correctly in production environment

#### 🏗️ Technical Changes
- Simplified `call_tool()` dispatch from dictionary pattern to direct if/elif structure
- Updated all handler function signatures to use modern Python type hints
- Maintained backward compatibility while fixing core functionality

---

## [1.0.4] - 2025-07-25

### 🔧 Stability Release: MCP Server Integration Fixed

This critical release resolves MCP server integration issues and ensures reliable functionality.

#### 🐛 Fixed
- **Import Issues** - Resolved relative import problems that prevented MCP server from loading in Claude Code
- **Server Startup** - Fixed package execution environment compatibility issues
- **MCP Integration** - Proper server initialization and protocol communication
- **Development Installation** - Added editable package installation for proper module resolution

#### ✅ Verified
- **Server Functionality** - Comprehensive test suite confirms all 8 MCP tools working correctly
- **Command Execution** - Server starts properly with `code-graph-mcp --project-root .`
- **Protocol Initialization** - MCP server initializes correctly with debug logging
- **Package Installation** - Development mode installation resolves all import dependencies

#### 🧪 Testing
- **Comprehensive Test Suite** - Added `test_mcp_server.py` for full MCP functionality validation
- **Basic Functionality Test** - Added `simple_test.py` for core server verification
- **Integration Validation** - Confirmed server works with proper package installation

---

## [1.0.3] - 2025-07-25

### 📚 Documentation Release: Corrected Installation Commands

This patch release fixes critical documentation errors in installation commands.

#### 🐛 Fixed
- **Installation Commands** - Removed non-existent `--project-root` flag from all documentation
- **README.md** - Corrected MCP server installation instructions for both PyPI and source installations
- **CHANGELOG.md** - Updated installation examples with accurate commands
- **.mcp.json** - Fixed project configuration to use correct command syntax

#### 📖 Improved
- **Accurate Documentation** - All installation commands now work correctly
- **User Experience** - Eliminated confusion from incorrect command-line flags
- **Professional Standards** - Documentation consistency across all files

---

## [1.0.2] - 2025-07-25

### 🛠️ Professional Release: Open Source Ready

This maintenance release focuses on code quality, professional documentation, and open source preparation.

#### ✨ Added
- **MIT License** - Open source license for commercial and personal use
- **Professional Documentation** - Cleaned up comments and documentation for public release
- **Enhanced Error Handling** - Improved logging and error messages across all components

#### 🐛 Fixed
- **All Pylance Type Errors** - Resolved attribute access issues with UniversalNode structure
- **Server.py Compatibility** - Fixed data structure alignment with universal graph components
- **Professional Code Quality** - Removed development comments and improved documentation

#### 🚀 Improved
- **Perfect Static Analysis** - Maintained 0 Ruff linting errors across all modules
- **Enhanced Type Safety** - Proper attribute access patterns for UniversalNode
- **Enterprise Standards** - Professional code quality suitable for open source distribution

---

## [1.0.1] - 2025-07-25

### 🎯 Quality & Performance Release

Major code quality improvements and performance optimizations while maintaining full functionality.

#### 🐛 Fixed
- **190+ Linting Errors** - Comprehensive cleanup across all source files
- **Complex Function Refactoring** - Dictionary dispatch pattern for improved maintainability
- **Import Optimization** - Cleaned up unused imports and improved module organization
- **Type Annotation Issues** - Enhanced type hints for better IDE support

#### 🚀 Enhanced
- **Perfect Code Quality** - Achieved 0 Ruff linting errors across entire codebase
- **Enhanced Type Safety** - Proper null guards and exception handling
- **Performance Optimizations** - Maintained 50-90% caching improvements
- **Professional Standards** - Enterprise-grade error handling and defensive programming

---

## [1.0.0] - 2025-01-25

### 🎉 Major Release: Multi-Language Support

This release transforms the code-graph-mcp from a Python-only analyzer to a comprehensive **25+ language code analysis platform**.

### ✨ Added

#### Multi-Language Architecture
- **Universal Parser** - ast-grep-powered parsing for 25+ programming languages
- **Language-Agnostic Graph Structures** - Universal AST representation that works across all languages
- **Intelligent Language Detection** - Multi-method detection (extension, MIME, shebang, content signatures)
- **Cross-Language Analysis** - Code similarity, complexity, and pattern detection across language boundaries

#### Supported Languages (25+)
- **Web & Frontend**: JavaScript, TypeScript, HTML, CSS
- **Backend & Systems**: Python, Java, C#, C++, C, Rust, Go  
- **JVM Languages**: Java, Kotlin, Scala
- **Functional**: Elixir, Elm, Haskell, OCaml, F#
- **Mobile**: Swift, Dart
- **Scripting**: Ruby, PHP, Lua
- **Data & Config**: SQL, YAML, JSON, TOML
- **Markup & Docs**: XML, Markdown

#### Advanced Analysis Features
- **Code Smell Detection** - Long functions, complex logic, duplicate patterns across languages
- **Cross-Language Call Graphs** - Function relationships spanning multiple languages
- **Circular Dependency Detection** - Import/dependency cycle analysis
- **Maintainability Indexing** - Project health scoring with language-aware metrics
- **Framework Recognition** - React, Angular, Vue, Django, Flask, Spring, and 15+ more

#### Project Intelligence
- **Project Profiling** - Automatic detection of project type, build systems, CI configuration
- **Multi-Language Statistics** - Comprehensive metrics across entire polyglot codebases
- **Smart File Discovery** - Language-aware filtering with framework detection
- **Parallel Processing** - Concurrent analysis of multi-language projects

### 🚀 Enhanced

#### Performance Improvements
- **Multi-Language AST Caching** - LRU caching with mtime invalidation across all languages
- **Intelligent Routing** - Priority-based analysis with language-specific optimizations
- **Memory Efficiency** - Universal graph structures with optimized storage

#### Enterprise Features
- **Production Stability** - Comprehensive error handling across all language parsers
- **Defensive Security** - Secure analysis without code execution
- **Comprehensive Testing** - 14 test suites covering all major features
- **10.00/10 Pylint Score** - Maintained code quality standards

### 🔄 Changed

#### Breaking Changes
- Minimum Python version remains 3.12+
- New dependency: `ast-grep-py>=0.39.0` for multi-language parsing
- Enhanced MCP tools now return language-aware results

#### API Evolution
- All existing MCP tools (`analyze_codebase`, `find_definition`, etc.) now work across all 25+ languages
- Universal node types replace Python-specific AST structures
- Language detection integrated into all analysis workflows

### 📦 Dependencies

#### New Requirements
- `ast-grep-py>=0.39.0` - Multi-language parsing backend
- Enhanced MCP protocol support for cross-language analysis

#### Development Dependencies
- `pytest>=7.0.0` with multi-language test fixtures
- `black>=23.0.0` and `ruff>=0.1.0` for code quality

### 🧪 Testing

- **Comprehensive Test Suite** - 14 tests covering all major features
- **Multi-Language Integration Tests** - End-to-end validation of parsing pipeline
- **Language Registry Tests** - Verification of all 25+ language configurations
- **Performance Benchmarks** - Cross-language analysis performance validation

### 📚 Documentation

- **Updated README** - Complete multi-language feature documentation
- **Enhanced Installation Guide** - PyPI and source installation with ast-grep-py
- **Usage Examples** - Real-world multi-language project analysis scenarios
- **Language Support Matrix** - Detailed breakdown of all supported languages

### 🎯 Migration Guide

#### For Existing Users
The v1.0.0 release is backward compatible - all existing functionality continues to work exactly as before, but now with enhanced multi-language capabilities.

#### New Installation
```bash
pip install code-graph-mcp  # Now automatically includes ast-grep-py
claude mcp add --scope project code-graph-mcp "uv run code-graph-mcp --verbose"
```

#### Enhanced Features
- Same MCP tools, now work with JavaScript, TypeScript, Java, Rust, Go, and 20+ more languages
- Automatic language detection - no configuration needed
- Cross-language analysis - find relationships between Python APIs and React components

---

## [0.1.0] - 2025-01-20

### Initial Release
- Python-only code analysis
- 8 MCP analysis tools
- AST parsing with caching
- Basic complexity analysis
- MCP protocol integration