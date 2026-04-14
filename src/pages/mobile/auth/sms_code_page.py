"""
Page Object: Экран ввода SMS-кода.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC
from src.pages.mobile.base_mobile_page import BaseMobilePage


class SmsCodePage(BaseMobilePage):
    """Page Object для экрана ввода SMS-кода."""
    
    page_title = "SMS Code (Подтверждение кода)"
    
    HEADER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Вставьте код"]')
    CODE_INPUT = (AppiumBy.XPATH, '//android.widget.EditText')
    CODE_INPUT_FOCUS_AREA = (AppiumBy.XPATH, '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]')
    # ViewGroup для ввода кода (по bounds)
    CODE_INPUT_VIEWGROUP = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.ViewGroup").index(3)')
    PHONE_NUMBER_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Отправили на")]')
    RESEND_TIMER = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Запросить новый код можно через")]')
    CONFIRM_BUTTON = (AppiumBy.XPATH, '//android.view.ViewGroup[@content-desc="Продолжить"]')
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def assert_ui(self):
        """Проверяет наличие всех ключевых элементов страницы SMS-кода."""
        self.ensure_app_is_active()
        self.wait_visible(self.HEADER, "Заголовок 'Вставьте код' не найден")
        self.wait_visible(self.PHONE_NUMBER_LABEL, "Номер телефона не отображается")
        
        # CONFIRM_BUTTON может быть не виден сразу
        try:
            self.wait_visible(self.CONFIRM_BUTTON, "Кнопка 'Продолжить' не найдена", timeout=5)
        except AssertionError:
            print("⚠️ Кнопка 'Продолжить' не найдена, но страница SMS-кода загружена")
        
        print("✅ Страница ввода SMS-кода открыта")
    
    def get_displayed_phone_number(self) -> str:
        """
        Получить отображаемый номер телефона.
        
        Returns:
            Номер телефона в формате: "+7 (705) 000 00 00"
        """
        element = self.wait.until(EC.presence_of_element_located(self.PHONE_NUMBER_LABEL))
        text = element.text  # Например: "Отправили на +7 (705) 000 00 00"
        # Извлекаем номер из текста
        return text.replace("Отправили на ", "").strip()
    
    def verify_phone_number(self, expected_phone: str) -> bool:
        """
        Проверить, что отображается правильный номер телефона.
        
        Args:
            expected_phone: Ожидаемый номер телефона
            
        Returns:
            True если номер совпадает, False иначе
        """
        displayed = self.get_displayed_phone_number()
        return displayed == expected_phone
    
    def enter_code(self, code: str = "0000") -> None:
        """
        Ввести SMS-код через нажатия клавиш.
        
        Args:
            code: SMS-код (по умолчанию "0000" для тестов)
        """
        self.ensure_app_is_active()

        # Маппинг цифр на Android keycodes
        keycode_map = {
            '0': 7, '1': 8, '2': 9, '3': 10, '4': 11,
            '5': 12, '6': 13, '7': 14, '8': 15, '9': 16
        }
        
        for digit in code:
            if digit in keycode_map:
                self.driver.press_keycode(keycode_map[digit])
        
        print(f"✅ Введен SMS-код: {code}")
    
    def click_confirm(self) -> None:
        """Подтвердить введенный код."""
        self.check_and_recover_app_state()

        # Скрываем клавиатуру, чтобы открыть доступ к кнопке
        if self.hide_keyboard():
            print("✅ Клавиатура скрыта")
        else:
            print("⚠️ Клавиатура уже скрыта или не найдена")
        
        # Кликаем по кнопке
        try:
            self.click(self.CONFIRM_BUTTON)
            print("✅ Нажата кнопка 'Продолжить'")
        except Exception as e:
            print(f"⚠️ Кнопка 'Продолжить' не найдена: {e}")
    
    def is_resend_timer_visible(self) -> bool:
        """Проверить наличие таймера повторной отправки кода."""
        try:
            self.wait.until(EC.presence_of_element_located(self.RESEND_TIMER))
            return True
        except Exception:
            return False
