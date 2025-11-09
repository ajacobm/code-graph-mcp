# Playwright Testing Guide - Frontend Development Strategy

**Strategy**: Test-driven development with Playwright as the foundation for all frontend work.

**Commitment**: Write Playwright tests BEFORE implementing features throughout all UI development sessions.

---

## Why Playwright-First Development?

### Benefits
1. **Automated Regression Testing** - Catch bugs before manual testing
2. **Living Documentation** - Tests describe expected behavior
3. **Efficiency Gains** - Eventually faster than manual Playwright sessions
4. **Visual Regression** - Automated screenshot comparison
5. **CI/CD Integration** - Run on every commit

### Efficiency Trajectory
- **Now**: Manual Playwright screenshots for discovery (~10-15 min per feature)
- **Short-term**: Write tests while building (~5 min overhead)
- **Long-term**: Automated tests run in <2 min, catch regressions instantly

---

## Testing Architecture

### Directory Structure
```
tests/
├── e2e/                          # Playwright end-to-end tests
│   ├── conftest.py              # Pytest fixtures (page, context)
│   ├── test_desktop_panels.py   # Panel system tests
│   ├── test_pagination.py       # Performance/pagination tests
│   ├── test_navigation.py       # User workflow tests
│   ├── test_code_preview.py     # Inspector panel tests
│   └── test_search.py           # Search functionality tests
├── components/                   # Component unit tests (Vitest)
└── integration/                  # Backend integration tests (pytest)
```

### Fixture Setup (conftest.py)
```python
import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_context():
    """Shared browser context for all tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser during dev
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},  # Desktop size
            locale='en-US'
        )
        yield context
        context.close()
        browser.close()

@pytest.fixture
def page(browser_context):
    """Fresh page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()

@pytest.fixture
def app_page(page):
    """Page navigated to app and ready for testing."""
    page.goto('http://localhost:5173')
    page.wait_for_selector('[data-test="app-loaded"]', timeout=5000)
    return page
```

---

## Page Object Model Pattern

### Why Page Objects?
- **Maintainability**: UI changes only affect page objects, not tests
- **Reusability**: Common actions defined once
- **Readability**: Tests read like user stories

### Example: Navigator Panel Page Object
```python
# tests/e2e/pages/navigator_panel.py
class NavigatorPanel:
    def __init__(self, page):
        self.page = page
        self.panel = page.locator('[data-test="navigator-panel"]')
    
    def switch_to_browse(self):
        """Switch to Browse mode."""
        self.page.click('[data-test="nav-browse-tab"]')
        self.page.wait_for_selector('[data-test="category-cards"]')
    
    def switch_to_search(self):
        """Switch to Search mode."""
        self.page.click('[data-test="nav-search-tab"]')
        self.page.wait_for_selector('[data-test="search-input"]')
    
    def select_category(self, category: str):
        """Click a category card."""
        self.page.click(f'[data-test="category-{category}"]')
        self.page.wait_for_selector('[data-test="node-grid"]')
    
    def search(self, query: str):
        """Enter search query and submit."""
        self.page.fill('[data-test="search-input"]', query)
        self.page.press('[data-test="search-input"]', 'Enter')
        self.page.wait_for_selector('[data-test="search-results"]')
```

### Example: Inspector Panel Page Object
```python
# tests/e2e/pages/inspector_panel.py
class InspectorPanel:
    def __init__(self, page):
        self.page = page
        self.panel = page.locator('[data-test="inspector-panel"]')
    
    def get_selected_node_name(self) -> str:
        """Get currently selected node name."""
        return self.panel.locator('[data-test="node-name"]').text_content()
    
    def is_code_preview_visible(self) -> bool:
        """Check if code preview is showing."""
        return self.panel.locator('[data-test="code-preview"]').is_visible()
    
    def expand_code_preview(self):
        """Expand code preview section."""
        if not self.is_code_preview_visible():
            self.panel.locator('[data-test="code-preview-toggle"]').click()
    
    def get_code_snippet(self) -> str:
        """Get displayed code snippet."""
        return self.panel.locator('[data-test="code-preview"] pre').text_content()
    
    def view_full_file(self):
        """Click 'View Full File' button."""
        self.panel.locator('[data-test="view-full-file-btn"]').click()
        self.page.wait_for_selector('[data-test="code-view"]')
```

