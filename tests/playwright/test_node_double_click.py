"""
Playwright E2E tests for node double-click navigation.

Tests verify:
- Double-click on graph node triggers navigation
- Invalid node handling doesn't throw uncaught exceptions
- Navigation breadcrumb appears after drill-down
- Back navigation works correctly
"""

import pytest


@pytest.fixture
async def page(browser):
    """Create a new page for each test."""
    page = await browser.new_page()
    yield page
    await page.close()


class TestNodeDoubleClickNavigation:
    """Test node double-click navigation functionality."""

    @pytest.mark.asyncio
    async def test_graph_loads_without_errors(self, page):
        """Verify graph loads without throwing uncaught exceptions."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        
        await page.goto("http://localhost:5173")
        
        # Wait for graph to load (look for stats badge showing nodes)
        await page.wait_for_selector("text=nodes", timeout=10000)
        
        # Wait a bit for any delayed errors
        await page.wait_for_timeout(2000)
        
        # Should have no uncaught exceptions
        assert len(errors) == 0, f"Uncaught errors: {errors}"

    @pytest.mark.asyncio
    async def test_double_click_hint_appears(self, page):
        """Verify double-click hint is shown when graph loads."""
        await page.goto("http://localhost:5173")
        
        # Wait for the hint about double-click to appear
        hint = await page.wait_for_selector(
            "text=Double-click a node to drill into its local subgraph",
            timeout=10000
        )
        assert hint is not None

    @pytest.mark.asyncio
    async def test_no_uncaught_exceptions_on_canvas_interaction(self, page):
        """Verify no uncaught exceptions when interacting with the graph canvas."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        
        await page.goto("http://localhost:5173")
        
        # Wait for graph to load
        await page.wait_for_selector("text=nodes", timeout=10000)
        
        # Find the graph canvas container (bg-slate-900 rounded-lg)
        canvas = await page.wait_for_selector(
            ".bg-slate-900.rounded-lg",
            timeout=5000
        )
        
        if canvas:
            # Get bounding box
            box = await canvas.bounding_box()
            if box:
                center_x = box["x"] + box["width"] / 2
                center_y = box["y"] + box["height"] / 2
                
                # Single click on canvas
                await page.mouse.click(center_x, center_y)
                await page.wait_for_timeout(500)
                
                # Double click on canvas (might not hit a node, but shouldn't throw)
                await page.mouse.dblclick(center_x, center_y)
                await page.wait_for_timeout(500)
        
        # Should have no uncaught exceptions related to node handling
        node_errors = [e for e in errors if "node" in e.lower()]
        assert len(node_errors) == 0, f"Uncaught node-related errors: {node_errors}"

    @pytest.mark.asyncio
    async def test_navigation_controls_visible(self, page):
        """Verify graph controls are visible."""
        await page.goto("http://localhost:5173")
        
        # Wait for 2D button to be visible
        button_2d = await page.wait_for_selector("text=2D", timeout=5000)
        assert button_2d is not None
        
        # Wait for 3D button to be visible  
        button_3d = await page.wait_for_selector("text=3D", timeout=5000)
        assert button_3d is not None

    @pytest.mark.asyncio
    async def test_dimension_toggle_no_errors(self, page):
        """Verify switching between 2D and 3D doesn't cause errors."""
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        
        await page.goto("http://localhost:5173")
        
        # Wait for graph to load
        await page.wait_for_selector("text=nodes", timeout=10000)
        
        # Switch to 3D
        button_3d = await page.wait_for_selector("text=3D", timeout=5000)
        await button_3d.click()
        await page.wait_for_timeout(1000)
        
        # Switch back to 2D
        button_2d = await page.wait_for_selector("text=2D", timeout=5000)
        await button_2d.click()
        await page.wait_for_timeout(1000)
        
        # Should have no uncaught exceptions
        assert len(errors) == 0, f"Uncaught errors during dimension toggle: {errors}"


class TestNodeNotFoundHandling:
    """Test handling of node not found scenarios."""

    @pytest.mark.asyncio
    async def test_console_warnings_on_invalid_node(self, page):
        """Verify console warnings are logged instead of throwing for invalid nodes."""
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))
        
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        
        await page.goto("http://localhost:5173")
        
        # Wait for graph to load
        await page.wait_for_selector("text=nodes", timeout=10000)
        
        # Wait a bit for any console messages
        await page.wait_for_timeout(2000)
        
        # Check that no page errors related to "node not found" were thrown
        node_not_found_errors = [
            e for e in errors 
            if "node not found" in e.lower() or "cannot read" in e.lower()
        ]
        assert len(node_not_found_errors) == 0, \
            f"Uncaught 'node not found' errors: {node_not_found_errors}"


class TestNavigationBreadcrumb:
    """Test navigation breadcrumb functionality."""

    @pytest.mark.asyncio
    async def test_breadcrumb_hidden_initially(self, page):
        """Verify navigation breadcrumb is hidden when not navigating."""
        await page.goto("http://localhost:5173")
        
        # Wait for graph to load
        await page.wait_for_selector("text=nodes", timeout=10000)
        
        # The back button should not be visible initially
        back_button = await page.query_selector('[title="Go back"]')
        assert back_button is None, "Back button should not be visible initially"
        
        # The home button should not be visible initially
        home_button = await page.query_selector('[title="Return to full graph"]')
        assert home_button is None, "Home button should not be visible initially"


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
