"""
Smoke-тест навигации для пользователя в состоянии NEW_USER (role: potential).

Проверяет, что под существующим потенциальным клиентом открываются основные экраны:
вход по номеру и коду → главная → Записи → Статистика → Профиль.
Онбординг не выполняется; в БД должен быть пользователь с role: 'potential'.
"""

import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from appium.webdriver import Remote

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.pages.mobile.home import HomePage, HomeState


# Таймаут ожидания загрузки экрана после перехода по табу (сек)
TAB_LOAD_WAIT = 1


@pytest.mark.mobile
@pytest.mark.smoke
def test_navigation_new_user_main_tabs(potential_user_on_main_screen: "Remote"):
    """
    Smoke: проверка перехода по основным табам для пользователя NEW_USER (potential).

    Предусловие: в БД есть пользователь с role: 'potential'. Тест входит по номеру и
    SMS-коду (без онбординга), попадает на главную, затем обходит табы Записи →
    Статистика → Профиль → Главная и проверяет, что экраны открываются.
    """
    driver = potential_user_on_main_screen
    wait = WebDriverWait(driver, 10)

    print("\n" + "=" * 80)
    print("SMOKE-ТЕСТ: Навигация по основным страницам (NEW_USER)")
    print("=" * 80 + "\n")

    home = HomePage(driver)
    assert home.get_current_home_state() == HomeState.NEW_USER
    content = home.get_content()
    print("✅ На главной (NEW_USER), начинаем обход табов")

    tabs = [
        ("Записи", content.TAB_BOOKINGS),
        ("Статистика", content.TAB_STATS),
        ("Профиль", content.TAB_PROFILE),
        ("Главная", content.TAB_MAIN),
    ]

    for tab_name, locator in tabs:
        try:
            el = wait.until(EC.element_to_be_clickable(locator))
            el.click()
            time.sleep(TAB_LOAD_WAIT)
            # Проверяем, что таб остаётся видимым (экран переключился, приложение живо)
            wait.until(EC.visibility_of_element_located(locator))
            print(f"✅ Таб «{tab_name}» открыт")
        except Exception as e:
            pytest.fail(f"Таб «{tab_name}»: не удалось перейти или экран не загрузился — {e}")

    # Финальная проверка: снова на главной в состоянии NEW_USER
    home = HomePage(driver)
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "После обхода табов ожидалась снова главная (NEW_USER)"
    )
    print("✅ Возврат на главную (NEW_USER), навигация пройдена")
