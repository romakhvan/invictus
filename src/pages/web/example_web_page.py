"""
Пример Page Object для веб-страницы.
"""

from playwright.sync_api import Page
from src.pages.web.base_web_page import BaseWebPage


class ExampleWebPage(BaseWebPage):
    """Пример Page Object для главной страницы."""
    
    # Селекторы
    LOGIN_BUTTON = "button.login"
    USERNAME_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='password']"
    SUBMIT_BUTTON = "button[type='submit']"
    
    def __init__(self, page: Page):
        """Инициализация страницы."""
        super().__init__(page)
    
    def is_loaded(self) -> bool:
        """Проверка загрузки страницы."""
        return self.is_visible(self.LOGIN_BUTTON)
    
    def click_login(self):
        """Клик по кнопке входа."""
        self.click(self.LOGIN_BUTTON)
    
    def enter_credentials(self, username: str, password: str):
        """Ввод учетных данных."""
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
    
    def submit_login(self):
        """Отправка формы входа."""
        self.click(self.SUBMIT_BUTTON)
    
    def login(self, username: str, password: str):
        """Полный процесс входа."""
        self.click_login()
        self.enter_credentials(username, password)
        self.submit_login()

