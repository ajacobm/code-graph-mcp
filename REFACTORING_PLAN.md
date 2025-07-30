# Code Graph MCP Refactoring Plan
## Multi-Tier Caching Architecture Optimization

### Executive Summary

This refactoring plan addresses critical caching inefficiencies in the UniversalParser while preserving and enhancing the sophisticated HybridCacheManager architecture. The primary focus is eliminating redundant LRU caches that conflict with the existing multi-tier caching strategy and optimizing the `_should_ignore_path` method performance bottleneck.

### Current State Analysis

#### Strengths
- **Excellent HybridCacheManager Design**: Well-architected multi-tier caching (L1: Memory, L2: Redis) with intelligent fallback strategies
- **Flexible Cache Strategies**: Supports memory-only, Redis-only, hybrid, and Redis-fallback modes
- **Comprehensive Cache API**: Rich interface for file-level caching with metadata tracking
- **Solid Foundation**: Good separation of concerns between cache management and parsing logic

#### Critical Issues
1. **Cache Architecture Conflict**: 6 separate `@lru_cache` decorators bypass the HybridCacheManager entirely
2. **Performance Bottleneck**: `_should_ignore_path` reads `.gitignore` on every file (potentially thousands of times)
3. **Memory Inefficiency**: Large LRU caches (50K-300K entries) consume memory even in Redis-backed scenarios
4. **Cache Invalidation Gaps**: No coordination between LRU caches and Redis invalidation logic
5. **Redundant Caching**: Same data cached at multiple levels without coordination

### Primary Use Case Focus

**Large, existing codebases with discrete changes over time** - This perfectly aligns with your Redis-backed caching strategy where:
- Initial analysis is expensive but subsequent runs leverage cached results
- Multiple clients/instances can share cached analysis
- File-level granular invalidation optimizes incremental updates
- Cross-session persistence maintains performance between runs

### Refactoring Strategy

## Phase 1: Critical Performance Fixes

### 1.1 Optimize `_should_ignore_path` Method

**Current Issue**: Reads `.gitignore` file on every invocation
**Solution**: Initialize gitignore patterns once, cache in class instance

```python
class UniversalParser:
    def __init__(self, ...):
        # ... existing initialization
        self._gitignore_patterns: Optional[List[str]] = None
        self._gitignore_compiled: Optional[Any] = None  # pathspec.PathSpec
        self._project_root: Optional[Path] = None

    def _load_gitignore_patterns(self, project_root: Path) -> None:
        """Load and compile gitignore patterns once per project."""
        if self._project_root == project_root and self._gitignore_patterns is not None:
            return  # Already loaded for this project
        
        self._project_root = project_root
        gitignore_path = project_root / '.gitignore'
        
        if not gitignore_path.exists():
            self._gitignore_patterns = []
            self._gitignore_compiled = None
            return
        
        try:
            import pathspec  # Use proper gitignore library
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                patterns = [line.strip() for line in f 
                           if line.strip() and not line.startswith('#')]
            
            self._gitignore_patterns = patterns
            self._gitignore_compiled = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
            logger.debug(f"Loaded {len(patterns)} gitignore patterns from {gitignore_path}")
            
        except Exception as e:
            logger.warning(f"Error loading .gitignore: {e}")
            self._gitignore_patterns = []
            self._gitignore_compiled = None

    def _should_ignore_path(self, file_path: Path, project_root: Path) -> bool:
        """Check if path should be ignored (optimized with cached patterns)."""
        # Load gitignore patterns if needed
        self._load_gitignore_patterns(project_root)
        
        # Always skip system/cache directories
        common_skip_dirs = {
            '__pycache__', '.git', '.svn', '.hg', '.bzr',
            '.pytest_cache', '.mypy_cache', '.tox', '.coverage',
            '.sass-cache', '.cache', '.DS_Store', '.idea', '.vscode', '.vs'
        }
        
        if any(part in common_skip_dirs for part in file_path.parts):
            return True
        
        # Check gitignore patterns using compiled pathspec
        if self._gitignore_compiled:
            relative_path = file_path.relative_to(project_root)
            return self._gitignore_compiled.match_file(str(relative_path))
        
        return False
```

**Benefits**:
- Eliminates file I/O on every call (massive performance improvement)
- Proper gitignore handling with negation patterns and nested gitignore support
- Memory efficient (patterns loaded once per project)

### 1.2 Remove Conflicting LRU Caches

