"""LoginPage – handles authentication on KeyCRM.

The page contains:
* Username input – ``input[name=\"username\"]`` (type="text").
* Password input – ``input[name=\"username\"][type=\"password\"]`` (the markup uses the same name attribute).
* Submit button – a button with the primary style that contains the text "Увійти".

All selectors are defined as class constants for easy updates.
"""

from __future__ import annotations

from playwright.sync_api import Page

from .base_page import BasePage
from ..config import settings
from ..logger import log


class LoginPage(BasePage):
    USERNAME_SELECTOR = "input[name=\"username\"]:not([type=\"password\"])"
    PASSWORD_SELECTOR = "input[name=\"username\"][type=\"password\"]"
    SUBMIT_SELECTOR = "button[type=\"submit\"], button.primary"
    TIMEOUT = 60_000

    def __init__(self, page: Page, timeout: int = 60_000):
        super().__init__(page, timeout)

    def goto(self) -> None:
        """Navigate to the login page and wait for it to be ready."""
        log.info("Navigating to KeyCRM login page", url=settings.keycrm_url)
        self.page.goto(settings.keycrm_url, wait_until="networkidle")
        self.wait_for_visible(self.USERNAME_SELECTOR)
        log.info("Login page loaded")

    def login(self, username: str | None = None, password: str | None = None) -> None:
        """Fill credentials and submit the form."""
        username = username or settings.keycrm_username
        password = password or settings.keycrm_password

        log.info("Filling login form")
        self.wait_for_visible(self.USERNAME_SELECTOR)
        self.page.fill(self.USERNAME_SELECTOR, username)
        self.wait_for_visible(self.PASSWORD_SELECTOR)
        self.page.fill(self.PASSWORD_SELECTOR, password)
        
        # Click submit - try multiple selectors
        try:
            self.page.click("button[type=\"submit\"]", timeout=5000)
        except:
            try:
                self.page.click("button.primary", timeout=5000)
            except:
                # Try any button with visible text
                self.page.click("form button", timeout=5000)
        
        # Wait for navigation after login
        self.page.wait_for_load_state("networkidle", timeout=self.timeout)
        log.info("Login submitted")
