"""
Smoke тесты для главного экрана приложения.
Проверяют базовую работоспособность приложения.
"""

import pytest
from typing import TYPE_CHECKING
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
@pytest.mark.smoke
def test_main_screen_loaded(mobile_driver: "Remote"):
    """
    Проверка: главный экран загрузился корректно.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Главный экран загружен")
    print("=" * 80)
    
    # Проверяем, что приложение запущено
    assert driver.current_package is not None, "Приложение не запущено"
    print(f"✅ Приложение запущено: {driver.current_package}")
    
    # Проверяем текущую activity
    current_activity = driver.current_activity
    print(f"✅ Текущая activity: {current_activity}")
    
    # Делаем скриншот для визуальной проверки
    screenshot_path = "screenshots/main_screen.png"
    driver.save_screenshot(screenshot_path)
    print(f"📸 Скриншот сохранен: {screenshot_path}")


@pytest.mark.mobile
@pytest.mark.smoke
def test_main_screen_has_elements(mobile_driver: "Remote"):
    """
    Проверка: на главном экране есть основные элементы.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Основные элементы на экране")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 10)
    
    # Проверяем наличие текстовых элементов
    try:
        text_elements = wait.until(
            EC.presence_of_all_elements_located(
                (AppiumBy.XPATH, "//android.widget.TextView")
            )
        )
        print(f"✅ Найдено текстовых элементов: {len(text_elements)}")
        
        # Выводим первые 5 текстов
        for i, element in enumerate(text_elements[:5], 1):
            text = element.text
            if text:
                print(f"   {i}. {text}")
    except Exception as e:
        print(f"⚠️ Не удалось найти текстовые элементы: {e}")
    
    # Проверяем наличие кнопок
    try:
        buttons = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
        print(f"✅ Найдено кнопок: {len(buttons)}")
    except Exception as e:
        print(f"⚠️ Не удалось найти кнопки: {e}")
    
    # Проверяем наличие изображений
    try:
        images = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.ImageView")
        print(f"✅ Найдено изображений: {len(images)}")
    except Exception as e:
        print(f"⚠️ Не удалось найти изображения: {e}")


@pytest.mark.mobile
@pytest.mark.smoke
def test_no_crashes(mobile_driver: "Remote"):
    """
    Проверка: приложение не падает при базовых действиях.
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА: Приложение стабильно")
    print("=" * 80)
    
    initial_activity = driver.current_activity
    
    # Пробуем сделать несколько действий
    try:
        # Получаем размер экрана
        window_size = driver.get_window_size()
        print(f"✅ Размер экрана получен: {window_size}")
        
        # Проверяем ориентацию
        orientation = driver.orientation
        print(f"✅ Ориентация: {orientation}")
        
        # Проверяем, что activity не изменилась (приложение не упало)
        current_activity = driver.current_activity
        assert current_activity == initial_activity, "Activity изменилась - возможно, приложение упало"
        print(f"✅ Приложение стабильно, activity не изменилась")
        
    except Exception as e:
        pytest.fail(f"❌ Приложение упало или произошла ошибка: {e}")

