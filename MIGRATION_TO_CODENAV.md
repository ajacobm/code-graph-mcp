# Migration Plan: code-graph-mcp → CodeNavigator

## Executive Summary

This document outlines the comprehensive migration plan for renaming the **code-graph-mcp** project to **CodeNavigator**. The migration will preserve git history and can be performed in-situ on the current repository.

## Naming Strategy

### Project Names
- **Display Name**: `CodeNavigator`
- **Python Package**: `codenav` (Pythonic, concise, baseline name)

**Confirmed**: Use `codenav` for brevity and Pythonic style, similar to popular packages like `pytest`, `numpy`, `pandas`.

### Package Architecture

The project consists of multiple components that can be packaged as optional extras:

1. **Core Analyzer** (`codenav`) - Base package with code analysis engine
   - Universal AST parsing
   - Graph construction
   - Analysis algorithms
   - Core utilities

2. **MCP Runtime Options**:
   - `codenav[mcp-stdio]` - MCP server with stdio transport
   - `codenav[mcp-http]` - MCP server with streamableHttp transport
   - `codenav[mcp]` - All MCP runtime options

3. **Web Components**:
   - `codenav[web]` - HTTP REST API server for frontend
   - `codenav[notebooks]` - Jupyter notebook support and utilities

4. **Development & Testing**:
   - `codenav[dev]` - Development dependencies
   - `codenav[test]` - Testing dependencies

5. **Full Installation**:
   - `codenav[all]` - All components and dependencies

### Command Line Tools
- Current: `code-graph-mcp`, `code-graph-sse`
- New: 
  - `codenav` - Main MCP server entry point (replaces `code-graph-mcp`)
  - `codenav-web` - HTTP REST API server (replaces http_server module)
  - Runtime selection via CLI flags: `--runtime stdio` or `--runtime http`

**Note**: The term "SSE" is outdated. The MCP protocol supports `stdio` and `streamableHttp` transports.

### Docker Images
- Current: `ghcr.io/ajacobm/code-graph-mcp`
- New: `ghcr.io/ajacobm/codenav`

### Repository
- Current: `ajacobm/code-graph-mcp`
- New: Rename to `ajacobm/codenav`

**Note**: GitHub repository renames preserve git history and automatically redirect old URLs to new ones.

## Project Architecture

### Current Structure

The CodeNavigator project consists of multiple interconnected components:

1. **Core Analyzer** (`src/code_graph_mcp/`)
   - Universal AST parsing and analysis
   - Graph construction algorithms
   - Language detection and routing
   - Code metrics and complexity analysis
   - Reusable by all other components

2. **MCP Server** (`server.py`, `sse_server.py`)
   - Model Context Protocol implementation
   - Two transport modes:
     - `stdio` - Standard input/output (default for Claude Desktop, Cline, etc.)
     - `streamableHttp` - HTTP streaming (for web-based clients)
   - Currently accessed via `code-graph-mcp` and `code-graph-sse` commands

3. **Web API** (`http_server.py`)
   - REST API for frontend application
   - Independent from MCP server
   - Uses core analyzer engine
   - Currently accessed as Python module

4. **Frontend Application** (`frontend/`)
   - Vue.js web interface
   - Visualizes code graphs and analysis results
   - Communicates with Web API
   - Can be hosted alongside notebooks

5. **Jupyter Notebooks** (`notebooks/`)
   - Interactive analysis and exploration
   - Graph visualization examples
   - Architectural pattern detection
   - May be hosted alongside frontend

6. **Tests** (`tests/`)
   - Unit and integration tests
   - Test infrastructure for all components

7. **Future Components**:
   - Interactive CLI (planned)
   - Additional visualization tools

### Component Dependencies

```
Core Analyzer (codenav base)
    ├── MCP Server (codenav[mcp])
    │   ├── stdio transport (codenav[mcp-stdio])
    │   └── streamableHttp transport (codenav[mcp-http])
    ├── Web API (codenav[web])
    ├── Notebooks (codenav[notebooks])
    └── Future CLI (codenav[cli])

Frontend (separate repo or subproject)
    └── Connects to Web API

All Components (codenav[all])
```

### Package Extras Implementation

The Python package will support optional extras following standard conventions:

```bash
# Base analyzer only
pip install codenav

# MCP server with stdio (most common)
pip install codenav[mcp-stdio]

# MCP server with HTTP streaming
pip install codenav[mcp-http]

# All MCP options
pip install codenav[mcp]

# Web API server
pip install codenav[web]

# Jupyter notebooks
pip install codenav[notebooks]

# Development
pip install codenav[dev]

# Everything
pip install codenav[all]
```

This architecture allows users to install only what they need, keeping dependencies minimal for specific use cases.

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

**Main Updates**:
- `[project]` → `name = "codenav"`
- Package path in `[tool.hatch.build.targets.wheel]` → `packages = ["src/codenav"]`
- Entry points:
  - `code-graph-mcp` → `codenav` (maps to `codenav:main`)
  - `code-graph-sse` → remove (outdated, functionality merged into `codenav`)
  - Add `codenav-web` for HTTP REST API (maps to `codenav.http_server:main`)
