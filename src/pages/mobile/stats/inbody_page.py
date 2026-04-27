"""
Page Object: модуль InBody внутри раздела «Статистика».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class InBodyPage(BaseShellPage):
    """Экран InBody с описанием оценки состава тела."""

    page_title = "InBody"

    TITLE_INBODY = (AppiumBy.XPATH, '//android.widget.TextView[@text="InBody"]')
    INTRO_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Пройдите оценку Inbody"]',
    )
    DETAILS_TEXT = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "Тест покажет точное количество")]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт модуль InBody."""
        self.wait_visible(
            self.TITLE_INBODY,
            "Заголовок 'InBody' не найден на экране InBody",
        )
        self.wait_visible(
            self.INTRO_TITLE,
            "Текст 'Пройдите оценку Inbody' не найден на экране InBody",
        )
        self.wait_visible(
            self.DETAILS_TEXT,
            "Описание теста InBody не найдено",
        )
        print("✅ Экран InBody открыт, все ключевые элементы присутствуют")
