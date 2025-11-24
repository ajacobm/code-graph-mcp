# Fix for "Graph has 0 Nodes" Issue

## Root Causes Identified

### Issue #1: File Watcher Watchdog API Incompatibility ✅
**Location**: `src/codenav/file_watcher.py:160`

**Problem**: 
```python
self._observer.schedule(
    event_handler,
    str(self.project_root),
    recursive=True,
    ignore_patterns=["**/{}".format(p) for p in ignore_patterns] + ["**/.*"]
)
```

The `ignore_patterns` parameter was removed in watchdog 6.0.0+. The modern watchdog API uses a different approach.

**Fix**: 
- Remove `ignore_patterns` parameter
- Use `ignore_paths` instead (if needed) or handle filtering in event handler

---

### Issue #2: Parsing Methods Are Text-Based Fallbacks ❌
**Location**: `src/codenav/universal_parser.py:555-700+`

**Problem**: 
The `_parse_functions()`, `_parse_classes()`, `_parse_variables()`, etc. methods use:
- Simple `line.strip().split()` pattern matching
- Text-based regex patterns
- No actual AST parsing with ast-grep

This is why:
- Every file gets added as a MODULE node
- NO FUNCTION, CLASS, VARIABLE, or IMPORT nodes are being created
- The graph ends up with 0 "real" nodes despite parsing 41 files

**Example Problem Code**:
```python
def _parse_functions(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> None:
    """Parse function definitions."""
    # This is a simplified implementation - real implementation would use ast-grep patterns
    # For now, we'll use text-based pattern matching as a fallback
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()

        for i, line in enumerate(lines, 1):
            for pattern in language_config.function_patterns:
                if pattern in line and not line.strip().startswith(language_config.comment_patterns[0]):
                    func_name = self._extract_function_name(line, pattern, language_config)
                    if func_name:
                        # ... creates node
```

This approach:
1. ✅ Creates nodes for simple patterns
2. ❌ Fails to parse actual AST from files
3. ❌ No real semantic analysis
4. ❌ High false positives/negatives

---

## Solution Strategy

### Two-Tier Fix

#### Fix #1: File Watcher (Immediate) ✅
Update `file_watcher.py` to use modern watchdog API:

```python
# OLD (broken):
self._observer.schedule(
    event_handler,
    str(self.project_root),
    recursive=True,
    ignore_patterns=[...]  # ❌ Not supported in watchdog 6.0.0+
)

# NEW (working):
self._observer.schedule(
    event_handler,
    str(self.project_root),
    recursive=True
)
```

The event handler can filter ignored paths internally.

#### Fix #2: Parsing Methods (Architecture Fix) ⚠️
Replace text-based fallback with proper ast-grep integration:

**Option A: Full AST-Grep Integration** (Recommended)
- Use `sg_root.find_all()` with proper AST patterns
- Parse actual syntax tree nodes
- Create proper FUNCTION/CLASS/VARIABLE nodes from AST

**Option B: Hybrid Approach** (Quick Win)
- Keep text-based as fallback
- Add proper ast-grep queries as primary path
- Better error handling when ast-grep succeeds

**Option C: Simplify and Document** (Current State)
- Accept that this is a "proof of concept" parser
- Focus on MODULE-level analysis
- Document limitations clearly

---

## Recommended Fix: Option A + File Watcher

### Step 1: Fix File Watcher
```python
# src/codenav/file_watcher.py - Line 155-165

# Remove ignore_patterns parameter
self._observer.schedule(
    event_handler,
    str(self.project_root),
    recursive=True
    # Removed: ignore_patterns=...
)

# Add ignore logic to event handler instead
def on_modified(self, event: FileSystemEvent) -> None:
    path = Path(event.src_path)
    
    # Skip ignored directories/files
    if any(part.startswith('.') for part in path.parts):
        return
    if any(part in {'__pycache__', '.git'} for part in path.parts):
        return
    
    if not event.is_directory:
        self.watcher._handle_file_change(path)
```

