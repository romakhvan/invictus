"""
Базовый класс для веб Page Objects (Playwright).
"""

from playwright.sync_api import Page, Locator
from src.pages.base_page import BasePage
from typing import Optional


class BaseWebPage(BasePage):
    """Базовый класс для веб-страниц."""
    
    def __init__(self, page: Page):
        """
        Инициализация веб-страницы.
        
        Args:
            page: Playwright Page объект
        """
        super().__init__(driver=page)
        self.page: Page = page
    
    def click(self, selector: str, timeout: Optional[int] = None):
        """Клик по элементу."""
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: Optional[int] = None):
        """Заполнение поля."""
        self.page.fill(selector, value, timeout=timeout)
    
    def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """Получить текст элемента."""
        return self.page.locator(selector).inner_text(timeout=timeout)
    
    def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """Ожидание появления элемента."""
        return self.page.wait_for_selector(selector, timeout=timeout)
    
    def is_visible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Проверка видимости элемента."""
        try:
            return self.page.locator(selector).is_visible(timeout=timeout)
        except Exception:
            return False
    
    def navigate_to(self, url: str):
        """Переход на URL."""
        self.page.goto(url)
    
    def get_current_url(self) -> str:
        """Получить текущий URL."""
        return self.page.url
    
    def is_loaded(self) -> bool:
        """Базовая проверка загрузки (можно переопределить)."""
        return True

