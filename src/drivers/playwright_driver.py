"""
Инициализация и управление Playwright драйвером.
"""

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
from typing import Optional
from src.config.app_config import WEB_BASE_URL, WEB_TIMEOUT


class PlaywrightDriver:
    """Управление Playwright браузером и страницами."""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def start(self, headless: bool = False, browser_type: str = "chromium"):
        """
        Запуск браузера.
        
        Args:
            headless: Запуск в headless режиме
            browser_type: Тип браузера (chromium, firefox, webkit)
        """
        self.playwright = sync_playwright().start()
        
        browser_map = {
            "chromium": self.playwright.chromium,
            "firefox": self.playwright.firefox,
            "webkit": self.playwright.webkit
        }
        
        browser_launcher = browser_map.get(browser_type, self.playwright.chromium)
        self.browser = browser_launcher.launch(headless=headless)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(WEB_TIMEOUT)
        self.page.goto(WEB_BASE_URL)
    
    def get_page(self) -> Page:
        """Получить текущую страницу."""
        if not self.page:
            raise RuntimeError("Браузер не запущен. Вызовите start() сначала.")
        return self.page
    
    def close(self):
        """Закрыть браузер и освободить ресурсы."""
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

