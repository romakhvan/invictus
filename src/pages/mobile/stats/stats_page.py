"""
Page Object: таб «Статистика».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class StatsPage(BaseShellPage):
    """Раздел «Статистика» (прогресс и аналитика тренировок)."""

    page_title = "Stats (Статистика)"

    # Ключевые элементы экрана «Статистика»
    TITLE_MY_STATS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Моя статистика"]',
    )
    EMPTY_STATE_LINE1 = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Тут появятся время в зале и история посещений"]',
    )
    EMPTY_STATE_LINE2 = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Ходите на тренировки, а потом заглядывайте сюда"]',
    )
    CTA_SELECT_SUBSCRIPTION = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Выбрать абонемент"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Статистика»."""
        self.wait_visible(
            self.TITLE_MY_STATS,
            "Заголовок 'Моя статистика' не найден на экране 'Статистика'",
        )
        self.wait_visible(
            self.EMPTY_STATE_LINE1,
            "Текст пустого состояния статистики не найден",
        )
        self.wait_visible(
            self.CTA_SELECT_SUBSCRIPTION,
            "Кнопка 'Выбрать абонемент' не найдена",
        )
        print("✅ Экран 'Статистика' открыт")
