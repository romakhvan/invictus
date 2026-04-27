from types import SimpleNamespace

from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    TestUserContext as MobileUserContext,
)
from tests.mobile.helpers import session_helpers


def test_ensure_new_user_on_home_screen_uses_selector(monkeypatch):
    selected = []
    ensured = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.POTENTIAL_USER,
                phone="7001234567",
                expected_home_state=HomeState.NEW_USER,
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    fake_profile = SimpleNamespace(nav=SimpleNamespace(open_main=lambda: "main"))
    fake_home = SimpleNamespace(nav=SimpleNamespace(open_profile=lambda: fake_profile))

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_restart_app_when_tabbar_missing",
        lambda mobile_driver: True,
    )
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: ensured.append((phone, expected_state)) or fake_home,
    )
    monkeypatch.setattr(
        session_helpers,
        "assert_profile_matches_potential_user",
        lambda db, profile, context=None: None,
    )

    result = session_helpers.ensure_new_user_on_home_screen(object(), object())

    assert selected == [(MobileTestUserScenario.POTENTIAL_USER, None)]
    assert ensured == [("7001234567", HomeState.NEW_USER)]
    assert result == "main"


def test_ensure_new_user_on_home_screen_uses_provided_context(monkeypatch):
    selected = []
    ensured = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7007654321",
        expected_home_state=HomeState.NEW_USER,
    )
    fake_profile = SimpleNamespace(nav=SimpleNamespace(open_main=lambda: "main"))
    fake_home = SimpleNamespace(nav=SimpleNamespace(open_profile=lambda: fake_profile))

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select_or_skip(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            raise AssertionError("selector should not be used when context is provided")

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_restart_app_when_tabbar_missing",
        lambda mobile_driver: True,
    )
    monkeypatch.setattr(
        session_helpers,
        "_try_reuse_existing_potential_home",
        lambda mobile_driver, db, context: None,
    )
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: ensured.append((phone, expected_state)) or fake_home,
    )
    monkeypatch.setattr(
        session_helpers,
        "assert_profile_matches_potential_user",
        lambda db, profile, context=None: None,
    )

    result = session_helpers.ensure_new_user_on_home_screen(object(), object(), context=context)

    assert selected == []
    assert ensured == [("7007654321", HomeState.NEW_USER)]
    assert result == "main"


def test_ensure_new_user_on_home_screen_logs_timing_when_mobile_ui_logs_enabled(
    monkeypatch, capsys
):
    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select_or_skip(self, scenario, override_phone=None):
            return MobileUserContext(
                scenario=MobileTestUserScenario.POTENTIAL_USER,
                phone="7001234567",
                expected_home_state=HomeState.NEW_USER,
            )

    fake_profile = SimpleNamespace(nav=SimpleNamespace(open_main=lambda: "main"))
    fake_home = SimpleNamespace(nav=SimpleNamespace(open_profile=lambda: fake_profile))

    monkeypatch.setenv("MOBILE_UI_LOGS", "1")
    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_restart_app_when_tabbar_missing",
        lambda mobile_driver: True,
    )
    monkeypatch.setattr(
        session_helpers,
        "_try_reuse_existing_potential_home",
        lambda mobile_driver, db, context: None,
    )
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: fake_home,
    )
    monkeypatch.setattr(
        session_helpers,
        "assert_profile_matches_potential_user",
        lambda db, profile, context=None: None,
    )

    session_helpers.ensure_new_user_on_home_screen(object(), object())

    output = capsys.readouterr().out
    assert "[mobile-ui] START ensure_new_user_on_home_screen" in output
    assert "[mobile-ui] DONE ensure_new_user_on_home_screen" in output
    assert "[mobile-ui] START select POTENTIAL_USER" in output
    assert "[mobile-ui] START auth to expected home state" in output


def test_ensure_new_user_on_home_screen_keeps_timing_logs_off_by_default(
    monkeypatch, capsys
):
    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select_or_skip(self, scenario, override_phone=None):
            return MobileUserContext(
                scenario=MobileTestUserScenario.POTENTIAL_USER,
                phone="7001234567",
                expected_home_state=HomeState.NEW_USER,
            )

    fake_profile = SimpleNamespace(nav=SimpleNamespace(open_main=lambda: "main"))
    fake_home = SimpleNamespace(nav=SimpleNamespace(open_profile=lambda: fake_profile))

    monkeypatch.setenv("MOBILE_UI_LOGS", "0")
    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_restart_app_when_tabbar_missing",
        lambda mobile_driver: True,
    )
    monkeypatch.setattr(
        session_helpers,
        "_try_reuse_existing_potential_home",
        lambda mobile_driver, db, context: None,
    )
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: fake_home,
    )
    monkeypatch.setattr(
        session_helpers,
        "assert_profile_matches_potential_user",
        lambda db, profile, context=None: None,
    )

    session_helpers.ensure_new_user_on_home_screen(object(), object())

    assert "[mobile-ui]" not in capsys.readouterr().out


