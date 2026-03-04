"""
Контент главного экрана для нового пользователя (нет абонемента, офферы, CTA).
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.mobile.base_mobile_page import BaseMobilePage


class HomeNewUserContent(BaseMobilePage):
    """Контент главного экрана: новый пользователь без абонемента."""

    page_title = "Home (New User)"

    # Маркер состояния: уникален для главной нового юзера.
    DETECT_LOCATOR = (AppiumBy.XPATH, '//android.widget.TextView[@text="Нет абонемента"]')

    # Ключевые элементы экрана
    NO_SUBSCRIPTION_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[@text="Нет абонемента"]')
    WANT_BONUSES_BTN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Хочу бонусы!"]')
    TELL_MORE_BTN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Расскажите подробнее!"]')
    OFFER_TITLE = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "10 ДНЕЙ") and contains(@text, "КОМБО-ТРЕНИРОВКИ")]')
    PROGRESS_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[@text="Весь ваш прогресс — в приложении"]')
    PROMO_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Акция для новых клиентов")]')
    # Нижняя навигация
    TAB_MAIN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Главная"]')
    TAB_BOOKINGS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Записи"]')
    TAB_STATS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Статистика"]')
    TAB_PROFILE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Профиль"]')

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что отображается контент для нового пользователя."""
        self.wait_visible(self.DETECT_LOCATOR, "Контент 'новый пользователь' не найден (нет текста 'Нет абонемента')")
        print("✅ Главный экран: контент для нового пользователя")

    def click_want_bonuses(self) -> None:
        """Нажать «Хочу бонусы!»."""
        self.click(self.WANT_BONUSES_BTN)

    def click_tell_more(self) -> None:
        """Нажать «Расскажите подробнее!» (переход к деталям оффера/онбордингу)."""
        self.click(self.TELL_MORE_BTN)
