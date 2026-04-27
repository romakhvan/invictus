"""
Page Object: экран «Гостевые посещения».

Открывается из таба «Профиль» по кнопке «Гостевые посещения».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class GuestVisitsPage(BaseMobilePage):
    """Экран гостевых посещений: покупка и подарки от друзей."""

    page_title = "Guest Visits (Гостевые посещения)"

    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Приходите в клуб вместе с друзьями"]',
    )
    CTA_BUY = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Купить"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Гостевые посещения»."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран 'Гостевые посещения': текст 'Приходите в клуб вместе с друзьями' не найден",
        )
        self.wait_visible(
            self.CTA_BUY,
            "Экран 'Гостевые посещения': кнопка 'Купить' не найдена",
        )
        print("✅ Экран 'Гостевые посещения' открыт: описание и кнопка 'Купить' присутствуют")