---

## Test Examples for Session 13

### Test 1: Desktop Panel Layout
```python
# tests/e2e/test_desktop_panels.py
import pytest
from tests.e2e.pages.navigator_panel import NavigatorPanel
from tests.e2e.pages.inspector_panel import InspectorPanel

def test_three_panel_layout_renders_on_desktop(app_page):
    """Verify three-panel layout is visible on desktop viewport."""
    # Arrange
    app_page.set_viewport_size({'width': 1920, 'height': 1080})
    
    # Assert
    expect(app_page.locator('[data-test="navigator-panel"]')).to_be_visible()
    expect(app_page.locator('[data-test="main-content-panel"]')).to_be_visible()
    expect(app_page.locator('[data-test="inspector-panel"]')).to_be_visible()
    
    # Verify widths
    nav_width = app_page.locator('[data-test="navigator-panel"]').bounding_box()['width']
    assert nav_width == 250  # Fixed 250px

def test_panels_collapse_on_mobile(app_page):
    """Mobile viewport should show single panel with tabs."""
    # Arrange
    app_page.set_viewport_size({'width': 375, 'height': 667})
    
    # Assert - Only one panel visible
    visible_panels = app_page.locator('[data-test*="panel"]:visible').count()
    assert visible_panels == 1

def test_inspector_panel_is_resizable(app_page):
    """User can resize inspector panel by dragging edge."""
    # Arrange
    inspector = app_page.locator('[data-test="inspector-panel"]')
    initial_width = inspector.bounding_box()['width']
    resize_handle = app_page.locator('[data-test="inspector-resize-handle"]')
    
    # Act - Drag resize handle 100px left
    resize_handle.drag_to(resize_handle, target_position={'x': -100, 'y': 0})
    
    # Assert
    new_width = inspector.bounding_box()['width']
    assert new_width == initial_width + 100
```

### Test 2: Pagination & Performance
```python
# tests/e2e/test_pagination.py
import pytest
from playwright.sync_api import expect

def test_high_degree_node_only_shows_50_callers_initially(app_page):
    """Nodes with 1000+ callers should only render 50 initially."""
    # Arrange
    nav = NavigatorPanel(app_page)
    nav.switch_to_browse()
    nav.select_category('entry_points')
    
    # Act - Click 're' import node (1,123 callers)
    app_page.click('[data-test="node-tile"][data-node-name="re"]')
    
    # Assert - Only 50 caller tiles rendered
    caller_tiles = app_page.locator('[data-test="caller-tile"]').count()
    assert caller_tiles == 50
    
    # Assert - "Load More" button visible with count
    load_more_btn = app_page.locator('[data-test="load-more-callers"]')
    expect(load_more_btn).to_be_visible()
    expect(load_more_btn).to_contain_text('1073 more')  # 1123 - 50

def test_load_more_button_fetches_next_page(app_page):
    """Load More button fetches next 50 callers."""
    # Arrange
    app_page.click('[data-test="node-tile"][data-node-name="re"]')
    initial_count = app_page.locator('[data-test="caller-tile"]').count()
    
    # Act
    app_page.click('[data-test="load-more-callers"]')
    app_page.wait_for_selector('[data-test="caller-tile"]:nth-child(51)')
    
    # Assert
    new_count = app_page.locator('[data-test="caller-tile"]').count()
    assert new_count == initial_count + 50  # 100 total

def test_page_does_not_timeout_with_1000_plus_connections(app_page):
    """Page remains responsive even with high-degree nodes."""
    # Arrange
    app_page.click('[data-test="node-tile"][data-node-name="re"]')
    
    # Act - Screenshot should complete in <2 seconds
    start = time.time()
    app_page.screenshot(path='test-high-degree-node.png')
    duration = time.time() - start
    
    # Assert
    assert duration < 2.0  # Should not timeout
```

