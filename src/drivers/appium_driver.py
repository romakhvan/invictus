"""
Инициализация и управление Appium драйвером.
"""

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from typing import Optional, Dict, Any
from src.config.app_config import (
    MOBILE_APPIUM_SERVER,
    MOBILE_PLATFORM,
    MOBILE_DEVICE_NAME,
    MOBILE_PLATFORM_VERSION,
    MOBILE_APP_PATH,
    MOBILE_APP_PACKAGE,
    MOBILE_APP_ACTIVITY,
    IMPLICIT_WAIT
)


class AppiumDriver:
    """Управление Appium драйвером для мобильных тестов."""
    
    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
    
    def start(self, **kwargs):
        """
        Запуск Appium драйвера.
        
        Args:
            **kwargs: Дополнительные опции для кастомизации
        
        Raises:
            ConnectionError: Если не удалось подключиться к Appium серверу
            WebDriverException: Если произошла ошибка при создании сессии
        """
        platform = kwargs.get("platform", MOBILE_PLATFORM)
        
        if platform.lower() == "android":
            capabilities = self._get_android_capabilities(**kwargs)
        elif platform.lower() == "ios":
            capabilities = self._get_ios_capabilities(**kwargs)
        else:
            raise ValueError(f"Неподдерживаемая платформа: {platform}")
        
        server_url = kwargs.get("server_url", MOBILE_APPIUM_SERVER)
        
        try:
            print(f"\n🚀 Запуск Appium драйвера...")
            print(f"   Сервер: {server_url}")
            print(f"   Платформа: {platform}")
            if platform.lower() == "android":
                print(f"   Устройство: {capabilities.device_name}")
                print(f"   Версия Android: {capabilities.platform_version}")
                if capabilities.app_package:
                    print(f"   Package: {capabilities.app_package}")
                if capabilities.app_activity:
                    print(f"   Activity: {capabilities.app_activity}")
            
            self.driver = webdriver.Remote(server_url, options=capabilities)
            self.driver.implicitly_wait(IMPLICIT_WAIT)
            print(f"✅ Драйвер успешно запущен")
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "Failed to establish" in error_msg:
                raise ConnectionError(
                    f"❌ Не удалось подключиться к Appium серверу на {server_url}\n"
                    f"   Убедитесь, что Appium запущен: appium"
                ) from e
            elif "No such device" in error_msg or "device" in error_msg.lower():
                raise RuntimeError(
                    f"❌ Устройство не найдено или недоступно\n"
                    f"   Проверьте: adb devices\n"
                    f"   Убедитесь, что устройство подключено и USB отладка включена"
                ) from e
            elif "app" in error_msg.lower() and ("not found" in error_msg.lower() or "not installed" in error_msg.lower()):
                raise RuntimeError(
                    f"❌ Приложение не найдено на устройстве\n"
                    f"   Package: {capabilities.app_package if hasattr(capabilities, 'app_package') else 'N/A'}\n"
                    f"   Убедитесь, что приложение установлено на устройстве"
                ) from e
            else:
                raise RuntimeError(
                    f"❌ Ошибка при запуске Appium драйвера: {error_msg}\n"
                    f"   Проверьте:\n"
                    f"   1. Appium сервер запущен: {server_url}\n"
                    f"   2. Устройство подключено: adb devices\n"
                    f"   3. Приложение установлено на устройстве"
                ) from e
    
    def _get_android_capabilities(self, **kwargs) -> UiAutomator2Options:
        """Получить capabilities для Android."""
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = kwargs.get("device_name", MOBILE_DEVICE_NAME)
        options.platform_version = kwargs.get("platform_version", MOBILE_PLATFORM_VERSION)
        
        # Automation name по умолчанию
        options.automation_name = kwargs.get("automation_name", "UiAutomator2")
        
        # Установка приложения
        app_path = kwargs.get("app_path", MOBILE_APP_PATH)
        if app_path:
            options.app = app_path
        else:
            # Используем package и activity (из kwargs или из конфига)
            app_package = kwargs.get("app_package", MOBILE_APP_PACKAGE)
            app_activity = kwargs.get("app_activity", MOBILE_APP_ACTIVITY)
            
            if app_package:
                options.app_package = app_package
            if app_activity:
                options.app_activity = app_activity
        
        # Дополнительные опции из kwargs
        if "no_reset" in kwargs:
            options.no_reset = kwargs["no_reset"]
        else:
            options.no_reset = True  # По умолчанию не сбрасываем данные приложения
        
        if "full_reset" in kwargs:
            options.full_reset = kwargs["full_reset"]
        
        # Дополнительные полезные опции
        if "auto_grant_permissions" in kwargs:
            options.auto_grant_permissions = kwargs["auto_grant_permissions"]
        else:
            options.auto_grant_permissions = True  # Автоматически давать разрешения
        
        return options
    
    def _get_ios_capabilities(self, **kwargs) -> XCUITestOptions:
        """Получить capabilities для iOS."""
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.device_name = kwargs.get("device_name", MOBILE_DEVICE_NAME)
        options.platform_version = kwargs.get("platform_version", MOBILE_PLATFORM_VERSION)
        
        if MOBILE_APP_PATH:
            options.bundle_id = MOBILE_APP_PATH
        elif "bundle_id" in kwargs:
            options.bundle_id = kwargs["bundle_id"]
        
        # Дополнительные опции из kwargs
        if "automation_name" in kwargs:
            options.automation_name = kwargs["automation_name"]
        if "no_reset" in kwargs:
            options.no_reset = kwargs["no_reset"]
        if "full_reset" in kwargs:
            options.full_reset = kwargs["full_reset"]
        
        return options
    
    def get_driver(self) -> webdriver.Remote:
        """Получить текущий драйвер."""
        if not self.driver:
            raise RuntimeError("Драйвер не запущен. Вызовите start() сначала.")
        return self.driver
    
    def close(self):
        """Закрыть драйвер и освободить ресурсы."""
        if self.driver:
            self.driver.quit()
            self.driver = None

