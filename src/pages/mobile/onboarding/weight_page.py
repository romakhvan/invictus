"""
Page Object: Экран выбора веса.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class WeightPage(BaseMobilePage):
    """Page Object для экрана выбора веса (кг)."""

    page_title = "Weight (Укажите ваш вес)"

    HEADER = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Укажите ваш вес").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Далее").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def _weight_option_locator(self, kg: int):
        """Локатор для значения веса вида 'XX кг'."""
        return (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{kg} кг").className("android.widget.TextView")'
        )

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов страницы выбора веса."""
        self.wait_present(self.HEADER, "Заголовок 'Укажите ваш вес' не найден")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора веса открыта, все элементы присутствуют")

    def select_weight_kg(self, kg: int) -> None:
        """Выбрать вес (в кг). Кликает по TextView с текстом '{kg} кг'."""
        locator = self._weight_option_locator(kg)
        self.click(locator)
        print(f"✅ Выбран вес: {kg} кг")

    def is_next_button_enabled(self) -> bool:
        """Проверить, активна ли кнопка 'Далее'."""
        try:
            el = self._wait(5).until(EC.presence_of_element_located(self.NEXT_BUTTON))
            return el.is_enabled()
        except TimeoutException:
            return False

    def click_next(self) -> None:
        """Нажать кнопку 'Далее'."""
        self.click(self.NEXT_BUTTON)
        print("✅ Нажата кнопка 'Далее'")
