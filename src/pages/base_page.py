"""
Базовый класс для Page Objects.
"""

from abc import ABC
from typing import Optional


class BasePage(ABC):
    """Базовый класс для всех Page Objects."""
    
    def __init__(self, driver=None):
        """
        Инициализация базовой страницы.
        
        Args:
            driver: Драйвер (Playwright Page или Appium WebDriver)
        """
        self.driver = driver
    
    def is_loaded(self) -> bool:
        """
        Проверка, что страница загружена.
        Должен быть переопределен в дочерних классах.
        """
        raise NotImplementedError("Метод is_loaded() должен быть реализован в дочернем классе")

