"""
Page Object: Экран выбора даты рождения.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class BirthDatePage(BaseMobilePage):
    """Page Object для экрана выбора даты рождения."""
    
    page_title = "Birth Date (Выбор даты рождения)"
    
    # UiAutomator локаторы (более надежны для Android)

    HEADER = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("родил")')
    SUBTITLE = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Выберите дату рождения").className("android.widget.TextView")'
    )
    NEXT_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().descriptionContains("Далее")'
    )
    
    # TODO: Добавить локаторы для элементов выбора даты (день, месяц, год)
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def assert_ui(self):
        """Проверяет наличие всех ключевых элементов страницы даты рождения."""

        self.wait_present(self.HEADER, "Заголовок 'Когда вы родились?' не найден")
        self.wait_present(self.SUBTITLE, "Подзаголовок 'Выберите дату рождения' не найден")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница выбора даты рождения открыта, все элементы присутствуют")
    
    def is_next_button_enabled(self) -> bool:
        """Проверить, активна ли кнопка 'Далее'."""
        try:
            el = self._wait(5).until(EC.presence_of_element_located(self.NEXT_BUTTON))
            return el.is_enabled()
        except TimeoutException:
            return False
    
    def swipe_date_picker(self, start_x: int = 933, start_y: int = 1004, 
                          end_x: int = 922, end_y: int = 1687) -> None:
        """
        Свайп по датапикеру для выбора даты.
        
        Args:
            start_x: Начальная координата X
            start_y: Начальная координата Y
            end_x: Конечная координата X
            end_y: Конечная координата Y
        """
        self.swipe_by_w3c_actions(start_x, start_y, end_x, end_y)
        print(f"✅ Выполнен свайп от ({start_x}, {start_y}) до ({end_x}, {end_y})")
    
    def click_next(self) -> None:
        """Нажать кнопку 'Далее'."""
        self.click(self.NEXT_BUTTON)
        print("✅ Нажата кнопка 'Далее'")
