"""BasePage – common utilities for all page objects.

Provides:
* A ``Page`` instance from Playwright (synchronous API).
* ``wait_for_visible`` – explicit wait for an element to be visible.
* ``wait_for_network_idle`` – waits until the page reports a ``networkidle`` state.
* ``retry`` decorator (using tenacity) for robust retry of flaky actions.
"""

from __future__ import annotations

from typing import Callable, TypeVar, Any

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# ---------------------------------------------------------------------------
# Generic type for methods that will be wrapped by the retry decorator.
# ---------------------------------------------------------------------------

F = TypeVar("F", bound=Callable[..., Any])


def retry_on_failure(max_attempts: int = 5, wait_min: float = 1, wait_max: float = 10):
    """Factory that returns a tenacity ``retry`` decorator.

    Parameters
    ----------
    max_attempts: maximum number of retries (including the first try).
    wait_min, wait_max: exponential back‑off bounds in seconds.
    """
    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(min=wait_min, max=wait_max),
        retry=retry_if_exception_type((PlaywrightTimeoutError, Exception)),
    )


class BasePage:
    """Base class for all Page‑Object classes.

    Attributes
    ----------
    page: Playwright ``Page`` – the active browser tab.
    timeout: default timeout for waits (ms).
    """

    def __init__(self, page: Page, timeout: int = 30_000):
        self.page = page
        self.timeout = timeout

    # ---------------------------------------------------------------------
    # Explicit wait helpers
    # ---------------------------------------------------------------------
    def wait_for_visible(self, selector: str) -> None:
        """Wait until *selector* is attached to the DOM and visible.

        Raises ``PlaywrightTimeoutError`` if the element does not become visible
        within ``self.timeout`` milliseconds.
        """
        self.page.wait_for_selector(selector, state="visible", timeout=self.timeout)

    def wait_for_network_idle(self) -> None:
        """Wait for the ``networkidle`` load state – no network requests for 500 ms.
        """
        self.page.wait_for_load_state("networkidle", timeout=self.timeout)

    # ---------------------------------------------------------------------
    # Convenience wrapper – can be used as ``@self.retry`` inside subclasses.
    # ---------------------------------------------------------------------
    @property
    def retry(self) -> Callable[[F], F]:
        """Return a tenacity ``retry`` decorator bound to this page.

        Example usage in a subclass::

            @BasePage.retry
            def click_button(self, selector):
                self.page.click(selector)
        """
        return retry_on_failure()

    # ---------------------------------------------------------------------
    # Generic helper to retrieve text content safely.
    # ---------------------------------------------------------------------
    def get_text(self, selector: str) -> str:
        """Return the trimmed ``inner_text`` of *selector*.

        The element must be visible; otherwise a ``PlaywrightTimeoutError`` is
        raised.
        """
        self.wait_for_visible(selector)
        return self.page.inner_text(selector).strip()

    # ---------------------------------------------------------------------
    # Generic helper for clicking an element.
    # ---------------------------------------------------------------------
    def click(self, selector: str) -> None:
        """Click an element after waiting for it to be visible."""
        self.wait_for_visible(selector)
        self.page.click(selector, timeout=self.timeout)
