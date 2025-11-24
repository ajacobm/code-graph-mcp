# Quick Reference: Seams & Ignore Patterns

## Ignore Patterns (.graphignore)

```bash
# Ignore paths
node_modules/
*.min.js
dist/
__pycache__/

# Filter languages (only analyze these)
language: csharp
language: typescript

# Whitelist exceptions
!node_modules/@types/*
```

```python
from codenav.ignore_patterns import IgnorePatternsManager

manager = IgnorePatternsManager("/repo")

# Check before analysis
if not manager.should_ignore_path("src/app.js"):
    analyze(file)

if manager.should_analyze_language("csharp"):
    process_csharp_files()

# Runtime config
manager.add_pattern("*.log")
manager.add_language_filter("python")
```

## Seam Detection

```python
from codenav.seam_detector import SeamDetector

detector = SeamDetector()

# Detect cross-language calls
code = "var client = new HttpClient(); await client.PostAsync(...)"
if detector.detect_seams("csharp", "node", code, "Func", "Service"):
    graph.add_relationship(src, tgt, RelationshipType.SEAM)

# Add custom seam
detector.add_pattern("rust", "go", r"ffi::.*")

# List registered seams
seams = detector.get_registered_seams()
# [('csharp', 'node'), ('csharp', 'sql'), ...]
```

## Registered Seams (6 Types)

| Source | Target | Detected Patterns |
|--------|--------|-------------------|
| C# | Node.js | `HttpClient`, `PostAsync`, `RestClient`, `npm` |
| C# | SQL | `SqlConnection`, `SqlCommand`, `DbContext`, `ExecuteReader` |
| TypeScript | Python | `fetch`, `axios`, `XMLHttpRequest`, `api` |
| TypeScript | Node.js | `import`, `require`, `@angular`, `@nestjs`, `express` |
| Python | Java | `subprocess`, `socket`, `grpc`, `requests` |
| Python | SQL | `sqlite3`, `psycopg2`, `pymysql`, `execute` |

## Common Use Cases

### Multi-Tier .NET + Node + SQL
```
.graphignore:
node_modules/
bin/
obj/
language: csharp
language: typescript
language: sql
```

### Focus on One Language
```
.graphignore:
language: python
node_modules/
.venv/
__pycache__/
*.pyc
```

### Legacy + Modern Code
```
.graphignore:
legacy/
old_vb_code/
!legacy/critical_function.vb
language: csharp
```

## Graph Relationships

After seam detection, graph has:

```
CALLS:  Node A → Node B  (same language)
SEAM:   Node A → Node B  (different language)
        ↓ (with metadata)
        { "source_lang": "csharp", "target_lang": "node" }
```

## Query Seams

```python
from codenav.universal_graph import RelationshipType

# All cross-language edges
seams = graph.get_relationships_by_type(RelationshipType.SEAM)

# From specific node
for rel in graph.get_outgoing(node_id):
    if rel.type == RelationshipType.SEAM:
        print(f"Seam: {rel.source_id} → {rel.target_id}")

# Trace through all languages
path = find_call_chain(start, end, follow_seams=True)
```

## Test Commands

```bash
# Run both test suites
./.venv/bin/python -m pytest \
  tests/test_ignore_patterns.py \
  tests/test_seam_detector.py -v

# Just patterns
./.venv/bin/python -m pytest tests/test_ignore_patterns.py -v

# Just seams
./.venv/bin/python -m pytest tests/test_seam_detector.py -v

# Specific test
./.venv/bin/python -m pytest tests/test_seam_detector.py::TestSeamDetector::test_csharp_to_node_detection -v
```

## Debug Seams

```python
import logging
logging.basicConfig(level=logging.DEBUG)

detector = SeamDetector()
result = detector.detect_seams("csharp", "node", code, "fn", "svc")
# Logs which patterns matched

manager = IgnorePatternsManager("/repo")
print(manager.patterns)  # View compiled regexes
print(manager.language_filters)  # View active languages
```

## Files Reference

| File | Purpose |
|------|---------|
| `src/codenav/ignore_patterns.py` | IgnorePatternsManager class |
| `src/codenav/seam_detector.py` | SeamDetector class |
| `tests/test_ignore_patterns.py` | 11 pattern tests |
| `tests/test_seam_detector.py` | 11 seam tests |
| `IGNORE_PATTERNS_GUIDE.md` | Full usage docs |
| `SESSION_PLAN_MULTI_LANGUAGE.md` | Roadmap (3 sessions) |
| `.graphignore.example` | Config template |

## Next Session

Branch: `feature/graph-query-api`

Features:
- REST API endpoints for graph traversal
- DFS/BFS algorithms with SEAM awareness
- Call chain queries across languages
- Response caching

Timeline: ~4-6 hours
