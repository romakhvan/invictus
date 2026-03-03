"""
Page Object: Экран выбора частоты тренировок в неделю.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class WorkoutFrequencyPage(BaseMobilePage):
    """Page Object для экрана «Сколько раз в неделю хотите заниматься?»."""

    page_title = "Workout Frequency (Частота тренировок)"

    HEADER = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Сколько раз в неделю хотите заниматься?").className("android.widget.TextView")'
    )
    SUBTITLE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Сможем напоминать вам о тренировках").className("android.widget.TextView")'
    )
    OPTION_ONCE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("1 раз").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Далее").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов страницы выбора частоты."""
        self.ensure_app_is_active()
        self.wait_present(self.HEADER, "Заголовок 'Сколько раз в неделю...' не найден")
        self.wait_present(self.SUBTITLE, "Подзаголовок не найден")
        self.wait_visible(self.OPTION_ONCE, "Вариант '1 раз' не найден")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора частоты тренировок открыта, все элементы присутствуют")

    def select_once_per_week(self) -> None:
        """Выбрать «1 раз в неделю»."""
        self.ensure_app_is_active()
        self.click(self.OPTION_ONCE)
        print("✅ Выбрана частота: 1 раз в неделю")

    def is_next_button_enabled(self) -> bool:
        """Проверить, активна ли кнопка 'Далее'."""
        try:
            el = self._wait(5).until(EC.presence_of_element_located(self.NEXT_BUTTON))
            return el.is_enabled()
        except TimeoutException:
            return False

    def click_next(self) -> None:
        """Нажать кнопку 'Далее'."""
        self.ensure_app_is_active()
        self.click(self.NEXT_BUTTON)
        print("✅ Нажата кнопка 'Далее'")
