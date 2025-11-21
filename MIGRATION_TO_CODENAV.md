# Migration Plan: code-graph-mcp → CodeNavigator

## Executive Summary

This document outlines the comprehensive migration plan for renaming the **code-graph-mcp** project to **CodeNavigator**. The migration will preserve git history and can be performed in-situ on the current repository.

## Naming Strategy

### Project Names
- **Display Name**: `CodeNavigator`
- **Python Package**: `codenav` (Pythonic, concise)
- **Alternative**: `code_navigator` (more explicit)

**Recommendation**: Use `codenav` for brevity and Pythonic style, similar to popular packages like `pytest`, `numpy`, `pandas`.

### Command Line Tools
- Current: `code-graph-mcp`, `code-graph-sse`
- New: `codenav`, `codenav-sse`

### Docker Images
- Current: `ghcr.io/ajacobm/code-graph-mcp`
- New: `ghcr.io/ajacobm/codenav`

### Repository
- Current: `ajacobm/code-graph-mcp`
- New: Keep as `ajacobm/code-graph-mcp` OR rename to `ajacobm/codenav`

**Note**: GitHub repository renames preserve git history and automatically redirect old URLs to new ones.

## Migration Phases

### Phase 1: Preparation and Documentation ✓
- [x] Create comprehensive migration document
- [x] Review current codebase structure
- [x] Identify all files requiring changes
- [x] Establish naming conventions

### Phase 2: Python Package Renaming

#### 2.1 Directory Structure Changes
```
src/code_graph_mcp/ → src/codenav/
```

Files affected:
- All Python files in `src/code_graph_mcp/`
- All test files in `tests/`
- All documentation

#### 2.2 Import Statement Updates
Update all Python imports:
```python
# OLD
from code_graph_mcp import ...
from code_graph_mcp.server import ...
import code_graph_mcp

# NEW
from codenav import ...
from codenav.server import ...
import codenav
```

Files requiring import updates:
- `src/code_graph_mcp/**/*.py` (all Python files)
- `tests/**/*.py` (all test files)
- Any scripts or example files

### Phase 3: Configuration Files

#### 3.1 pyproject.toml
Update:
- `[project]` → `name = "codenav"`
- Package path in `[tool.hatch.build.targets.wheel]`
- Entry points: `code-graph-mcp` → `codenav`
- Entry points: `code-graph-sse` → `codenav-sse`
- URLs (if repository is renamed)
- Description text

#### 3.2 package.json (Frontend)
Update:
- Package name references (if any)
- Documentation links

#### 3.3 Docker Configuration
Update `Dockerfile`:
- Command references: `code-graph-mcp` → `codenav`
- Package installation commands
- Environment variable names (if needed)
- Comments and documentation

#### 3.4 Docker Compose Files
Files to update:
- `infrastructure/docker-compose.yml`
- All profile files in `infrastructure/profiles/`

Changes:
- Service names (optional, for clarity)
- Image names (if rebuilding)
- Command references
- Environment variables
- Volume names (optional)

### Phase 4: GitHub Configuration

#### 4.1 GitHub Workflows
Update `.github/workflows/`:
- `docker-publish.yml` - Image names and references
- `test.yml` - Command references and test execution
- `deploy-pages.yml` - Documentation references

#### 4.2 GitHub Issues Templates
Update any issue templates with new project name.

#### 4.3 Repository Settings
If renaming repository:
1. Go to Settings → General → Repository name
2. Change from `code-graph-mcp` to `codenav`
3. GitHub automatically handles redirects

### Phase 5: Documentation

#### 5.1 README.md
Update:
- Project title and headers
- Installation commands: `pip install codenav`
- CLI commands: `codenav` instead of `code-graph-mcp`
- MCP configuration examples
- Docker image references
- All URLs (if repository renamed)
- Badge URLs (if any)

#### 5.2 Other Documentation
Files to update:
- `CHANGELOG.md`
- `PLANNING.md`
- `CURRENT_STATE.md`
- All files in `docs/` directory
- `SESSION_*.md` files
- Markdown files in root