**Target Methods**: Remove `@lru_cache` decorators from:
- `get_language_by_extension` (50K cache)
- `get_language_by_name` (10K cache)  
- `is_supported_file` (50K cache)
- `detect_language` (50K cache)
- `_extract_function_name` (100K cache)
- `_extract_class_name` (50K cache)
- `_extract_import_target` (100K cache)
- `_extract_function_calls` (200K cache)
- `_extract_variable_references` (300K cache)
- `_extract_method_invocations` (150K cache)

**Replacement Strategy**: Integrate with HybridCacheManager using `@cached_method` decorator

## Phase 2: Integrate with HybridCacheManager

### 2.1 Convert Language Detection Methods

```python
class LanguageRegistry:
    def __init__(self, cache_manager: Optional[HybridCacheManager] = None):
        self.cache_manager = cache_manager

    @cached_method(ttl=3600)  # Cache for 1 hour
    async def get_language_by_extension(self, file_path: Path) -> Optional[LanguageConfig]:
        """Get language configuration by file extension with hybrid caching."""
        suffix = file_path.suffix.lower()
        for lang_config in self.LANGUAGES.values():
            if suffix in lang_config.extensions:
                return lang_config
        return None
```

### 2.2 Convert Parser Methods

```python
class UniversalParser:
    @cached_method(ttl=1800, key_generator=lambda self, fp: f"supported:{fp.suffix}")
    async def is_supported_file(self, file_path: Path) -> bool:
        """Check if file is supported (cached)."""
        return file_path.suffix.lower() in self.registry.get_supported_extensions()

    @cached_method(ttl=1800, key_generator=lambda self, fp: f"lang:{fp.suffix}")  
    async def detect_language(self, file_path: Path) -> Optional[LanguageConfig]:
        """Detect programming language (cached)."""
        return await self.registry.get_language_by_extension(file_path)
```

### 2.3 Convert Extraction Methods

```python
# Convert heavy extraction methods to use file-level caching
@cached_method(ttl=3600, key_generator=lambda self, fp: f"file_analysis:{fp}")
async def _analyze_file_content(self, file_path: Path) -> Dict[str, Any]:
    """Comprehensive file analysis with caching."""
    # Combine multiple extraction operations into single cached operation
    content = await self._read_file_content(file_path)
    language_config = await self.detect_language(file_path)
    
    return {
        'functions': self._extract_all_functions(content, language_config),
        'classes': self._extract_all_classes(content, language_config),
        'imports': self._extract_all_imports(content, language_config),
        'calls': self._extract_all_calls(content, language_config),
        'variables': self._extract_all_variables(content, language_config)
    }
```

## Phase 3: Enhanced Caching Strategies

### 3.1 File-Level Granular Caching

Leverage existing file-level caching in HybridCacheManager:

```python
async def parse_file(self, file_path: Path) -> bool:
    """Parse file with comprehensive caching."""
    # Check if file is cached and valid
    if await self.cache_manager.is_file_cached(file_path):
        # Load from cache
        cached_nodes = await self.cache_manager.get_file_nodes(str(file_path))
        cached_rels = await self.cache_manager.get_file_relationships(str(file_path))
        
        if cached_nodes and cached_rels:
            # Add to graph
            for node_data in cached_nodes:
                self.graph.add_node(UniversalNode.from_dict(node_data))
            for rel_data in cached_rels:
                self.graph.add_relationship(UniversalRelationship.from_dict(rel_data))
            return True
    
    # Parse and cache
    nodes, relationships = await self._parse_file_fresh(file_path)
    
    # Cache results
    await self.cache_manager.set_file_nodes(str(file_path), nodes)
    await self.cache_manager.set_file_relationships(str(file_path), relationships)
    
    return True
```

### 3.2 Intelligent Cache Invalidation

```python
async def invalidate_changed_files(self, project_root: Path) -> int:
    """Invalidate cache for modified files only."""
    # Use git or file timestamps to detect changes
    changed_files = await self._detect_file_changes(project_root)
    
    invalidation_count = 0
    for file_path in changed_files:
        count = await self.cache_manager.invalidate_file(str(file_path))
        invalidation_count += count
    
    logger.info(f"Invalidated cache for {len(changed_files)} changed files")
    return invalidation_count
```

## Phase 4: Performance Optimizations

### 4.1 Batch Operations

