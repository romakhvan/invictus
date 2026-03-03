"""
Page Object: Экран выбора роста.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class HeightPage(BaseMobilePage):
    """Page Object для экрана выбора роста (см)."""

    page_title = "Height (Укажите ваш рост)"

    HEADER = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Укажите ваш рост").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Далее").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def _height_option_locator(self, cm: int):
        """Локатор для значения роста вида 'XXX см'."""
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{cm} см").className("android.widget.TextView")'
        )

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов страницы выбора роста."""
        self.ensure_app_is_active()
        self.wait_present(self.HEADER, "Заголовок 'Укажите ваш рост' не найден")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора роста открыта, все элементы присутствуют")

    def select_height_cm(self, cm: int) -> None:
        """Выбрать рост (в см). Кликает по TextView с текстом '{cm} см'."""
        self.ensure_app_is_active()
        locator = self._height_option_locator(cm)
        self.click(locator)
        print(f"✅ Выбран рост: {cm} см")

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