### Test 3: Code Preview Feature
```python
# tests/e2e/test_code_preview.py
def test_code_preview_loads_when_function_selected(app_page):
    """Selecting a function shows syntax-highlighted code in inspector."""
    # Arrange
    nav = NavigatorPanel(app_page)
    inspector = InspectorPanel(app_page)
    
    nav.switch_to_browse()
    nav.select_category('entry_points')
    
    # Act - Select a Python function
    app_page.click('[data-test="node-tile"][data-node-type="function"]:first-child')
    
    # Assert - Code preview appears
    expect(app_page.locator('[data-test="code-preview"]')).to_be_visible()
    
    # Verify syntax highlighting applied
    code_element = app_page.locator('[data-test="code-preview"] pre code')
    expect(code_element).to_have_class('language-python')
    
    # Verify code content includes 'def'
    code_text = inspector.get_code_snippet()
    assert 'def ' in code_text

def test_code_preview_collapses_on_toggle(app_page):
    """Code preview section can be collapsed/expanded."""
    # Arrange
    inspector = InspectorPanel(app_page)
    app_page.click('[data-test="node-tile"]:first-child')
    
    # Act - Click collapse button
    app_page.click('[data-test="code-preview-toggle"]')
    
    # Assert - Code hidden
    expect(app_page.locator('[data-test="code-preview"] pre')).to_be_hidden()
    
    # Act - Click expand button
    app_page.click('[data-test="code-preview-toggle"]')
    
    # Assert - Code visible again
    expect(app_page.locator('[data-test="code-preview"] pre')).to_be_visible()

def test_view_full_file_switches_to_code_view(app_page):
    """'View Full File' button switches main panel to Code View."""
    # Arrange
    inspector = InspectorPanel(app_page)
    app_page.click('[data-test="node-tile"]:first-child')
    inspector.expand_code_preview()
    
    # Act
    inspector.view_full_file()
    
    # Assert - Main panel shows code view
    expect(app_page.locator('[data-test="main-content-panel"]')).to_contain_text('Code View')
    expect(app_page.locator('[data-test="code-editor"]')).to_be_visible()
```

### Test 4: Complete User Workflow
```python
# tests/e2e/test_navigation.py
def test_complete_code_exploration_workflow(app_page):
    """
    User story: Developer explores codebase to understand authentication flow.
    
    1. Browse entry points to find auth functions
    2. Select 'authenticate_user' function
    3. View code preview in inspector
    4. See callers to understand where it's used
    5. Navigate to a caller
    6. Search for related functions
    """
    # Step 1: Browse entry points
    app_page.click('[data-test="nav-browse-tab"]')
    app_page.click('[data-test="category-entry-points"]')
    
    # Step 2: Find and select authentication function
    auth_node = app_page.locator('[data-test="node-tile"]', has_text='authenticate')
    auth_node.first.click()
    
    # Step 3: Verify code preview shows function definition
    code_preview = app_page.locator('[data-test="code-preview"]')
    expect(code_preview).to_be_visible()
    expect(code_preview).to_contain_text('def authenticate')
    
    # Step 4: Check callers section
    app_page.click('[data-test="connections-tab"]')
    callers_section = app_page.locator('[data-test="callers-section"]')
    expect(callers_section).to_be_visible()
    
    caller_count = app_page.locator('[data-test="caller-tile"]').count()
    assert caller_count > 0  # Should have callers
    
    # Step 5: Navigate to first caller
    app_page.locator('[data-test="caller-tile"]').first.click()
    
    # Verify selection changed
    new_node_name = app_page.locator('[data-test="inspector-panel"] [data-test="node-name"]').text_content()
    assert 'authenticate' not in new_node_name.lower()  # Different function
    
    # Step 6: Use search to find more auth-related code
    app_page.click('[data-test="nav-search-tab"]')
    app_page.fill('[data-test="search-input"]', 'auth')
    app_page.press('[data-test="search-input"]', 'Enter')
    
    # Verify search results
    results = app_page.locator('[data-test="search-result"]').count()
    assert results >= 1
```

---

## Data Test IDs Convention

### Naming Pattern
```
data-test="{component}-{element}-{variant?}"
```