#### 5.3 Code Comments
Search and replace in all source files:
- "code-graph-mcp" → "codenav" or "CodeNavigator"
- "Code Graph MCP" → "CodeNavigator"

### Phase 6: Scripts and Tools

#### 6.1 Shell Scripts
Update `scripts/`:
- `dev-server.sh`
- `codespaces-redis.sh`
- `setup-ghcr.sh`
- `test-codespaces.sh`

#### 6.2 Makefile
Update:
- Comments and help text
- Any hardcoded references
- Service names in docker-compose commands

#### 6.3 Configuration Files
- `.mcp.json`
- `.graphignore.example`
- `.devcontainer/devcontainer.json`
- Any other config files

### Phase 7: Build and Distribution

#### 7.1 Build Configuration
- Verify `pyproject.toml` package metadata
- Update `uv.lock` if needed
- Verify entry points work correctly

#### 7.2 Docker Images
- Rebuild all Docker images with new names
- Tag appropriately
- Push to GHCR with new names
- Optionally maintain old names as aliases temporarily

#### 7.3 PyPI Package
When ready to publish:
1. Register new package name on PyPI: `codenav`
2. Update version to indicate major change (e.g., 2.0.0)
3. Publish to PyPI
4. Consider deprecation notice on old package

### Phase 8: Testing and Validation

#### 8.1 Unit Tests
- Run full test suite: `pytest tests/`
- Verify all imports work
- Check test discovery works
- Verify no references to old names

#### 8.2 Integration Tests
- Test CLI commands: `codenav --help`
- Test SSE server: `codenav-sse`
- Test Docker images
- Test MCP client integration

#### 8.3 Documentation Tests
- Verify all documentation links work
- Test installation instructions
- Verify Docker commands work
- Check GitHub redirects (if renamed)

### Phase 9: Deployment

#### 9.1 Version Bump
Update to major version (2.0.0) to indicate breaking change:
- `pyproject.toml` version
- `__init__.py` __version__
- `CHANGELOG.md` entry

#### 9.2 Release Process
1. Create release branch
2. Merge to main
3. Create GitHub release
4. Publish to PyPI
5. Publish Docker images
6. Update documentation site

#### 9.3 Communication
- Update project description on GitHub
- Announce on relevant channels
- Update any listings or registries
- Add migration guide for users

### Phase 10: Cleanup and Maintenance

#### 10.1 Deprecation Period (Optional)
- Maintain old package name as alias for transition period
- Add deprecation warnings
- Document migration path for users

#### 10.2 Archive Old References
- Archive old documentation
- Maintain redirect notes
- Keep migration guide accessible

## Git History Preservation

### Strategy
All changes will be made through normal git commits. Git automatically tracks:
- File renames (using `git mv`)
- Content changes within renamed files
- History follows renamed files

### Recommended Approach
1. Make all changes in a feature branch off `main`
2. Use atomic commits for each phase
3. Use descriptive commit messages
4. Git will preserve history through the rename

### Verification
After migration, verify history preservation:
```bash
# Check file history after rename
git log --follow src/codenav/__init__.py

# Compare with old path
git log --follow src/code_graph_mcp/__init__.py
```

## Upstream Fork Divergence

Since the project has completely diverged from the upstream fork:

1. **No action needed** - Just continue development on current repository
2. **Optional**: Remove fork relationship in GitHub UI:
   - Settings → General → "This is a fork" section
   - Contact GitHub support to detach fork if needed
3. The git history is independent and will be preserved

## File-by-File Checklist

### Python Source Files (src/)
- [ ] `src/code_graph_mcp/__init__.py` → `src/codenav/__init__.py`
- [ ] `src/code_graph_mcp/server.py` → `src/codenav/server.py`
- [ ] `src/code_graph_mcp/sse_server.py` → `src/codenav/sse_server.py`
- [ ] All other `.py` files in package
- [ ] Update all internal imports

