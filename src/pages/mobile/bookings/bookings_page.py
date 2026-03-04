"""
Page Object: таб «Записи».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class BookingsPage(BaseShellPage):
    """Раздел «Записи» (список записей/бронирований)."""

    page_title = "Bookings (Записи)"

    # Ключевые элементы экрана «Записи»
    TITLE_MY_BOOKINGS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Мои записи"]',
    )
    EMPTY_STATE_TEXT = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Здесь будут ваши записи"]',
    )
    SECTION_PERSONAL_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Персональные"]',
    )
    SECTION_PERSONAL_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Доверьтесь тренеру"]',
    )
    SECTION_GROUP_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Групповые"]',
    )
    SECTION_GROUP_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Расписание и программы"]',
    )
    SECTION_DOCTORS_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Доктора"]',
    )
    SECTION_DOCTORS_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Список довереных докторов"]',
    )
    SECTION_EVENTS_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Ивенты"]',
    )
    SECTION_EVENTS_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Загляните в афишу"]',
    )
    SECTION_FAQ_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Вопросы и ответы"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Записи»."""
        self.wait_visible(
            self.TITLE_MY_BOOKINGS,
            "Заголовок 'Мои записи' не найден на экране 'Записи'",
        )
        self.wait_visible(
            self.EMPTY_STATE_TEXT,
            "Текст пустого состояния 'Здесь будут ваши записи' не найден",
        )
        self.wait_visible(
            self.SECTION_PERSONAL_TITLE,
            "Заголовок секции 'Персональные' не найден",
        )
        self.wait_visible(
            self.SECTION_GROUP_TITLE,
            "Заголовок секции 'Групповые' не найден",
        )
        self.wait_visible(
            self.SECTION_DOCTORS_TITLE,
            "Заголовок секции 'Доктора' не найден",
        )
        self.wait_visible(
            self.SECTION_EVENTS_TITLE,
            "Заголовок секции 'Ивенты' не найден",
        )
        self.wait_visible(
            self.SECTION_FAQ_TITLE,
            "Заголовок секции 'Вопросы и ответы' не найден",
        )
        print("✅ Экран 'Записи' открыт")
