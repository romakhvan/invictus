"""
Пример Page Object для мобильного экрана.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.mobile.base_mobile_page import BaseMobilePage


class ExampleMobilePage(BaseMobilePage):
    """Пример Page Object для главного экрана приложения."""
    
    # Селекторы (примеры для Android)
    LOGIN_BUTTON = (AppiumBy.ID, "com.example.app:id/login_button")
    USERNAME_INPUT = (AppiumBy.ID, "com.example.app:id/username_input")
    PASSWORD_INPUT = (AppiumBy.ID, "com.example.app:id/password_input")
    SUBMIT_BUTTON = (AppiumBy.ID, "com.example.app:id/submit_button")
    
    def __init__(self, driver: Remote):
        """Инициализация страницы."""
        super().__init__(driver)
    
    def is_loaded(self) -> bool:
        """Проверка загрузки экрана."""
        return self.is_visible(*self.LOGIN_BUTTON)
    
    def click_login(self):
        """Клик по кнопке входа."""
        self.click(*self.LOGIN_BUTTON)
    
    def enter_username(self, username: str):
        """Ввод имени пользователя."""
        self.send_keys(*self.USERNAME_INPUT, username)
    
    def enter_password(self, password: str):
        """Ввод пароля."""
        self.send_keys(*self.PASSWORD_INPUT, password)
    
    def submit_login(self):
        """Отправка формы входа."""
        self.click(*self.SUBMIT_BUTTON)
    
    def login(self, username: str, password: str):
        """Полный процесс входа."""
        self.click_login()
        self.enter_username(username)
        self.enter_password(password)
        self.submit_login()

