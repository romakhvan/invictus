"""
Диагностический тест для проверки подключения Appium.
"""

import pytest
from src.config.app_config import (
    MOBILE_APPIUM_SERVER,
    MOBILE_DEVICE_NAME,
    MOBILE_PLATFORM_VERSION,
    MOBILE_APP_PACKAGE,
    MOBILE_APP_ACTIVITY
)


@pytest.mark.mobile
def test_appium_server_connection():
    """Проверка подключения к Appium серверу."""
    import requests
    
    print(f"\n🔍 Проверка Appium сервера: {MOBILE_APPIUM_SERVER}")
    try:
        response = requests.get(f"{MOBILE_APPIUM_SERVER}/status", timeout=5)
        assert response.status_code == 200, f"Сервер вернул код {response.status_code}"
        status = response.json()
        print(f"✅ Appium сервер доступен: {status.get('value', {}).get('message', 'OK')}")
        assert status.get('value', {}).get('ready', False), "Сервер не готов принимать соединения"
    except requests.exceptions.ConnectionError:
        pytest.fail(f"❌ Не удалось подключиться к Appium серверу на {MOBILE_APPIUM_SERVER}\n"
                   f"   Убедитесь, что Appium запущен: appium")
    except Exception as e:
        pytest.fail(f"❌ Ошибка при проверке Appium сервера: {e}")


@pytest.mark.mobile
def test_device_connection():
    """Проверка подключения устройства."""
    import subprocess
    
    print(f"\n🔍 Проверка подключения устройства: {MOBILE_DEVICE_NAME}")
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = result.stdout
        print(f"📱 Список устройств:\n{output}")
        
        if MOBILE_DEVICE_NAME not in output:
            pytest.fail(f"❌ Устройство {MOBILE_DEVICE_NAME} не найдено в списке подключенных устройств")
        
        if "device" not in output or "offline" in output:
            pytest.fail(f"❌ Устройство {MOBILE_DEVICE_NAME} не готово к работе")
        
        print(f"✅ Устройство {MOBILE_DEVICE_NAME} подключено и готово")
    except FileNotFoundError:
        pytest.fail("❌ ADB не найден. Убедитесь, что Android SDK установлен и добавлен в PATH")
    except Exception as e:
        pytest.fail(f"❌ Ошибка при проверке устройства: {e}")


@pytest.mark.mobile
def test_appium_driver_initialization(mobile_driver):
    """Проверка инициализации Appium драйвера."""
    driver = mobile_driver
    
    print(f"\n🔍 Проверка инициализации драйвера...")
    print(f"   Сервер: {MOBILE_APPIUM_SERVER}")
    print(f"   Устройство: {MOBILE_DEVICE_NAME}")
    print(f"   Версия Android: {MOBILE_PLATFORM_VERSION}")
    print(f"   Package: {MOBILE_APP_PACKAGE}")
    print(f"   Activity: {MOBILE_APP_ACTIVITY}")
    
    try:
        # Проверяем, что драйвер создан
        assert driver is not None, "Драйвер не создан"
        
        # Проверяем текущий package
        current_package = driver.current_package
        print(f"\n✅ Драйвер инициализирован:")
        print(f"   Текущий package: {current_package}")
        
        if current_package:
            assert current_package == MOBILE_APP_PACKAGE, \
                f"Ожидался package {MOBILE_APP_PACKAGE}, получен {current_package}"
        
        # Проверяем текущую activity
        current_activity = driver.current_activity
        print(f"   Текущая activity: {current_activity}")
        
        print(f"\n✅ Все проверки пройдены успешно!")
    except Exception as e:
        pytest.fail(f"❌ Ошибка при инициализации драйвера: {e}\n"
                   f"   Убедитесь, что:\n"
                   f"   1. Appium сервер запущен\n"
                   f"   2. Устройство подключено\n"
                   f"   3. Приложение установлено на устройстве")

