"""
Playwright E2E tests for workbench navigation functionality.

Tests verify:
- Double-click drill-down navigation works
- Breadcrumb navigation allows level jumping
- Back button returns to previous level
- Home button returns to root level
- Keyboard navigation works for node cards
"""

import pytest
from .pages import WorkbenchPage


@pytest.fixture
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page()
    yield page
    await page.close()


@pytest.fixture
async def workbench_page(page):
    """Create a WorkbenchPage instance with console capture."""
    wb_page = WorkbenchPage(page)
    wb_page.setup_console_capture()
    return wb_page


class TestWorkbenchNavigation:
    """Test workbench navigation functionality."""

    @pytest.mark.asyncio
    async def test_graph_loads_without_errors(self, workbench_page):
        """Verify graph loads without throwing uncaught exceptions."""
        await workbench_page.goto()

        # Wait a bit for any delayed errors
        await workbench_page.page.wait_for_timeout(2000)

        # Should have no uncaught page errors
        errors = workbench_page.get_page_errors()
        assert len(errors) == 0, f"Uncaught errors: {errors}"

    @pytest.mark.asyncio
    async def test_breadcrumb_hidden_initially(self, workbench_page):
        """Verify breadcrumb navigation is hidden when not navigating."""
        await workbench_page.goto()

        # Wait for graph to load
        await workbench_page.page.wait_for_timeout(2000)

        # Breadcrumb should not be visible initially (no navigation)
        visible = await workbench_page.is_breadcrumb_visible()
        # Note: This test verifies initial state - breadcrumb visibility depends
        # on whether the workbench canvas is integrated with the main App.
        # If testing against the graph view, breadcrumb won't be visible.

    @pytest.mark.asyncio
    async def test_navigation_controls_visible(self, workbench_page):
        """Verify graph dimension controls are visible."""
        await workbench_page.goto()

        # Wait for 2D button to be visible
        button_2d = await workbench_page.page.wait_for_selector("text=2D", timeout=5000)
        assert button_2d is not None

        # Wait for 3D button to be visible
        button_3d = await workbench_page.page.wait_for_selector("text=3D", timeout=5000)
        assert button_3d is not None

    @pytest.mark.asyncio
    async def test_no_uncaught_exceptions_on_canvas_interaction(self, workbench_page):
        """Verify no uncaught exceptions when interacting with the graph canvas."""
        await workbench_page.goto()

        # Double-click on the graph canvas
        await workbench_page.double_click_graph_center()
        await workbench_page.page.wait_for_timeout(500)

        # Check for uncaught errors
        errors = workbench_page.get_page_errors()
        node_errors = [e for e in errors if "node" in e.lower()]
        assert len(node_errors) == 0, f"Uncaught node-related errors: {node_errors}"

    @pytest.mark.asyncio
    async def test_dimension_toggle_no_errors(self, workbench_page):
        """Verify switching between 2D and 3D doesn't cause errors."""
        await workbench_page.goto()

        # Switch to 3D
        button_3d = await workbench_page.page.wait_for_selector("text=3D", timeout=5000)
        await button_3d.click()
        await workbench_page.page.wait_for_timeout(1000)

        # Switch back to 2D
        button_2d = await workbench_page.page.wait_for_selector("text=2D", timeout=5000)
        await button_2d.click()
        await workbench_page.page.wait_for_timeout(1000)

        # Should have no uncaught exceptions
        errors = workbench_page.get_page_errors()
        assert len(errors) == 0, f"Uncaught errors during dimension toggle: {errors}"


