"""
Page Object: экран «Скидки от партнёров».

Открывается из таба «Профиль» по кнопке «Смотреть».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class PartnerDiscountsPage(BaseMobilePage):
    """Экран партнёрских скидок с категориями и карточками партнёров."""

    page_title = "Partner Discounts (Скидки от партнёров)"

    CATEGORY_ENTERTAINMENT = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Развлечение"]',
    )
    CATEGORY_RESTAURANTS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Рестораны"]',
    )

    DETECT_LOCATORS = (CATEGORY_ENTERTAINMENT, CATEGORY_RESTAURANTS)

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Скидки от партнёров»."""
        self.wait_visible(
            self.CATEGORY_ENTERTAINMENT,
            "Экран 'Скидки от партнёров': категория 'Развлечение' не найдена",
        )
        self.wait_visible(
            self.CATEGORY_RESTAURANTS,
            "Экран 'Скидки от партнёров': категория 'Рестораны' не найдена",
        )
        print("✅ Экран 'Скидки от партнёров' открыт: категории 'Развлечение' и 'Рестораны' видимы")
