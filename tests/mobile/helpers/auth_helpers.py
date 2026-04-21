"""
Хелперы для авторизации и работы с экраном ввода телефона.
"""

from typing import TYPE_CHECKING
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.webdriver.common.appiumby import AppiumBy
from src.utils.ui_helpers import click_element_with_fallback
import time

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.pages.mobile.auth import PhoneAuthPage
from tests.mobile.helpers.onboarding_helpers import run_auth_to_home


def enter_phone_number(driver: "Remote", wait: WebDriverWait, phone_number: str) -> None:
    """
    Вводит номер телефона в поле ввода.
    
    Сначала проверяет наличие поля ввода (подтверждает что мы на странице авторизации),
    затем вводит номер телефона.
    
    Args:
        driver: Appium WebDriver объект
        wait: WebDriverWait объект
        phone_number: Номер телефона для ввода (10 цифр без кода страны)
    """
    PhoneAuthPage(driver).wait_loaded().enter_phone(phone_number)
    return

    # Универсальный XPath для поиска поля ввода телефона (работает для любой страны)
    # Вариант 1: Ищем EditText с маской телефона (содержит скобки или нули)
    # Вариант 2: Если не найдет, ищем любой EditText на странице
    phone_input_xpaths = [
        '//android.widget.EditText[contains(@text, "000")]',  # С маской
        '//android.widget.EditText[contains(@text, "00")]',   # Упрощенная маска
        '//android.widget.EditText',                           # Любой EditText
    ]
    
    # Проверка что мы на странице ввода телефона
    phone_input = None
    phone_input_xpath = None
    
    # Пробуем найти поле ввода разными способами
    for xpath in phone_input_xpaths:
        try:
            phone_input = wait.until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath))
            )
            phone_input_xpath = xpath
            print("✅ Страница ввода телефона открыта")
            print(f"✅ Поле ввода номера телефона найдено (XPath: {xpath})")
            break
        except Exception:
            continue
    
    if not phone_input or not phone_input_xpath:
        print(f"❌ Поле ввода номера телефона не найдено")
        raise Exception("Не удалось найти поле ввода телефона")
    
    # Клик по полю ввода для фокусировки
    click_element_with_fallback(driver, wait, phone_input_xpath)
    time.sleep(1.5)
    
    # Находим поле заново после клика (может обновиться)
    phone_input = wait.until(
        EC.presence_of_element_located((AppiumBy.XPATH, phone_input_xpath))
    )
    
    phone_input.send_keys(phone_number)
    time.sleep(1.5)
    print(f"✅ Номер телефона введен: {phone_number}")


def authorize_user(
    driver: "Remote",
    wait: WebDriverWait,
    phone_number: str = "7001234567",
    expected_state=None,
) -> None:
    """
    Выполняет полный флоу авторизации пользователя.
    
    Включает минимальные проверки открытия каждой страницы:
    - Пропуск превью экрана (проверяет наличие кнопки "Начать")
    - Ввод номера телефона (проверяет наличие поля ввода)
    - Переход к следующему шагу
    
    Args:
        driver: Appium WebDriver объект
        wait: WebDriverWait объект
        phone_number: Номер телефона для авторизации (по умолчанию тестовый)
    """
    print("\n--- АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ ---")
    print(f"📱 Номер телефона для авторизации: {phone_number}")
    run_auth_to_home(driver, phone_number, expected_state=expected_state)
    print("✅ Авторизация завершена\n")
    return
    
    # Пропуск превью экрана
    start_button_xpath = '//android.widget.TextView[@text="Начать"]'
    try:
        wait.until(EC.presence_of_element_located((AppiumBy.XPATH, start_button_xpath)))
        print("✅ Превью экран открыт")
    except Exception as e:
        print(f"❌ Превью экран не открыт")
        raise
    click_element_with_fallback(driver, wait, start_button_xpath)
    print("✅ Превью экран пропущен")
    
    # Ввод номера телефона
    enter_phone_number(driver, wait, phone_number)
    
    # Клик по кнопке "Продолжить"
    next_button_xpath = '//android.widget.Button[@text="Продолжить"] | //android.widget.TextView[@text="Продолжить"]'
    click_element_with_fallback(driver, wait, next_button_xpath)
    print("✅ Кнопка 'Продолжить' нажата")
    
    print("✅ Авторизация завершена\n")
