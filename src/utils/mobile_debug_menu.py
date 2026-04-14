"""
Interactive mobile diagnostics menu used by keepalive / interactive_mobile tests.
"""

from __future__ import annotations

from datetime import datetime

from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage
from src.utils.ui_helpers import take_screenshot


def interactive_debug_menu(driver) -> None:
    """Minimal interactive menu for post-test mobile debugging."""
    while True:
        print("\n" + "=" * 72)
        print("INTERACTIVE MOBILE DEBUG MENU")
        print("=" * 72)
        print("1. Show current package/activity")
        print("2. Save screen diagnostics")
        print("3. Save screenshot")
        print("4. List visible text elements")
        print("0. Exit")

        try:
            choice = input("Select action: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[interactive] Menu interrupted by user")
            return

        if choice == "0":
            print("[interactive] Exit menu")
            return

        if choice == "1":
            _print_current_app_info(driver)
            continue

        if choice == "2":
            context = input("Diagnostics context (optional): ").strip()
            filepath = BaseMobilePage(driver).diagnose_current_screen(context=context)
            print(f"[interactive] Diagnostics saved: {filepath}")
            continue

        if choice == "3":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = take_screenshot(driver, f"keepalive_{timestamp}.png")
            print(f"[interactive] Screenshot saved: {screenshot_path}")
            continue

        if choice == "4":
            _print_visible_text_elements(driver)
            continue

        print("[interactive] Unknown command. Use 0-4.")


def _print_current_app_info(driver) -> None:
    """Prints active mobile package/activity."""
    try:
        print(f"Package:  {driver.current_package}")
        print(f"Activity: {driver.current_activity}")
    except Exception as exc:
        print(f"[interactive] Failed to read package/activity: {exc}")


def _print_visible_text_elements(driver, limit: int = 25) -> None:
    """Prints visible text-like elements for quick locator discovery."""
    try:
        elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
    except Exception as exc:
        print(f"[interactive] Failed to read text elements: {exc}")
        return

    visible = []
    for element in elements:
        try:
            if not element.is_displayed():
                continue
            text = (element.text or "").strip()
            content_desc = (element.get_attribute("content-desc") or "").strip()
            resource_id = (element.get_attribute("resource-id") or "").strip()
            if text or content_desc or resource_id:
                visible.append((text, content_desc, resource_id))
        except Exception:
            continue

    if not visible:
        print("[interactive] No visible text elements found.")
        return

    print(f"[interactive] Visible text elements: {len(visible)}")
    for idx, (text, content_desc, resource_id) in enumerate(visible[:limit], 1):
        print(
            f"[{idx}] text='{text}' | content-desc='{content_desc}' | resource-id='{resource_id}'"
        )
