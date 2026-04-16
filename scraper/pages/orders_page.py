"""OrdersPage – handles filter application, pagination and data extraction.

The selectors are based on the HTML snippets you provided. If the exact
structure changes, adjust the constants accordingly.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict

from playwright.sync_api import Page

from .base_page import BasePage
from ..logger import log


def parse_order_date(date_str: str):
    """Parse date string like 'Сьогодні 20:18', 'Вчора 14:30', '14.04 10:00', '13.04.2026 10:00'.
    
    Returns only date, no time.
    """
    import re
    from datetime import date, time, datetime
    
    today = date.today()
    
    stripped = date_str.strip()
    
    # Check for patterns that look like "WORD HH:MM" where WORD could be garbled
    time_pattern_match = re.match(r"^([a-zA-Zа-яА-ЯёЁ?]+)\s+(\d{1,2}):(\d{2})$", stripped)
    if time_pattern_match:
        word = time_pattern_match.group(1)
        
        # Try to detect readable Cyrillic first
        lower_word = word.lower()
        if 'сьогодн' in lower_word:
            return today
        if 'вчора' in lower_word:
            if today.day > 1:
                return today.replace(day=today.day - 1)
            else:
                if today.month > 1:
                    import calendar
                    prev_month = today.month - 1
                    last_day = calendar.monthrange(today.year, prev_month)[1]
                    return today.replace(month=prev_month, day=last_day)
                else:
                    return today.replace(year=today.year - 1, month=12, day=31)
        
        # Check if word contains replacement characters, question marks, or non-ASCII
        # (garbled text - could be "Сьогодні" or "Вчора")
        has_replacement = '\ufffd' in word
        has_question = '?' in word
        has_non_ascii = any(ord(c) > 127 for c in word)
        
        if has_replacement or has_question or has_non_ascii:
            # Use word length to determine: "Вчора" = 5 chars, "Сьогодні" = 8 chars
            word_len = len(word)
            if word_len <= 6:
                # Likely "Вчора" (5-6 chars) - yesterday
                if today.day > 1:
                    return today.replace(day=today.day - 1)
                else:
                    if today.month > 1:
                        import calendar
                        prev_month = today.month - 1
                        last_day = calendar.monthrange(today.year, prev_month)[1]
                        return today.replace(month=prev_month, day=last_day)
                    else:
                        return today.replace(year=today.year - 1, month=12, day=31)
            else:
                # Likely "Сьогодні" (7+ chars) - today
                return today
        
        # If we can't determine, default to today
        return today
    
    # Try parsing as DD.MM.YYYY HH:MM or DD.MM.YYYY
    for fmt in ["%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            dt = datetime.strptime(stripped, fmt)
            return dt.date()
        except ValueError:
            continue
    
    # Try parsing as DD.MM HH:MM (without year - assume current year)
    match = re.match(r"(\d{1,2})\.(\d{1,2})\s+(\d{1,2}):(\d{2})", stripped)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        try:
            return today.replace(month=month, day=day)
        except ValueError:
            pass
    
    # Try ISO format
    try:
        dt = datetime.fromisoformat(stripped)
        return dt.date()
    except ValueError:
        pass
    
    # Default to today if parsing fails
    return today


class OrdersPage(BasePage):
    # ---------------------------------------------------------------------
    # Selectors (CSS) – derived from the HTML fragments you gave.
    # ---------------------------------------------------------------------
    FILTER_ICON_SELECTOR = "span.search__filter-button i.key-icon--sliders"

    # Manager filter – the input inside the manager select dropdown.
    MANAGER_INPUT_SELECTOR = "div.el-select__tags input.el-select__input.is-small"

    # Status filter – each status is a <div class='status ...'> with a child
    # <span class='name'> containing the human‑readable name.
    # We will locate a status block by the visible text of the inner span.
    STATUS_BLOCK_XPATH = "//div[contains(@class, 'status') and .//span[contains(@class, 'name') and normalize-space(text())='{name}']]"

    # Rows‑per‑page – clicking the caret opens a dropdown, then we select the
    # option with the exact numeric text.
    ROWS_CARET_SELECTOR = "i.el-icon-arrow-up"
    ROWS_OPTION_XPATH = "//div[contains(@class, 'el-select-dropdown')]//li[normalize-space(text())='{rows}']"

    # Table rows – each order appears as a <tr> that contains the specific
    # data‑title attributes. We locate rows by the presence of the order number
    # cell.
    ORDER_ROW_SELECTOR = "tr:has(td[data-title='№ замовлення'])"

    # Individual cells inside a row.
    ORDER_ID_CELL = "td[data-title='№ замовлення']"
    CREATED_AT_CELL = "td[data-title='Час створення']"
    STATUS_SPAN = "span.status"  # matches <span class='status ...'> inside the row
    MANAGER_NAME_SELECTOR = "div.order-manager span:not(.user-avatar)"  # manager name
    TOTAL_COST_CELL = "td[data-title='Загальна вартість'] .price-value"
    CLOSED_AT_CELL = "td[data-title='Час закриття']"

    # Pagination – next button.
    NEXT_BUTTON_SELECTOR = "button.btn-next"
    
    # Rows per page selector (on main page, not in filter panel)
    ROWS_DROPDOWN_SELECTOR = "div.el-select.transparent.el-select--small input.el-input__inner"
    ROWS_OPTION_SELECTOR = "li.el-select-dropdown__item:has-text('{rows}')"

    def __init__(self, page: Page, timeout: int = 30_000):
        super().__init__(page, timeout)

    # ---------------------------------------------------------------------
    # Filter panel handling
    # ---------------------------------------------------------------------
    SAVED_FILTER_BUTTON = "div.el-button-group button:has-text('А/С')"
    DELETE_SAVED_FILTER = "button.el-icon-delete"
    
    def open_filter_panel(self) -> None:
        """Click the filter icon to reveal the filter sidebar/panel."""
        log.info("Opening filter panel")
        self.click(self.FILTER_ICON_SELECTOR)
        self.wait_for_network_idle()
        self.page.wait_for_timeout(1000)

    def apply_saved_filter(self) -> None:
        """Click the saved filter button to apply saved filter."""
        log.info("Applying saved filter")
        
        # Wait for button to be present
        self.page.wait_for_selector(self.SAVED_FILTER_BUTTON, timeout=10000)
        
        # Wait until button is NOT disabled
        log.info("Waiting for filter button to be enabled...")
        try:
            # Wait for the button to become enabled (not disabled)
            self.page.wait_for_selector(
                "div.el-button-group button:has-text('А/С'):not([disabled])",
                timeout=30000
            )
            log.info("Filter button is now enabled, clicking...")
            self.page.click("div.el-button-group button:has-text('А/С')")
            self.wait_for_network_idle()
            self.page.wait_for_timeout(2000)
            log.info("Saved filter applied")
        except Exception as e:
            log.error("Filter button still disabled or not found", error=str(e))
            # Try clicking anyway
            self.page.click("div.el-button-group button:has-text('А/С')")
        
        # After applying filter, ensure all status checkboxes are checked
        self.ensure_all_statuses_enabled()

    def ensure_all_statuses_enabled(self) -> None:
        """Click on each status to ensure it's checked (enabled)."""
        log.info("Ensuring all status filters are enabled")
        
        statuses = ["Новий", "Погодження", "Виробництво", "Доставка", "Виконано", "Відмінено"]
        
        for status_name in statuses:
            try:
                # Find the status element
                status_selector = f"div.status:has-text('{status_name}')"
                status_elem = self.page.query_selector(status_selector)
                
                if status_elem:
                    # Check if it has 'checked' class
                    classes = status_elem.get_attribute("class") or ""
                    if "checked" not in classes:
                        log.info(f"Enabling status: {status_name}")
                        status_elem.click()
                        self.page.wait_for_timeout(300)
                    else:
                        log.debug(f"Status already enabled: {status_name}")
            except Exception as e:
                log.error(f"Could not toggle status {status_name}", error=str(e))
        
        self.wait_for_network_idle()
        self.page.wait_for_timeout(1000)
        log.info("All status filters enabled")

    # ---------------------------------------------------------------------
    # Manager filter – type manager name into the searchable select, wait for
    # dropdown to appear, then click on the option.
    # ---------------------------------------------------------------------
    def apply_manager_filters(self, managers: List[str]) -> None:
        if not managers:
            log.info("No manager filters provided – skipping")
            return
        log.info("Applying manager filters", managers=managers)
        self.open_filter_panel()
        
        # Wait for the manager input to be visible
        self.wait_for_visible(self.MANAGER_INPUT_SELECTOR)
        
        for manager in managers:
            log.info("Adding manager filter", manager=manager)
            
            # Click on the tags container to focus the input
            self.page.click("div.el-select__tags")
            
            # Fill the manager name using type (character by character)
            self.page.type(self.MANAGER_INPUT_SELECTOR, manager, delay=50)
            
            # Wait a moment for dropdown to appear
            self.page.wait_for_timeout(500)
            
            # Click on the option in dropdown
            option_selector = f"li.el-select-dropdown__item:has-text('{manager}')"
            try:
                self.wait_for_visible(option_selector)
                self.page.click(option_selector)
                log.info("Added manager", manager=manager)
            except Exception as e:
                log.error("Could not find manager option", manager=manager, error=str(e))
                # Try pressing Enter instead
                self.page.keyboard.press("Enter")
            
            # Wait before adding next manager
            self.page.wait_for_timeout(300)
        
        log.info("Manager filters applied")

    # ---------------------------------------------------------------------
    # Status filter – click status blocks to toggle them. By default all statuses
    # are checked, but we allow explicit selection.
    # ---------------------------------------------------------------------
    def apply_status_filters(self, statuses: List[str]) -> None:
        if not statuses:
            log.info("No status filters provided – keeping defaults (all)")
            return
        log.info("Applying status filters", statuses=statuses)
        self.open_filter_panel()
        for status in statuses:
            xpath = self.STATUS_BLOCK_XPATH.format(name=status)
            try:
                # Wait for the status block to be visible then click it.
                self.page.wait_for_selector(xpath, state="visible", timeout=self.timeout)
                self.page.click(xpath)
                log.debug("Toggled status filter", status=status)
            except Exception as exc:
                log.warning("Status filter element not found", status=status, error=str(exc))
        # Close panel
        self.page.click(self.FILTER_ICON_SELECTOR)
        self.wait_for_network_idle()

    # ---------------------------------------------------------------------
    # Rows‑per‑page selector
    # ---------------------------------------------------------------------
    def set_rows_per_page(self, rows: int) -> None:
        log.info("Setting rows per page", rows=rows)
        self.open_filter_panel()
        # Click the caret to open the dropdown.
        self.click(self.ROWS_CARET_SELECTOR)
        # Choose the option matching the number.
        option_xpath = self.ROWS_OPTION_XPATH.format(rows=rows)
        self.page.wait_for_selector(option_xpath, state="visible", timeout=self.timeout)
        self.page.click(option_xpath)
        self.wait_for_network_idle()

    def set_rows_per_page_on_page(self, rows: int) -> None:
        """Set rows per page directly on the orders page (not in filter panel)."""
        log.info("Setting rows per page on page", rows=rows)
        try:
            # Press Escape multiple times to close any open panels
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
            
            # Click on the select trigger element
            select_trigger = "div.el-select.transparent.el-select--small"
            self.page.click(select_trigger)
            self.page.wait_for_timeout(500)
            
            # Wait for dropdown to appear and click option
            option_xpath = f"//li[contains(@class, 'el-select-dropdown__item')]//span[text()='{rows}']"
            self.page.wait_for_selector(option_xpath, state="visible", timeout=10000)
            self.page.click(option_xpath)
            
            # Wait longer for the page to reload with new row count
            self.page.wait_for_timeout(2000)
            self.wait_for_network_idle()
            self.page.wait_for_timeout(1000)
            
            # Verify the setting was applied by checking the display text
            display_text = self.page.inner_text(".display-text")
            log.info("Display text after setting rows", text=display_text)
            
            log.info("Rows per page set successfully")
        except Exception as e:
            log.error("Failed to set rows per page", error=str(e))

    # ---------------------------------------------------------------------
    # Data extraction from the current page
    # ---------------------------------------------------------------------
    def _get_displayed_count(self) -> int:
        """Get the number of rows shown on page from display text (e.g. '1 - 50')."""
        try:
            display_elem = self.page.query_selector(".display-text")
            if display_elem:
                text = display_elem.inner_text()
                import re
                match = re.search(r"(\d+)\s*-\s*(\d+)", text)
                if match:
                    return int(match.group(2)) - int(match.group(1)) + 1
        except Exception:
            pass
        return 0

    def extract_orders_from_page(self, expected_rows: int = 50) -> List[Dict]:
        """Parse all order rows visible on the current page.

        Args:
            expected_rows: Expected row count to verify extraction success.
        """
        log.info("Extracting orders from current page")
        self.wait_for_visible(self.ORDER_ROW_SELECTOR)
        
        max_retries = 3
        rows = []
        
        displayed_count = self._get_displayed_count()
        target_rows = displayed_count if displayed_count > 0 else expected_rows
        
        for attempt in range(max_retries):
            rows = self.page.query_selector_all(self.ORDER_ROW_SELECTOR)
            log.info("Found rows in DOM", count=len(rows), attempt=attempt + 1)
            
            # Get expected count from display text
            log.info("Displayed count from UI", count=displayed_count)
            
            # If we have enough rows matching displayed count, stop retrying
            if len(rows) >= target_rows:
                log.info("Got expected row count")
                break
            
            # Wait and retry
            log.info("Retrying to get more rows...", current=len(rows), expected=target_rows)
            self.page.wait_for_timeout(1000)
        
        if not rows:
            log.warning("No order rows found on page")
            return []
        orders: List[Dict] = []
        for idx, row in enumerate(rows):
            try:
                order_id = row.query_selector(self.ORDER_ID_CELL).inner_text().strip()
                created_at_raw = row.query_selector(self.CREATED_AT_CELL).inner_text().strip()
                created_at = parse_order_date(created_at_raw)
                
                # Parse closed_at (optional - may be empty)
                closed_at = None
                closed_at_elem = row.query_selector(self.CLOSED_AT_CELL)
                if closed_at_elem:
                    closed_at_raw = closed_at_elem.inner_text().strip()
                    if closed_at_raw:
                        closed_at = parse_order_date(closed_at_raw)
                
                status = row.query_selector(self.STATUS_SPAN).inner_text().strip()
                manager = row.query_selector(self.MANAGER_NAME_SELECTOR).inner_text().strip()
                total_raw = row.query_selector(self.TOTAL_COST_CELL).inner_text().strip()
                # Normalise total cost – replace non‑breaking spaces and commas.
                total_clean = total_raw.replace("\xa0", "").replace(",", ".")
                # Remove any currency symbols / letters.
                total_clean = "".join(ch for ch in total_clean if ch.isdigit() or ch == ".")
                total = float(total_clean) if total_clean else 0.0

                orders.append(
                    {
                        "order_id": order_id,
                        "created_at": created_at,
                        "closed_at": closed_at,
                        "status": status,
                        "manager": manager,
                        "total_cost": total,
                    }
                )
            except Exception as exc:
                log.error("Failed to parse row", index=idx, error=str(exc), row_html=row.inner_html()[:200] if row else "N/A")
                continue
        log.info("Extracted orders count", count=len(orders))
        return orders

    # ---------------------------------------------------------------------
    # Pagination handling
    # ---------------------------------------------------------------------
    def go_to_next_page(self) -> bool:
        """Click the "next" button if it is enabled.

        Returns ``True`` when the click succeeded and a new page is loading,
        ``False`` when the button is disabled (last page).
        """
        try:
            btn = self.page.query_selector(self.NEXT_BUTTON_SELECTOR)
            if not btn:
                log.info("Next button not found – assuming single page")
                return False
            # Check for disabled attribute or class – the implementation may vary.
            disabled = btn.get_attribute("disabled") or "disabled" in (btn.get_attribute("class") or "")
            if disabled:
                log.info("Next button disabled – reached last page")
                return False
            log.info("Clicking next page button")
            btn.click()
            self.wait_for_network_idle()
            return True
        except Exception as exc:
            log.warning("Error while trying to go to next page", error=str(exc))
            return False