### Test Files (tests/)
- [ ] Update imports in all `test_*.py` files
- [ ] Verify test discovery still works
- [ ] Update any test data or fixtures

### Configuration Files
- [ ] `pyproject.toml`
- [ ] `package.json`
- [ ] `Dockerfile`
- [ ] `.mcp.json`
- [ ] `pytest.ini`
- [ ] `.ruff.toml`
- [ ] `.devcontainer/devcontainer.json`
- [ ] `uv.lock` (regenerate)

### Docker & Infrastructure
- [ ] `infrastructure/docker-compose.yml`
- [ ] All files in `infrastructure/profiles/`
- [ ] Docker image tags in workflows

### GitHub Workflows
- [ ] `.github/workflows/docker-publish.yml`
- [ ] `.github/workflows/test.yml`
- [ ] `.github/workflows/deploy-pages.yml`

### Scripts
- [ ] `scripts/dev-server.sh`
- [ ] `scripts/codespaces-redis.sh`
- [ ] `scripts/setup-ghcr.sh`
- [ ] `scripts/test-codespaces.sh`
- [ ] `start-dev.sh`

### Build & Development
- [ ] `Makefile`

### Documentation
- [ ] `README.md`
- [ ] `CHANGELOG.md`
- [ ] `PLANNING.md`
- [ ] `CURRENT_STATE.md`
- [ ] All `docs/**/*.md` files
- [ ] All `SESSION_*.md` files
- [ ] `LICENSE` (verify author info)

### Examples & Config Templates
- [ ] `.graphignore.example`
- [ ] Any example configuration files

## Rollback Plan

If issues arise during migration:

1. **Before PyPI publish**: Simply revert commits
2. **After PyPI publish**: 
   - Cannot unpublish from PyPI
   - Publish fix version immediately
   - Document issues in CHANGELOG

## Timeline Estimate

- **Preparation**: 1-2 hours (complete)
- **Code Changes**: 2-4 hours
- **Testing**: 2-3 hours
- **Documentation**: 1-2 hours
- **Deployment**: 1 hour
- **Total**: ~8-12 hours

## Risk Assessment

### Low Risk
- File/directory renames - Git handles well
- Import updates - Systematic and testable
- Documentation updates - No functional impact

### Medium Risk
- Docker image publishing - Can be tested before production
- PyPI publishing - Cannot be undone, but can publish fixes

### High Risk
- None identified - This is a straightforward rename operation

## Success Criteria

✅ All tests pass with new package name
✅ CLI commands work: `codenav --help`
✅ Package installs correctly: `pip install codenav`
✅ Docker images build and run
✅ Git history is preserved and followable
✅ Documentation is complete and accurate
✅ No references to old package name (except in deprecation notices)

## Post-Migration Tasks

1. Update package on PyPI
2. Update Docker images on GHCR
3. Announce migration
4. Monitor for issues
5. Update any external references
6. Archive old package (with redirect/deprecation)

## Questions for Consideration

1. **Package Name**: Prefer `codenav` or `code_navigator`?
   - Recommendation: `codenav` (shorter, Pythonic)

2. **Repository Rename**: Rename GitHub repo from `code-graph-mcp` to `codenav`?
   - Pros: Consistency across all assets
   - Cons: Breaks some external links (though GitHub redirects)
   - Recommendation: Yes, rename for consistency

3. **Docker Naming**: Keep `code-graph-mcp` images as aliases?
   - Recommendation: Publish both for transition period

4. **Version Bump**: Use 2.0.0 to indicate breaking change?
   - Recommendation: Yes, follows semver

5. **Deprecation Period**: How long to maintain old package on PyPI?
   - Recommendation: 6-12 months with deprecation warnings

## Notes

- Git history will be preserved through the rename
- GitHub automatically redirects old repository URLs
- The project is self-contained; upstream fork is irrelevant
- All changes can be made in-situ on current repository
- Changes should be made in a branch off main as requested
