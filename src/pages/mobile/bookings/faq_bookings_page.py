"""
Page Object: раздел «Вопросы и ответы» внутри таба «Записи».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class FaqBookingsPage(BaseShellPage):
    """Раздел «Вопросы и ответы» в «Записях»."""

    page_title = "Bookings — Вопросы и ответы"

    # Заголовок рендерится как android.view.View, не TextView
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.view.View[@text="Вопросы и ответы"]',
    )

    # Первый пункт FAQ (всегда присутствует на экране)
    FIRST_FAQ_ITEM = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "не могу записаться")]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет ключевые элементы экрана FAQ."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Заголовок 'Вопросы и ответы' не найден",
        )
        self.wait_visible(
            self.FIRST_FAQ_ITEM,
            "Первый пункт FAQ не найден",
        )
        print("✅ Экран 'Вопросы и ответы' открыт, основные элементы присутствуют")
