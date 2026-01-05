"""
Тест для запуска мобильного приложения.
"""

import pytest
from typing import TYPE_CHECKING
from src.config.app_config import MOBILE_APP_PACKAGE, MOBILE_APP_ACTIVITY

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
@pytest.mark.smoke
def test_app_launches(mobile_driver: "Remote"):
    """
    Тест: проверка запуска мобильного приложения.
    """
    driver = mobile_driver
    
    print(f"\n📱 Проверка запуска приложения...")
    print(f"   Package: {MOBILE_APP_PACKAGE}")
    print(f"   Activity: {MOBILE_APP_ACTIVITY}")
    
    # Проверяем, что приложение запущено
    current_package = driver.current_package
    current_activity = driver.current_activity
    
    print(f"\n✅ Приложение запущено:")
    print(f"   Текущий package: {current_package}")
    print(f"   Текущая activity: {current_activity}")
    
    # Проверяем, что package соответствует ожидаемому
    assert current_package == MOBILE_APP_PACKAGE, \
        f"Ожидался package {MOBILE_APP_PACKAGE}, получен {current_package}"
    
    # Проверяем, что activity содержит ожидаемое значение
    assert MOBILE_APP_ACTIVITY in current_activity or current_activity.endswith(MOBILE_APP_ACTIVITY), \
        f"Activity {current_activity} не соответствует ожидаемому {MOBILE_APP_ACTIVITY}"
    
    print(f"\n✅ Тест пройден успешно!")

