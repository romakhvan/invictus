"""
Page Object: раздел персональных записей внутри таба «Записи».
"""

from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class PersonalBookingsPage(BaseShellPage):
    """Раздел «Персональные» в «Записях»."""

    page_title = "Bookings — Персональные"

    # Ключевые элементы раздела «Персональные»
    TITLE_PERSONAL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Персональные"]',
    )
    # Единый маркер страницы (используется для детекта/валидации открытия экрана)
    DETECT_LOCATOR = TITLE_PERSONAL
    TAB_TRAINERS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Тренеры"]',
    )
    TAB_SCHEDULE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Расписание"]',
    )

    def assert_ui(self) -> None:
        """Проверяет, что открыт раздел персональных записей."""
        self.wait_visible(
            self.TITLE_PERSONAL,
            "Заголовок 'Персональные' не найден на экране персональных тренировок",
        )
        self.wait_visible(
            self.TAB_TRAINERS,
            "Таб 'Тренеры' не найден на экране персональных тренировок",
        )
        self.wait_visible(
            self.TAB_SCHEDULE,
            "Таб 'Расписание' не найден на экране персональных тренировок",
        )