### Examples
```vue
<!-- Navigator Panel -->
<div data-test="navigator-panel">
  <button data-test="nav-browse-tab">📂 Browse</button>
  <button data-test="nav-search-tab">🔍 Search</button>
  <button data-test="nav-tools-tab">🛠️ Tools</button>
</div>

<!-- Category Cards -->
<button data-test="category-entry-points">Entry Points</button>
<button data-test="category-hubs">Hubs</button>

<!-- Node Tiles -->
<div 
  data-test="node-tile"
  :data-node-name="node.name"
  :data-node-type="node.node_type"
  :data-node-id="node.id"
>

<!-- Inspector Panel -->
<div data-test="inspector-panel">
  <div data-test="node-details">
    <span data-test="node-name">{{ node.name }}</span>
    <span data-test="node-type">{{ node.node_type }}</span>
  </div>
  
  <div data-test="code-preview">
    <button data-test="code-preview-toggle">Expand/Collapse</button>
    <pre data-test="code-content"><code>...</code></pre>
    <button data-test="view-full-file-btn">View Full File</button>
  </div>
  
  <div data-test="metadata-section">
    <div data-test="ai-summary">...</div>
  </div>
</div>

<!-- Pagination -->
<button data-test="load-more-callers">Load More (1073 more)</button>
<button data-test="load-more-callees">Load More</button>
```

---

## Session 13 Test Plan

### P0 Tests (Write BEFORE implementing features)

**Test File**: `tests/e2e/test_pagination.py`
```python
def test_callers_endpoint_returns_max_50_by_default(app_page):
    """Backend endpoint limits results to 50."""
    # Direct API test
    response = requests.get('http://localhost:8000/api/graph/query/callers?symbol=re')
    data = response.json()
    
    assert data['total_callers'] == 1123
    assert len(data['callers']) == 50
    assert data['has_more'] == True
    assert data['offset'] == 0
    assert data['limit'] == 50

def test_load_more_button_appears_when_more_results_available(app_page):
    """Load More button shows when results exceed page size."""
    # Arrange - Select high-degree node
    app_page.click('[data-test="node-tile"][data-node-name="re"]')
    
    # Assert
    load_more = app_page.locator('[data-test="load-more-callers"]')
    expect(load_more).to_be_visible()
    expect(load_more).to_contain_text('1073 more')  # 1123 total - 50 shown

def test_no_horizontal_scroll_on_desktop(app_page):
    """Page should not have horizontal scrollbar on desktop."""
    # Arrange
    app_page.set_viewport_size({'width': 1920, 'height': 1080})
    
    # Assert
    scroll_width = app_page.evaluate('document.documentElement.scrollWidth')
    client_width = app_page.evaluate('document.documentElement.clientWidth')
    assert scroll_width == client_width  # No overflow

def test_stdlib_imports_not_in_entry_points(app_page):
    """Common imports like 're' should not appear in Entry Points category."""
    # Arrange
    app_page.click('[data-test="category-entry-points"]')
    
    # Assert
    node_names = app_page.locator('[data-test="node-tile"]').all_text_contents()
    assert 're' not in node_names
    assert 'asyncio' not in node_names
    assert 'logging' not in node_names
```

**Test File**: `tests/e2e/test_code_preview.py`
```python
def test_code_preview_section_exists_in_inspector(app_page):
    """Inspector panel has code preview section."""
    # Arrange - Select any function node
    app_page.click('[data-test="category-entry-points"]')
    app_page.click('[data-test="node-tile"][data-node-type="function"]:first-child')
    
    # Assert
    expect(app_page.locator('[data-test="code-preview"]')).to_be_visible()

def test_code_preview_syntax_highlighting_applied(app_page):
    """Code preview shows syntax-highlighted Python code."""
    # Arrange
    app_page.click('[data-test="node-tile"][data-node-type="function"]:first-child')
    
    # Assert
    code_element = app_page.locator('[data-test="code-preview"] pre code')
    
    # Should have language class
    classes = code_element.get_attribute('class')
    assert 'language-' in classes or 'hljs' in classes
```

### P1 Tests (Write during implementation)