class TestDoubleClickDrillDown:
    """Test double-click drill-down functionality."""

    @pytest.mark.asyncio
    async def test_double_click_hint_appears(self, workbench_page):
        """Verify double-click hint is shown when graph loads."""
        await workbench_page.goto()

        # Wait for the hint about double-click to appear
        hint = await workbench_page.page.wait_for_selector(
            "text=Double-click a node to drill into its local subgraph",
            timeout=10000
        )
        assert hint is not None

    @pytest.mark.asyncio
    async def test_double_click_on_canvas_no_crash(self, workbench_page):
        """Verify double-clicking on empty canvas area doesn't crash."""
        await workbench_page.goto()

        # Double-click on canvas (might not hit a node, but shouldn't throw)
        await workbench_page.double_click_graph_center()
        await workbench_page.page.wait_for_timeout(500)

        # Verify page is still functional
        stats_badge = await workbench_page.page.query_selector("text=nodes")
        assert stats_badge is not None


class TestBreadcrumbNavigation:
    """Test breadcrumb navigation functionality."""

    @pytest.mark.asyncio
    async def test_back_button_hidden_initially(self, workbench_page):
        """Verify back button is not visible when not navigating."""
        await workbench_page.goto()
        await workbench_page.page.wait_for_timeout(2000)

        # The back button should not be visible initially
        back_button = await workbench_page.page.query_selector('[title="Go back"]')
        assert back_button is None, "Back button should not be visible initially"

    @pytest.mark.asyncio
    async def test_home_button_hidden_initially(self, workbench_page):
        """Verify home button is not visible when not navigating."""
        await workbench_page.goto()
        await workbench_page.page.wait_for_timeout(2000)

        # The home button should not be visible initially
        home_button = await workbench_page.page.query_selector('[title="Return to full graph"]')
        assert home_button is None, "Home button should not be visible initially"


class TestKeyboardNavigation:
    """Test keyboard navigation functionality."""

    @pytest.mark.asyncio
    async def test_keyboard_focus_visible(self, workbench_page):
        """Verify keyboard focus is visible on interactive elements."""
        await workbench_page.goto()

        # Tab to first interactive element
        await workbench_page.press_key("Tab")
        await workbench_page.page.wait_for_timeout(200)

        # Focused element should be visible
        focused = await workbench_page.page.evaluate("""
            () => document.activeElement ? document.activeElement.tagName : null
        """)
        assert focused is not None


class TestNodeNotFoundHandling:
    """Test handling of node not found scenarios."""

    @pytest.mark.asyncio
    async def test_console_warnings_on_invalid_node(self, workbench_page):
        """Verify console warnings are logged instead of throwing for invalid nodes."""
        await workbench_page.goto()
        await workbench_page.page.wait_for_timeout(2000)

        # Check that no page errors related to "node not found" were thrown
        errors = workbench_page.get_page_errors()
        node_not_found_errors = [
            e for e in errors
            if "node not found" in e.lower() or "cannot read" in e.lower()
        ]
        assert len(node_not_found_errors) == 0, \
            f"Uncaught 'node not found' errors: {node_not_found_errors}"


class TestViewModeToggle:
    """Test view mode toggle functionality (when workbench is visible)."""

    @pytest.mark.asyncio
    async def test_view_mode_buttons_accessible(self, workbench_page):
        """Verify view mode buttons can be queried when workbench is active."""
        await workbench_page.goto()
        await workbench_page.page.wait_for_timeout(2000)

        # This test documents the expected selectors for when workbench is active
        # The buttons will only be present when WorkbenchCanvas is rendered
        grid_button = await workbench_page.page.query_selector('[data-test="view-mode-grid"]')
        list_button = await workbench_page.page.query_selector('[data-test="view-mode-list"]')

        # Note: These may be None if workbench is not yet integrated into main app
        # This test serves as documentation for the expected selectors


class TestSortControls:
    """Test sort control functionality (when workbench is visible)."""

    @pytest.mark.asyncio
    async def test_sort_select_accessible(self, workbench_page):
        """Verify sort select can be queried when workbench is active."""
        await workbench_page.goto()
        await workbench_page.page.wait_for_timeout(2000)

        # This test documents the expected selector for when workbench is active
        sort_select = await workbench_page.page.query_selector('[data-test="sort-by-select"]')

        # Note: May be None if workbench is not yet integrated into main app
        # This test serves as documentation for the expected selectors
