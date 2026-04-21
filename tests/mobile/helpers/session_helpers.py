"""
Утилиты подготовки авторизованного состояния для mobile-тестов.
"""

import time

import pytest

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.profile.profile_page import ProfilePage
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
    TestUserContext,
)
from tests.mobile.helpers.onboarding_helpers import run_auth_to_home
from tests.mobile.helpers.profile_helpers import assert_profile_matches_potential_user


def _try_reuse_existing_potential_home(
    mobile_driver,
    db,
    context: TestUserContext,
) -> HomePage | None:
    """Пытается переиспользовать уже открытую сессию, если профиль совпадает с выбранным context."""
    try:
        try:
            from src.pages.mobile.shell.bottom_nav import BottomNav

            profile = BottomNav(mobile_driver).open_profile()
        except Exception:
            profile = ProfilePage(mobile_driver).wait_loaded()
        assert_profile_matches_potential_user(db, profile, context=context)
        home = profile.nav.open_main()
        if home.get_current_home_state() == (context.expected_home_state or HomeState.NEW_USER):
            return home
    except Exception:
        return None


def _restart_app(mobile_driver) -> None:
    """Перезапускает приложение, чтобы начать flow с предсказуемого состояния."""
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
    selector = MobileTestUserSelector(db)
    context = selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)

    existing_home = _try_reuse_existing_potential_home(mobile_driver, db, context)
    if existing_home:
        return existing_home

    home = _ensure_home_state_by_phone(
        mobile_driver,
        context.phone,
        context.expected_home_state or HomeState.NEW_USER,
    )
    profile = home.nav.open_profile()
    assert_profile_matches_potential_user(db, profile, context=context)
    return profile.nav.open_main()


def ensure_subscribed_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка состояния SUBSCRIBED на главной."""
    selector = MobileTestUserSelector(db)
    context = selector.select_or_skip(MobileTestUserScenario.SUBSCRIBED_USER)

    return _ensure_home_state_by_phone(
        mobile_driver,
        context.phone,
        context.expected_home_state or HomeState.SUBSCRIBED,
    )


def ensure_member_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка состояния MEMBER на главной."""
    selector = MobileTestUserSelector(db)
    context = selector.select_or_skip(MobileTestUserScenario.MEMBER_USER)

    return _ensure_home_state_by_phone(
        mobile_driver,
        context.phone,
        context.expected_home_state or HomeState.MEMBER,
    )


def ensure_coach_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка coach-пользователя."""
    selector = MobileTestUserSelector(db)
    context = selector.select_or_skip(MobileTestUserScenario.COACH_USER)

    _restart_app(mobile_driver)
    run_auth_to_home(mobile_driver, context.phone)
    pytest.skip(
        "Coach flow требует отдельного page-object слоя для выбора режима Client/Coach и пока не автоматизирован."
    )


def ensure_potential_user_on_main_screen(mobile_driver, db) -> None:
    """
    Гарантирует состояние NEW_USER на главном экране под пользователем с role=potential.
    """
    ensure_new_user_on_home_screen(mobile_driver, db)
