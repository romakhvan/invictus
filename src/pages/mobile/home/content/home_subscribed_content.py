"""
Контент главного экрана для клиента с подпиской.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.mobile.base_content_block import BaseContentBlock


class HomeSubscribedContent(BaseContentBlock):
    """Контент главного экрана: клиент с активной подпиской (секция, не страница)."""

    page_title = "Home (Subscribed)"  # для контекста в сообщениях об ошибках

    # Уникальный элемент для определения этого состояния. TODO: заменить на реальный селектор.
    DETECT_LOCATOR = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Подписка") or contains(@resource-id, "subscription")]')

    # TODO: Добавить селекторы (дашборд подписки, разделы и т.д.)

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что отображается контент для клиента с подпиской."""
        self.wait_visible(self.DETECT_LOCATOR, "Контент 'подписка' не найден")
