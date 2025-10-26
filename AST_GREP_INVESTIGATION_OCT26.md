# AST-Grep Hanging Issue - Investigation Oct 26, 2025

## 🔴 Critical Issue: ast-grep-py Hangs on sg.root() Call

The analyze_codebase tool returns 0 nodes despite:
- ✅ Unit tests passing (patterns correct)
- ✅ Iterator fixes applied
- ✅ Pattern dictionary expanded to 25 languages

**Root Cause: `sg.root()` call HANGS INDEFINITELY**

## Reproduction

```python
from ast_grep_py import SgRoot

test_code = '''def hello():
    print("world")
'''

sg = SgRoot(test_code, 'python')
print("SgRoot created")

root = sg.root()  # <-- HANGS HERE, never returns
print("root() returned")

functions = list(root.find_all({"rule": {"kind": "function_definition"}}))
print(f"Found {len(functions)} functions")
```

**Result**: Hangs indefinitely after "SgRoot created"

## What Works

✅ SgRoot(content, language_id) constructor - completes immediately
✅ Language detection - works fine
✅ Pattern dictionary - all 25 languages configured
✅ echo commands in container - responsive

## What Doesn't Work

❌ sg.root() - hangs indefinitely
❌ root().find_all() - never reached
❌ Any code depending on sg.root() - hangs the entire parser

## Possible Root Causes

### 1. ast-grep-py Version/Compatibility
- Required: `ast-grep-py>=0.39.0`
- Even checking version hangs: `pip show ast-grep-py` times out
- Suggests fundamental issue with package

### 2. Missing Language Server Setup
- ast-grep is a language server at its core
- Maybe sg.root() tries to start/connect to language server?
- Need to check if there's initialization code missing

### 3. Threading/Async Issue
- C/Rust bindings might not be async-safe
- Maybe sg.root() blocks on something?
- Could be event loop or GIL issue

### 4. Container Environment
- Running in Docker with mcp-specific setup
- Maybe some capability or environment variable is missing?
- Timeout happens even in simple Python scripts

## Current Code Status

**File**: `src/code_graph_mcp/universal_parser.py`

Lines with the hanging code:
- Line 784: `root_node = sg_root.root()` (in _parse_functions_ast)
- Line 849: `root_node = sg_root.root()` (in _parse_classes_ast)
- Line 914: `root_node = sg_root.root()` (in _parse_imports_ast)

These are never reached because sg_root.root() hangs.

## Alternative Approaches to Consider

### Option A: Use subprocess/CLI instead of library
Instead of Python binding, shell out to `ast-grep` CLI command:
```python
# Instead of:
sg_root = SgRoot(content, 'python')
root = sg_root.root()
functions = root.find_all(...)

# Use:
result = subprocess.run([
    'ast-grep', 'scan',
    '--pattern', 'function_definition',
    '--json'
], input=content, capture_output=True)
```

**Pros**: Avoids the Rust binding issue, CLI is more stable
**Cons**: subprocess overhead, need ast-grep CLI installed

### Option B: Downgrade or try different ast-grep-py version
- Current requirement: `>=0.39.0`
- Try: `0.39.0` exactly, or `0.38.0`, or `0.40.0`
- Check if this is a recent regression

### Option C: Use alternative AST parsing library
- `tree-sitter` (Python binding) - more stable?
- `pygments` (syntax highlighting, limited AST)
- `parso` (Python-only)
- `treefmt` (Nix-based, multi-language)

### Option D: Async wrapper with timeout
Wrap sg_root.root() in asyncio timeout to at least fail gracefully:
```python
try:
    root = await asyncio.wait_for(
        asyncio.to_thread(sg_root.root), 
        timeout=5.0
    )
except asyncio.TimeoutError:
    logger.error(f"ast-grep-py timed out for {file_path}")
    return False
```

## Testing Code (Working)
```bash
# Language detection works:
docker exec <id> /app/.venv/bin/python3 -c "
from src.code_graph_mcp.universal_parser import LanguageRegistry
import asyncio
async def test():
    reg = LanguageRegistry()
    lang = await reg.get_language_by_extension(Path('/app/workspace/test.py'))
    print(lang)
asyncio.run(test())
"

# Pattern retrieval works:
docker exec <id> /app/.venv/bin/python3 -c "
from src.code_graph_mcp.universal_parser import ASTGrepPatterns
print(ASTGrepPatterns.get_pattern('python', 'function'))
"

# SgRoot creation works:
docker exec <id> /app/.venv/bin/python3 -c "
from ast_grep_py import SgRoot
sg = SgRoot('def x(): pass', 'python')
print('Success')
"

# HANGS:
docker exec <id> /app/.venv/bin/python3 -c "
from ast_grep_py import SgRoot
sg = SgRoot('def x(): pass', 'python')
root = sg.root()  # HANGS
"
```

## Immediate Next Steps

### 1. **Investigate ast-grep-py hanging** (Priority: HIGH)
- Try: `python3 -c "from ast_grep_py import SgRoot; print(SgRoot.__doc__)"`
- Check: Is there initialization code needed?
- Look for: Any threading/GIL issues in C bindings
- Compare: Different versions of ast-grep-py

### 2. **Test subprocess alternative** (Priority: MEDIUM)
- Install `ast-grep` CLI tool in container
- Create subprocess-based parser that shells out to CLI
- Benchmark performance vs Python binding (if working)

### 3. **Review ast-grep-py documentation** (Priority: MEDIUM)
- Check if there's setup/initialization required
- Look for known issues with Rust bindings
- See if there's a different API (maybe not sg.root()?)

### 4. **Check Python version/environment** (Priority: LOW)
- Container runs Python 3.12, requirements specify `>=3.12`
- Could 3.13 have issues with Rust bindings?
- Check if there's a known incompatibility

## Impact

**Current**: Parser hangs indefinitely when trying to parse any file
**Result**: analyze_codebase tool returns 0 nodes
**Workaround**: None currently available (SSE server still runs but returns empty graphs)

## Timeline

- Oct 26 morning: Iterator bug fixed, patterns expanded, unit tests passing
- Oct 26 (now): Discovered actual root cause is ast-grep-py hanging
- Oct 26 (to do): Test and implement workaround/fix

---

## Test Results Log

```
✅ Language detection works
✅ Pattern retrieval works
✅ SgRoot creation works
❌ sg.root() call - HANGS
❌ root().find_all() - never reached

Verdict: ast-grep-py C/Rust bindings have a fundamental issue
Next: Try subprocess alternative or different version
```