**Test File**: `tests/e2e/test_search_panel.py`
```python
def test_search_panel_opens_with_keyboard_shortcut(app_page):
    """Ctrl+K opens search panel."""
    # Act
    app_page.keyboard.press('Control+k')
    
    # Assert
    expect(app_page.locator('[data-test="search-input"]')).to_be_focused()

def test_search_filters_by_language(app_page):
    """Search can filter results by language."""
    # Arrange
    app_page.click('[data-test="nav-search-tab"]')
    app_page.fill('[data-test="search-input"]', 'authenticate')
    
    # Act - Select Python filter
    app_page.click('[data-test="filter-language"]')
    app_page.click('[data-test="language-option-python"]')
    app_page.press('[data-test="search-input"]', 'Enter')
    
    # Assert - All results are Python
    results = app_page.locator('[data-test="search-result"]').all()
    for result in results:
        language = result.get_attribute('data-language')
        assert language == 'Python'
```

---

## Running Tests

### Local Development
```bash
# Install Playwright
pip install pytest-playwright
playwright install chromium

# Run all E2E tests (headless)
pytest tests/e2e/ -v

# Run with visible browser (for debugging)
pytest tests/e2e/ -v --headed

# Run specific test file
pytest tests/e2e/test_pagination.py -v

# Run with screenshot on failure
pytest tests/e2e/ -v --screenshot=only-on-failure

# Run with video recording
pytest tests/e2e/ -v --video=retain-on-failure
```

### In Docker
```bash
# Run tests in backend container
docker exec code-graph-mcp-code-graph-http-1 \
  uv run pytest tests/e2e/ -v

# Or build dedicated test image
docker build -t code-graph-mcp:test -f Dockerfile.test .
docker run --rm code-graph-mcp:test pytest tests/e2e/
```

### CI/CD (GitHub Actions)
```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on: [push, pull_request]

jobs:
  playwright:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-playwright
          playwright install --with-deps chromium
      
      - name: Start Docker stack
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 10
      
      - name: Run Playwright tests
        run: pytest tests/e2e/ -v --screenshot=only-on-failure
      
      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-screenshots
          path: tests/e2e/screenshots/
```

---

## Best Practices

### 1. Use Accessibility Selectors
```python
# Good - Stable, accessible
page.get_by_role('button', name='Load More').click()
page.get_by_label('Search').fill('authenticate')

# Bad - Fragile, implementation-dependent
page.locator('.btn-primary.load-more-btn').click()
page.locator('input[placeholder="Search..."]').fill('authenticate')
```

### 2. Auto-Waiting Assertions
```python
# Good - Playwright waits automatically
expect(page.locator('[data-test="loading"]')).to_be_hidden()
expect(page.locator('[data-test="results"]')).to_be_visible()

# Bad - Manual waiting
page.wait_for_timeout(2000)
assert not page.locator('[data-test="loading"]').is_visible()
```

### 3. Page Object Methods Return Self
```python
class NavigatorPanel:
    def switch_to_browse(self):
        self.page.click('[data-test="nav-browse-tab"]')
        return self  # Enable chaining
    
    def select_category(self, category):
        self.page.click(f'[data-test="category-{category}"]')
        return self

# Usage - Fluent interface
nav = NavigatorPanel(page)
nav.switch_to_browse().select_category('entry_points')
```

### 4. Isolate Tests
```python
# Each test should be independent
@pytest.fixture(autouse=True)
def reset_app_state(app_page):
    """Reset app to initial state before each test."""
    app_page.goto('http://localhost:5173')
    app_page.click('[data-test="clear-selection"]', force=True)
    yield
    # Cleanup after test if needed
```

---

## Migration Path for Existing Tests

### Current State
- Manual Playwright screenshot sessions
- No automated E2E tests
- Backend unit tests (68+ passing)

### Migration Steps
1. **Session 13**: Write Playwright tests for P0 fixes (pagination, layout)
2. **Session 14**: Write tests for desktop panel system
3. **Session 15**: Backfill tests for existing features (Browse, Connections)
4. **Session 16**: Add CI/CD pipeline with automated test runs

