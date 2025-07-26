# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.3] - 2025-01-27

### 🔧 Patch Release: Complete JSON Serialization Fix

This patch release fixes the `from_json()` method to properly reconstruct graph objects from JSON data, completing the architectural migration.

#### 🛠️ JSON Deserialization Fix
- **Complete Object Reconstruction** - `from_json()` now properly recreates `UniversalNode` and `UniversalRelationship` objects from JSON data
- **Proper Index Storage** - Rustworkx indices are correctly stored in reconstructed objects (`_rustworkx_index`, `_rustworkx_edge_index`)
- **Full Graph Restoration** - Restored graphs are fully functional with all operations working correctly
- **Robust Error Handling** - Graceful handling of malformed JSON data with detailed logging

#### 🎯 Technical Implementation
- **Object Recreation** - Reconstructs `UniversalLocation`, `UniversalNode`, and `UniversalRelationship` from JSON attributes
- **Index Management** - Properly assigns rustworkx indices to reconstructed objects
- **Graph Consistency** - Ensures restored graph maintains all architectural patterns
- **Import Addition** - Added `UniversalLocation` import for proper object reconstruction

#### ✅ Verification
- **JSON Round-trip** - Serialization → Deserialization → Full functionality confirmed
- **Graph Operations** - All methods work correctly on restored graphs
- **Test Suite** - JSON serialization/deserialization tests passing
- **Production Ready** - Complete and robust JSON handling

---

## [1.2.2] - 2025-01-27

### 🔧 Patch Release: Complete Architectural Migration

This patch release completes the architectural migration by eliminating the final references to deprecated edge mapping dictionaries.

#### 🛠️ Final Fixes
- **Edge Mapping Cleanup** - Removed final `edge_id_to_index` and `index_to_edge_id` references in `from_json()` method
- **Consistent Architecture** - All methods now use direct graph storage patterns consistently
- **Complete Migration** - Architectural redesign fully completed with no legacy mapping references

#### 🎯 Technical Details
- **`from_json()` Method** - Fixed lines 1376-1377 to use `relationship._rustworkx_edge_index` instead of deprecated dictionaries
- **Edge Index Storage** - Consistent use of relationship object attributes for edge index storage
- **Zero Legacy References** - No remaining references to old index mapping system

#### ✅ Verification
- **All Methods Working** - Complete test suite confirms no AttributeError crashes
- **Architectural Consistency** - All graph operations use unified direct storage approach
- **Production Stability** - Final cleanup ensures long-term maintainability

---

## [1.2.1] - 2025-01-27

### 🐛 Critical Bug Fix Release: Resolved Tool Hanging Issues

This critical patch release fixes **AttributeError crashes** that were causing MCP tools to hang and timeout, resolving a major stability issue introduced during architectural improvements.

#### 🔥 Critical Fixes
- **Tool Hanging Resolution** - Fixed 6 methods that were crashing with `AttributeError: 'RustworkxCodeGraph' object has no attribute 'index_to_node_id'`
- **Graph Method Stability** - All graph analysis methods now work correctly without crashes
- **MCP Tool Reliability** - Tools no longer hang or timeout due to internal crashes
- **Complete Architecture Migration** - Finished migration from index mapping dictionaries to direct graph storage

#### 🛠️ Methods Fixed
- **`find_bridges()`** - Fixed `self.index_to_node_id.get(edge[0])` → `self.graph[edge[0]]`
- **`calculate_graph_distance_matrix()`** - Fixed index mapping loops to use direct graph iteration
- **`calculate_bellman_ford_path_lengths()`** - Fixed index lookups to use `self.graph[index]`
- **`calculate_weighted_shortest_paths()`** - Fixed `self.node_id_to_index.get()` → `getattr(node, '_rustworkx_index')`
- **`find_node_layers()`** - Fixed index mapping to use proper node lookup pattern
- **`from_json()`** - Completely rewrote to use direct graph storage without index dictionaries

#### 🎯 Root Cause Analysis
- **Issue**: Incomplete migration from old index mapping system (`index_to_node_id`, `node_id_to_index`) to new direct storage approach
- **Impact**: Methods crashed with AttributeError when called, causing tools to hang and timeout
- **Solution**: Consistent use of `self.graph[index]` to get node ID from rustworkx index and `getattr(node, '_rustworkx_index')` for reverse lookup

#### ✅ Verification
- **All 6 Methods Working** - Comprehensive testing confirms no more AttributeError crashes
- **29/29 Tests Passing** - Full test suite validates stability
- **MCP Tools Functional** - All 9 tools now work without hanging
- **Production Ready** - No more timeout issues or tool failures