def test_ensure_new_user_on_home_screen_reuses_matching_profile_context(monkeypatch):
    selected = []
    assert_calls = []
    ensure_calls = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.POTENTIAL_USER,
                phone="7001234567",
                user_id="user-123",
                expected_home_state=HomeState.NEW_USER,
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    fake_home = SimpleNamespace(get_current_home_state=lambda: HomeState.NEW_USER)
    fake_profile = SimpleNamespace(nav=SimpleNamespace(open_main=lambda: fake_home))

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_restart_app_when_tabbar_missing",
        lambda mobile_driver: True,
    )
    monkeypatch.setattr(
        session_helpers,
        "ProfilePage",
        lambda driver: SimpleNamespace(wait_loaded=lambda: fake_profile),
    )
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda *args, **kwargs: ensure_calls.append((args, kwargs)),
    )
    monkeypatch.setattr(
        session_helpers,
        "assert_profile_matches_potential_user",
        lambda db, profile, context=None: assert_calls.append(context),
    )

    result = session_helpers.ensure_new_user_on_home_screen(object(), object())

    assert selected == [(MobileTestUserScenario.POTENTIAL_USER, None)]
    assert assert_calls and assert_calls[0].user_id == "user-123"
    assert ensure_calls == []
    assert result is fake_home


def test_ensure_new_user_on_home_screen_restarts_when_tabbar_missing(monkeypatch):
    checks = iter([False, True])
    restarts = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select_or_skip(self, scenario, override_phone=None):
            return MobileUserContext(
                scenario=MobileTestUserScenario.POTENTIAL_USER,
                phone="7001234567",
                expected_home_state=HomeState.NEW_USER,
            )

    fake_home = SimpleNamespace()

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "is_authorized_shell_visible",
        lambda driver: next(checks),
    )
    monkeypatch.setattr(
        session_helpers,
        "_restart_app",
        lambda mobile_driver: restarts.append(mobile_driver),
    )
    monkeypatch.setattr(
        session_helpers,
        "_try_reuse_existing_potential_home",
        lambda mobile_driver, db, context: fake_home,
    )
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("auth should not run")),
    )

    driver = object()
    result = session_helpers.ensure_new_user_on_home_screen(driver, object())

    assert restarts == [driver]
    assert result is fake_home


def test_ensure_subscribed_user_on_home_screen_uses_selector(monkeypatch):
    selected = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.SUBSCRIBED_USER,
                phone="7001234568",
                expected_home_state=HomeState.SUBSCRIBED,
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: (phone, expected_state),
    )

    result = session_helpers.ensure_subscribed_user_on_home_screen(object(), object())

    assert selected == [(MobileTestUserScenario.SUBSCRIBED_USER, None)]
    assert result == ("7001234568", HomeState.SUBSCRIBED)


def test_ensure_member_user_on_home_screen_uses_selector(monkeypatch):
    selected = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.MEMBER_USER,
                phone="7001234569",
                expected_home_state=HomeState.MEMBER,
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: (phone, expected_state),
    )

    result = session_helpers.ensure_member_user_on_home_screen(object(), object())

    assert selected == [(MobileTestUserScenario.MEMBER_USER, None)]
    assert result == ("7001234569", HomeState.MEMBER)


def test_ensure_rabbit_hole_user_on_home_screen_uses_selector(monkeypatch):
    selected = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.RABBIT_HOLE_USER,
                phone="7001234570",
                expected_home_state=HomeState.RABBIT_HOLE,
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_ensure_home_state_by_phone",
        lambda mobile_driver, phone, expected_state: (phone, expected_state),
    )

    result = session_helpers.ensure_rabbit_hole_user_on_home_screen(object(), object())

    assert selected == [(MobileTestUserScenario.RABBIT_HOLE_USER, None)]
    assert result == ("7001234570", HomeState.RABBIT_HOLE)


def test_ensure_coach_user_on_home_screen_uses_selector(monkeypatch):
    selected = []
    auth_calls = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.COACH_USER,
                phone="7010000000",
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    monkeypatch.setattr(session_helpers, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(session_helpers, "_restart_app", lambda mobile_driver: None)
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda mobile_driver, phone: auth_calls.append(phone),
    )

    try:
        session_helpers.ensure_coach_user_on_home_screen(object(), object())
    except BaseException as exc:  # pytest.skip.Exception inherits BaseException
        assert exc.__class__.__name__ == "Skipped"
    else:
        raise AssertionError("Expected coach flow to skip after auth attempt.")

    assert selected == [(MobileTestUserScenario.COACH_USER, None)]
    assert auth_calls == ["7010000000"]


