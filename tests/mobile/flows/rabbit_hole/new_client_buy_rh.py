"""
Тест: Новый клиент покупает Rabbit Hole.

Сценарий:
1. Запуск приложения
2. Регистрация/Вход нового пользователя (через хелпер)
3. Навигация к Rabbit Hole
4. Выбор продукта Rabbit Hole
5. Оформление покупки
6. Проверка в БД (rabbitholev2)
"""

import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

from selenium.webdriver.support.ui import WebDriverWait
from src.config.app_config import MOBILE_APP_PACKAGE
from src.repositories.rabbitholev2_repository import get_rabbitholev2_subscriptions_by_user
from src.utils.ui_helpers import take_screenshot
from tests.mobile.helpers.auth_helpers import authorize_user
from datetime import datetime, timedelta
import time


@pytest.mark.mobile
@pytest.mark.flow
def test_new_client_buys_rabbit_hole(mobile_driver: "Remote", db):
    """
    Flow-тест: Новый клиент покупает Rabbit Hole.
    
    Шаги:
    1. Запуск приложения (автоматически через фикстуру)
    2. Авторизация пользователя (через хелпер)
    3. Навигация к Rabbit Hole
    4. Выбор продукта
    5. Оформление покупки
    6. Проверка в БД
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("FLOW-ТЕСТ: Новый клиент покупает Rabbit Hole")
    print("=" * 80)
    
    wait = WebDriverWait(driver, 20)
    
    try:
        # Проверка запуска приложения
        assert driver.current_package == MOBILE_APP_PACKAGE, \
            f"Неверный package: ожидался {MOBILE_APP_PACKAGE}, получен {driver.current_package}"
        print(f"✅ Приложение запущено: {driver.current_package}")
        
        # ШАГ 1: Авторизация пользователя (используем хелпер)
        print("\n--- ШАГ 1: Авторизация пользователя ---")
        test_phone = "7001234567"
        authorize_user(driver, wait, test_phone)
        
        # TODO: Добавить остальные шаги теста
        # ШАГ 2: Навигация к Rabbit Hole
        # ШАГ 3: Выбор продукта
        # ШАГ 4: Оформление покупки
        # ШАГ 5: Проверка в БД
        
    except Exception as e:
        # Автоматический скриншот при ошибке
        try:
            screenshot_path = take_screenshot(
                driver, 
                f"error_new_client_buy_rh_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            print(f"📸 Скриншот ошибки сохранен: {screenshot_path}")
        except Exception as screenshot_error:
            print(f"⚠️ Не удалось сделать скриншот при ошибке: {screenshot_error}")
        
        raise

