Original task query: 
Improve the following code from [object Promise] (e.g., suggest refactorings, optimizations, or better practices):
src/code_graph_mcp/universal_parser.py line 1069
def _should_ignore_path(self, file_path: Path, project_root: Path) -> bool:
... the .gitignore logic needs to happen once and stored in a data structure, not re-called per file path.. there are other optimizations, I'm sure.

Result:
I've analyzed the `_should_ignore_path` method and the broader `UniversalParser` class. Here are my key findings and improvement suggestions:

## Current Issues with `_should_ignore_path` Method

1. **Performance Issues:**
   - The method reads `.gitignore` file on every call, which is extremely inefficient
   - No caching of gitignore patterns despite potentially thousands of file checks
   - String operations and pattern matching repeated unnecessarily

2. **Logic Problems:**
   - The method doesn't handle nested `.gitignore` files (only checks project root)
   - Pattern matching is overly simplistic and doesn't follow full gitignore spec
   - Missing support for negation patterns (`!pattern`)
   - Doesn't handle absolute vs relative patterns correctly

3. **Error Handling:**
   - Silent failures when reading `.gitignore` could mask real issues
   - No validation of gitignore patterns

## Broader Code Quality Issues

1. **Memory Usage:**
   - Excessive use of `@lru_cache` decorators (6 different caches) without size limits consideration
   - Large cache sizes (300K entries) could consume significant memory
   - No cache invalidation strategy

2. **Method Complexity:**
   - Several methods are too long and do multiple things (violating SRP)
   - `_parse_file_content` method is 50+ lines and handles multiple concerns
   - Complex nested logic in parsing methods

3. **Code Duplication:**
   - Similar pattern extraction logic repeated across multiple methods
   - Redundant error handling patterns

## Proposed Improvements

### 1. Optimize `_should_ignore_path` Method
- Cache gitignore patterns at class level
- Use proper gitignore parsing library (like `pathspec`)
- Support nested gitignore files
- Add proper error handling and logging

### 2. Refactor Large Methods
- Split `_parse_file_content` into smaller, focused methods
- Extract common pattern matching logic into utilities
- Separate concerns (parsing vs relationship building)

### 3. Improve Caching Strategy
- Implement cache size monitoring and cleanup
- Use more appropriate cache sizes based on actual usage
- Add cache hit/miss metrics for optimization

### 4. Add Better Error Handling
- Replace silent failures with proper logging
- Add retry mechanisms for transient failures
- Validate inputs more thoroughly

### 5. Performance Optimizations
- Batch file operations where possible
- Use async I/O more effectively
- Implement early termination for large directories

Would you like me to create a detailed implementation plan for these improvements? I can focus on the most critical issues first (like the gitignore caching) or provide a comprehensive refactoring approach.

Now I understand the context better! Looking at your sophisticated `HybridCacheManager`, I can see you've already implemented an excellent multi-tiered caching strategy. Your dual caching approach is very well thought out:

**Your Current Caching Architecture:**
- **L1 (Memory)**: Fast in-memory LRU for immediate access
- **L2 (Redis)**: Persistent, shared cache for distributed scenarios
- **Hybrid Strategy**: Intelligent fallback between memory-only and Redis-backed modes

This perfectly addresses your use cases:
- **(A) No Redis**: Quick analysis on smaller codebases with memory-only caching
- **(B) With Redis**: Distributed, multi-client, large codebase scenarios with persistent graphs

**The Key Issue**: The current `@lru_cache` decorators in `UniversalParser` are creating a **third caching layer** that's actually working against your sophisticated cache manager:

1. **Cache Conflict**: The LRU caches (with sizes like 300K entries) are bypassing your hybrid cache manager entirely
2. **Memory Bloat**: These caches can consume significant memory even in Redis-backed scenarios
3. **Cache Invalidation**: No coordination between LRU caches and your Redis invalidation logic
4. **Redundancy**: Caching the same data at multiple levels without coordination

**The Solution**: We should refactor to use your `HybridCacheManager` consistently throughout the parser, removing the conflicting LRU caches and leveraging your `@cached_method` decorator instead.

Would you like me to create a comprehensive refactoring plan that:
1. Removes conflicting LRU caches
2. Integrates all caching through your `HybridCacheManager`
3. Fixes the `_should_ignore_path` performance issues
4. Maintains your excellent dual-mode caching strategy
5. Adds proper cache invalidation coordination

This would give you a unified, efficient caching strategy that scales from quick local analysis to distributed enterprise scenarios.
`

