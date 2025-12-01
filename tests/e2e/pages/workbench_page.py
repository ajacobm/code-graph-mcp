"""
Workbench Page Object Model for Playwright E2E tests.

This module provides a page object for interacting with the workbench
navigation components in the CodeNav frontend.
"""

from typing import Optional


class WorkbenchPage:
    """Page Object Model for the workbench canvas and navigation components."""

    def __init__(self, page):
        """
        Initialize the WorkbenchPage with a Playwright page instance.

        Args:
            page: Playwright page instance
        """
        self.page = page
        self.base_url = "http://localhost:5173"

    async def goto(self):
        """Navigate to the application."""
        await self.page.goto(self.base_url)
        # Wait for the page to be ready (stats badge appears when graph loads)
        await self.page.wait_for_selector("text=nodes", timeout=15000)

    async def wait_for_loading_complete(self):
        """Wait for any loading overlays to disappear."""
        # Wait for loading spinner to disappear
        try:
            loading = await self.page.query_selector(".animate-spin")
            if loading:
                await self.page.wait_for_selector(".animate-spin", state="hidden", timeout=10000)
        except Exception:
            pass  # No loading indicator found

    # ==================
    # Breadcrumb Navigation
    # ==================

    async def get_breadcrumb_navigation(self):
        """Get the breadcrumb navigation element."""
        return await self.page.query_selector('[data-test="breadcrumb-navigation"]')

    async def is_breadcrumb_visible(self) -> bool:
        """Check if the breadcrumb navigation is visible."""
        breadcrumb = await self.get_breadcrumb_navigation()
        return breadcrumb is not None

    async def click_home_button(self):
        """Click the home button in the breadcrumb navigation."""
        button = await self.page.wait_for_selector('[data-test="nav-home-button"]', timeout=5000)
        await button.click()
        await self.wait_for_loading_complete()

    async def click_back_button(self):
        """Click the back button in the breadcrumb navigation."""
        button = await self.page.wait_for_selector('[data-test="nav-back-button"]', timeout=5000)
        await button.click()
        await self.wait_for_loading_complete()

    async def click_breadcrumb_level(self, level: int):
        """
        Click a specific breadcrumb level.

        Args:
            level: The zero-based index of the breadcrumb level to click
        """
        selector = f'[data-test="breadcrumb-{level}"]'
        button = await self.page.wait_for_selector(selector, timeout=5000)
        await button.click()
        await self.wait_for_loading_complete()

    async def get_breadcrumb_count(self) -> int:
        """Get the number of breadcrumb levels currently displayed."""
        breadcrumbs = await self.page.query_selector_all('[data-test^="breadcrumb-"]')
        return len(breadcrumbs)

    # ==================
    # Node Cards
    # ==================

    async def get_node_card(self, node_id: str):
        """
        Get a specific node card by ID.

        Args:
            node_id: The ID of the node

        Returns:
            The node card element or None if not found
        """
        return await self.page.query_selector(f'[data-test="node-card-{node_id}"]')

    async def get_all_node_cards(self):
        """Get all node card elements on the page."""
        return await self.page.query_selector_all('[data-test^="node-card-"]')

    async def get_hero_card(self):
        """Get the hero card (root node card)."""
        return await self.page.query_selector('[data-testid="node-card-hero"]')

    async def get_grid_cards(self):
        """Get all grid variant cards."""
        return await self.page.query_selector_all('[data-testid="node-card-grid"]')

    async def get_list_cards(self):
        """Get all list variant cards."""
        return await self.page.query_selector_all('[data-testid="node-card-list"]')

    async def click_node_card(self, node_id: str):
        """
        Single click on a node card.

        Args:
            node_id: The ID of the node to click
        """
        card = await self.page.wait_for_selector(f'[data-test="node-card-{node_id}"]', timeout=5000)
        await card.click()

    async def double_click_node_card(self, node_id: str):
        """
        Double click on a node card to drill down.

        Args:
            node_id: The ID of the node to drill into
        """
        card = await self.page.wait_for_selector(f'[data-test="node-card-{node_id}"]', timeout=5000)
        await card.dblclick()
        await self.wait_for_loading_complete()

    # ==================
    # WorkbenchCanvas
    # ==================

    async def get_workbench_canvas(self):
        """Get the workbench canvas element."""
        return await self.page.query_selector('[data-test="workbench-canvas"]')

    async def is_workbench_empty(self) -> bool:
        """Check if the workbench shows the empty state."""
        empty = await self.page.query_selector('[data-testid="workbench-canvas-empty"]')
        return empty is not None

    # ==================
    # View Mode Controls
    # ==================

    async def set_view_mode_grid(self):
        """Switch to grid view mode."""
        button = await self.page.wait_for_selector('[data-test="view-mode-grid"]', timeout=5000)
        await button.click()

    async def set_view_mode_list(self):
        """Switch to list view mode."""
        button = await self.page.wait_for_selector('[data-test="view-mode-list"]', timeout=5000)
        await button.click()

    async def get_current_view_mode(self) -> Optional[str]:
        """
        Get the current view mode.

        Returns:
            'grid', 'list', or None if unable to determine
        """
        grid_button = await self.page.query_selector('[data-test="view-mode-grid"]')
        if grid_button:
            is_pressed = await grid_button.get_attribute('aria-pressed')
            if is_pressed == 'true':
                return 'grid'

        list_button = await self.page.query_selector('[data-test="view-mode-list"]')
        if list_button:
            is_pressed = await list_button.get_attribute('aria-pressed')
            if is_pressed == 'true':
                return 'list'

        return None

    async def get_children_grid(self):
        """Get the children grid container."""
        return await self.page.query_selector('[data-test="children-grid"]')

    async def get_children_list(self):
        """Get the children list container."""
        return await self.page.query_selector('[data-test="children-list"]')

    # ==================
    # Sort Controls
    # ==================

    async def set_sort_by(self, sort_option: str):
        """
        Set the sort option.

        Args:
            sort_option: One of 'complexity', 'name', 'type', 'lines'
        """
        select = await self.page.wait_for_selector('[data-test="sort-by-select"]', timeout=5000)
        await select.select_option(value=sort_option)

    async def get_sort_by(self) -> Optional[str]:
        """Get the current sort option."""
        select = await self.page.query_selector('[data-test="sort-by-select"]')
        if select:
            return await select.input_value()
        return None

    # ==================
    # Graph Interactions (for testing drill-down from graph view)
    # ==================

    async def get_graph_canvas(self):
        """Get the force graph canvas container."""
        return await self.page.query_selector('.bg-slate-900.rounded-lg')

    async def double_click_graph_center(self):
        """Double-click in the center of the graph canvas."""
        canvas = await self.get_graph_canvas()
        if canvas:
            box = await canvas.bounding_box()
            if box:
                center_x = box["x"] + box["width"] / 2
                center_y = box["y"] + box["height"] / 2
                await self.page.mouse.dblclick(center_x, center_y)
                await self.wait_for_loading_complete()

    # ==================
    # Keyboard Navigation
    # ==================

    async def press_key(self, key: str):
        """
        Press a keyboard key.

        Args:
            key: The key to press (e.g., 'Enter', 'ArrowDown', 'Escape')
        """
        await self.page.keyboard.press(key)

    async def focus_first_node_card(self):
        """Focus the first node card on the page."""
        cards = await self.get_all_node_cards()
        if cards and len(cards) > 0:
            await cards[0].focus()
            return True
        return False

    # ==================
    # Console and Errors
    # ==================

    def setup_console_capture(self):
        """Set up console message capture. Call before navigation."""
        self.console_messages = []
        self.page_errors = []

        self.page.on("console", lambda msg: self.console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))
        self.page.on("pageerror", lambda err: self.page_errors.append(str(err)))

    def get_console_errors(self):
        """Get all console error messages."""
        return [m for m in self.console_messages if m["type"] == "error"]

    def get_page_errors(self):
        """Get all uncaught page errors."""
        return self.page_errors