### Test Coverage Goals
- **Session 13**: 10+ E2E tests (pagination, layout, code preview)
- **Session 14**: 20+ E2E tests (panels, search, navigation)
- **Session 15**: 30+ E2E tests (full coverage of user workflows)

---

## Debugging Failed Tests

### Screenshot on Failure
```python
# pytest.ini
[pytest]
markers =
    e2e: End-to-end tests with Playwright

# Automatically enabled with --screenshot flag
```

### Video Recording
```python
# Record video of test execution
context = browser.new_context(record_video_dir="test-results/")
```

### Trace Viewer (Most Powerful!)
```python
# conftest.py
@pytest.fixture
def page(browser_context):
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    yield page
    context.tracing.stop(path="trace.zip")
    page.close()

# View trace after test failure
# playwright show-trace trace.zip
```

---

## Integration with Architecture Decisions

### Event-Driven Graph Updates
**Testing Real-Time Updates** (Phase 1: Redis Streams):
```python
# tests/e2e/test_real_time_updates.py
import asyncio
import pytest
from playwright.sync_api import expect

def test_graph_updates_on_file_change(app_page):
    """When file changes, graph updates in real-time via WebSocket."""
    # Arrange - Open graph view with specific file
    app_page.click('[data-test="nav-browse-tab"]')
    app_page.click('[data-test="category-entry-points"]')
    initial_node_count = app_page.locator('[data-test="node-tile"]').count()
    
    # Act - Trigger file change (via test fixture that modifies watched directory)
    # Backend detects change → re-parses → publishes to Redis Stream → WebSocket pushes to frontend
    app_page.evaluate('window.testTriggerFileChange("src/new_function.py")')
    
    # Assert - New node appears without page reload
    app_page.wait_for_selector('[data-test="node-tile"]:nth-child(' + str(initial_node_count + 1) + ')')
    new_node_count = app_page.locator('[data-test="node-tile"]').count()
    assert new_node_count == initial_node_count + 1
    
    # Verify notification appears
    expect(app_page.locator('[data-test="toast-notification"]')).to_contain_text('Graph updated')

def test_analysis_progress_updates(app_page):
    """Analysis progress shows real-time updates via Pub/Sub."""
    # Arrange
    app_page.click('[data-test="admin-panel"]')
    
    # Act - Trigger re-analysis
    app_page.click('[data-test="reanalyze-btn"]')
    
    # Assert - Progress bar updates in real-time
    expect(app_page.locator('[data-test="progress-bar"]')).to_be_visible()
    
    # Wait for incremental updates (backend publishes progress events)
    app_page.wait_for_function('''
        () => {
            const progress = document.querySelector('[data-test="progress-percent"]').textContent;
            return parseInt(progress) > 50;  // Wait until >50%
        }
    ''')
    
    # Final completion notification
    app_page.wait_for_selector('[data-test="analysis-complete"]', timeout=30000)
```

### Memgraph Integration Testing (Phase 2)
**Testing Complex Cypher Queries**:
```python
# tests/e2e/test_memgraph_queries.py
import pytest
from playwright.sync_api import expect

def test_find_business_logic_paths(app_page):
    """MCP Resource: Entry Point → DB Paths query works."""
    # Arrange - Navigate to MCP Resources panel
    app_page.click('[data-test="nav-tools-tab"]')
    app_page.click('[data-test="mcp-resources-section"]')
    
    # Act - Select pre-built Cypher query
    app_page.click('[data-test="resource-entry-to-db-paths"]')
    
    # Assert - Results show call paths from HTTP endpoints to DB operations
    expect(app_page.locator('[data-test="query-results"]')).to_be_visible()
    
    # Verify path structure (entry → ... → db operation)
    paths = app_page.locator('[data-test="result-path"]').all()
    assert len(paths) > 0
    
    first_path = paths[0]
    expect(first_path.locator('[data-test="path-start"]')).to_have_attribute('data-is-entry', 'true')
    expect(first_path.locator('[data-test="path-end"]')).to_contain_text('insert|update|delete|save', use_regex=True)

def test_impact_analysis_query(app_page):
    """MCP Prompt: 'What breaks if I change X?' works."""
    # Arrange
    app_page.click('[data-test="nav-tools-tab"]')
    app_page.click('[data-test="mcp-prompts-section"]')
    
    # Act - Select impact analysis prompt
    app_page.click('[data-test="prompt-impact-analysis"]')
    app_page.fill('[data-test="symbol-input"]', 'authenticate_user')
    app_page.click('[data-test="execute-prompt-btn"]')
    
    # Assert - Shows impacted functions with distance
    expect(app_page.locator('[data-test="impact-results"]')).to_be_visible()
    
    # Verify results sorted by distance (closest first)
    distances = app_page.locator('[data-test="impact-distance"]').all_text_contents()
    distances_int = [int(d) for d in distances]
    assert distances_int == sorted(distances_int)  # Ascending order
    
    # Verify test coverage indicator
    first_result = app_page.locator('[data-test="impact-result"]:first-child')
    test_coverage = first_result.locator('[data-test="test-coverage"]').text_content()
    assert 'tests' in test_coverage.lower()  # Shows test count or "No tests"
```

