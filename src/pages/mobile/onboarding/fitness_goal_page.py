"""
Page Object: Экран выбора цели тренировок.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class FitnessGoalPage(BaseMobilePage):
    """Page Object для экрана выбора цели тренировок."""

    page_title = "Fitness Goal (Выбор цели тренировок)"

    HEADER = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Выберите цель тренировок").className("android.widget.TextView")'
    )
    SUBTITLE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("групповые тренировки").className("android.widget.TextView")'
    )
    OPTION_MASS = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Набор массы").className("android.widget.TextView")'
    )
    OPTION_WEIGHT_LOSS = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Похудение").className("android.widget.TextView")'
    )
    OPTION_STRENGTH = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Увеличение силы").className("android.widget.TextView")'
    )
    OPTION_ENDURANCE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Выносливость").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Далее").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов страницы выбора цели тренировок."""
        self.wait_present(self.HEADER, "Заголовок 'Выберите цель тренировок' не найден")
        self.wait_present(self.SUBTITLE, "Подзаголовок не найден")
        self.wait_present(self.OPTION_MASS, "Вариант 'Набор массы' не найден")
        self.wait_present(self.OPTION_WEIGHT_LOSS, "Вариант 'Похудение и тонус' не найден")
        self.wait_present(self.OPTION_STRENGTH, "Вариант 'Увеличение силы' не найден")
        self.wait_present(self.OPTION_ENDURANCE, "Вариант 'Выносливость' не найден")
        self.wait_present(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора цели тренировок открыта, все элементы присутствуют")

    def select_mass(self) -> None:
        """Выбрать цель «Набор массы»."""
        self.click(self.OPTION_MASS)
        print("✅ Выбрана цель: Набор массы")

    def select_weight_loss(self) -> None:
        """Выбрать цель «Похудение и тонус»."""
        self.click(self.OPTION_WEIGHT_LOSS)
        print("✅ Выбрана цель: Похудение")

    def select_strength(self) -> None:
        """Выбрать цель «Увеличение силы»."""
        self.click(self.OPTION_STRENGTH)
        print("✅ Выбрана цель: Увеличение силы")

    def select_endurance(self) -> None:
        """Выбрать цель «Выносливость»."""
        self.click(self.OPTION_ENDURANCE)
        print("✅ Выбрана цель: Выносливость")

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
