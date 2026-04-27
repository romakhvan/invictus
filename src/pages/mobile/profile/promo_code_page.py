"""
Page Object: экран ввода промокода.

Открывается из таба «Профиль» по кнопке «Использовать промокод».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class PromoCodePage(BaseMobilePage):
    """Экран ввода промокода."""

    page_title = "Promo Code (Промокод)"

    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Введите свой промокод"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран ввода промокода."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран промокода: поле 'Введите свой промокод' не найдено",
        )
        print("✅ Экран ввода промокода открыт")