### Step 2: Fix Parsing - Use ast-grep Properly
```python
# src/codenav/universal_parser.py - Replace _parse_file_content method

async def _parse_file_content(self, file_path: Path, language_config: LanguageConfig) -> bool:
    """Parse file content using proper AST-Grep integration."""
    try:
        content = self._read_file_with_encoding_detection(file_path)

        if SgRoot is None:
            logger.error("ast-grep-py not available")
            return False
            
        sg_root = SgRoot(content, language_config.ast_grep_id)

        # Create file node
        file_node = self._create_file_node(file_path, language_config, content)
        self.graph.add_node(file_node)
        self.graph.add_processed_file(str(file_path))

        # PROPER AST-GREP USAGE:
        
        # 1. Find all function definitions
        self._extract_functions_from_ast(sg_root, file_path, language_config)
        
        # 2. Find all class definitions  
        self._extract_classes_from_ast(sg_root, file_path, language_config)
        
        # 3. Find all imports
        self._extract_imports_from_ast(sg_root, file_path, language_config)
        
        # 4. Parse relationships
        self._extract_relationships_from_ast(sg_root, file_path, language_config)

        logger.debug("Successfully parsed %s (%s)", file_path, language_config.name)
        return True

    except Exception as e:
        logger.error("Error parsing %s: %s", file_path, e)
        return False
```

### Step 3: Implement Proper AST Extraction Methods
```python
def _extract_functions_from_ast(self, sg_root, file_path: Path, language_config: LanguageConfig) -> None:
    """Extract functions using ast-grep AST."""
    try:
        # Language-specific function patterns using ast-grep
        patterns = {
            'python': 'function()',
            'javascript': 'function() or arrow_function()',
            'typescript': 'function_declaration() or arrow_function()',
            'java': 'method_declaration()',
            # ... etc for other languages
        }
        
        pattern = patterns.get(language_config.ast_grep_id, 'function()')
        
        # Query AST for function nodes
        matches = sg_root.find_all(pattern)
        
        for match in matches:
            func_node = UniversalNode(
                id=f"function:{file_path}:{match.name()}:{match.start().line}",
                name=match.name(),
                node_type=NodeType.FUNCTION,
                location=UniversalLocation(
                    file_path=str(file_path),
                    start_line=match.start().line,
                    end_line=match.end().line,
                    language=language_config.name
                ),
                complexity=self._calculate_complexity(match),
                language=language_config.name
            )
            self.graph.add_node(func_node)
            
            # Add contains relationship
            rel = UniversalRelationship(
                id=f"contains:{file_path}:{func_node.id}",
                source_id=f"file:{file_path}",
                target_id=func_node.id,
                relationship_type=RelationshipType.CONTAINS
            )
            self.graph.add_relationship(rel)
            
    except Exception as e:
        logger.debug(f"Error extracting functions from {file_path}: {e}")

def _calculate_complexity(self, ast_node) -> int:
    """Calculate cyclomatic complexity from AST node."""
    # Count decision points: if, for, while, catch, ?:, &&, ||, etc.
    complexity = 1
    try:
        # This would need proper implementation based on ast-grep API
        # For now, simplified approach
        text = str(ast_node)
        decision_keywords = ['if', 'for', 'while', 'catch', '&&', '||', '?', 'switch', 'case']
        for keyword in decision_keywords:
            complexity += text.count(keyword)
    except:
        pass
    return max(1, complexity)
```

---

## Quick Verification

### After Fix #1 (File Watcher):
```bash
# Container should NOT show:
# "Failed to start file watcher: BaseObserver.schedule() got an unexpected keyword argument 'ignore_patterns'"
```

### After Fix #2 (Parsing):
```bash
# Container should show something like:
# "Analysis complete: 25 nodes, 18 relationships"  # Instead of "0 nodes"
```

---

## Why Current State Has 0 Nodes

The logs show:
```
2025-10-25 22:11:33,690 - codenav.universal_parser - INFO - Optimized parsing complete: 41/44 files parsed
2025-10-25 22:11:33,703 - codenav.graph.rustworkx_unified - DEBUG - get_statistics: 0 nodes, 0 relationships, 41 files
```

This happens because:

1. ✅ Files ARE being parsed and cached
2. ✅ FILE MODULEs are being created but...
3. ❌ The text-based `_parse_functions()` method isn't finding function patterns
4. ❌ So NO FUNCTION nodes are created
5. ❌ Result: Only counting file nodes initially, but stats filtered to 0

The text pattern matching is TOO STRICT (false negatives) or TOO LOOSE (false positives), but the real problem is it's not using actual AST parsing.

---

## Implementation Priority

1. **HIGH**: Fix file watcher (`ignore_patterns` → remove parameter)
2. **HIGH**: Implement proper ast-grep extraction methods
3. **MEDIUM**: Add proper complexity calculation
4. **LOW**: Optimize performance with caching

---

## Testing After Fix

```bash
# Build container
uv build

# Run container
docker build -t codenav .
docker run codenav

# Should see in logs:
# - No file watcher error
# - "Analysis complete: X nodes, Y relationships" (NOT 0)
# - Actual functions/classes parsed from code
```
