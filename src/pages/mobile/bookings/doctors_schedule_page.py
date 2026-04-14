"""
Page Object: страница записи к врачу со списком врачей и расписанием.
"""

from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class DoctorsSchedulePage(BaseShellPage):
    """Экран «Запись к врачу» со списком врачей."""

    page_title = "Bookings — Запись к врачу"

    TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Запись к врачу"]',
    )
    DETECT_LOCATOR = TITLE
    DOCTORS_LIST = (AppiumBy.CLASS_NAME, "android.widget.ScrollView")

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран записи к врачу."""
        self.wait_visible(
            self.TITLE,
            "Заголовок 'Запись к врачу' не найден",
        )
        self.wait_visible(
            self.DOCTORS_LIST,
            "Список врачей не найден на экране 'Запись к врачу'",
        )
        print("✅ Экран 'Запись к врачу' открыт, список врачей отображается")
