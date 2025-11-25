# GraphIgnore & SEAM Patterns Guide

## Quick Start

### 1. Create `.graphignore` in your repo root

```
# Ignore entire directories
node_modules/
.git/
dist/
build/

# Ignore file patterns
*.min.js
*.pyc
__pycache__/

# Focus on specific languages
language: csharp
language: typescript

# Whitelist overrides (!)
!node_modules/@types/*
```

### 2. Load in code

```python
from codenav.ignore_patterns import IgnorePatternsManager

manager = IgnorePatternsManager("/path/to/repo")

# Check if path should be ignored
if not manager.should_ignore_path("node_modules/lodash/index.js"):
    # Analyze this file
    pass

# Check if language is in scope
if manager.should_analyze_language("csharp"):
    # Include C# files
    pass
```

---

## Ignore Patterns Syntax

### Basic Patterns
- `*.min.js` - matches app.min.js, lib.min.js, etc
- `node_modules/` - matches node_modules/ directory anywhere
- `dist/*` - matches files in dist/
- `test/*.js` - matches JS files in test/ at root level

### Whitelist (Include)
Prefix with `!` to override ignore patterns:
```
node_modules/
!node_modules/@types/*
!node_modules/@shared/*
```

### Language Filters
```
language: csharp
language: typescript
language: python
```

When language filters are set, only those languages are analyzed. All others are skipped.

### Comments
Lines starting with `#` are comments:
```
# This is a comment
node_modules/
```

---

## Seam Detection

### What Are Seams?

A **seam** is a connection between code in different languages within the same call chain.

**Example**:
```csharp
// C# calling Node.js service
var client = new HttpClient();
var response = await client.PostAsync("http://node-service:3000/api", data);
```

The graph creates a `SEAM` relationship from the C# function to the Node.js service endpoint.

### Registered Seam Patterns

#### C# → Node.js
Detects: HttpClient, PostAsync, RestClient, npm references, node service calls
```csharp
var client = new HttpClient();
await client.PostAsync("http://node-api:3000/users", content);
```

#### C# → SQL Server
Detects: SqlConnection, SqlCommand, DbContext, ExecuteReader, ExecuteNonQuery
```csharp
using (var conn = new SqlConnection(connString)) {
    var cmd = new SqlCommand("SELECT * FROM Users", conn);
    cmd.ExecuteReader();
}
```

#### TypeScript → Python
Detects: fetch, axios, XMLHttpRequest, api calls
```typescript
const response = await fetch('/api/python-service', { method: 'POST' });
const data = await axios.get('/api/data');
```

#### TypeScript/Angular → Node
Detects: import/require, @angular, @nestjs, express
```typescript
import { HttpClient } from '@angular/common/http';
import * as express from 'express';
```

#### Python → Java
Detects: subprocess, socket, gRPC, requests
```python
import subprocess
subprocess.Popen(['java', '-jar', 'service.jar'])
```

#### Python → SQL
Detects: sqlite3, psycopg2, pymysql, execute
```python
import psycopg2
conn = psycopg2.connect("dbname=mydb")
cursor.execute("SELECT * FROM users")
```

### Using SeamDetector

```python
from codenav.seam_detector import SeamDetector

detector = SeamDetector()

code = """
var client = new HttpClient();
await client.PostAsync("http://node-service:3000/api", data);
"""

if detector.detect_seams("csharp", "node", code, "ProcessOrder", "OrderService"):
    print("Seam detected: C# calling Node.js")
```

### Adding Custom Seams

```python
detector.add_pattern("rust", "go", r"ffi::.*call")

code = "unsafe { ffi::go_function_call() }"
if detector.detect_seams("rust", "go", code, "rust_func", "go_func"):
    print("Custom seam detected")
```

### Listing Available Seams

```python
detector = SeamDetector()
seams = detector.get_registered_seams()
# Output: [('csharp', 'node'), ('csharp', 'sql'), ('typescript', 'python'), ...]
```

---

## Integration with Analysis Engine

### Example: Multi-Tier .NET + Node + SQL Architecture