def test_ensure_test_user_session_reuses_matching_tabbar_profile(monkeypatch):
    auth_calls = []
    returned_nav = object()
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    fake_profile = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 123 45 67",
        nav=returned_nav,
    )

    class FakeBottomNav:
        def __init__(self, driver):
            self.driver = driver

        def open_profile(self):
            return fake_profile

    monkeypatch.setattr(session_helpers, "is_authorized_shell_visible", lambda driver: True)
    monkeypatch.setattr(session_helpers, "BottomNav", FakeBottomNav, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda *args, **kwargs: auth_calls.append((args, kwargs)),
    )

    result = session_helpers.ensure_test_user_session(object(), object(), context)

    assert result is returned_nav
    assert auth_calls == []


def test_ensure_test_user_session_auths_immediately_from_preview(monkeypatch):
    calls = []
    restarts = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    returned_nav = object()

    monkeypatch.setattr(
        session_helpers,
        "_detect_startup_app_state",
        lambda driver: session_helpers.StartupAppState.PREVIEW,
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "_restart_app",
        lambda driver: restarts.append(driver),
    )
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda driver, phone, expected_state=None: calls.append(
            ("auth", phone, expected_state)
        ),
    )
    monkeypatch.setattr(session_helpers, "BottomNav", lambda driver: returned_nav, raising=False)

    result = session_helpers.ensure_test_user_session(object(), object(), context)

    assert restarts == []
    assert calls == [("auth", "7001234567", HomeState.NEW_USER)]
    assert result is returned_nav


def test_ensure_test_user_session_auths_immediately_from_phone_auth(monkeypatch):
    calls = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    returned_nav = object()

    monkeypatch.setattr(
        session_helpers,
        "_detect_startup_app_state",
        lambda driver: session_helpers.StartupAppState.PHONE_AUTH,
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda driver, phone, expected_state=None: calls.append(
            ("auth", phone, expected_state)
        ),
    )
    monkeypatch.setattr(session_helpers, "BottomNav", lambda driver: returned_nav, raising=False)

    result = session_helpers.ensure_test_user_session(object(), object(), context)

    assert calls == [("auth", "7001234567", HomeState.NEW_USER)]
    assert result is returned_nav


def test_ensure_test_user_session_resets_sms_code_before_auth(monkeypatch):
    calls = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    returned_nav = object()

    monkeypatch.setattr(
        session_helpers,
        "_detect_startup_app_state",
        lambda driver: session_helpers.StartupAppState.SMS_CODE,
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "_reset_sms_auth_state",
        lambda driver: calls.append("reset_sms"),
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda driver, phone, expected_state=None: calls.append(
            ("auth", phone, expected_state)
        ),
    )
    monkeypatch.setattr(session_helpers, "BottomNav", lambda driver: returned_nav, raising=False)

    result = session_helpers.ensure_test_user_session(object(), object(), context)

    assert calls == ["reset_sms", ("auth", "7001234567", HomeState.NEW_USER)]
    assert result is returned_nav


def test_ensure_test_user_session_logs_timing_when_mobile_ui_logs_enabled(
    monkeypatch, capsys
):
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    fake_profile = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 123 45 67",
        nav=object(),
    )

    class FakeBottomNav:
        def __init__(self, driver):
            self.driver = driver

        def open_profile(self):
            return fake_profile

    monkeypatch.setenv("MOBILE_UI_LOGS", "1")
    monkeypatch.setattr(session_helpers, "is_authorized_shell_visible", lambda driver: True)
    monkeypatch.setattr(session_helpers, "BottomNav", FakeBottomNav, raising=False)

    session_helpers.ensure_test_user_session(object(), object(), context)

    output = capsys.readouterr().out
    assert "[mobile-ui] START ensure_test_user_session" in output
    assert "[mobile-ui] START detect authorized shell" in output
    assert "[mobile-ui] START open profile for session check" in output


