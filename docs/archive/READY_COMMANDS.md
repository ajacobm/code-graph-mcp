# CodeNavigator - Ready-to-Use Commands

## Current Status

**Location**: `/mnt/c/Users/ADAM/GitHub/codenav`

**What Works**:
- ✅ File watcher (watchdog API compatible)
- ✅ AST-Grep integration (all 25 languages)
- ✅ Iterator bug fixed
- ✅ Patterns complete

**What Doesn't Work**:
- ❌ Graph nodes not appearing (need tracing to debug)

**Container**: `ajacobm/codenav:sse`

---

## 🔧 Build Commands

### Fresh Build (clears Docker cache)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker build -t ajacobm/codenav:sse --target sse --no-cache .
```

### Regular Build (uses cache)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker build -t ajacobm/codenav:sse --target sse .
```

### Build Both SSE and STDIO (optional)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker build -t ajacobm/codenav:sse --target sse .
docker build -t ajacobm/codenav:stdio --target stdio .
```

---

## 🚀 Deployment Commands

### Start Services (with logs)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml up
```

### Start Services (detached)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml up -d
```

### Stop Services (clean)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml down
```

### Stop Services (clean volumes)
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml down -v
```

---

## 📋 Useful Log Commands

### Watch Main App Logs
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml logs -f code-graph-codegraphmcp-sse
```

### Watch Redis Logs
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml logs -f redis
```

### Watch All Logs
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml logs -f
```

### Filter for TRACE Output Only
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml logs code-graph-codegraphmcp-sse | grep TRACE
```

### Follow TRACE Output in Real-Time
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml logs -f code-graph-codegraphmcp-sse | grep --line-buffered TRACE
```

### Check Service Status
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml ps
```

---

## 🧪 Testing Commands

### Health Check (once services running)
```bash
curl -s http://localhost:10101/health | jq
```

### Expected Response
```json
{
  "status": "healthy",
  "timestamp": "2025-10-26T...",
  "version": "1.0.0",
  "details": {
    "cache": "connected",
    "parser": "ready"
  }
}
```

### MCP Tools List (HTTP GET)
```bash
curl -s http://localhost:10101/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Analyze Code Graph (via HTTP)
```bash
curl -s -X POST http://localhost:10101/mcp/analyze \
  -H "Content-Type: application/json" \
  -d '{"path":"/app/workspace/src"}'
```

---

## 🔍 Debugging Workflow

### Phase 1: Prepare
```bash
# 1. Go to project
cd /mnt/c/Users/ADAM/GitHub/codenav

# 2. Read the guide
cat SESSION4_QUICK_START.md

# 3. Edit universal_parser.py to add [TRACE] output
# (See SESSION4_QUICK_START.md for exact edits)
```

### Phase 2: Deploy
```bash
# 1. Rebuild with tracing
docker build -t ajacobm/codenav:sse --target sse .

# 2. Start fresh deployment
docker-compose -f docker-compose-multi.yml down -v
docker-compose -f docker-compose-multi.yml up -d

# 3. Wait for container to start
sleep 5
```

### Phase 3: Monitor
```bash
# Terminal 1: Watch all logs
cd /mnt/c/Users/ADAM/GitHub/codenav
docker-compose -f docker-compose-multi.yml logs -f code-graph-codegraphmcp-sse

# Terminal 2: Check health
curl http://localhost:10101/health

# Terminal 3: Trigger analysis (after health check passes)
curl -s http://localhost:10101/analyze 2>&1 | head -100
```

### Phase 4: Analyze Output
```bash
# Filter just TRACE lines
docker-compose -f docker-graph-mcp.yml logs code-graph-codegraphmcp-sse | grep TRACE

# Or save to file for detailed analysis
docker-compose -f docker-compose-multi.yml logs > /tmp/code-graph-logs.txt
grep TRACE /tmp/code-graph-logs.txt > /tmp/trace-output.txt
cat /tmp/trace-output.txt
```

