"""DashboardPage – navigation from the main dashboard to other sections.

Currently only implements navigation to the Orders page. The selector is based on the
`<i>` element with classes ``icon-menu`` and ``icon-menu-orders`` that appears in the
sidebar/menu. If the actual clickable element is a parent ``a``/``button`` wrapping
the icon, clicking the icon itself works in most browsers; otherwise the selector
can be adjusted later.
"""

from __future__ import annotations

from playwright.sync_api import Page

from .base_page import BasePage
from ..logger import log


class DashboardPage(BasePage):
    ORDERS_MENU_SELECTOR = "a[href=\"/app/orders/\"]"

    def __init__(self, page: Page, timeout: int = 30_000):
        super().__init__(page, timeout)

    def go_to_orders(self) -> None:
        """Navigate from the dashboard to the Orders list page.

        Clicks directly on Orders menu item, then waits for the network to become idle.
        """
        log.info("Clicking Orders menu item")
        self.click(self.ORDERS_MENU_SELECTOR)
        
        self.wait_for_network_idle()
        
        # Move mouse away to close any open dropdowns/menus
        self.page.mouse.move(0, 0)
        self.page.wait_for_timeout(500)
        
        log.info("Navigated to Orders page (load state networkidle)")
