from types import SimpleNamespace

import pytest

from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    TestUserContext as MobileUserContext,
)
from tests.mobile.helpers import profile_helpers


def test_assert_profile_matches_potential_user_prefers_context_user_id(monkeypatch):
    profile_page = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 123 45 67",
        assert_profile_data_matches_db=lambda first_name, phone_display: (
            first_name,
            phone_display,
        ),
    )
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        user_id="user-123",
    )

    monkeypatch.setattr(
        profile_helpers,
        "get_user_display_info_by_user_id",
        lambda db, user_id: {
            "firstName": "Ainur",
            "fullName": "Ainur Test",
            "role": "potential",
            "phone_display": "+7 700 123 45 67",
        },
    )
    calls = []
    profile_page.assert_profile_data_matches_db = lambda first_name, phone_display: calls.append(
        (first_name, phone_display)
    )

    profile_helpers.assert_profile_matches_potential_user(object(), profile_page, context=context)

    assert calls == [("Ainur", "+7 700 123 45 67")]


def test_assert_profile_matches_test_user_uses_context_user_id(monkeypatch):
    profile_page = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 765 43 21",
    )
    context = MobileUserContext(
        scenario=MobileTestUserScenario.RABBIT_HOLE_USER,
        phone="7007654321",
        user_id="rabbit-hole-user",
    )

    monkeypatch.setattr(
        profile_helpers,
        "get_user_display_info_by_user_id",
        lambda db, user_id: {
            "firstName": "Rabbit",
            "fullName": "Rabbit Hole",
            "role": "client",
            "phone_display": "+7 700 765 43 21",
        },
    )
    calls = []
    profile_page.assert_profile_data_matches_db = lambda first_name, phone_display: calls.append(
        (first_name, phone_display)
    )

    profile_helpers.assert_profile_matches_test_user(object(), profile_page, context=context)

    assert calls == [("Rabbit", "+7 700 765 43 21")]


def test_assert_profile_matches_potential_user_requires_context_with_user_id(monkeypatch):
    profile_page = SimpleNamespace(
        get_displayed_phone=lambda: "+7 700 123 45 67",
    )

    with pytest.raises(ValueError, match="context"):
        profile_helpers.assert_profile_matches_potential_user(object(), profile_page)
