"""
Page Object: Экран превью/онбординга.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from src.pages.mobile.base_mobile_page import BaseMobilePage


class PreviewPage(BaseMobilePage):
    """Page Object для экрана превью (онбординг)."""
    
    page_title = "Preview (Превью)"
    
    # Селекторы
    START_BUTTON = (AppiumBy.XPATH, '//android.widget.TextView[@text="Начать"]')
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def assert_ui(self):
        """Проверяет наличие кнопки 'Начать'."""
        self.wait_visible(self.START_BUTTON, "Кнопка 'Начать' не найдена")
        print("✅ Превью экран открыт")
    
    def skip_preview(self) -> None:
        """Пропуск экрана превью."""
        self.click(self.START_BUTTON)
        print("✅ Превью экран пропущен")

    def wait_loaded(self) -> "PreviewPage":
        """
        Ждёт загрузки экрана превью с проверкой, что приложение активно.

        Returns:
            PreviewPage: загруженная страница.
        """
        # Восстанавливаем состояние приложения, если оно свернулось/потеряло фокус.
        self.check_and_recover_app_state()
        return super().wait_loaded()

    def is_loaded(self) -> bool:
        """
        Устаревший метод. Используйте wait_loaded() вместо него.
        
        Проверка загрузки экрана превью.
        """
        try:
            self.wait.until(EC.visibility_of_element_located(self.START_BUTTON))
            return True
        except Exception:
            return False
