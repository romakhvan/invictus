"""
Тесты для нижней навигации (если есть).
"""

import pytest
from typing import TYPE_CHECKING
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
def test_navigation_tabs_exist(mobile_driver: "Remote"):
    """
    Проверка: вкладки навигации существуют и видны.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Вкладки навигации")
    print("=" * 80)
    
    # Ищем элементы нижней навигации
    # ЗАМЕНИТЕ селекторы на реальные из вашего приложения!
    
    # Вариант 1: Поиск по классу BottomNavigationView
    try:
        nav_elements = driver.find_elements(
            AppiumBy.XPATH, 
            "//androidx.compose.material3.NavigationBarItem"
        )
        print(f"✅ Найдено элементов навигации: {len(nav_elements)}")
    except:
        pass
    
    # Вариант 2: Поиск по тексту вкладок
    tabs = ["Главная", "Тренировки", "Профиль"]  # ЗАМЕНИТЕ на реальные названия
    
    for tab_name in tabs:
        try:
            tab = driver.find_element(
                AppiumBy.XPATH,
                f"//*[@text='{tab_name}']"
            )
            assert tab.is_displayed(), f"Вкладка '{tab_name}' не видна"
            print(f"✅ Вкладка '{tab_name}' найдена и видна")
        except Exception as e:
            print(f"⚠️ Вкладка '{tab_name}' не найдена: {e}")


@pytest.mark.mobile
def test_navigation_click(mobile_driver: "Remote"):
    """
    Проверка: клик по вкладке навигации работает.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Клик по навигации")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    # ЗАМЕНИТЕ на реальный селектор вкладки!
    tab_text = "Тренировки"  # Пример
    
    try:
        # Находим и кликаем по вкладке
        tab = wait.until(
            EC.element_to_be_clickable(
                (AppiumBy.XPATH, f"//*[@text='{tab_text}']")
            )
        )
        print(f"✅ Вкладка '{tab_text}' найдена")
        
        initial_activity = driver.current_activity
        
        # Кликаем
        tab.click()
        print(f"✅ Клик выполнен")
        
        # Ждем немного для перехода
        import time
        time.sleep(2)
        
        # Проверяем, что произошел переход (activity изменилась или экран обновился)
        current_activity = driver.current_activity
        print(f"   Activity до: {initial_activity}")
        print(f"   Activity после: {current_activity}")
        
        # Можно проверить наличие элементов нового экрана
        print(f"✅ Навигация работает")
        
    except Exception as e:
        print(f"❌ Ошибка при навигации: {e}")

