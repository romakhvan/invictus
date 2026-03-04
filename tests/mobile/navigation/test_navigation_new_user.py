"""
Smoke-тест навигации для пользователя в состоянии NEW_USER (role: potential).

Проверяет, что под существующим потенциальным клиентом открываются основные экраны:
вход по номеру и коду → главная → Записи → Статистика → Профиль → Главная.
Онбординг не выполняется; в БД должен быть пользователь с role: 'potential' и полем firstName.
Переходы выполняются через BottomNav (.nav) без прямого обращения к локаторам.
"""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.pages.mobile.home import HomePage, HomeState
from src.repositories.users_repository import get_potential_user_display_info


@pytest.mark.mobile
@pytest.mark.smoke
def test_navigation_new_user_main_tabs(potential_user_on_main_screen: "Remote", db):
    """
    Smoke: проверка перехода по основным табам для пользователя NEW_USER (potential).

    Предусловие: в БД есть пользователь с role: 'potential' и полем firstName.
    Фикстура выполняет вход (превью → телефон → SMS-код) без онбординга. После входа проверяется
    переход по всем табам: Записи → Статистика → Профиль → Главная.
    """
    driver = potential_user_on_main_screen

    print("\n" + "=" * 80)
    print("SMOKE-ТЕСТ: Навигация по основным страницам (NEW_USER)")
    print("=" * 80 + "\n")

    # Шаг 1: Проверка главного экрана
    home = HomePage(driver).wait_loaded()
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "Ожидалось состояние NEW_USER после входа под potential-пользователем"
    )
    print("✅ На главной (NEW_USER), начинаем обход табов")

    # Шаг 2: Записи
    bookings = home.nav.open_bookings()

    # Шаг 3: Статистика
    stats = bookings.nav.open_stats()

    # Шаг 4: Профиль — проверка имени и телефона по БД
    profile = stats.nav.open_profile()
    user_info = get_potential_user_display_info(db)
    if user_info:
        profile.assert_profile_data_matches_db(
            user_info["fullName"],
            user_info["phone_display"],
        )

    # Шаг 5: Возврат на главную
    home = profile.nav.open_main()
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "После обхода табов ожидалась снова главная (NEW_USER)"
    )
    print("✅ Возврат на главную (NEW_USER), навигация пройдена")

    # Интерактивное меню отладки после прохождения теста
    from tests.conftest import _interactive_debug_menu
    _interactive_debug_menu(driver)