---

## 🛠️ Code Editing

### Files to Edit

**Main parsing logic**:
```bash
# Edit this file to add [TRACE] output
nano /mnt/c/Users/ADAM/GitHub/codenav/src/codenav/universal_parser.py
```

**Key functions to trace**:
- `_parse_file_content` (line ~1011)
- `_parse_functions_ast` (line ~654)
- `_parse_classes_ast` (line ~718)
- `_parse_imports_ast` (line ~784)

**Quick edit pattern**:
```bash
# Replace logger.debug() with print()
sed -i 's/logger\.debug(/print(f"[DEBUG] {/g' universal_parser.py

# Add [TRACE] prefix to key lines
```

---

## 📊 Local Testing (Before Container)

### Test ast-grep-py directly
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav

# Start Python
python

# Run test
from ast_grep_py import SgRoot
code = "def hello(): pass\ndef world(): pass"
sg = SgRoot(code, 'python')
root = sg.root()
functions = list(root.find_all({"rule": {"kind": "function_definition"}}))
print(f"Found {len(functions)} functions")
# Expected: Found 2 functions

# Test with real file
with open('src/codenav/universal_parser.py', 'r') as f:
    code = f.read()
sg = SgRoot(code, 'python')
root = sg.root()
functions = list(root.find_all({"rule": {"kind": "function_definition"}}))
print(f"Found {len(functions)} functions in universal_parser.py")
# Expected: Found 30+ functions
```

---

## 🎯 Success Indicators

### Good Signs
- ✅ No file watcher error in logs
- ✅ Redis connection successful
- ✅ HTTP server starts on 0.0.0.0:8000
- ✅ Health check returns 200 OK
- ✅ [TRACE] output appears in logs
- ✅ TRACE output shows functions found > 0

### Bad Signs
- ❌ "Failed to start file watcher" error
- ❌ "Redis connection failed"
- ❌ HTTP server fails to start
- ❌ Health check returns error
- ❌ No [TRACE] output (method not called)
- ❌ "Analysis complete: 0 nodes, 0 relationships"

---

## 🔄 Iterate Quickly

**Once you identify the issue**, the fix should be quick:

### Issue: parse_functions_ast not called
- Fix: Add tracing to _parse_file_content to see what happens before
- Test: ~2 minutes

### Issue: sg_root.root() fails
- Fix: Add error handling, test with simpler code
- Test: ~5 minutes

### Issue: find_all returns empty
- Fix: Verify pattern name, test locally with sg_root
- Test: ~5 minutes

### Issue: Nodes created but not in graph
- Fix: Check graph.add_node() implementation, verify no exceptions
- Test: ~10 minutes

---

## 📚 Reference Files

| File | Purpose |
|------|---------|
| `SESSION3_COMPREHENSIVE_SUMMARY.md` | Full investigation (350+ lines) |
| `SESSION4_QUICK_START.md` | Step-by-step tracing guide |
| `src/codenav/universal_parser.py` | Main file to edit |
| `docker-compose-multi.yml` | Deployment config |
| `Dockerfile` | Container build |

---

## 🚀 Expected Outcome

After adding tracing and following the debugging workflow:

**Before**:
```
Analysis complete: 0 nodes, 0 relationships
```

**After (when working)**:
```
[TRACE] _parse_functions_ast found 32 functions
[TRACE] _parse_classes_ast found 4 classes
[TRACE] _parse_imports_ast found 6 imports
Analysis complete: 42 nodes, 45 relationships
```

---

## ⏱️ Time Estimate

- Tracing implementation: 10 minutes
- Rebuild + deploy: 5 minutes
- Initial log review: 5 minutes
- Issue identification: 10-30 minutes
- Fix implementation: 5-30 minutes (depends on issue)

**Total**: 30-80 minutes to complete fix

---

**Ready to debug? Start with `SESSION4_QUICK_START.md` for detailed instructions!** 🎯
