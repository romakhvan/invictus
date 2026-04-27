import pytest
import uuid
from pathlib import Path

import src.repositories.mobile_test_users_repository as mobile_test_users_repository
from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_cache import MobileTestUsersCache
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)


def _cache_path() -> Path:
    workspace = Path("tests/.tmp/mobile-test-users-selector")
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace / f"{uuid.uuid4().hex}.json"


def _selector(db=object()) -> MobileTestUserSelector:
    return MobileTestUserSelector(db=db, cache=MobileTestUsersCache(_cache_path()))


def test_select_onboarding_new_user_uses_override_phone():
    selector = _selector()

    context = selector.select(
        scenario=MobileTestUserScenario.ONBOARDING_NEW_USER,
        override_phone="77781000001",
    )

    assert context.scenario == MobileTestUserScenario.ONBOARDING_NEW_USER
    assert context.phone == "77781000001"
    assert context.is_new_user is True
    assert context.country_code == "+7"
    assert context.selection_source == "override"
    assert context.expected_home_state is None


def test_select_onboarding_new_user_requests_free_phone(monkeypatch):
    selector = _selector()

    def fake_get_available_test_phone(db, base_phone, max_attempts):
        assert base_phone == selector.DEFAULT_ONBOARDING_BASE_PHONE
        assert max_attempts == selector.DEFAULT_MAX_PHONE_ATTEMPTS
        return "77781000002"

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_available_test_phone",
        fake_get_available_test_phone,
    )

    context = selector.select(
        scenario=MobileTestUserScenario.ONBOARDING_NEW_USER,
    )

    assert context.phone == "77781000002"
    assert context.is_new_user is True
    assert context.selection_source == "generated_free_phone"


def test_select_potential_user_returns_expected_home_state(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db, **kwargs: "7001234567",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-123",
    )

    context = selector.select(MobileTestUserScenario.POTENTIAL_USER)

    assert context.phone == "7001234567"
    assert context.user_id == "user-123"
    assert context.expected_home_state == HomeState.NEW_USER
    assert context.is_new_user is False
    assert context.role == "potential"
    assert context.selection_source == "db_lookup"
    assert "POTENTIAL_USER" in context.description


def test_select_subscribed_user_returns_expected_home_state(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_active_subscription_user",
        lambda db, **kwargs: "7001234568",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-456",
    )

    context = selector.select(MobileTestUserScenario.SUBSCRIBED_USER)

    assert context.phone == "7001234568"
    assert context.user_id == "user-456"
    assert context.expected_home_state == HomeState.SUBSCRIBED


def test_select_member_user_returns_expected_home_state(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_active_service_product_user",
        lambda db, **kwargs: "7001234569",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-789",
    )

    context = selector.select(MobileTestUserScenario.MEMBER_USER)

    assert context.phone == "7001234569"
    assert context.user_id == "user-789"
    assert context.expected_home_state == HomeState.MEMBER


def test_select_rabbit_hole_user_returns_expected_home_state(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_active_rabbit_hole_user",
        lambda db, **kwargs: "7001234570",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-rabbit",
    )

    context = selector.select(MobileTestUserScenario.RABBIT_HOLE_USER)

    assert context.phone == "7001234570"
    assert context.user_id == "user-rabbit"
    assert context.expected_home_state == HomeState.RABBIT_HOLE
    assert context.is_new_user is False
    assert context.selection_source == "db_lookup"
    assert "RABBIT_HOLE_USER" in context.description


def test_select_existing_candidate_raises_when_user_id_not_found(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db, **kwargs: "7001234567",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: None,
    )

    with pytest.raises(ValueError, match="user_id"):
        selector.select(MobileTestUserScenario.POTENTIAL_USER)


def test_select_kyrgyzstan_onboarding_requires_override_phone():
    selector = _selector()

    with pytest.raises(ValueError, match="KYRGYZSTAN_ONBOARDING_NEW_USER"):
        selector.select(MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER)


def test_select_raises_meaningful_error_when_candidate_not_found(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db, **kwargs: None,
    )

    with pytest.raises(ValueError, match="POTENTIAL_USER"):
        selector.select(MobileTestUserScenario.POTENTIAL_USER)