**Repository structure**:
```
my-app/
├── backend/           # C# .NET
│   ├── Services/
│   ├── Controllers/
│   └── Data/
├── api-gateway/       # Node.js
│   ├── routes/
│   ├── services/
│   └── node_modules/
├── frontend/          # TypeScript/Angular
│   ├── src/
│   ├── dist/
│   └── node_modules/
└── database/          # SQL schemas
    ├── migrations/
    └── stored-procs/
```

**`.graphignore`**:
```
# Ignore build outputs
bin/
obj/
node_modules/
dist/

# Focus on C# and TypeScript
language: csharp
language: typescript
language: sql

# Keep types
!node_modules/@types/*
```

**Usage**:
```python
from codenav.ignore_patterns import IgnorePatternsManager
from codenav.seam_detector import SeamDetector

manager = IgnorePatternsManager("/path/to/my-app")
detector = SeamDetector()

# Analyze backend
for file in all_files:
    if manager.should_ignore_path(file):
        continue
    
    language = detect_language(file)
    if not manager.should_analyze_language(language):
        continue
    
    # Analyze and parse
    ast = parse(file)
    nodes, relationships = extract_graph(ast)
    
    # Detect cross-language calls
    for rel in relationships:
        if detector.detect_seams(
            src_lang, tgt_lang,
            file_content, src_name, tgt_name
        ):
            # Create SEAM relationship instead of CALLS
            graph.add_relationship(
                source, target,
                RelationshipType.SEAM,
                metadata={'tier': 'cross-language'}
            )
```

---

## Query Examples

Once seams are detected, query them:

```python
# Find all cross-language seams
seams = graph.get_relationships_by_type(RelationshipType.SEAM)

# Find seams from C# to other languages
for seam in seams:
    if nodes[seam.source_id].language == 'csharp':
        target_lang = nodes[seam.target_id].language
        print(f"C# calling {target_lang}: {seam.source_id} -> {seam.target_id}")

# Trace execution through all tiers
call_chain = trace_call_chain(
    start_node="ProcessOrderFunction",
    follow_seams=True
)
# Returns: Process (C#) -> API (Node) -> Query (SQL)
```

---

## Best Practices

1. **Start with ignore patterns**: Focus analysis on relevant code first
2. **Use language filters** for multi-repo architectures: Reduces noise
3. **Enable seams** when analyzing tiered systems
4. **Whitelist carefully**: `!` patterns can override ignores, use sparingly
5. **Test patterns** on a small repo first before large analysis
6. **Cache ignore config**: Load once, reuse across files

---

## Testing

Run tests:
```bash
./.venv/bin/python -m pytest tests/test_ignore_patterns.py tests/test_seam_detector.py -v
```

Expected output:
```
tests/test_ignore_patterns.py::test_load_graphignore_patterns PASSED
tests/test_seam_detector.py::test_csharp_to_node_detection PASSED
... (22 tests total)
```

---

## Troubleshooting

### Pattern not matching

Check the pattern syntax:
```python
manager = IgnorePatternsManager("/path")
print(manager.patterns)  # View compiled patterns
print(manager.should_ignore_path("test/file.js"))  # Test match
```

### Language filter not working

Ensure language is lowercase and matches exactly:
```python
manager.add_language_filter("csharp")
assert manager.should_analyze_language("csharp")  # ✓
assert not manager.should_analyze_language("C#")  # ✗ Different case
```

### Seam not detected

Check regex pattern:
```python
detector = SeamDetector()
patterns = detector.patterns[("csharp", "node")]
for p in patterns:
    print(p.pattern)  # View actual regex
```

Add debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
detector.detect_seams(...)  # Shows which patterns match
```

---

## Reference

### IgnorePatternsManager Methods
- `should_ignore_path(path: str) -> bool`
- `should_analyze_language(language: str) -> bool`
- `add_pattern(pattern: str, include: bool = False)`
- `add_language_filter(language: str)`
- `clear_language_filters()`
- `get_config() -> IgnoreConfig`

### SeamDetector Methods
- `detect_seams(source_lang, target_lang, code, src_name, tgt_name) -> bool`
- `add_pattern(source_lang, target_lang, pattern)`
- `get_registered_seams() -> List[Tuple[str, str]]`
