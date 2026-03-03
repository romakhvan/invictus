"""
Утилиты для UI тестирования.
"""

import time
from typing import Optional, Callable
from pathlib import Path
from datetime import datetime


def take_screenshot(page_or_driver, filename: Optional[str] = None) -> str:
    """
    Сделать скриншот.
    
    Args:
        page_or_driver: Playwright Page или Appium WebDriver
        filename: Имя файла (если None, генерируется автоматически)
    
    Returns:
        Путь к сохраненному скриншоту
    """
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
    
    screenshot_path = screenshots_dir / filename
    
    # Для Playwright
    if hasattr(page_or_driver, 'screenshot'):
        page_or_driver.screenshot(path=str(screenshot_path))
    # Для Appium
    elif hasattr(page_or_driver, 'save_screenshot'):
        page_or_driver.save_screenshot(str(screenshot_path))
    else:
        raise ValueError("Неподдерживаемый тип объекта для скриншота")
    
    return str(screenshot_path)


def wait_with_retry(
    condition: Callable[[], bool],
    timeout: int = 10,
    retry_interval: float = 0.5,
    error_message: str = "Условие не выполнено за отведенное время"
) -> bool:
    """
    Ожидание выполнения условия с повторными попытками.
    
    Args:
        condition: Функция, возвращающая True при успехе
        timeout: Максимальное время ожидания в секундах
        retry_interval: Интервал между попытками в секундах
        error_message: Сообщение об ошибке
    
    Returns:
        True если условие выполнено, иначе False
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if condition():
            return True
        time.sleep(retry_interval)
    
    raise TimeoutError(f"{error_message} (timeout: {timeout}s)")


def log_action(action: str, details: Optional[str] = None):
    """
    Логирование действия в тесте.
    
    Args:
        action: Описание действия
        details: Дополнительные детали
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    message = f"[{timestamp}] {action}"
    if details:
        message += f" - {details}"
    print(message)


def format_selector_info(selector: str, by_type: Optional[str] = None) -> str:
    """
    Форматирование информации о селекторе для логов.
    
    Args:
        selector: Селектор элемента
        by_type: Тип селектора (для Appium: ID, XPATH, etc.)
    
    Returns:
        Отформатированная строка
    """
    if by_type:
        return f"{by_type}: {selector}"
    return selector


def detect_element_type(xpath: str) -> str:
    """
    Определяет тип элемента по XPath для автоматической генерации имени.
    
    Args:
        xpath: XPath селектор элемента
    
    Returns:
        Тип элемента (Кнопка, Текст, Поле ввода и т.д.)
    """
    xpath_lower = xpath.lower()
    
    # Определяем по типу Android виджета
    if 'button' in xpath_lower:
        return "Кнопка"
    elif 'edittext' in xpath_lower:
        return "Поле ввода"
    elif 'textview' in xpath_lower:
        return "Текст"
    elif 'imageview' in xpath_lower:
        return "Изображение"
    elif 'checkbox' in xpath_lower:
        return "Чекбокс"
    elif 'switch' in xpath_lower:
        return "Переключатель"
    elif 'radiobutton' in xpath_lower:
        return "Радиокнопка"
    elif 'viewgroup' in xpath_lower and 'clickable' in xpath_lower:
        return "Кнопка"
    elif 'viewgroup' in xpath_lower:
        return "Элемент"
    else:
        return "Элемент"


def verify_text_on_screen(wait, xpath: str, element_name: str, timeout: int = 20):
    """
    Проверка наличия элемента на экране для мобильных тестов.
    
    Args:
        wait: WebDriverWait объект
        xpath: XPath селектор элемента
        element_name: Имя элемента для логов (текст, кнопка, селектор и т.д.)
        timeout: Таймаут ожидания в секундах
    
    Raises:
        AssertionError: Если элемент не найден
    """
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        element = wait.until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )
        assert element is not None, f"Элемент '{element_name}' не найден"
        print(f"✅ {element_name} найден")
    except Exception as e:
        print(f"❌ {element_name} не найден")
        raise AssertionError(f"Элемент '{element_name}' не найден на экране\nXPath: {xpath}") from e


def click_element_with_fallback(driver, wait, xpath: str, element_name: Optional[str] = None, timeout: int = 20):
    """
    Клик по элементу с несколькими fallback методами для мобильных тестов.
    
    Пробует методы в следующем порядке:
    1. Прямой клик по элементу
    2. Клик по родительскому кликабельному элементу
    3. Клик по координатам центра элемента
    
    Args:
        driver: Appium WebDriver объект
        wait: WebDriverWait объект
        xpath: XPath селектор элемента
        element_name: Имя элемента для логов (если None, определяется автоматически)
        timeout: Таймаут ожидания в секундах
    
    Raises:
        Exception: Если все методы клика не сработали
    """
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.support import expected_conditions as EC
    import pytest
    
    # Автоматическое определение типа элемента, если не указан element_name
    if element_name is None:
        element_type = detect_element_type(xpath)
        # Пытаемся извлечь текст из XPath для более читабельного имени
        if '@text="' in xpath:
            text = xpath.split('@text="')[1].split('"')[0]
            element_name = f'{element_type} "{text}"'
        elif 'content-desc="' in xpath:
            text = xpath.split('content-desc="')[1].split('"')[0]
            element_name = f'{element_type} "{text}"'
        else:
            element_name = element_type
    
    # Метод 1: Прямой клик по элементу
    try:
        element = wait.until(
            EC.element_to_be_clickable((AppiumBy.XPATH, xpath))
        )
        print(f"✅ {element_name} найден и кликабелен")
        element.click()
        print(f"✅ Клик по {element_name} выполнен")
        return
    except Exception as e:
        print(f"⚠️ {element_name} не кликабелен напрямую, ищем родительский: {e}")
    
    # Метод 2: Клик по родительскому кликабельному элементу
    try:
        # Извлекаем базовый селектор из xpath для построения родительского
        parent_xpath = f"{xpath}/parent::*[@clickable='true']"
        parent_element = wait.until(
            EC.element_to_be_clickable((AppiumBy.XPATH, parent_xpath))
        )
        print(f"✅ Найден родительский кликабельный элемент для {element_name}")
        parent_element.click()
        print(f"✅ Клик по родительскому элементу выполнен")
        return
    except Exception as e2:
        print(f"⚠️ Родительский элемент не найден, используем координаты: {e2}")
    
    # Метод 3: Клик по координатам центра элемента
    try:
        element = wait.until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )
        # Получаем координаты центра элемента
        location = element.location
        size = element.size
        center_x = location['x'] + size['width'] // 2
        center_y = location['y'] + size['height'] // 2
        # Кликаем по координатам
        driver.tap([(center_x, center_y)], 100)
        print(f"✅ Клик по координатам выполнен: ({center_x}, {center_y})")
        return
    except Exception as e3:
        print(f"❌ Клик по {element_name} не выполнен")
        pytest.fail(f"Не удалось кликнуть по '{element_name}'\nXPath: {xpath}")