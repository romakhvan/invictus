"""
Page Object: раздел записей к докторам внутри таба «Записи».

Локаторы для валидации будут добавлены позже.
"""

from appium.webdriver import Remote

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class DoctorsBookingsPage(BaseShellPage):
    """Раздел «Доктора» в «Записях»."""

    page_title = "Bookings — Доктора"

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """
        Проверяет, что открыт раздел записей к докторам.

        TODO: добавить локаторы ключевых элементов и проверки.
        """
        print("✅ Открыт раздел 'Доктора' (детальные проверки будут добавлены позже)")

