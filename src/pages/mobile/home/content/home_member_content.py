"""
Контент главного экрана для клиента с абонементом.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.mobile.base_mobile_page import BaseMobilePage


class HomeMemberContent(BaseMobilePage):
    """Контент главного экрана: клиент с абонементом."""

    page_title = "Home (Member)"

    # Уникальный элемент для определения этого состояния. TODO: заменить на реальный селектор.
    DETECT_LOCATOR = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Абонемент") or contains(@resource-id, "membership")]')

    # TODO: Добавить селекторы (дашборд абонемента, остаток занятий и т.д.)

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что отображается контент для клиента с абонементом."""
        self.wait_visible(self.DETECT_LOCATOR, "Контент 'абонемент' не найден")
        print("✅ Главный экран: контент для клиента с абонементом")
