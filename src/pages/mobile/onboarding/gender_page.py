"""
Page Object: Экран выбора пола.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class GenderPage(BaseMobilePage):
    """Page Object для экрана выбора пола (Женщина / Мужчина)."""

    page_title = "Gender (Выбор пола)"

    HEADER = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Выберите ваш пол").className("android.widget.TextView")'
    )
    SUBTITLE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("раздевалку").className("android.widget.TextView")'
    )
    OPTION_FEMALE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Женщина").className("android.widget.TextView")'
    )
    OPTION_MALE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Мужчина").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Далее").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов страницы выбора пола."""
        self.ensure_app_is_active()
        self.wait_present(self.HEADER, "Заголовок 'Выберите ваш пол' не найден")
        self.wait_present(self.SUBTITLE, "Подзаголовок не найден")
        self.wait_visible(self.OPTION_FEMALE, "Вариант 'Женщина' не найден")
        self.wait_visible(self.OPTION_MALE, "Вариант 'Мужчина' не найден")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора пола открыта, все элементы присутствуют")

    def select_female(self) -> None:
        """Выбрать пол «Женщина»."""
        if self.ensure_app_is_active():
            self.assert_ui()  # после реактивации перепроверяем, что экран пола открыт
        self.click(self.OPTION_FEMALE)
        print("✅ Выбран пол: Женщина")

    def select_male(self) -> None:
        """Выбрать пол «Мужчина»."""
        if self.ensure_app_is_active():
            self.assert_ui()
        self.click(self.OPTION_MALE)
        print("✅ Выбран пол: Мужчина")

    def is_next_button_enabled(self) -> bool:
        """Проверить, активна ли кнопка 'Далее'."""
        try:
            el = self._wait(5).until(EC.presence_of_element_located(self.NEXT_BUTTON))
            return el.is_enabled()
        except TimeoutException:
            return False

    def click_next(self) -> None:
        """Нажать кнопку 'Далее'."""
        if self.ensure_app_is_active():
            self.assert_ui()
        self.click(self.NEXT_BUTTON)
        print("✅ Нажата кнопка 'Далее'")
