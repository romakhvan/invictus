"""
Базовый класс для страниц внутри main shell (с нижней навигацией / tabbar).

Только страницы, унаследованные от BaseShellPage, имеют доступ к .nav.
Auth / Onboarding / fullscreen-флоу наследуются от BaseMobilePage напрямую.
"""

from typing import TYPE_CHECKING

from appium.webdriver import Remote

from src.pages.mobile.base_mobile_page import BaseMobilePage

if TYPE_CHECKING:
    from src.pages.mobile.shell.bottom_nav import BottomNav


class BaseShellPage(BaseMobilePage):
    """Базовый класс для страниц внутри main shell (с нижней навигацией)."""

    def __init__(self, driver: Remote):
        super().__init__(driver)

    @property
    def nav(self) -> "BottomNav":
        """
        Доступ к нижней навигации (tabbar).

        Доступен только на страницах, унаследованных от BaseShellPage.
        Ленивый импорт для избежания циклических зависимостей.
        """
        from src.pages.mobile.shell.bottom_nav import BottomNav

        return BottomNav(self.driver)