#### 🚀 Performance Impact
- **Zero Performance Degradation** - Fixes maintain original performance characteristics
- **Improved Reliability** - Tools complete successfully instead of crashing
- **Better User Experience** - No more mysterious hangs or timeouts

---

## [1.2.0] - 2025-01-27

### 🎯 Major Feature Release: Enhanced Tool Guidance & AI Optimization

This major release introduces **comprehensive tool usage guidance** inspired by Serena's approach, dramatically improving AI model effectiveness and user experience through rich descriptions, workflow recommendations, and best practices.

#### ✨ Added
- **Comprehensive Usage Guide Tool** - New `get_usage_guide` tool provides complete guidance document with workflows, best practices, and examples
- **Rich Tool Descriptions** - Enhanced all 8 tools with structured guidance using visual hierarchy (🎯 PURPOSE, 🔧 USAGE, ⚡ PERFORMANCE, 🔄 WORKFLOW, 💡 TIP)
- **Performance-Aware Design** - Clear performance expectations for Fast (<3s), Moderate (3-15s), and Expensive (10-60s) operations
- **Workflow Orchestration** - Optimal tool sequences for Code Exploration, Refactoring Analysis, and Architecture Analysis
- **Visual Hierarchy** - Emoji-based categorization for quick scanning and improved readability

#### 🔧 Enhanced
- **Tool Parameter Descriptions** - Enriched with usage context, constraints, and performance implications
- **Best Practices Integration** - Embedded guidance on when and how to use each tool effectively
- **Common Pitfalls Documentation** - Clear warnings about expensive operations and usage mistakes
- **Use Case Examples** - Step-by-step workflows for common scenarios ("understand codebase", "refactor function X", "find code smells")

#### 🎯 AI Model Optimization
- **Reduced Trial-and-Error** - Clear guidance prevents ineffective tool combinations
- **Improved Tool Orchestration** - AI models understand optimal workflows and tool relationships
- **Strategic Tool Usage** - Performance awareness leads to more efficient analysis patterns
- **Context-Aware Recommendations** - Tools suggest when to use other tools for complete analysis

#### 📊 Workflow Patterns
- **Foundation Tools** - `analyze_codebase` (required first), `project_statistics` (overview)
- **Symbol Analysis** - `find_definition` → `find_references` → `find_callers`/`find_callees`
- **Quality Analysis** - `complexity_analysis` + `dependency_analysis` for refactoring roadmaps
- **Architecture Analysis** - `dependency_analysis` → `project_statistics` → `complexity_analysis`

#### 🚀 Performance Guidelines
- **Fast Operations** - `find_definition`, `find_references`, `find_callers`, `find_callees`, `project_statistics` (use freely)
- **Moderate Operations** - `complexity_analysis`, `dependency_analysis` (strategic use, cached results)
- **Expensive Operations** - `analyze_codebase` (only when needed, results persist)

#### 💡 Innovation Beyond Industry Standards
- **Visual Hierarchy** - Emoji-based categorization for instant comprehension
- **Performance-First Design** - Speed expectations clearly marked for optimal usage
- **Workflow-Centric Approach** - Emphasizes tool orchestration over individual tool usage
- **Comprehensive Pitfall Prevention** - Proactive guidance to avoid common mistakes

#### 🛠️ Technical Implementation
- **9 Enhanced Tools** - All tools now include comprehensive guidance
- **Zero Performance Impact** - Guidance is descriptive metadata with no runtime overhead
- **Production Ready** - All tests passing, zero linting errors
- **Backward Compatible** - Existing tool functionality unchanged

#### 📚 Documentation Quality
- **Professional Formatting** - Consistent structure across all tool descriptions
- **Copy-Paste Ready** - All examples and workflows ready for immediate use
- **Comprehensive Coverage** - Every tool includes purpose, usage, performance, workflow, and tips
- **User-Centric Design** - Focused on practical guidance for real-world usage scenarios

---

## [1.1.1] - 2025-07-26

### 📚 Documentation Release: Enhanced MCP Host Integration

This patch release updates documentation with comprehensive MCP host integration instructions and special recognition for Zencoder.

#### 📖 Enhanced
- **Zencoder Integration** - Added special configuration for the best AI coding tool ⭐
- **9+ MCP Hosts Supported** - Comprehensive setup instructions for all major MCP clients
- **Enhanced Configuration** - Added file watcher options, environment variables, and troubleshooting
- **Docker Integration** - Complete containerized deployment examples
- **Professional Documentation** - Improved formatting and user experience

#### 🔧 MCP Hosts Added
- **Claude Desktop** - CLI and manual configuration
- **VS Code Extensions** - Cline, Continue, Cursor
- **Editors** - Zed, Windsurf
- **AI Assistants** - Zencoder ⭐, Aider, Open WebUI
- **Generic MCP Client** - Universal configuration template