- URLs (update to `ajacobm/codenav`)
- Description text

**Optional Dependencies Structure**:

```toml
[project.optional-dependencies]
# MCP server with stdio transport (most common, minimal deps)
mcp-stdio = [
    "mcp>=1.12.2",
    "anyio>=4.0.0",
    "click>=8.0.0",
]

# MCP server with streamableHttp transport
mcp-http = [
    "mcp>=1.12.2",
    "anyio>=4.0.0", 
    "click>=8.0.0",
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sse-starlette>=2.0.0",
]

# All MCP options
mcp = [
    "codenav[mcp-stdio]",
    "codenav[mcp-http]",
]

# Web REST API server
web = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "httpx>=0.24.0",
]

# Jupyter notebook support
notebooks = [
    "jupyter>=1.0.0",
    "ipykernel>=6.0.0",
    "matplotlib>=3.7.0",
    "pandas>=2.0.0",
]

# Development dependencies
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

# Testing dependencies
test = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.23.0",
]

# Everything
all = [
    "codenav[mcp]",
    "codenav[web]",
    "codenav[notebooks]",
    "codenav[dev]",
]
```

**Base Dependencies** (always installed):
- Core analysis engine dependencies (ast-grep-py, rustworkx, networkx, etc.)
- Redis cache support
- Graph database support (neo4j)
- File watching (watchdog)
- Pattern matching (pathspec)

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

#### 7.3 Package Distribution
**Note**: PyPI publishing will be deferred until the project is ready for public release. For now:
1. Package can be installed locally or from git
2. Docker images will be the primary distribution method
3. Future PyPI publication will happen when project reaches 1.0.0

### Phase 8: Testing and Validation

#### 8.1 Unit Tests
- Run full test suite: `pytest tests/`
- Verify all imports work
- Check test discovery works
- Verify no references to old names

#### 8.2 Integration Tests
- Test CLI commands: `codenav --help`
- Test MCP server with stdio: `codenav --runtime stdio`
- Test MCP server with HTTP: `codenav --runtime http`
- Test Web API: `codenav-web`
- Test Docker images
- Test MCP client integration (Claude Desktop, Cline, etc.)
- Test optional extras installation

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
4. Publish Docker images to GHCR
5. Update documentation site

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

1. **Remove upstream remote** - Can be done directly: `git remote remove upstream` (if it exists)
2. **Optional**: Remove fork relationship in GitHub UI:
   - Settings → General → "This is a fork" section
   - Note: For public repositories, you can manage the fork relationship yourself through Settings
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

1. Simply revert commits using git
2. Rebuild and republish Docker images if needed
3. Document issues in CHANGELOG

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

### High Risk
- None identified - This is a straightforward rename operation

## Success Criteria

✅ All tests pass with new package name
✅ CLI commands work:
  - `codenav --help`
  - `codenav --runtime stdio`
  - `codenav --runtime http`
  - `codenav-web`
✅ Package installs correctly from source:
  - Base: `pip install -e .`
  - With extras: `pip install -e ".[mcp-stdio]"`, `pip install -e ".[all]"`, etc.
✅ Optional dependencies properly separated
✅ Docker images build and run
✅ Git history is preserved and followable
✅ Documentation is complete and accurate
✅ No references to old package name
✅ Frontend and notebooks still function with renamed package

## Post-Migration Tasks

1. Update Docker images on GHCR with new names
2. Monitor for issues
3. Update any external references (if needed)

**Note**: 
- PyPI publishing will be deferred until the project is ready for public release.
- No public migration announcement needed (private project).

## Confirmed Decisions

All key decisions have been finalized:

1. **Package Name**: `codenav` ✓
   - Baseline name for all components
   - Pythonic, concise, memorable

2. **Package Architecture**: Optional extras pattern ✓
   - `codenav` - Core analyzer (base)
   - `codenav[mcp-stdio]` - MCP with stdio transport
   - `codenav[mcp-http]` - MCP with streamableHttp transport  
   - `codenav[mcp]` - All MCP options
   - `codenav[web]` - HTTP REST API
   - `codenav[notebooks]` - Jupyter support
   - `codenav[all]` - Everything

3. **Repository Rename**: `ajacobm/codenav` ✓
   - GitHub will automatically redirect old URLs
   - Maintains full consistency across all assets

4. **Docker Naming**: `ghcr.io/ajacobm/codenav` ✓
   - Remove old `code-graph-mcp` images
   - No transition period needed

5. **Version**: Reset to `0.5.0` ✓
   - Project is still in alpha/preview stage
   - Semver can reset with the rename
   - Will reach 1.0.0 when ready for public release

6. **Distribution**: Docker images primary, no PyPI until 1.0 ✓

7. **Visibility**: Private project, no public announcements ✓

## Notes

- Git history will be preserved through the rename
- GitHub automatically redirects old repository URLs
- The project is self-contained; upstream fork is irrelevant
- All changes can be made in-situ on current repository
- Changes should be made in a branch off main as requested
