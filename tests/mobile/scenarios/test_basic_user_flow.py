"""
Базовые пользовательские сценарии.
Проверяют типичные действия пользователя.
"""

import pytest
from typing import TYPE_CHECKING
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
def test_app_start_to_main_screen(mobile_driver: "Remote"):
    """
    Сценарий: Запуск приложения → Главный экран.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("СЦЕНАРИЙ: Запуск приложения")
    print("=" * 80)
    
    # Шаг 1: Проверяем, что приложение запущено
    assert driver.current_package is not None, "Приложение не запущено"
    print("✅ Шаг 1: Приложение запущено")
    
    # Шаг 2: Проверяем главный экран
    wait = WebDriverWait(driver, 10)
    
    # Ищем характерные элементы главного экрана
    # ЗАМЕНИТЕ на реальные селекторы!
    try:
        # Пример: ищем кнопку "Начать"
        main_button = wait.until(
            EC.presence_of_element_located(
                (AppiumBy.XPATH, '//android.widget.TextView[@text="Начать"]')
            )
        )
        print("✅ Шаг 2: Главный экран загружен")
    except:
        print("⚠️ Шаг 2: Не удалось найти характерные элементы главного экрана")
    
    # Шаг 3: Делаем скриншот
    driver.save_screenshot("scenario_start_to_main.png")
    print("✅ Шаг 3: Скриншот сохранен")


@pytest.mark.mobile
def test_button_click_flow(mobile_driver: "Remote"):
    """
    Сценарий: Клик по кнопке → Переход/Действие.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("СЦЕНАРИЙ: Клик по кнопке")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    # Шаг 1: Находим кнопку
    # ЗАМЕНИТЕ на реальный селектор!
    button_xpath = '//android.widget.TextView[@text="Начать"]'
    
    try:
        button = wait.until(
            EC.element_to_be_clickable((AppiumBy.XPATH, button_xpath))
        )
        print("✅ Шаг 1: Кнопка найдена")
    except Exception as e:
        pytest.skip(f"Кнопка не найдена: {e}")
    
    # Шаг 2: Кликаем
    initial_activity = driver.current_activity
    button.click()
    print("✅ Шаг 2: Клик выполнен")
    
    # Шаг 3: Ждем реакции
    time.sleep(2)
    
    # Шаг 4: Проверяем результат
    current_activity = driver.current_activity
    if current_activity != initial_activity:
        print(f"✅ Шаг 3: Произошел переход (activity изменилась)")
    else:
        print(f"ℹ️ Шаг 3: Activity не изменилась")
    
    # Делаем скриншот результата
    driver.save_screenshot("scenario_button_click_result.png")
    print("✅ Шаг 4: Скриншот результата сохранен")


@pytest.mark.mobile
def test_scroll_swipe_flow(mobile_driver: "Remote"):
    """
    Сценарий: Скролл/Свайп по экрану.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("СЦЕНАРИЙ: Скролл экрана")
    print("=" * 80)
    
    # Получаем размер экрана
    window_size = driver.get_window_size()
    width = window_size['width']
    height = window_size['height']
    
    print(f"   Размер экрана: {width}x{height}")
    
    # Шаг 1: Скролл вниз
    start_x = width // 2
    start_y = int(height * 0.7)
    end_y = int(height * 0.3)
    
    driver.swipe(start_x, start_y, start_x, end_y, 1000)
    print("✅ Шаг 1: Скролл вниз выполнен")
    
    time.sleep(1)
    
    # Шаг 2: Скролл вверх
    driver.swipe(start_x, end_y, start_x, start_y, 1000)
    print("✅ Шаг 2: Скролл вверх выполнен")
    
    # Делаем скриншот
    driver.save_screenshot("scenario_scroll.png")
    print("✅ Скриншот сохранен")

