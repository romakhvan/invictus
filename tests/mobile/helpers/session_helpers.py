"""
Утилиты подготовки авторизованного состояния для mobile-тестов.
"""

import time
import pytest

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.profile.profile_page import ProfilePage
from src.repositories.users_repository import (
    get_phone_for_active_service_product_user,
    get_phone_for_active_subscription_user,
    get_phone_for_coach_user,
    get_phone_for_potential_user,
    get_user_role_by_phone,
)
from tests.mobile.helpers.onboarding_helpers import run_auth_to_home, run_auth_to_main
from tests.mobile.helpers.profile_helpers import assert_profile_matches_potential_user


def _get_current_user_role_via_profile(driver, db):
    """
    Пытается открыть «Профиль» через таббар и вернуть роль текущего пользователя из БД.
    Если профиль недоступен, возвращает None.
    """
    try:
        from src.pages.mobile.shell.bottom_nav import BottomNav

        profile = BottomNav(driver).open_profile()
        phone_ui = profile.get_displayed_phone()
        if not phone_ui:
            return None
        return get_user_role_by_phone(db, phone_ui)
    except Exception:
        return None


def _restart_app(mobile_driver) -> None:
    """Перезапускает приложение, чтобы начать флоу с предсказуемого состояния."""
    try:
        mobile_driver.terminate_app(MOBILE_APP_PACKAGE)
        time.sleep(1)
        mobile_driver.activate_app(MOBILE_APP_PACKAGE)
        time.sleep(2)
    except Exception:
        pass


def _ensure_home_state_by_phone(
    mobile_driver,
    phone: str,
    expected_state: HomeState,
) -> HomePage:
    """Авторизует пользователя по номеру и приводит приложение к ожидаемому HomeState."""
    _restart_app(mobile_driver)
    home = run_auth_to_home(mobile_driver, phone, expected_state=expected_state)
    current_state = home.get_current_home_state()
    if current_state != expected_state:
        pytest.skip(
            f"После авторизации получено состояние {current_state.value}, "
            f"хотя ожидалось {expected_state.value}."
        )
    return home


def ensure_new_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Гарантирует состояние NEW_USER на главной."""
    role = _get_current_user_role_via_profile(mobile_driver, db)
    if role == "potential":
        profile = ProfilePage(mobile_driver).wait_loaded()
        assert_profile_matches_potential_user(db, profile)
        home = profile.nav.open_main()
        if home.get_current_home_state() == HomeState.NEW_USER:
            return home

    phone = get_phone_for_potential_user(db)
    if not phone:
        pytest.skip(
            "В БД не найден potential-пользователь с заполненным firstName для mobile NEW_USER сценариев."
        )

    home = _ensure_home_state_by_phone(mobile_driver, phone, HomeState.NEW_USER)
    profile = home.nav.open_profile()
    assert_profile_matches_potential_user(db, profile)
    return profile.nav.open_main()


def ensure_subscribed_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка состояния SUBSCRIBED на главной."""
    phone = get_phone_for_active_subscription_user(db)
    if not phone:
        pytest.skip("В БД не найден пользователь с активной подпиской для mobile SUBSCRIBED сценариев.")
    return _ensure_home_state_by_phone(mobile_driver, phone, HomeState.SUBSCRIBED)


def ensure_member_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка состояния MEMBER на главной."""
    phone = get_phone_for_active_service_product_user(db)
    if not phone:
        pytest.skip("В БД не найден пользователь с активным service product для mobile MEMBER сценариев.")
    return _ensure_home_state_by_phone(mobile_driver, phone, HomeState.MEMBER)


def ensure_coach_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка coach-пользователя. Пока режим coach не покрыт отдельным shell-слоем."""
    phone = get_phone_for_coach_user(db)
    if not phone:
        pytest.skip("В БД не найден coach-пользователь для mobile coach сценариев.")

    _restart_app(mobile_driver)
    run_auth_to_home(mobile_driver, phone)
    pytest.skip(
        "Coach flow требует отдельного page-object слоя для выбора режима Client/Coach и пока не автоматизирован."
    )


def ensure_potential_user_on_main_screen(mobile_driver, db) -> None:
    """
    Гарантирует состояние NEW_USER на главном экране под пользователем с role=potential.
    """
    ensure_new_user_on_home_screen(mobile_driver, db)
    return

    try:
        mobile_driver.terminate_app(MOBILE_APP_PACKAGE)
        time.sleep(1)
        mobile_driver.activate_app(MOBILE_APP_PACKAGE)
        time.sleep(2)
    except Exception:
        pass

    role = _get_current_user_role_via_profile(mobile_driver, db)
    if role is not None:
        if role == "potential":
            profile = ProfilePage(mobile_driver).wait_loaded()
            print("Проверка: сверка данных в профиле с potential-пользователем в БД...")
            assert_profile_matches_potential_user(db, profile)
            home = profile.nav.open_main()
            if home.get_current_home_state() != HomeState.NEW_USER:
                pytest.skip(
                    "Вход под potential, но главный экран не в состоянии NEW_USER. "
                    "Возможна рассинхронизация состояния приложения."
                )
            return
        pytest.skip(
            f"В приложении выполнен вход не под new user (potential). "
            f"Роль текущего пользователя в БД: {role}. "
            "Сбросьте данные приложения или выполните вход под пользователем с role: potential."
        )

    phone = get_phone_for_potential_user(db)
    if not phone:
        pytest.skip(
            "В БД нет пользователя с role: 'potential' и полем firstName. "
            "Создайте такого пользователя (например, пройдите онбординг в отдельном тесте)."
        )

    # _get_current_user_role_via_profile могла перейти на экран Профиля,
    # поэтому перезапускаем приложение перед авторизацией, чтобы оказаться на Preview
    try:
        mobile_driver.terminate_app(MOBILE_APP_PACKAGE)
        time.sleep(1)
        mobile_driver.activate_app(MOBILE_APP_PACKAGE)
        time.sleep(2)
    except Exception:
        pass

    run_auth_to_main(mobile_driver, phone)

    home = HomePage(mobile_driver).wait_loaded()
    profile = home.nav.open_profile()
    print("Проверка: сверка данных в профиле с potential-пользователем в БД...")
    assert_profile_matches_potential_user(db, profile)
    profile.nav.open_main()
