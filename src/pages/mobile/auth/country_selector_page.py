"""
Page Object: Экран выбора страны.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from src.pages.mobile.base_mobile_page import BaseMobilePage


class CountrySelectorPage(BaseMobilePage):
    """Page Object для экрана выбора страны."""
    
    # Селекторы
    HEADER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Выберите страну"]')
    COUNTRY_KAZAKHSTAN = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Казахстан")]')
    COUNTRY_KYRGYZSTAN = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Кыргызстан")]')
    DONE_BUTTON = (AppiumBy.XPATH, '//android.widget.TextView[@text="Готово"]')
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def assert_ui(self):
        """Проверяет наличие всех ключевых элементов страницы."""
        self.wait_visible(self.HEADER, "Заголовок 'Выберите страну' не найден")
        self.wait_visible(self.COUNTRY_KAZAKHSTAN, "Страна 'Казахстан' не найдена")
        self.wait_visible(self.COUNTRY_KYRGYZSTAN, "Страна 'Кыргызстан' не найдена")
        self.wait_visible(self.DONE_BUTTON, "Кнопка 'Готово' не найдена")
        print("✅ Страница выбора страны открыта, страны отображаются")
    
    def is_loaded(self) -> bool:
        """
        Устаревший метод. Используйте wait_loaded() вместо него.
        
        Проверка загрузки экрана выбора страны.
        """
        try:
            self.wait.until(EC.visibility_of_element_located(self.HEADER))
            return True
        except Exception:
            return False
    
    def verify_countries_displayed(self) -> bool:
        """Устаревший метод. Используйте assert_ui()."""
        try:
            self.assert_ui()
            return True
        except AssertionError:
            return False
    
    def select_country(self, country_name: str) -> None:
        """
        Выбрать страну из списка.
        
        Args:
            country_name: Название страны ('Казахстан' или 'Кыргызстан')
        """
        if country_name == "Кыргызстан":
            self.click(self.COUNTRY_KYRGYZSTAN)
        else:
            self.click(self.COUNTRY_KAZAKHSTAN)
    
    def click_done(self) -> None:
        """Подтвердить выбор страны (нажать 'Готово')."""
        self.click(self.DONE_BUTTON)
