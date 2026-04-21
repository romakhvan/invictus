"""
Page Object: Экран ввода номера телефона.
"""

from typing import TYPE_CHECKING
from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from src.pages.mobile.base_mobile_page import BaseMobilePage

if TYPE_CHECKING:
    from src.pages.mobile.auth.country_selector_page import CountrySelectorPage


class PhoneAuthPage(BaseMobilePage):
    """Page Object для экрана ввода номера телефона."""
    
    page_title = "Phone Auth (Ввод телефона)"
    
    # Селекторы
    HEADER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Введите ваш номер телефона"]')
    SUBTITLE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Отправим проверочный код"]')
    TERMS = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Нажимая «Продолжить», вы соглашаетесь c Условиями использования")]')
    
    # Селектор кода страны - универсальный (работает для +7, +996 и т.д.)
    COUNTRY_CODE_SELECTOR = (AppiumBy.XPATH, '//android.widget.TextView[starts-with(@text, "+")]')
    
    CONTINUE_BUTTON_GROUP = (AppiumBy.XPATH, '//android.view.ViewGroup[@content-desc="Продолжить"]')
    CONTINUE_BUTTON = (AppiumBy.XPATH, '//android.widget.Button[@text="Продолжить"] | //android.widget.TextView[@text="Продолжить"]')
    
    # Варианты поиска поля ввода телефона (приоритет: с маской → любое EditText)
    PHONE_INPUT_XPATHS = [
        (AppiumBy.XPATH, '//android.widget.EditText[contains(@text, "000")]'),
        (AppiumBy.XPATH, '//android.widget.EditText[contains(@text, "00")]'),
        (AppiumBy.XPATH, '//android.widget.EditText'),
    ]
    
    # Селекторы модалки выбора способа получения кода
    MODAL_HEADER = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Как вам удобнее получить код")]')
    MODAL_SMS_OPTION = (AppiumBy.XPATH, '//android.widget.TextView[@text="SMS"]')
    MODAL_WHATSAPP_OPTION = (AppiumBy.XPATH, '//android.widget.TextView[@text="WhatsApp"]')
    MODAL_CONTINUE_BUTTON = (AppiumBy.XPATH, '//android.widget.TextView[@text="Продолжить"]')
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def assert_ui(self):
        """Проверяет наличие всех ключевых элементов страницы."""
        self.wait_visible(self.HEADER, "Заголовок 'Введите ваш номер телефона' не найден")
        self.wait_visible(self.SUBTITLE, "Подзаголовок 'Отправим проверочный код' не найден")
        self.wait_visible(self.TERMS, "Текст с условиями использования не найден")
        self.wait_visible(self.COUNTRY_CODE_SELECTOR, "Селектор кода страны не найден")
        self.wait_visible(self.CONTINUE_BUTTON_GROUP, "Кнопка 'Продолжить' не найдена")
        print("✅ Страница ввода телефона открыта, все элементы присутствуют")
    
    def _find_phone_input(self):
        """
        Найти поле ввода телефона (пробует несколько вариантов).
        
        Returns:
            WebElement: Найденный элемент поля ввода
        
        Raises:
            AssertionError: Если поле не найдено
        """
        for locator in self.PHONE_INPUT_XPATHS:
            try:
                # Используем visibility + clickable для надежности
                element = self.wait.until(EC.visibility_of_element_located(locator))
                # Проверяем что элемент кликабелен
                self.wait.until(EC.element_to_be_clickable(locator))
                return element
            except TimeoutException:
                continue
        raise AssertionError("❌ Поле ввода телефона не найдено или не кликабельно")
    
    def _clear_phone_input(self, element) -> None:
        """
        Очищает поле ввода телефона.
        
        На Android clear() иногда не работает, поэтому используем set_value.
        
        Args:
            element: WebElement поля ввода
        """
        try:
            # Для Appium set_value более стабилен чем clear()
            element.set_value("")
        except Exception:
            # Fallback на стандартный clear
            try:
                element.clear()
            except Exception:
                # Если и это не сработало, логируем но продолжаем
                print("⚠️ Не удалось очистить поле ввода, продолжаем без очистки")

    @staticmethod
    def _format_phone_for_log(phone_number: str) -> str:
        """Форматирует номер телефона для человекочитаемого вывода в логах."""
        digits = "".join(c for c in str(phone_number) if c.isdigit())
        if len(digits) >= 10:
            digits = digits[-10:]
            return f"+7 {digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"
        return str(phone_number)
    
    def enter_phone(self, phone_number: str, silent: bool = False) -> None:
        """
        Ввод номера телефона.
        
        Args:
            phone_number: Номер телефона (10 цифр без кода страны)
            silent: Не выводить print если True
        """
        # Находим поле (уже с проверкой видимости и кликабельности)
        phone_input = self._find_phone_input()
        
        # Кликаем по найденному элементу (не ищем заново!)
        phone_input.click()
        
        # Ждём фокусировки (вместо sleep)
        # Проверяем что элемент остался кликабельным/видимым
        try:
            self.wait.until(lambda d: phone_input.is_displayed() and phone_input.is_enabled())
        except TimeoutException:
            raise AssertionError("❌ Поле ввода не получило фокус")
        
        # Очищаем поле перед вводом
        self._clear_phone_input(phone_input)
        
        # Вводим номер
        phone_input.send_keys(phone_number)
        
        # Ждём что текст появился (вместо sleep)
        try:
            self.wait.until(lambda d: len(phone_input.text.replace(" ", "").replace("-", "")) >= len(phone_number) - 1)
        except TimeoutException:
            # Не критично, продолжаем
            pass
        
        if not silent:
            print(f"📱 Номер телефона для авторизации: {self._format_phone_for_log(phone_number)}")
            print(f"✅ Номер телефона введен: {phone_number}")
    
    def click_country_selector(self) -> None:
        """Открыть селектор выбора страны."""
        self.click(self.COUNTRY_CODE_SELECTOR)
    
    def click_continue(self) -> None:
        """Нажать кнопку 'Продолжить'."""
        self.click(self.CONTINUE_BUTTON)
    
    def handle_code_delivery_modal(self, method: str = "SMS", timeout: int = 5) -> bool:
        """
        Обработать модалку выбора способа получения кода (если появилась).
        
        Args:
            method: Способ получения кода ('SMS' или 'WhatsApp')
            timeout: Время ожидания появления модалки
            
        Returns:
            True если модалка появилась и была обработана, False если модалки не было
        """
        
        # Проверяем наличие модалки
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.visibility_of_element_located(self.MODAL_HEADER))
            print("✅ Обнаружена модалка выбора способа получения кода")
            
            # Выбираем способ получения (SMS уже выбран по умолчанию)
            if method == "WhatsApp":
                self.click(self.MODAL_WHATSAPP_OPTION)
                print("✅ Выбран способ: WhatsApp")
            else:
                # SMS уже выбран по умолчанию, но кликнем для надежности
                try:
                    self.click(self.MODAL_SMS_OPTION)
                    print("✅ Выбран способ: SMS")
                except Exception:
                    print("✅ SMS выбран по умолчанию")
            
            # Нажимаем кнопку "Продолжить" в модалке
            self.wait_visible(
                self.MODAL_CONTINUE_BUTTON,
                "Кнопка 'Продолжить' в модалке не найдена",
                timeout=3,
            )
            self.click(self.MODAL_CONTINUE_BUTTON)
            print("✅ Модалка закрыта, код отправлен")
            return True
            
        except TimeoutException:
            # Модалка не появилась - это нормально
            return False
    
    def is_continue_enabled(self) -> bool:
        """Проверка активности кнопки 'Продолжить'."""
        try:
            button = self.wait.until(EC.visibility_of_element_located(self.CONTINUE_BUTTON))
            return button.is_enabled()
        except TimeoutException:
            return False
    
    def open_country_selector(self) -> "CountrySelectorPage":
        """
        Открывает селектор страны и возвращает его Page Object.
        
        Returns:
            CountrySelectorPage: Page Object селектора страны
        """
        from src.pages.mobile.auth.country_selector_page import CountrySelectorPage
        
        self.click_country_selector()
        print("✅ Селектор страны открыт")
        
        country_page = CountrySelectorPage(self.driver)
        country_page.wait_loaded()
        return country_page
    
    def select_country_and_enter(self, country_name: str, phone_number: str) -> None:
        """
        Выбор страны и ввод номера телефона (комплексное действие).
        
        Args:
            country_name: Название страны ('Казахстан' или 'Кыргызстан')
            phone_number: Номер телефона (10 цифр без кода страны)
        """
        # Открываем селектор
        country_page = self.open_country_selector()
        
        # Выбираем страну
        country_page.select_country(country_name)
        print(f"✅ Страна '{country_name}' выбрана")
        
        # Подтверждаем
        country_page.click_done()
        print("✅ Выбор подтвержден")
        
        # Вводим номер (поле будет очищено автоматически)
        self.enter_phone(phone_number, silent=True)
        print(
            f"📱 Номер телефона для авторизации ({country_name}): "
            f"{self._format_phone_for_log(phone_number)}"
        )
        print(f"✅ Номер для {country_name} введен: {phone_number}")
    
    def diagnose(self) -> None:
        """Диагностирует все элементы страницы (для отладки)."""
        elements = {
            "HEADER": self.HEADER,
            "SUBTITLE": self.SUBTITLE,
            "TERMS": self.TERMS,
            "COUNTRY_CODE_SELECTOR": self.COUNTRY_CODE_SELECTOR,
            "CONTINUE_BUTTON_GROUP": self.CONTINUE_BUTTON_GROUP,
            "CONTINUE_BUTTON": self.CONTINUE_BUTTON,
            "PHONE_INPUT_PRIMARY": self.PHONE_INPUT_XPATHS[0],
            "MODAL_HEADER": self.MODAL_HEADER,
            "MODAL_SMS_OPTION": self.MODAL_SMS_OPTION,
            "MODAL_WHATSAPP_OPTION": self.MODAL_WHATSAPP_OPTION,
            "MODAL_CONTINUE_BUTTON": self.MODAL_CONTINUE_BUTTON,
        }
        self.print_page_diagnosis(elements)
