from types import SimpleNamespace

from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    TestUserContext as MobileUserContext,
)
from tests.mobile.navigation import test_navigation_new_user


def test_navigation_new_user_passes_context_to_profile_assertion(monkeypatch):
    profile_assert_calls = []

    fake_profile = SimpleNamespace(nav=SimpleNamespace(open_main=lambda: SimpleNamespace(get_current_home_state=lambda: HomeState.NEW_USER)))
    fake_stats = SimpleNamespace(nav=SimpleNamespace(open_profile=lambda: fake_profile))
    fake_bookings = SimpleNamespace(
        nav=SimpleNamespace(
            open_qr=lambda: SimpleNamespace(
                assert_texts_present=lambda: None,
                close=lambda: fake_bookings,
            ),
            open_stats=lambda: fake_stats,
        )
    )
    fake_home = SimpleNamespace(
        get_current_home_state=lambda: HomeState.NEW_USER,
        nav=SimpleNamespace(open_bookings=lambda: fake_bookings),
    )
    fake_driver = object()
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        user_id="user-123",
    )

    monkeypatch.setattr(
        test_navigation_new_user,
        "HomePage",
        lambda driver: SimpleNamespace(wait_loaded=lambda: fake_home),
    )
    monkeypatch.setattr(
        test_navigation_new_user,
        "assert_profile_matches_potential_user",
        lambda db, profile, context=None: profile_assert_calls.append(context),
    )

    test_navigation_new_user.test_navigation_new_user_main_tabs(
        potential_user_on_main_screen=fake_driver,
        potential_user_context=context,
        db=object(),
    )

    assert profile_assert_calls == [context]
