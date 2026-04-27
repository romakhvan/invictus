"""
Утилиты подготовки авторизованного состояния для mobile-тестов.
"""

import os
import time
from contextlib import contextmanager
from enum import Enum

import pytest

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.profile.profile_page import ProfilePage
from src.pages.mobile.shell.bottom_nav import BottomNav
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
    TestUserContext,
)
from tests.mobile.helpers.onboarding_helpers import run_auth_to_home
from tests.mobile.helpers.profile_helpers import assert_profile_matches_potential_user
from tests.mobile.helpers.screen_detection import (
    MobileScreen,
    detect_current_screen,
    home_state_for_screen,
    is_authorized_shell_visible,
)


class StartupAppState(Enum):
    AUTHORIZED_SHELL = "authorized_shell"
    PREVIEW = "preview"
    PHONE_AUTH = "phone_auth"
    SMS_CODE = "sms_code"
    HOME = "home"
    UNKNOWN = "unknown"


def _mobile_ui_logs_enabled() -> bool:
    return os.getenv("MOBILE_UI_LOGS") == "1"


@contextmanager
def _mobile_ui_timing(step_name: str):
    if not _mobile_ui_logs_enabled():
        yield
        return

    start = time.perf_counter()
    print(f"[mobile-ui] START {step_name}", flush=True)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[mobile-ui] DONE {step_name}: {elapsed:.2f}s", flush=True)