```python
async def parse_directory_batch(self, directory: Path, batch_size: int = 50) -> int:
    """Parse files in batches for better performance."""
    files_to_parse = []
    cached_files = []
    
    # Separate cached vs non-cached files
    for file_path in self._discover_files(directory):
        if await self.cache_manager.is_file_cached(file_path):
            cached_files.append(file_path)
        else:
            files_to_parse.append(file_path)
    
    logger.info(f"Found {len(cached_files)} cached, {len(files_to_parse)} to parse")
    
    # Load cached files in batch
    await self._load_cached_files_batch(cached_files)
    
    # Parse new files in batches
    for i in range(0, len(files_to_parse), batch_size):
        batch = files_to_parse[i:i+batch_size]
        await self._parse_files_batch(batch)
```

### 4.2 Memory Management

```python
class UniversalParser:
    def __init__(self, ...):
        # Configure memory limits for cache manager
        self.cache_manager = HybridCacheManager(
            redis_config=redis_config,
            strategy=CacheStrategy.HYBRID,
            memory_limit_mb=256  # Limit memory cache size
        )
```

## Phase 5: Testing & Validation

### 5.1 Performance Benchmarks

```python
# Before/after performance tests
async def benchmark_gitignore_performance():
    # Test _should_ignore_path with 1000 files
    # Measure: old vs new implementation

async def benchmark_cache_performance():
    # Test cache hit rates, memory usage
    # Compare LRU vs HybridCache

async def benchmark_large_codebase():
    # Test on large codebase (10K+ files)
    # Measure: initial parse, incremental updates
```

### 5.2 Cache Validation Tests

```python
async def test_cache_consistency():
    # Ensure Redis and memory caches stay synchronized
    
async def test_invalidation_accuracy():
    # Verify only changed files are invalidated
    
async def test_fallback_behavior():
    # Test Redis unavailable scenarios
```

## Implementation Timeline

### Week 1: Critical Fixes
- [ ] Optimize `_should_ignore_path` method
- [ ] Remove conflicting LRU caches
- [ ] Add pathspec dependency

### Week 2: Cache Integration  
- [ ] Convert language detection methods
- [ ] Convert parser methods to use `@cached_method`
- [ ] Implement file-level analysis caching

### Week 3: Enhanced Features
- [ ] Implement intelligent cache invalidation
- [ ] Add batch processing optimizations
- [ ] Add memory management controls

### Week 4: Testing & Optimization
- [ ] Performance benchmarking
- [ ] Cache consistency validation  
- [ ] Documentation updates

## Expected Performance Improvements

### Large Codebase Scenario (10K+ files):
- **Initial Parse**: 60% faster (gitignore optimization + batch processing)
- **Incremental Updates**: 90% faster (file-level granular caching)
- **Memory Usage**: 40% reduction (eliminate redundant LRU caches)
- **Cache Hit Rate**: 85%+ on subsequent runs

### Distributed Scenario (Multiple Clients):
- **Shared Cache Efficiency**: 95% of previously analyzed files available immediately
- **Cross-Instance Performance**: Near-local performance for cached analyses
- **Memory Efficiency**: Each client only caches working set, not entire codebase

### Redis vs Memory-Only Performance:
- **Small Projects (<1K files)**: Memory-only remains fastest for single-session use
- **Large Projects (>5K files)**: Redis-backed provides 3-5x improvement on subsequent runs
- **Multi-Session Usage**: Redis provides 10x+ improvement by eliminating re-analysis

## Risk Mitigation

### Compatibility
- Maintain backward compatibility through gradual migration
- Keep memory-only mode as fallback for environments without Redis
- Preserve existing API interfaces

### Performance
- Implement performance monitoring and alerting
- Add cache statistics and hit rate tracking
- Provide cache tuning recommendations

### Reliability  
- Graceful fallback when Redis is unavailable
- Cache corruption detection and recovery
- Comprehensive error handling and logging

## Conclusion

This refactoring plan transforms the existing caching architecture from conflicting multi-level caches to a unified, efficient system that:

1. **Eliminates Performance Bottlenecks**: Fixes the gitignore file reading issue and redundant caching
2. **Leverages Existing Architecture**: Enhances rather than replaces the excellent HybridCacheManager
3. **Optimizes Primary Use Case**: Large codebases with incremental changes get maximum benefit
4. **Maintains Flexibility**: Preserves all existing cache strategies and fallback modes
5. **Improves Resource Efficiency**: Reduces memory usage while increasing cache effectiveness

The result will be a caching system that scales efficiently from small projects to enterprise codebases while maintaining the sophisticated multi-tier architecture you've already built.