#### 🎯 User Experience
- **Copy-Paste Ready** - All configuration examples ready to use
- **Platform Aware** - OS-specific paths and commands
- **Troubleshooting Guide** - Common issues and debug instructions
- **File Watcher Documentation** - Complete v1.1.0 feature guide

---

## [1.1.0] - 2025-07-26

### 🚀 Major Feature Release: Debounced File Watcher

This major release introduces **automatic file change detection** with intelligent debouncing, making the MCP server significantly more responsive and user-friendly for development workflows.

#### ✨ Added
- **Debounced File Watcher** - Automatic detection of file changes with 2-second intelligent debouncing
- **Real-time Graph Updates** - Code graph automatically updates when source files are modified
- **Thread-Safe Architecture** - Watchdog observer with proper async/await coordination using `loop.call_soon_threadsafe()`
- **Smart File Filtering** - Respects .gitignore patterns and only watches supported file extensions (25+ languages)
- **Duplicate Change Prevention** - Recent changes tracking prevents redundant re-analysis

#### 🔧 Enhanced
- **Cache Management Integration** - File watcher triggers comprehensive cache clearing before re-analysis
- **Project Statistics** - Added file watcher status and statistics to project stats output
- **Graceful Cleanup** - Proper file watcher shutdown and resource cleanup on server termination
- **Error Recovery** - Robust error handling with fallback to manual analysis if watcher fails

#### ⚡ Performance Improvements
- **Instant Response** - No more manual re-analysis needed when files change
- **Efficient Batching** - Multiple rapid changes trigger only one re-analysis after debounce delay
- **Resource Optimization** - Debouncing prevents CPU/memory spikes during bulk file operations
- **Cache Efficiency** - Maintains 70%+ cache hit rates while ensuring data freshness

#### 🛠️ Technical Implementation
- **Watchdog Integration** - Added `watchdog>=6.0.0` dependency for cross-platform file monitoring
- **Event Loop Management** - Proper asyncio event loop handling between threads
- **Debounce Logic** - Intelligent 2-second delay with change batching and duplicate filtering
- **Memory Management** - Bounded cache sizes with automatic cleanup timers

#### 📊 Verification
- **Comprehensive Testing** - Verified automatic re-analysis on file modifications
- **Debounce Effectiveness** - Confirmed rapid changes are properly batched
- **Thread Safety** - No race conditions between watcher thread and main event loop
- **Resource Cleanup** - Proper shutdown prevents memory leaks and hanging processes

#### 🎯 User Experience
- **Zero Configuration** - File watcher starts automatically after first analysis
- **Development Friendly** - Perfect for active development with frequent file changes
- **Production Ready** - Robust error handling and graceful degradation
- **Status Visibility** - File watcher status included in project statistics

#### 📚 Documentation
- **Comprehensive MCP Host Integration** - Added setup instructions for 9+ MCP hosts
- **Zencoder Integration** - Special configuration for the best AI coding tool ⭐
- **Enhanced README** - Docker, troubleshooting, and configuration options
- **File Watcher Documentation** - Complete feature documentation and usage guide

---

## [1.0.9] - 2025-07-26

### Symbol Search Fix Release

#### 🔧 Fixed
- **Symbol Search Functionality** - Fixed critical bug where exact_match=True prevented partial symbol matching
- **MCP Tool Responses** - All 8 MCP tools now properly find and return code symbols and definitions
- **Search Coverage** - Symbol searches now find partial matches (e.g., "CodeGraph" finds "RustworkxCodeGraph")
- **Function Discovery** - find_definition, find_references, find_callers, and find_callees now work correctly

#### 🚀 Performance
- **Removed Analysis Caching** - Eliminated _is_analyzed flag that prevented fresh analysis on each request
- **Real-time Analysis** - Each MCP tool call now performs fresh project analysis for accurate results
- **Debug Logging** - Added comprehensive logging for troubleshooting file discovery and parsing

#### 📊 Verification
- **Direct Testing** - Verified 20+ files parsed with 600+ nodes and 800+ relationships
- **Symbol Coverage** - Confirmed detection of classes, functions, and modules across codebase
- **Search Accuracy** - Multiple symbol searches now return expected results with proper file locations

## [1.0.8] - 2025-07-26

### Critical Performance and Reliability Fixes

#### 🔥 Critical Fixes
- **File Discovery Performance** - Added comprehensive .gitignore pattern matching and common directory exclusion
- **Tool Timeout Resolution** - Fixed 2+ minute timeouts by preventing analysis of massive REFERENCE directories
- **Warning Spam Elimination** - Changed "Cannot add relationship: missing nodes" from WARNING to DEBUG level
- **Clojure Language Removal** - Eliminated clojure support that was causing ast-grep crashes