def test_select_or_skip_returns_context_when_selection_succeeds(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db, **kwargs: "7001234567",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-123",
    )

    context = selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)

    assert context.phone == "7001234567"
    assert context.user_id == "user-123"


def test_select_or_skip_logs_timing_when_mobile_ui_logs_enabled(monkeypatch, capsys):
    selector = _selector()

    monkeypatch.setenv("MOBILE_UI_LOGS", "1")
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db, **kwargs: "7001234567",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-123",
    )

    selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)

    output = capsys.readouterr().out
    assert "[mobile-ui] START select_or_skip POTENTIAL_USER" in output
    assert "[mobile-ui] DONE select_or_skip POTENTIAL_USER" in output


def test_select_uses_valid_cached_user_without_expensive_lookup(monkeypatch):
    cache = MobileTestUsersCache(_cache_path())
    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7001234567",
        user_id="user-123",
        expected_home_state="new_user",
        role="potential",
    )
    selector = MobileTestUserSelector(db=object(), cache=cache)

    monkeypatch.setattr(
        mobile_test_users_repository,
        "get_phone_for_potential_user",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("expensive lookup used")),
    )
    monkeypatch.setattr(
        mobile_test_users_repository,
        "validate_cached_test_user",
        lambda db, scenario, entry: (True, None),
    )

    context = selector.select(MobileTestUserScenario.POTENTIAL_USER)

    assert context.phone == "7001234567"
    assert context.user_id == "user-123"
    assert context.selection_source == "cache"


def test_select_marks_invalid_cached_user_and_appends_new_candidate(monkeypatch):
    cache = MobileTestUsersCache(_cache_path())
    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7000000001",
        user_id="old-user",
        expected_home_state="new_user",
        role="potential",
    )
    selector = MobileTestUserSelector(db=object(), cache=cache)
    lookup_calls = []

    monkeypatch.setattr(
        mobile_test_users_repository,
        "validate_cached_test_user",
        lambda db, scenario, entry: (False, "has related visits"),
    )

    def fake_lookup(db, excluded_user_ids=None):
        lookup_calls.append(tuple(excluded_user_ids or ()))
        return "7000000002"

    monkeypatch.setattr(
        mobile_test_users_repository,
        "get_phone_for_potential_user",
        fake_lookup,
    )
    monkeypatch.setattr(
        mobile_test_users_repository,
        "get_user_id_by_phone",
        lambda db, phone: "new-user",
    )

    context = selector.select(MobileTestUserScenario.POTENTIAL_USER)

    users = cache.get_category_users("POTENTIAL_USER")
    assert context.user_id == "new-user"
    assert lookup_calls == [("old-user",)]
    assert [user["user_id"] for user in users] == ["old-user", "new-user"]
    assert [user["status"] for user in users] == ["invalid", "valid"]
    assert users[0]["invalid_reason"] == "has related visits"


def test_select_keeps_cache_categories_separate(monkeypatch):
    cache = MobileTestUsersCache(_cache_path())
    cache.append_valid_user(
        "SUBSCRIBED_USER",
        phone="7001111111",
        user_id="sub-user",
        expected_home_state="subscribed",
        role=None,
    )
    selector = MobileTestUserSelector(db=object(), cache=cache)

    monkeypatch.setattr(
        mobile_test_users_repository,
        "validate_cached_test_user",
        lambda db, scenario, entry: (True, None),
    )

    context = selector.select(MobileTestUserScenario.SUBSCRIBED_USER)

    assert context.user_id == "sub-user"
    assert cache.get_category_users("POTENTIAL_USER") == []


def test_select_or_skip_skips_when_selection_fails(monkeypatch):
    selector = _selector()

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db, **kwargs: None,
    )

    class SkipCalled(Exception):
        pass

    monkeypatch.setattr(
        mobile_test_users_repository.pytest,
        "skip",
        lambda message: (_ for _ in ()).throw(SkipCalled(message)),
    )

    with pytest.raises(SkipCalled, match="POTENTIAL_USER"):
        selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)
