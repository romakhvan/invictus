"""
Базовый класс для мобильных Page Objects (Appium).
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.base_page import BasePage
from typing import Optional, Union
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class BaseMobilePage(BasePage):
    """Базовый класс для мобильных страниц."""
    
    def __init__(self, driver: Remote):
        """
        Инициализация мобильной страницы.
        
        Args:
            driver: Appium WebDriver объект
        """
        super().__init__(driver=driver)
        self.driver: Remote = driver
        self.wait = WebDriverWait(driver, 20)
    
    def find_element(self, by: Union[AppiumBy, str], value: str):
        """Найти элемент."""
        return self.driver.find_element(by, value)
    
    def find_elements(self, by: Union[AppiumBy, str], value: str):
        """Найти элементы."""
        return self.driver.find_elements(by, value)
    
    def click(self, by: Union[AppiumBy, str], value: str, timeout: Optional[int] = None):
        """Клик по элементу."""
        wait = WebDriverWait(self.driver, timeout or 20)
        element = wait.until(EC.element_to_be_clickable((by, value)))
        element.click()
    
    def send_keys(self, by: Union[AppiumBy, str], value: str, text: str, timeout: Optional[int] = None):
        """Ввод текста в поле."""
        wait = WebDriverWait(self.driver, timeout or 20)
        element = wait.until(EC.presence_of_element_located((by, value)))
        element.clear()
        element.send_keys(text)
    
    def get_text(self, by: Union[AppiumBy, str], value: str, timeout: Optional[int] = None) -> str:
        """Получить текст элемента."""
        wait = WebDriverWait(self.driver, timeout or 20)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element.text
    
    def is_visible(self, by: Union[AppiumBy, str], value: str, timeout: Optional[int] = None) -> bool:
        """Проверка видимости элемента."""
        try:
            wait = WebDriverWait(self.driver, timeout or 5)
            wait.until(EC.visibility_of_element_located((by, value)))
            return True
        except TimeoutException:
            return False
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 1000):
        """Свайп по экрану."""
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
    
    def is_loaded(self) -> bool:
        """Базовая проверка загрузки (можно переопределить)."""
        return True

