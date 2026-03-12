"""
Page Object: экран/модалка «Онлайн тренер Gym Buddy».

Открывается с главной по entrypoint «Gym Buddy» / «Онлайн тренер».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class GymBuddyPage(BaseMobilePage):
    """Экран онлайн-тренера Gym Buddy."""

    page_title = "Gym Buddy (Онлайн тренер)"

    # Маркер экрана: заголовок или подпись (на целевом экране может быть тот же текст или заголовок)
    DETECT_LOCATOR = (AppiumBy.XPATH, '//android.widget.TextView[@text="Что такое Gym Buddy?"]')

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран Gym Buddy."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран 'Gym Buddy' не найден (ожидался видимый текст 'Gym Buddy')",
        )
        print("✅ Экран 'Gym Buddy' открыт")

    def wait_loaded(self) -> "GymBuddyPage":
        """Ждёт загрузки экрана Gym Buddy и возвращает self."""
        self.check_and_recover_app_state()
        return super().wait_loaded()
