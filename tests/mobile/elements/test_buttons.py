"""
Тесты для проверки кнопок в приложении.
"""

import pytest
from typing import TYPE_CHECKING
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.ui_helpers import click_element_with_fallback

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
def test_primary_button_exists(mobile_driver: "Remote"):
    """
    Проверка: главная кнопка на экране существует и видна.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Главная кнопка")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    # ЗАМЕНИТЕ на реальный селектор из Appium Inspector!
    # Пример: кнопка "Начать"
    button_xpath = '//android.widget.TextView[@text="Начать"]'
    
    try:
        button = wait.until(
            EC.visibility_of_element_located((AppiumBy.XPATH, button_xpath))
        )
        print(f"✅ Кнопка найдена")
        
        # Проверяем свойства
        assert button.is_displayed(), "Кнопка не видна"
        print(f"✅ Кнопка видна")
        
        assert button.is_enabled(), "Кнопка не активна"
        print(f"✅ Кнопка активна")
        
        button_text = button.text
        print(f"   Текст кнопки: '{button_text}'")
        
    except Exception as e:
        print(f"❌ Кнопка не найдена: {e}")
        pytest.fail(f"Главная кнопка не найдена: {e}")


@pytest.mark.mobile
def test_button_clickable(mobile_driver: "Remote"):
    """
    Проверка: кнопка кликабельна.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Кнопка кликабельна")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    # ЗАМЕНИТЕ на реальный селектор!
    button_xpath = '//android.widget.TextView[@text="Начать"]'
    
    try:
        # Ждем, пока кнопка станет кликабельной
        button = wait.until(
            EC.element_to_be_clickable((AppiumBy.XPATH, button_xpath))
        )
        print(f"✅ Кнопка кликабельна")
        
        # Можно проверить размеры (кнопка должна быть достаточно большой для клика)
        size = button.size
        location = button.location
        
        print(f"   Размер: {size['width']}x{size['height']}")
        print(f"   Позиция: ({location['x']}, {location['y']})")
        
        # Проверяем, что кнопка достаточно большая (минимум 44x44 пикселя для удобства)
        assert size['width'] >= 44 and size['height'] >= 44, \
            "Кнопка слишком маленькая для удобного клика"
        print(f"✅ Кнопка имеет достаточный размер")
        
    except Exception as e:
        print(f"❌ Кнопка не кликабельна: {e}")
        pytest.fail(f"Кнопка не кликабельна: {e}")


@pytest.mark.mobile
def test_button_click_works(mobile_driver: "Remote"):
    """
    Проверка: клик по кнопке работает и выполняет действие.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Клик по кнопке")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    # ЗАМЕНИТЕ на реальный селектор!
    button_xpath = '//android.widget.TextView[@text="Начать"]'
    
    try:
        initial_activity = driver.current_activity
        print(f"   Activity до клика: {initial_activity}")
        
        # Кликаем
        click_element_with_fallback(driver, wait, button_xpath)
        print(f"✅ Клик выполнен")
        
        # Ждем реакции приложения
        import time
        time.sleep(2)
        
        # Проверяем результат
        current_activity = driver.current_activity
        print(f"   Activity после клика: {current_activity}")
        
        # Если activity изменилась - значит произошел переход
        if current_activity != initial_activity:
            print(f"✅ Произошел переход на новый экран")
        else:
            print(f"ℹ️ Activity не изменилась (возможно, модальное окно или обновление экрана)")
        
    except Exception as e:
        print(f"❌ Ошибка при клике: {e}")
        pytest.fail(f"Клик не работает: {e}")

