"""
Page Object: раздел групповых записей внутри таба «Записи».
"""

from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class GroupBookingsPage(BaseShellPage):
    """Раздел «Групповые» в «Записях»."""

    page_title = "Bookings — Групповые"

    # Ключевые элементы раздела «Групповые»
    TITLE_GROUPS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Групповые"]',
    )
    # Единый маркер страницы (используется для детекта/валидации открытия экрана)
    DETECT_LOCATOR = TITLE_GROUPS
    TAB_SCHEDULE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Расписание"]',
    )
    TAB_PROGRAMS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Программы"]',
    )

    def assert_ui(self) -> None:
        """Проверяет, что открыт раздел групповых записей."""
        self.wait_visible(
            self.TITLE_GROUPS,
            "Заголовок 'Групповые' не найден на экране групповых записей",
        )
        self.wait_visible(
            self.TAB_SCHEDULE,
            "Таб 'Расписание' не найден на экране групповых записей",
        )
        self.wait_visible(
            self.TAB_PROGRAMS,
            "Таб 'Программы' не найден на экране групповых записей",
        )

