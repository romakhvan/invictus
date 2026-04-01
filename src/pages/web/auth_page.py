"""
Page Object для страницы авторизации invictus.kz/auth
"""

from playwright.sync_api import Page
from src.pages.web.base_web_page import BaseWebPage
from src.config.app_config import WEB_BASE_URL


class AuthPage(BaseWebPage):
    """Страница авторизации по номеру телефона /auth"""

    URL = f"{WEB_BASE_URL}/auth"

    # Заголовок
    PAGE_HEADING = "h1:has-text('Телефон')"

    # Форма
    PHONE_INPUT = "input[placeholder='(000) 000 00 00']"
    COUNTRY_CODE_BUTTON = "button:has-text('+7')"
    SUBMIT_BUTTON = "button:has-text('Келесі')"
    BACK_BUTTON = "button:has-text('Артқа')"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self):
        """Перейти на страницу авторизации."""
        self.navigate_to(self.URL)

    def is_loaded(self) -> bool:
        """Проверка загрузки страницы авторизации."""
        return self.is_visible(self.PHONE_INPUT)

    def get_heading_text(self) -> str:
        return self.get_text(self.PAGE_HEADING)

    def enter_phone(self, phone: str):
        """Ввести номер телефона (без кода страны)."""
        self.fill(self.PHONE_INPUT, phone)

    def clear_phone(self):
        self.page.locator(self.PHONE_INPUT).clear()

    def is_submit_enabled(self) -> bool:
        return self.page.locator(self.SUBMIT_BUTTON).is_enabled()

    def submit(self):
        self.click(self.SUBMIT_BUTTON)

    def go_back(self):
        self.click(self.BACK_BUTTON)

    def get_country_code(self) -> str:
        return self.page.locator(self.COUNTRY_CODE_BUTTON).inner_text().strip()
