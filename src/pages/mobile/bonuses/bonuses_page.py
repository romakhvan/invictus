"""
Page Object: экран «Бонусы».

Открывается с главной (NEW_USER) по кнопке «Хочу бонусы!».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class BonusesPage(BaseMobilePage):
    """Экран бонусов."""

    page_title = "Bonuses (Бонусы)"

    # Маркер экрана: заголовок «Ваши бонусы»
    DETECT_LOCATOR = (AppiumBy.XPATH, '//android.widget.TextView[@text="Ваши бонусы"]')

    # Ключевые элементы экрана
    TITLE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Ваши бонусы"]')
    HISTORY_LINK = (AppiumBy.XPATH, '//android.widget.TextView[@text="История бонусов"]')
    WHAT_ARE_BONUSES = (AppiumBy.XPATH, '//android.widget.TextView[@text="Что это за бонусы такие"]')
    FAQ_LINK = (AppiumBy.XPATH, '//android.widget.TextView[@text="Вопросы и ответы"]')
    HOW_TO_GET = (AppiumBy.XPATH, '//android.widget.TextView[@text="Как получить бонусы"]')
    BUY_ABONEMENTS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Покупайте абонементы"]')

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Бонусы» (заголовок «Ваши бонусы»)."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            'Экран "Бонусы" не найден (ожидался заголовок "Ваши бонусы")',
        )
        print('✅ Экран "Бонусы" открыт')

    def wait_loaded(self) -> "BonusesPage":
        """Ждёт загрузки экрана «Бонусы» и возвращает self."""
        self.check_and_recover_app_state()
        return super().wait_loaded()