def test_ensure_test_user_session_logs_in_when_profile_phone_differs(monkeypatch):
    calls = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.RABBIT_HOLE_USER,
        phone="7001234570",
        expected_home_state=HomeState.RABBIT_HOLE,
    )
    fake_profile = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 999 99 99",
        nav=object(),
    )

    class FakeBottomNav:
        def __init__(self, driver):
            self.driver = driver

        def open_profile(self):
            return fake_profile

    returned_nav = object()

    monkeypatch.setattr(
        session_helpers,
        "_detect_startup_app_state",
        lambda driver: session_helpers.StartupAppState.AUTHORIZED_SHELL,
        raising=False,
    )
    monkeypatch.setattr(session_helpers, "BottomNav", FakeBottomNav, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_logout_current_user",
        lambda profile: calls.append("logout"),
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda driver, phone, expected_state=None: calls.append(
            ("auth", phone, expected_state)
        ),
    )
    monkeypatch.setattr(
        session_helpers,
        "BottomNav",
        lambda driver: SimpleNamespace(open_profile=lambda: fake_profile, nav=returned_nav),
        raising=False,
    )

    result = session_helpers.ensure_test_user_session(object(), object(), context)

    assert calls == ["logout", ("auth", "7001234570", HomeState.RABBIT_HOLE)]
    assert result.open_profile() is fake_profile


def test_ensure_test_user_session_clears_data_when_logout_fails(monkeypatch):
    calls = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.RABBIT_HOLE_USER,
        phone="7001234570",
        expected_home_state=HomeState.RABBIT_HOLE,
    )
    fake_profile = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 999 99 99",
        nav=object(),
    )
    class FakeBottomNav:
        def __init__(self, driver):
            self.driver = driver

        def open_profile(self):
            return fake_profile

    def fail_logout(profile):
        calls.append("logout")
        raise AssertionError("logout button not found")

    monkeypatch.setattr(
        session_helpers,
        "_detect_startup_app_state",
        lambda driver: session_helpers.StartupAppState.AUTHORIZED_SHELL,
        raising=False,
    )
    monkeypatch.setattr(session_helpers, "BottomNav", FakeBottomNav, raising=False)
    monkeypatch.setattr(session_helpers, "_logout_current_user", fail_logout, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_clear_app_data_for_auth",
        lambda driver: calls.append("clear"),
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda driver, phone, expected_state=None: calls.append(
            ("auth", phone, expected_state)
        ),
    )

    result = session_helpers.ensure_test_user_session(object(), object(), context)

    assert calls == ["logout", "clear", ("auth", "7001234570", HomeState.RABBIT_HOLE)]
    assert result.open_profile() is fake_profile


def test_ensure_test_user_session_restarts_then_reuses_matching_tabbar_profile(monkeypatch):
    states = iter(
        [
            session_helpers.StartupAppState.UNKNOWN,
            session_helpers.StartupAppState.AUTHORIZED_SHELL,
        ]
    )
    restarts = []
    auth_calls = []
    returned_nav = object()
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    fake_profile = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 123 45 67",
        nav=returned_nav,
    )

    class FakeBottomNav:
        def __init__(self, driver):
            self.driver = driver

        def open_profile(self):
            return fake_profile

    monkeypatch.setattr(session_helpers, "_detect_startup_app_state", lambda driver: next(states), raising=False)
    monkeypatch.setattr(
        session_helpers,
        "_restart_app",
        lambda mobile_driver: restarts.append(mobile_driver),
    )
    monkeypatch.setattr(
        session_helpers,
        "_wait_for_startup_app_state",
        lambda mobile_driver: next(states),
        raising=False,
    )
    monkeypatch.setattr(session_helpers, "BottomNav", FakeBottomNav, raising=False)
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda *args, **kwargs: auth_calls.append((args, kwargs)),
    )

    driver = object()
    result = session_helpers.ensure_test_user_session(driver, object(), context)

    assert restarts == [driver]
    assert result is returned_nav
    assert auth_calls == []


def test_ensure_test_user_session_logs_in_when_tabbar_is_not_visible(monkeypatch):
    calls = []
    restarts = []
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        expected_home_state=HomeState.NEW_USER,
    )
    returned_nav = object()

    monkeypatch.setattr(
        session_helpers,
        "_detect_startup_app_state",
        lambda driver: session_helpers.StartupAppState.UNKNOWN,
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "_restart_app",
        lambda mobile_driver: restarts.append(mobile_driver),
    )
    monkeypatch.setattr(
        session_helpers,
        "_wait_for_startup_app_state",
        lambda mobile_driver: session_helpers.StartupAppState.UNKNOWN,
        raising=False,
    )
    monkeypatch.setattr(
        session_helpers,
        "run_auth_to_home",
        lambda driver, phone, expected_state=None: calls.append(
            ("auth", phone, expected_state)
        ),
    )
    monkeypatch.setattr(
        session_helpers,
        "_clear_app_data_for_auth",
        lambda driver: calls.append("clear"),
        raising=False,
    )
    monkeypatch.setattr(session_helpers, "BottomNav", lambda driver: returned_nav, raising=False)

    driver = object()
    result = session_helpers.ensure_test_user_session(driver, object(), context)

    assert restarts == [driver]
    assert calls == ["clear", ("auth", "7001234567", HomeState.NEW_USER)]
    assert result is returned_nav
