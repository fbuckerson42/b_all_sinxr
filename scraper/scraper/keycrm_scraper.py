"""Core scraping workflow for KeyCRM.

The module brings together the Page Object classes, database persistence,
and user confirmations into a single executable flow.
"""

from __future__ import annotations

from typing import List

from playwright.sync_api import sync_playwright, Browser, Page

from ..config import settings
from ..logger import log
from ..db.repository import init_db, upsert_orders_batch
from ..pages.login_page import LoginPage
from ..pages.dashboard_page import DashboardPage
from ..pages.orders_page import OrdersPage


def run(
    headless: bool = False,
    managers: List[str] | None = None,
    statuses: List[str] | None = None,
    rows_per_page: int = 100,
    skip_confirmation: bool = False,
    limit: int | None = None,
) -> None:
    """Execute the complete scraping workflow.

    Parameters
    ----------
    headless: Run browser in headless mode.
    managers: List of manager names to filter.
    statuses: List of order statuses to filter.
    rows_per_page: Number of rows per page (default 100).
    skip_confirmation: Skip interactive confirmations.
    limit: Maximum number of orders to scrape (for testing). None = scrape all.
    """
    managers = managers or []
    statuses = statuses or []

    log.info(
        "Starting scraper",
        headless=headless,
        managers=managers,
        statuses=statuses,
        rows_per_page=rows_per_page,
    )

    # ---------------------------------------------------------------------
    # 1. Initialise database
    # ---------------------------------------------------------------------
    init_db()

    # ---------------------------------------------------------------------
    # 2. Launch Playwright
    # ---------------------------------------------------------------------
    playwright = sync_playwright().start()
    browser: Browser = playwright.chromium.launch(headless=headless)
    page: Page = browser.new_page()

    try:
        # -----------------------------------------------------------------
        # 3. Login
        # -----------------------------------------------------------------
        login_page = LoginPage(page)
        login_page.goto()
        login_page.login()

        # Confirm with the user
        _ask_confirmation("Login", skip=skip_confirmation)

        # -----------------------------------------------------------------
        # 4. Navigate to Orders
        # -----------------------------------------------------------------
        dashboard = DashboardPage(page)
        dashboard.go_to_orders()

        orders_page = OrdersPage(page)

        # -----------------------------------------------------------------
        # 5. Apply filters
        # -----------------------------------------------------------------
        # Open filter panel and apply saved filter
        orders_page.open_filter_panel()
        orders_page.apply_saved_filter()
        
        # Set rows per page to 50
        orders_page.set_rows_per_page_on_page(50)
        
        # Confirm with the user before scraping
        _ask_confirmation("Filtry prymeno", skip=skip_confirmation)

        # -----------------------------------------------------------------
        # 6. Scrape all pages (pagination)
        # -----------------------------------------------------------------
        total_collected = 0
        page_number = 1

        while True:
            log.info("Scraping page", page=page_number)
            orders = orders_page.extract_orders_from_page()

            if not orders:
                log.info("No orders found on page – stopping")
                break

            # Insert batch after each page
            try:
                upsert_orders_batch(orders)
                log.info("Batch inserted", count=len(orders))
            except Exception as exc:
                log.error("Failed to insert batch", error=str(exc))

            total_collected += len(orders)
            log.info("Collected orders so far", page=page_number, count=len(orders), total=total_collected)

            # Check if we've reached the limit
            if limit and total_collected >= limit:
                log.info("Reached limit", limit=limit)
                break

            # Move to next page
            if not orders_page.go_to_next_page():
                log.info("No more pages – pagination finished")
                break

            page_number += 1

        log.success("Scraping complete", total_orders=total_collected)

    except Exception as exc:
        log.error("Scraper failed", error=str(exc))
        raise
    finally:
        browser.close()
        playwright.stop()


def _ask_confirmation(step: str, skip: bool = False) -> None:
    """Prompt the user for confirmation after a major step.

    If skip is True (--yes flag), skips the interactive prompt.
    Otherwise blocks until the user confirms with Enter (or any text other than 'no').
    If the user enters 'no', the process aborts.
    """
    import sys

    if skip:
        print(f"\n[OK] {step} zaversheno. (auto-confirmed)")
        return

    print(f"\n[OK] {step} zaversheno.")
    try:
        resp = input("Vse vyhlyadaye pravylno? Press Enter or type 'no': ")
    except EOFError:
        resp = ""
    resp = resp.strip().lower()

    if resp == "no":
        print("Proces zupyneno korustuvachem.")
        sys.exit(0)
