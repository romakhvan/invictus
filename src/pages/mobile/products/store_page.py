"""
Page Object: экран/лендинг «Store».

Открывается с главной по entrypoint «Store».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class StorePage(BaseMobilePage):
    """Экран магазина Store."""

    page_title = "Store"

    # Ключевые элементы экрана Store.
    TITLE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Store"]')
    CATEGORY_CLOTHES = (AppiumBy.XPATH, '//android.widget.TextView[@text="Одежда и прочее"]')
    CATEGORY_SUPPLEMENTS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Спортпит и БАДы"]')

    # Маркер экрана: сам заголовок Store.
    DETECT_LOCATOR = TITLE

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран Store."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран 'Store' не найден (ожидался заголовок 'Store')",
        )
        self.wait_visible(
            self.CATEGORY_CLOTHES,
            "Экран 'Store': не найдена категория 'Одежда и прочее'",
        )
        self.wait_visible(
            self.CATEGORY_SUPPLEMENTS,
            "Экран 'Store': не найдена категория 'Спортпит и БАДы'",
        )
        print("✅ Экран 'Store' открыт")

    def wait_loaded(self) -> "StorePage":
        """Ждёт загрузки экрана Store и возвращает self."""
        self.check_and_recover_app_state()
        return super().wait_loaded()