def _phone_suffix(phone_value: str | None) -> str:
    digits = "".join(c for c in str(phone_value or "") if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else digits


def _profile_phone_matches_context(profile: ProfilePage, context: TestUserContext) -> bool:
    profile_phone = _phone_suffix(profile.get_displayed_phone())
    expected_phone = _phone_suffix(context.phone)
    return bool(profile_phone and expected_phone and profile_phone == expected_phone)


def _detect_startup_app_state(mobile_driver) -> StartupAppState:
    """Detect the current high-level app state used by session preparation."""
    with _mobile_ui_timing("detect startup app state"):
        with _mobile_ui_timing("detect authorized shell"):
            if is_authorized_shell_visible(mobile_driver):
                return StartupAppState.AUTHORIZED_SHELL

        screen = detect_current_screen(mobile_driver)
        if screen == MobileScreen.PREVIEW:
            return StartupAppState.PREVIEW
        if screen == MobileScreen.PHONE_AUTH:
            return StartupAppState.PHONE_AUTH
        if screen == MobileScreen.SMS_CODE:
            return StartupAppState.SMS_CODE
        if home_state_for_screen(screen) is not None:
            return StartupAppState.HOME
        return StartupAppState.UNKNOWN


def _wait_for_startup_app_state(
    mobile_driver,
    *,
    timeout: float = 4.0,
    poll_interval: float = 0.5,
) -> StartupAppState:
    """Wait briefly after app activation until a known app state is visible."""
    with _mobile_ui_timing("wait app state after restart"):
        deadline = time.monotonic() + timeout
        while True:
            state = _detect_startup_app_state(mobile_driver)
            if state != StartupAppState.UNKNOWN:
                if _mobile_ui_logs_enabled():
                    print(f"[mobile-ui] detected app state: {state.value}", flush=True)
                return state
            if time.monotonic() >= deadline:
                return StartupAppState.UNKNOWN
            time.sleep(poll_interval)


def _reset_sms_auth_state(mobile_driver) -> None:
    """Leave SMS-code entry before starting auth for the selected phone."""
    with _mobile_ui_timing("reset sms auth state"):
        mobile_driver.back()


def _logout_current_user(profile: ProfilePage) -> None:
    """Logout through the Profile UI."""
    with _mobile_ui_timing("logout current user"):
        profile.logout()


def _log_unknown_startup_state_diagnostics(mobile_driver) -> None:
    """Print compact diagnostics before falling back from an unknown startup state."""
    with _mobile_ui_timing("diagnose unknown startup state"):
        try:
            print(
                "⚠️ Не удалось распознать состояние приложения после restart: "
                f"package={getattr(mobile_driver, 'current_package', 'unknown')}, "
                f"activity={getattr(mobile_driver, 'current_activity', 'unknown')}",
                flush=True,
            )
        except Exception as exc:
            print(f"⚠️ Не удалось собрать диагностику startup state: {exc}", flush=True)


def _restart_app_when_tabbar_missing(mobile_driver) -> bool:
    """
    Return whether the authorized tabbar is visible after one startup guard pass.

    If the first check cannot see the shell, restart the app once and re-check.
    Callers decide whether to reuse the visible shell or continue auth fallback.
    """
    with _mobile_ui_timing("detect authorized shell"):
        authorized_shell_visible = is_authorized_shell_visible(mobile_driver)

    if authorized_shell_visible:
        return True

    print("ℹ️ Авторизованный tabbar не найден в начале подготовки, перезапускаем приложение")
    _restart_app(mobile_driver)

    with _mobile_ui_timing("detect authorized shell after restart"):
        return is_authorized_shell_visible(mobile_driver)


def _clear_app_data_for_auth(mobile_driver) -> None:
    """Clear persisted Android app data so auth starts without the old session."""
    with _mobile_ui_timing("clear app data before auth"):
        try:
            mobile_driver.terminate_app(MOBILE_APP_PACKAGE)
            mobile_driver.execute_script(
                "mobile: clearApp",
                {"appId": MOBILE_APP_PACKAGE},
            )
            mobile_driver.activate_app(MOBILE_APP_PACKAGE)
            _wait_for_startup_app_state(mobile_driver, timeout=10.0)
        except Exception as exc:
            raise AssertionError(
                "Не удалось очистить данные приложения перед авторизацией. "
                "Переключение пользователя с --mobile-no-reset нельзя гарантировать, "
                "пока старая сессия остаётся активной."
            ) from exc


def ensure_test_user_session(mobile_driver, db, context: TestUserContext) -> BottomNav:
    """
    Ensure the app is authorized as the selected test user and return shell navigation.

    Entrypoint tests use this guard to validate session ownership without making
    Home screen recognition part of the scenario under test.
    """
    with _mobile_ui_timing("ensure_test_user_session"):
        startup_state = _detect_startup_app_state(mobile_driver)

        if startup_state == StartupAppState.UNKNOWN:
            print("ℹ️ Известное состояние приложения не найдено, перезапускаем приложение")
            _restart_app(mobile_driver)
            startup_state = _wait_for_startup_app_state(mobile_driver, timeout=10.0)

        if startup_state in {StartupAppState.PREVIEW, StartupAppState.PHONE_AUTH}:
            print(f"ℹ️ Открыт auth screen ({startup_state.value}), авторизуемся под {context.phone}")
        elif startup_state == StartupAppState.SMS_CODE:
            print("ℹ️ Открыт SMS-код для неизвестного номера, сбрасываем auth-flow")
            try:
                _reset_sms_auth_state(mobile_driver)
            except Exception as exc:
                print(f"⚠️ Не удалось сбросить SMS auth state, используем clearApp fallback: {exc}")
                _clear_app_data_for_auth(mobile_driver)
        elif startup_state in {StartupAppState.AUTHORIZED_SHELL, StartupAppState.HOME}:
            try:
                with _mobile_ui_timing("open profile for session check"):
                    profile = BottomNav(mobile_driver).open_profile()
                with _mobile_ui_timing("compare profile phone with selected user"):
                    if _profile_phone_matches_context(profile, context):
                        print(f"ℹ️ Уже открыт подходящий тестовый пользователь: {context.phone}")
                        return profile.nav

                actual_phone = profile.get_displayed_phone()
                print(
                    "ℹ️ Открыт другой пользователь "
                    f"({actual_phone or 'телефон не найден'}), выходим и авторизуемся под {context.phone}"
                )
                try:
                    _logout_current_user(profile)
                except Exception as exc:
                    print(f"⚠️ Logout через UI не сработал, используем clearApp fallback: {exc}")
                    with _mobile_ui_timing("clear app data after logout fallback"):
                        _clear_app_data_for_auth(mobile_driver)
            except Exception as exc:
                print(f"⚠️ Не удалось проверить текущий профиль, авторизуемся заново: {exc}")
                _clear_app_data_for_auth(mobile_driver)
        else:
            _log_unknown_startup_state_diagnostics(mobile_driver)
            _clear_app_data_for_auth(mobile_driver)

        with _mobile_ui_timing("run auth from ensure_test_user_session"):
            run_auth_to_home(
                mobile_driver,
                context.phone,
                expected_state=context.expected_home_state,
            )
        return BottomNav(mobile_driver)


def _try_reuse_existing_potential_home(
    mobile_driver,
    db,
    context: TestUserContext,
) -> HomePage | None:
    """Пытается переиспользовать уже открытую сессию, если профиль совпадает с выбранным context."""
    with _mobile_ui_timing("try reuse existing potential home"):
        profile = None
        try:
            try:
                from src.pages.mobile.shell.bottom_nav import BottomNav

                with _mobile_ui_timing("open profile from existing shell"):
                    profile = BottomNav(mobile_driver).open_profile()
            except Exception:
                with _mobile_ui_timing("wait existing profile page"):
                    profile = ProfilePage(mobile_driver).wait_loaded()
            with _mobile_ui_timing("assert profile matches selected user"):
                assert_profile_matches_potential_user(db, profile, context=context)
            with _mobile_ui_timing("return from profile to main"):
                home = profile.nav.open_main()
            with _mobile_ui_timing("detect existing home state"):
                if home.get_current_home_state() == (context.expected_home_state or HomeState.NEW_USER):
                    return home
        except Exception as exc:
            if _mobile_ui_logs_enabled():
                print(f"[mobile-ui] reuse existing potential home failed: {exc}", flush=True)
            # Если профиль был открыт — выходим из текущего пользователя,
            # чтобы перезапуск приложения не восстановил чужую сессию
            if profile is not None:
                try:
                    with _mobile_ui_timing("logout wrong user before re-auth"):
                        profile.logout()
                except Exception as logout_exc:
                    if _mobile_ui_logs_enabled():
                        print(
                            f"[mobile-ui] logout failed, clearing app data: {logout_exc}",
                            flush=True,
                        )
                    _clear_app_data_for_auth(mobile_driver)
            return None


def _restart_app(mobile_driver) -> None:
    """Перезапускает приложение, чтобы начать flow с предсказуемого состояния."""
    with _mobile_ui_timing("restart app"):
        try:
            with _mobile_ui_timing("terminate app"):
                mobile_driver.terminate_app(MOBILE_APP_PACKAGE)
            time.sleep(1)
            with _mobile_ui_timing("activate app"):
                mobile_driver.activate_app(MOBILE_APP_PACKAGE)
            time.sleep(2)
        except Exception as exc:
            if _mobile_ui_logs_enabled():
                print(f"[mobile-ui] restart app failed: {exc}", flush=True)


def _ensure_home_state_by_phone(
    mobile_driver,
    phone: str,
    expected_state: HomeState,
) -> HomePage:
    """Авторизует пользователя по номеру и приводит приложение к ожидаемому HomeState."""
    with _mobile_ui_timing("ensure home state by phone"):
        _restart_app(mobile_driver)
        with _mobile_ui_timing("run auth to home"):
            home = run_auth_to_home(mobile_driver, phone, expected_state=expected_state)
        with _mobile_ui_timing("detect home state after auth"):
            current_state = home.get_current_home_state()
        if current_state != expected_state:
            pytest.skip(
                f"После авторизации получено состояние {current_state.value}, "
                f"хотя ожидалось {expected_state.value}."
            )
        return home


def ensure_new_user_on_home_screen(
    mobile_driver,
    db,
    *,
    context: TestUserContext | None = None,
) -> HomePage:
    """Гарантирует состояние NEW_USER на главной."""
    with _mobile_ui_timing("ensure_new_user_on_home_screen"):
        if context is None:
            selector = MobileTestUserSelector(db)
            with _mobile_ui_timing("select POTENTIAL_USER"):
                context = selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)

        _restart_app_when_tabbar_missing(mobile_driver)

        existing_home = _try_reuse_existing_potential_home(mobile_driver, db, context)
        if existing_home:
            return existing_home

        with _mobile_ui_timing("auth to expected home state"):
            home = _ensure_home_state_by_phone(
                mobile_driver,
                context.phone,
                context.expected_home_state or HomeState.NEW_USER,
            )
        with _mobile_ui_timing("open profile after auth"):
            profile = home.nav.open_profile()
        with _mobile_ui_timing("assert profile after auth"):
            assert_profile_matches_potential_user(db, profile, context=context)
        with _mobile_ui_timing("return main after profile assert"):
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


def ensure_rabbit_hole_user_on_home_screen(mobile_driver, db) -> HomePage:
    """Best-effort подготовка состояния RABBIT_HOLE на главной."""
    selector = MobileTestUserSelector(db)
    context = selector.select_or_skip(MobileTestUserScenario.RABBIT_HOLE_USER)

    return _ensure_home_state_by_phone(
        mobile_driver,
        context.phone,
        context.expected_home_state or HomeState.RABBIT_HOLE,
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


def ensure_potential_user_on_main_screen(
    mobile_driver,
    db,
    *,
    context: TestUserContext | None = None,
) -> None:
    """
    Гарантирует состояние NEW_USER на главном экране под пользователем с role=potential.
    """
    ensure_new_user_on_home_screen(mobile_driver, db, context=context)