### MCP Resources Library Testing
**Testing Pre-Built Navigation Patterns**:
```python
# tests/e2e/test_mcp_resources.py
import pytest
from playwright.sync_api import expect

def test_mcp_resources_library_loads(app_page):
    """MCP Resources panel shows all pre-built Cypher queries."""
    # Arrange
    app_page.click('[data-test="nav-tools-tab"]')
    
    # Assert - Resource categories visible
    expect(app_page.locator('[data-test="resource-category-navigation"]')).to_be_visible()
    expect(app_page.locator('[data-test="resource-category-analysis"]')).to_be_visible()
    expect(app_page.locator('[data-test="resource-category-quality"]')).to_be_visible()
    
    # Verify resource count
    resources = app_page.locator('[data-test^="resource-"]').count()
    assert resources >= 10  # At least 10 pre-built queries

def test_resource_shows_cypher_query(app_page):
    """Clicking resource shows underlying Cypher query for learning."""
    # Arrange
    app_page.click('[data-test="nav-tools-tab"]')
    
    # Act - Click "Show Query" for a resource
    app_page.click('[data-test="resource-entry-to-db-paths"]')
    app_page.click('[data-test="show-query-btn"]')
    
    # Assert - Cypher query visible with syntax highlighting
    expect(app_page.locator('[data-test="cypher-query-display"]')).to_be_visible()
    cypher_text = app_page.locator('[data-test="cypher-query-display"]').text_content()
    assert 'MATCH' in cypher_text
    assert '-[:CALLS*' in cypher_text  # Multi-hop relationship
    
    # Verify syntax highlighting applied
    expect(app_page.locator('[data-test="cypher-query-display"] .hljs-keyword')).to_be_visible()
```

---

## Session-by-Session Testing Plan

### Session 13: P0 Performance + Redis Streams CDC
**Write These Tests First**:
1. `test_pagination.py` - Backend pagination, Load More button
2. `test_layout.py` - No horizontal scroll, responsive panels
3. `test_stdlib_filtering.py` - Entry points exclude stdlib modules
4. `test_redis_streams_cdc.py` - CDC events published on mutations

### Session 14: Redis Pub/Sub + Search
**Write These Tests First**:
1. `test_real_time_notifications.py` - Analysis complete, progress updates
2. `test_redis_search.py` - Full-text search with ranking
3. `test_websocket_updates.py` - Frontend receives live events

### Session 15: Memgraph Integration
**Write These Tests First**:
1. `test_memgraph_sync.py` - Events flow Redis → Memgraph
2. `test_cypher_queries.py` - Complex queries execute correctly
3. `test_query_routing.py` - Simple → rustworkx, complex → Memgraph

### Session 16: MCP Resources Library
**Write These Tests First**:
1. `test_mcp_resources.py` - 10+ pre-built queries available
2. `test_mcp_prompts.py` - Natural language workflows work
3. `test_query_builder.py` - Visual query composition

---

**Commitment**: Every session starts with writing Playwright tests for planned features. Implementation follows to make tests pass (TDD red-green-refactor cycle).
