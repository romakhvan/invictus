"""
Smoke-тест: Страница авторизации (ввод номера телефона).
РЕФАКТОРЕННАЯ ВЕРСИЯ с использованием Page Object Model.

Проверяет:
- Загрузку страницы ввода телефона
- Наличие всех UI элементов
- Ввод корректного номера телефона
- Смену страны и повторный ввод
"""

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.auth import PreviewPage, PhoneAuthPage, SmsCodePage


@pytest.mark.mobile
@pytest.mark.smoke
def test_phone_input_page_refactored(mobile_driver: "Remote"):
    """
    Smoke-тест: Страница ввода номера телефона (версия с Page Objects).
    
    Сценарий:
    1. Запуск приложения и пропуск превью
    2. Проверка элементов страницы авторизации
    3. Ввод номера для Казахстана
    4. Смена страны на Кыргызстан и ввод номера
    5. Проверка активности кнопки "Продолжить"
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("SMOKE-ТЕСТ: Страница авторизации (ввод телефона) — Page Object Model")
    print("=" * 80 + "\n")
    
    # Шаг 1: Проверка запуска
    assert driver.current_package == MOBILE_APP_PACKAGE, \
        f"Неверный package: ожидался {MOBILE_APP_PACKAGE}, получен {driver.current_package}"
    print(f"✅ Приложение запущено: {driver.current_package}")
    
    # Шаг 2: Пропуск превью
    preview = PreviewPage(driver).wait_loaded()
    preview.skip_preview()
    
    # Шаг 3: Проверка страницы авторизации
    phone = PhoneAuthPage(driver).wait_loaded()
    
    # Шаг 4: Ввод номера для Казахстана
    phone.enter_phone("7001234567")
    
    # Шаг 5: Смена страны на Кыргызстан и ввод
    phone.select_country_and_enter("Кыргызстан", "7001234567")
    
    # Шаг 6: Проверка кнопки "Продолжить"
    assert phone.is_continue_enabled(), "Кнопка 'Продолжить' должна быть активна"
    print("✅ Кнопка 'Продолжить' активна")
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТ ПРОЙДЕН")
    print("=" * 80)


@pytest.mark.mobile
@pytest.mark.smoke
def test_sms_code_page_refactored(mobile_driver: "Remote"):
    """
    Smoke-тест: Страница ввода SMS-кода (версия с Page Objects).
    
    Сценарий:
    1. Проход через ввод телефона (предусловие)
    2. Переход на страницу SMS-кода
    3. Проверка элементов страницы SMS-кода
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("SMOKE-ТЕСТ: Страница ввода SMS-кода — Page Object Model")
    print("=" * 80 + "\n")
    
    # Проверка запуска
    assert driver.current_package == MOBILE_APP_PACKAGE
    print(f"✅ Приложение запущено: {driver.current_package}")
    
    # Предусловие: пропуск превью и ввод телефона
    preview = PreviewPage(driver).wait_loaded()
    preview.skip_preview()
    
    phone = PhoneAuthPage(driver).wait_loaded()
    entered_phone = "+7 (700) 123 45 67"
    phone.enter_phone("7001234567")
    phone.click_continue()
    print("✅ Перешли на страницу SMS-кода")
    
    # Проверка страницы SMS-кода
    sms = SmsCodePage(driver).wait_loaded()
    print("✅ Страница SMS-кода загружена")
    
    # Проверка отображения корректного номера телефона
    assert sms.verify_phone_number(entered_phone), \
        f"Номер телефона не совпадает: ожидался {entered_phone}"
    print(f"✅ Отображается корректный номер: {entered_phone}")
    
    # Проверка наличия таймера повторной отправки
    assert sms.is_resend_timer_visible(), "Таймер повторной отправки не найден"
    print("✅ Таймер повторной отправки отображается")
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТ ПРОЙДЕН")
    print("=" * 80)