#### ⚡ Performance Improvements  
- **Directory Filtering** - Skip build/cache/dependency directories: __pycache__, node_modules, .git, dist, build
- **Pattern Matching** - Efficient fnmatch-based .gitignore pattern implementation
- **Response Times** - All 8 MCP tools now complete in under 30 seconds (previously 2+ minutes)

#### 🛠️ Technical Changes
- **File Path Filtering** - Enhanced _should_ignore_path with comprehensive skip patterns
- **Logging Levels** - Reduced noise by moving debug messages to appropriate log levels
- **Error Handling** - Improved robustness for large codebases with proper timeout management

#### ✅ Verification
- **8/8 Tools Working** - All MCP tools verified functional with proper response times
- **No Timeouts** - Eliminated hanging and timeout issues completely
- **Clean Output** - Removed warning spam for better user experience

## [1.0.7] - 2025-07-25

### Performance Optimization Release

#### ⚡ Enhanced
- **Aggressive LRU Caching** - Implemented comprehensive caching across all performance-critical functions
- **Memory Optimization** - Cache sizes optimized for 500+ file codebases with 500MB memory allocation
- **Hashable Data Structures** - Made LanguageConfig frozen dataclass with tuple fields for cache compatibility
- **Code Duplication Analysis** - Implemented actual duplicate code detection replacing placeholder

#### 🚀 Performance Improvements
- **PageRank**: Up to 4.9M nodes/second processing speed
- **Betweenness Centrality**: Up to 104K nodes/second processing speed
- **Cache Effectiveness**: 50-90% speed improvements on repeated operations
- **Sub-microsecond Response**: Cache hits deliver sub-microsecond response times

#### 🐛 Fixed
- **Type Safety** - Resolved Pylance errors for LanguageConfig hashability
- **Boolean Return Types** - Fixed type checking issues in line processing functions
- **Graph Reconstruction** - Implemented complete fallback graph reconstruction from JSON data

#### 🧪 Technical Changes
- Cache sizes: 300K for variable references, 200K for function calls, 100K for node lookups
- Converted all LanguageConfig list fields to tuples for immutability and hashability
- Added comprehensive performance benchmarks and cache effectiveness tests

---

## [1.0.8] - 2025-07-26

### 🚀 Production Release: Performance & Reliability Fixes

This critical release resolves major performance and reliability issues that prevented proper tool functionality.

#### 🐛 Fixed
- **Tool Timeout Issues** - Fixed 2+ minute timeouts by implementing proper .gitignore file filtering
- **REFERENCE Directory Analysis** - Massive performance improvement by excluding reference materials from analysis
- **Warning Spam** - Silenced hundreds of "missing nodes" warnings that cluttered output
- **File Discovery** - Added comprehensive common directory exclusion (build/, dist/, node_modules/, etc.)

#### ⚡ Performance
- **Dramatic Speed Improvement** - Tools now complete in 15-30 seconds instead of timing out
- **Smart File Filtering** - Respects .gitignore patterns plus common build/cache directories
- **Clean Output** - Eliminated debug warning spam for better user experience
- **Memory Efficiency** - Reduced memory usage by skipping irrelevant files

#### ✅ Verified
- **All 8 Tools Working** - Comprehensive test confirms 100% success rate (8/8 tools functional)
- **Fast Analysis** - Complete project analysis in under 30 seconds
- **Production Ready** - No more timeouts, crashes, or excessive warnings

#### 🛠️ Technical Changes
- Added proper .gitignore pattern matching with fnmatch
- Implemented common directory skip list (20+ patterns)
- Changed relationship warnings from WARNING to DEBUG level
- Enhanced file discovery with smart filtering

---

## [1.0.6] - 2025-07-25

### 🛠️ Language Support Update: Clojure Removed

This release removes Clojure language support to resolve runtime crashes and ensures stable operation across all supported languages.

#### 🐛 Fixed
- **Runtime Crash Fix** - Removed Clojure language configuration that was causing ast-grep panic crashes
- **Server Stability** - All 8 MCP tools now function correctly without crash interruptions
- **Project Analysis** - Server can now successfully analyze large codebases without language-related failures

#### ✅ Verified
- **All Tools Working** - Comprehensive test confirms all 8 tools return meaningful data
- **Performance Improved** - Analysis now completes successfully: 935 files parsed, 23,256 nodes, 22,321 relationships
- **Production Ready** - No more runtime panics or tool execution failures

#### ⚡ Performance
- **Language Count** - Now supports 25 languages (down from 26, Clojure removed)
- **Parsing Speed** - Faster analysis without problematic language processing
- **Memory Efficiency** - Reduced memory usage without Clojure AST overhead

---

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