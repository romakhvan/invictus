"""
Контент главного экрана для клиента с абонементом.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.mobile.base_content_block import BaseContentBlock


class HomeMemberContent(BaseContentBlock):
    """Контент главного экрана: клиент с абонементом (секция, не страница)."""

    page_title = "Home (Member)"  # для контекста в сообщениях об ошибках

    # Уникальный элемент для определения этого состояния. TODO: заменить на реальный селектор.
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[(contains(@text, "Абонемент") '
        'and not(@text="Абонементы") '
        'and not(@text="Купить абонемент")) '
        'or contains(@resource-id, "membership")]',
    )

    # TODO: Добавить селекторы (дашборд абонемента, остаток занятий и т.д.)

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что отображается контент для клиента с абонементом."""
        self.wait_visible(self.DETECT_LOCATOR, "Контент 'абонемент' не найден")
