# CodeNavigator - Session 4 Quick Start Guide

## 🎯 Your Mission (If You Choose to Accept It)

The CodeNavigator project has all fixes in place BUT graph nodes still aren't being created. Your job: **Add tracing output to find where the code is failing**.

## ⚡ Quick Facts

- ✅ All library APIs verified working (local tests found 32 functions, 4 classes, 6 imports)
- ✅ All 25 language patterns defined
- ✅ AST-Grep integration complete
- ✅ Iterator bug fixed
- ❌ But container still produces 0 nodes
- 🔍 Root cause: Unknown (likely debug logs suppressed or exception hidden)

## 🚀 3-Step Fix Plan

### Step 1: Add Tracing (10 minutes)

Edit `src/codenav/universal_parser.py`

**Find**: `def _parse_functions_ast(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> int:`

**Replace** the function with tracing version:

```python
def _parse_functions_ast(self, sg_root: Any, file_path: Path, language_config: LanguageConfig) -> int:
    """Parse functions using AST-Grep queries with TRACING for debugging."""
    count = 0
    print(f"[TRACE] _parse_functions_ast START: file={file_path.name}")
    try:
        pattern = ASTGrepPatterns.get_pattern(language_config.ast_grep_id, "function")
        print(f"[TRACE] pattern='{pattern}' for lang={language_config.ast_grep_id}")
        if pattern:
            try:
                print(f"[TRACE] calling sg_root.root()...")
                root_node = sg_root.root()
                print(f"[TRACE] sg_root.root() succeeded")
                print(f"[TRACE] calling find_all with query...")
                functions = list(root_node.find_all({"rule": {"kind": pattern}}))
                print(f"[TRACE] find_all returned {len(functions)} functions")
                
                for func_node in functions:
                    try:
                        func_name = self._extract_name_from_ast(func_node, language_config)
                        print(f"[TRACE]   Extracted name: {func_name}")
                        if not func_name:
                            print(f"[TRACE]   Skipping: name extraction failed")
                            continue
                        
                        start_pos = func_node.start()
                        end_pos = func_node.end()
                        start_line = start_pos.line
                        end_line = end_pos.line
                        
                        node = UniversalNode(
                            id=f"function:{file_path}:{func_name}:{start_line}",
                            name=func_name,
                            node_type=NodeType.FUNCTION,
                            location=UniversalLocation(
                                file_path=str(file_path),
                                start_line=start_line,
                                end_line=end_line,
                                language=language_config.name
                            ),
                            language=language_config.name,
                            complexity=self._calculate_complexity_from_ast(func_node),
                            metadata={"ast_pattern": pattern}
                        )
                        print(f"[TRACE]   Node created: {node.id}")
                        
                        print(f"[TRACE]   Calling graph.add_node()...")
                        self.graph.add_node(node)
                        print(f"[TRACE]   Node successfully added to graph")
                        
                        rel = UniversalRelationship(
                            id=f"contains:{file_path}:{node.id}",
                            source_id=f"file:{file_path}",
                            target_id=node.id,
                            relationship_type=RelationshipType.CONTAINS
                        )
                        print(f"[TRACE]   Adding relationship...")
                        self.graph.add_relationship(rel)
                        print(f"[TRACE]   Relationship added")
                        
                        count += 1
                        
                    except Exception as e:
                        print(f"[TRACE]   ERROR processing function node: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                        
            except Exception as e:
                print(f"[TRACE] ERROR querying functions: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[TRACE] No pattern found for {language_config.ast_grep_id}")
        
        print(f"[TRACE] _parse_functions_ast END: found {count} functions")
        
    except Exception as e:
        print(f"[TRACE] OUTER EXCEPTION in _parse_functions_ast: {e}")
        import traceback
        traceback.print_exc()
    
    return count
```

**Do the same for `_parse_classes_ast` and `_parse_imports_ast`**:
- Replace "functions" with "classes" or "imports"
- Replace "FUNCTION" node type with "CLASS" or "IMPORT"
- Adjust name extraction accordingly

### Step 2: Rebuild & Deploy (5 minutes)

```bash
cd /mnt/c/Users/ADAM/GitHub/codenav

# Clean rebuild
docker build -t ajacobm/codenav:sse --target sse .

# Deploy fresh
docker-compose -f docker-compose-multi.yml down -v
docker-compose -f docker-compose-multi.yml up

# In another terminal, watch logs
docker-compose -f docker-compose-multi.yml logs -f code-graph-codegraphmcp-sse
```

### Step 3: Analyze & Fix (15-60 minutes)

**Look for [TRACE] output in logs**

**If you see**:
```
[TRACE] _parse_functions_ast START: file=example.py
[TRACE] pattern='function_definition' for lang=python
[TRACE] calling sg_root.root()...
[TRACE] sg_root.root() succeeded
[TRACE] calling find_all with query...
[TRACE] find_all returned 32 functions
[TRACE]   Extracted name: hello
[TRACE]   Node created: function:...
[TRACE]   Calling graph.add_node()...
[TRACE] _parse_functions_ast END: found 32 functions
```

→ **GOOD!** Graph.add_node() is working. Issue is somewhere else (maybe cache manager or graph persistence).

---

**If you see**:
```
[TRACE] _parse_functions_ast START: file=example.py
[TRACE] pattern='function_definition' for lang=python
[TRACE] calling sg_root.root()...
[TRACE] sg_root.root() succeeded
[TRACE] calling find_all with query...
[TRACE] find_all returned 0 functions
[TRACE] _parse_functions_ast END: found 0 functions
```

→ **Pattern query returning empty.** Check:
- Is language_config.ast_grep_id correct?
- Is pattern name correct for that language?
- Test locally: `sg.root().find_all({"rule": {"kind": "function_definition"}})` 

---

**If you see**:
```
[TRACE] _parse_functions_ast START: file=example.py
[TRACE] pattern='function_definition' for lang=python
[TRACE] calling sg_root.root()...
ERROR: ... traceback ...
```

→ **sg_root.root() is failing.** Check:
- Is SgRoot created correctly?
- Is content properly encoded?
- Run local test to confirm ast-grep-py works

---

**If you DON'T see any [TRACE] output**:

→ **Method not being called at all.** Check:
- Is _parse_file_content being called?
- Are there exceptions before reaching _parse_functions_ast?
- Add tracing to _parse_file_content earlier in the flow

## 📊 What the Stats Tell You

After fix, you should see in logs:
```
Found X functions in file.py using AST-Grep
Found Y classes in file.py using AST-Grep
Found Z imports in file.py using AST-Grep
Analysis complete: N nodes, M relationships
```

Instead of the current:
```
Analysis complete: 0 nodes, 0 relationships
```

## 🎓 Key Learning

This investigation revealed an important pattern:
- Just because your library works doesn't mean integration works
- Silent exception handling makes debugging harder
- Logging levels can hide critical information
- Always add tracing when you have "mysterious" bugs

## 🏁 Success Criteria

Session 4 is successful when:
1. ✅ You see [TRACE] output with detailed execution path
2. ✅ You identify exact failure point
3. ✅ Container logs show non-zero node counts
4. ✅ Graph now has function/class/import nodes

## 📖 Full Documentation

For complete context, read: `SESSION3_COMPREHENSIVE_SUMMARY.md`

## 💡 Pro Tips

- Test locally first: `cd /mnt/c/Users/ADAM/GitHub/codenav && uv run`
- Keep one terminal watching logs while you make changes
- Use grep to filter logs: `docker-compose ... logs | grep TRACE`
- Commit your tracing code - it helps future debugging

---

**You've got this! The fix is close - just need visibility into the execution flow.** 🚀
