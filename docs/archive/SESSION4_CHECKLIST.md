# Session 4 Pre-Flight Checklist

## Before You Start Debugging

- [ ] Read MASTER_SUMMARY.md (executive overview - 5 min)
- [ ] Read SESSION4_QUICK_START.md (step-by-step guide - 10 min)
- [ ] Have READY_COMMANDS.md open in a window (reference)
- [ ] Set up two terminals ready to use

## Code Changes Verification

- [ ] Verify universal_parser.py has ASTGrepPatterns class (lines 607-619)
- [ ] Verify _parse_functions_ast has correct AST API (line ~664)
- [ ] Verify _parse_classes_ast has correct AST API (line ~728)
- [ ] Verify _parse_imports_ast has correct AST API (line ~798)
- [ ] Verify file_watcher.py has ignore_patterns removed

Quick check:
```bash
grep -n "class ASTGrepPatterns" src/codenav/universal_parser.py
grep -n "list(root_node.find_all" src/codenav/universal_parser.py
```

Should show 3 results for list() conversion.

## Container Readiness

- [ ] Docker installed and running
- [ ] docker-compose installed
- [ ] Port 10101 available (or change in docker-compose-multi.yml)
- [ ] Redis running (docker-compose starts it)
- [ ] Previous containers stopped: `docker-compose -f docker-compose-multi.yml down`

## Documentation Review

- [ ] Understand the [TRACE] output approach
- [ ] Know the 4 key functions to trace
- [ ] Have expected output patterns memorized
- [ ] Know what each log output means

## Terminal Setup

### Terminal 1: Build & Deploy
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
# Will run build and deploy commands here
```

### Terminal 2: Monitor Logs
```bash
cd /mnt/c/Users/ADAM/GitHub/codenav
# Will run: docker-compose -f docker-compose-multi.yml logs -f
```

### Terminal 3: Testing (Optional)
```bash
# For manual tests and health checks
curl http://localhost:10101/health
```

## Key Files Ready

- [ ] SESSION4_QUICK_START.md in text editor
- [ ] READY_COMMANDS.md bookmarked or printed
- [ ] universal_parser.py open for editing
- [ ] docker-compose-multi.yml reviewed

## Expected Sequence

1. **Add tracing** (Terminal 1)
   - Edit universal_parser.py
   - Add [TRACE] print statements
   - 3 functions to modify

2. **Build** (Terminal 1)
   - `docker build -t ajacobm/codenav:sse --target sse .`
   - Takes ~2-3 minutes

3. **Deploy** (Terminal 1)
   - `docker-compose -f docker-compose-multi.yml down -v`
   - `docker-compose -f docker-compose-multi.yml up`

4. **Monitor** (Terminal 2)
   - `docker-compose -f docker-compose-multi.yml logs -f`
   - Watch for [TRACE] output

5. **Test** (Terminal 3)
   - `curl http://localhost:10101/health`
   - Check for TRACE output in logs

6. **Analyze**
   - Look for where execution stops
   - Reference SESSION4_QUICK_START.md for interpretation

7. **Fix**
   - Based on findings
   - Rebuild and test

## Success Criteria

### Minimum Success
- ✅ [TRACE] output appears in logs
- ✅ Can identify where code stops

### Full Success
- ✅ Graph shows 40+ nodes
- ✅ Functions, classes, imports all populated
- ✅ "Analysis complete: X nodes" shows correct count

## Failure Modes & Workarounds

**If container won't start:**
```bash
docker-compose -f docker-compose-multi.yml logs
# Look for error messages
# Common: port already in use, image pull failure
```

**If logs show no output:**
```bash
# Container might be stuck. Try:
docker-compose -f docker-compose-multi.yml down -v
docker-compose -f docker-compose-multi.yml up --build
```

**If [TRACE] output doesn't appear:**
- Check if print() was actually added
- Verify indentation is correct
- Try: `echo "test" | docker-compose ... logs | grep test`

**If graph still 0 nodes after tracing:**
- Look for exception tracebacks
- Check if self.graph.add_node() is being called
- Verify no exceptions in exception handlers

## Time Tracking

Start time: ___________

- Build: 2-3 min
- Deploy: 1-2 min
- Initial test: 1 min
- Log analysis: 30-60 min
- Fix: 5-30 min
- Final test: 2-5 min

End time: ___________

Total time: ___________

## Notes Section

Use this space for discoveries during debugging:

```
Issue identified:
_________________________________________________________________________

Root cause:
_________________________________________________________________________

Solution implemented:
_________________________________________________________________________

Test result:
_________________________________________________________________________

Time spent:
_________________________________________________________________________
```

## Resources

📚 Documentation:
- MASTER_SUMMARY.md - Overview
- SESSION4_QUICK_START.md - Step-by-step
- SESSION3_COMPREHENSIVE_SUMMARY.md - Deep dive
- READY_COMMANDS.md - Command reference

💾 Code:
- src/codenav/universal_parser.py - Main file to edit
- src/codenav/file_watcher.py - Already fixed
- docker-compose-multi.yml - Deployment config
- Dockerfile - Container definition

🎯 Quick Commands:
```bash
# Build
docker build -t ajacobm/codenav:sse --target sse .

# Deploy fresh
docker-compose -f docker-compose-multi.yml down -v && docker-compose -f docker-compose-multi.yml up

# Watch logs
docker-compose -f docker-compose-multi.yml logs -f code-graph-codegraphmcp-sse

# Filter TRACE
docker-compose -f docker-compose-multi.yml logs code-graph-codegraphmcp-sse | grep TRACE

# Health check
curl http://localhost:10101/health
```

## Final Thoughts

This is the last piece. All the hard investigation work is done. Now you just need to add visibility (tracing), identify the issue, and fix it. Should be straightforward once you can see what's happening.

Good luck! 🚀

---

✅ Ready to begin Session 4? Start with reading MASTER_SUMMARY.md, then SESSION4_QUICK_START.md!
