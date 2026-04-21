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
