"""
Page Object: Экран заполнения имени и фамилии.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.base_mobile_page import BaseMobilePage


class NamePage(BaseMobilePage):
    """Page Object для экрана ввода имени и фамилии."""
    
    page_title = "Name (Ввод имени и фамилии)"
    
    HEADER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Как вас зовут?"]')
    SUBTITLE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Укажите данные из удостоверения"]')
    NAME_INPUT = (AppiumBy.XPATH, '//android.widget.EditText[@text="Имя"]')
    SURNAME_INPUT = (AppiumBy.XPATH, '//android.widget.EditText[@text="Фамилия"]')
    NEXT_BUTTON = (AppiumBy.XPATH, '//android.widget.TextView[@text="Далее"]')
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def assert_ui(self):
        """Проверяет наличие всех ключевых элементов страницы имени."""
        self.wait_present(self.HEADER, "Заголовок 'Как вас зовут?' не найден")
        self.wait_present(self.SUBTITLE, "Подзаголовок 'Укажите данные из удостоверения' не найден")
        self.wait_visible(self.NAME_INPUT, "Поле 'Имя' не найдено")
        self.wait_visible(self.SURNAME_INPUT, "Поле 'Фамилия' не найдено")
        self.wait_visible(self.NEXT_BUTTON, "Кнопка 'Далее' не найдена")
        print("✅ Страница ввода имени открыта, все элементы присутствуют")
    
    def enter_name(self, name: str) -> None:
        """
        Ввести имя.
        
        Args:
            name: Имя клиента
        """
        name_input = self.wait.until(EC.presence_of_element_located(self.NAME_INPUT))
        name_input.clear()
        name_input.send_keys(name)
        print(f"✅ Введено имя: {name}")
    
    def enter_surname(self, surname: str) -> None:
        """
        Ввести фамилию.
        
        Args:
            surname: Фамилия клиента
        """
        surname_input = self.wait.until(EC.presence_of_element_located(self.SURNAME_INPUT))
        surname_input.clear()
        surname_input.send_keys(surname)
        print(f"✅ Введена фамилия: {surname}")
    
    def enter_full_name(self, name: str, surname: str) -> None:
        """
        Ввести имя и фамилию одним методом.
        
        Args:
            name: Имя клиента
            surname: Фамилия клиента
        """
        self.enter_name(name)
        self.enter_surname(surname)
    
    def get_name_value(self) -> str:
        """Получить текущее значение поля 'Имя'."""
        name_input = self.wait.until(EC.presence_of_element_located(self.NAME_INPUT))
        return name_input.text
    
    def get_surname_value(self) -> str:
        """Получить текущее значение поля 'Фамилия'."""
        surname_input = self.wait.until(EC.presence_of_element_located(self.SURNAME_INPUT))
        return surname_input.text
    
    def is_next_button_enabled(self) -> bool:
        """Проверить, активна ли кнопка 'Далее'."""
        try:
            el = self._wait(5).until(EC.presence_of_element_located(self.NEXT_BUTTON))
            return el.is_enabled()
        except TimeoutException:
            return False
    
    def click_next(self) -> None:
        """Нажать кнопку 'Далее'."""
        # Скрываем клавиатуру перед нажатием кнопки
        try:
            self.driver.hide_keyboard()
            print("✅ Клавиатура скрыта перед нажатием кнопки 'Далее'")
        except Exception:
            pass  # Клавиатура уже скрыта
        
        self.click(self.NEXT_BUTTON)
        print("✅ Нажата кнопка 'Далее'")
