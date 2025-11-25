# Graph Query Zero Results Issue - Root Cause Analysis

## Summary
The tools `find_references`, `find_function_callers`, and `find_function_callees` return zero results because the graph does not contain the relationship types they're looking for.

## Root Cause

### What the query tools expect:
- **find_symbol_references**: Looks for `RelationshipType.REFERENCES` relationships
- **find_function_callers**: Looks for `RelationshipType.CALLS` relationships (incoming)
- **find_function_callees**: Looks for `RelationshipType.CALLS` relationships (outgoing)

### What the parser creates:
The `UniversalParser` currently only creates these relationship types:
- `RelationshipType.CONTAINS` - File/class contains functions/classes
- `RelationshipType.IMPORTS` - File imports another file

**Missing:**
- `RelationshipType.CALLS` - Function A calls Function B
- `RelationshipType.REFERENCES` - Symbol X is referenced in location Y

## Why This Happened

The parser uses `ast_grep` to extract AST nodes, which works well for:
- Extracting function/class definitions ✓
- Extracting import statements ✓

But `ast_grep` patterns currently:
- Don't capture function call expressions
- Don't capture symbol references
- Focus on static structure, not call graph

## Solution Path

### Option 1: Enhance UniversalParser (Recommended)
Add CALLS relationship extraction to `_parse_functions_ast`:
1. After extracting function definitions, analyze the function body
2. Use ast_grep patterns to find function calls within the body
3. Create CALLS relationships from the parent function to called functions
4. For each call, store line number for context

### Option 2: Add separate call graph analysis
Create a new analyzer component:
1. Parse function bodies for call expressions
2. Build call graph separately
3. Inject CALLS relationships into the existing graph

### Option 3: Use language-specific AST analysis
For each language parser (Python, JavaScript, etc.):
1. Extract call expressions from AST
2. Resolve call targets to function nodes
3. Add CALLS relationships

## Testing Strategy

Created test files:
- `test_graph_queries.py` - Comprehensive test suite for graph queries
- `test_zero_results_diagnosis.py` - Diagnostic script showing what relationships exist

Run diagnostics:
```bash
python tests/test_zero_results_diagnosis.py
```

Expected output with fix:
```
CALLS relationships: > 0
REFERENCES relationships: > 0 (or at least CALLS works)
find_symbol_references: Returns results
find_function_callers: Returns results
find_function_callees: Returns results
```

## Files to Modify

1. **`src/codenav/universal_parser.py`**
   - Add `_extract_calls_from_function()` method
   - Call it after function extraction
   - Create CALLS relationships

2. **`tests/test_graph_queries.py`**
   - Already created - use for validation

3. **`src/codenav/server/mcp_server.py`**
   - No changes needed - tools already use correct relationship types

## Impact
- ✓ find_references will work (if REFERENCES implemented)
- ✓ find_function_callers will work (with CALLS implementation)
- ✓ find_function_callees will work (with CALLS implementation)
- ✓ Code smell detection will improve (dead code detection)
- ✓ Complexity analysis will be more complete
