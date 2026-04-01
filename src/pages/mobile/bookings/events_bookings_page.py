"""
Page Object: раздел ивентов внутри таба «Записи».

Локаторы для валидации будут добавлены позже.
"""

from appium.webdriver import Remote

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class EventsBookingsPage(BaseShellPage):
    """Раздел «Ивенты» в «Записях»."""

    page_title = "Bookings — Ивенты"

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """
        Проверяет, что открыт раздел ивентов.

        TODO: добавить локаторы ключевых элементов и проверки.
        """
        print("✅ Открыт раздел 'Ивенты' (детальные проверки будут добавлены позже)")

