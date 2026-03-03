"""
Page Object: Экран выбора опыта занятий фитнесом.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class WorkoutExperiencePage(BaseMobilePage):
    """Page Object для экрана «Занимались ли фитнесом до этого?»."""

    page_title = "Workout Experience (Опыт занятий)"

    HEADER = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Занимались").className("android.widget.TextView")'
    )
    OPTION_NO = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Нет").className("android.widget.TextView")'
    )
    OPTION_AT_HOME = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Да, дома").className("android.widget.TextView")'
    )
    OPTION_AT_GYM = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("в зале").className("android.widget.TextView")'
    )
    OPTION_REGULAR = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Регулярно занимаюсь в зале").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Далее").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов страницы выбора опыта."""
        self.ensure_app_is_active()
        self.wait_present(self.HEADER, "Заголовок 'Занимались ли фитнесом до этого?' не найден")
        self.wait_visible(self.OPTION_NO, "Вариант 'Нет' не найден")
        self.wait_visible(self.OPTION_AT_HOME, "Вариант 'Да, дома' не найден")
        self.wait_visible(self.OPTION_AT_GYM, "Вариант 'Да, в зале' не найден")
        self.wait_visible(self.OPTION_REGULAR, "Вариант 'Регулярно занимаюсь в зале' не найден")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора опыта занятий открыта, все элементы присутствуют")

    def select_no(self) -> None:
        """Выбрать «Нет»."""
        self.ensure_app_is_active()
        self.click(self.OPTION_NO)
        print("✅ Выбран опыт: Нет")

    def select_at_home(self) -> None:
        """Выбрать «Да, дома»."""
        self.ensure_app_is_active()
        self.click(self.OPTION_AT_HOME)
        print("✅ Выбран опыт: Да, дома")

    def select_at_gym(self) -> None:
        """Выбрать «Да, в зале»."""
        self.ensure_app_is_active()
        self.click(self.OPTION_AT_GYM)
        print("✅ Выбран опыт: Да, в зале")

    def select_regular(self) -> None:
        """Выбрать «Регулярно занимаюсь в зале»."""
        self.ensure_app_is_active()
        self.click(self.OPTION_REGULAR)
        print("✅ Выбран опыт: Регулярно занимаюсь в зале")

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
