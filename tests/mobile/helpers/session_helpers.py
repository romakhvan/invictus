"""
Утилиты подготовки авторизованного состояния для mobile-тестов.
"""

import time
import pytest

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.profile.profile_page import ProfilePage
from src.repositories.users_repository import (
    get_phone_for_potential_user,
    get_user_role_by_phone,
)
from tests.mobile.helpers.onboarding_helpers import run_auth_to_main
from tests.mobile.helpers.profile_helpers import assert_profile_matches_potential_user


def _get_current_user_role_via_profile(driver, db):
    """
    Пытается открыть «Профиль» через таббар и вернуть роль текущего пользователя из БД.
    Если профиль недоступен, возвращает None.
    """
    try:
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        from src.pages.mobile.shell.bottom_nav import BottomNav

        wait_probe = WebDriverWait(driver, 6)
        nav = BottomNav(driver)
        wait_probe.until(EC.element_to_be_clickable(nav.TAB_PROFILE))
        nav.click(nav.TAB_PROFILE)
        profile = ProfilePage(driver).wait_loaded()
        phone_ui = profile.get_displayed_phone()
        if not phone_ui:
            return None
        return get_user_role_by_phone(db, phone_ui)
    except Exception:
        return None


def ensure_potential_user_on_main_screen(mobile_driver, db) -> None:
    """
    Гарантирует состояние NEW_USER на главном экране под пользователем с role=potential.
    """
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
    run_auth_to_main(mobile_driver, phone)

    home = HomePage(mobile_driver).wait_loaded()
    profile = home.nav.open_profile()
    print("Проверка: сверка данных в профиле с potential-пользователем в БД...")
    assert_profile_matches_potential_user(db, profile)
    profile.nav.open_main()
