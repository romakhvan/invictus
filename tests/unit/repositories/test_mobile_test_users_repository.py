import pytest

import src.repositories.mobile_test_users_repository as mobile_test_users_repository
from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)


def test_select_onboarding_new_user_uses_override_phone():
    selector = MobileTestUserSelector(db=object())

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
    selector = MobileTestUserSelector(db=object())

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
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db: "7001234567",
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
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_active_subscription_user",
        lambda db: "7001234568",
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
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_active_service_product_user",
        lambda db: "7001234569",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-789",
    )

    context = selector.select(MobileTestUserScenario.MEMBER_USER)

    assert context.phone == "7001234569"
    assert context.user_id == "user-789"
    assert context.expected_home_state == HomeState.MEMBER


def test_select_existing_candidate_raises_when_user_id_not_found(monkeypatch):
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db: "7001234567",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: None,
    )

    with pytest.raises(ValueError, match="user_id"):
        selector.select(MobileTestUserScenario.POTENTIAL_USER)


def test_select_kyrgyzstan_onboarding_requires_override_phone():
    selector = MobileTestUserSelector(db=object())

    with pytest.raises(ValueError, match="KYRGYZSTAN_ONBOARDING_NEW_USER"):
        selector.select(MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER)


def test_select_raises_meaningful_error_when_candidate_not_found(monkeypatch):
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db: None,
    )

    with pytest.raises(ValueError, match="POTENTIAL_USER"):
        selector.select(MobileTestUserScenario.POTENTIAL_USER)


def test_select_or_skip_returns_context_when_selection_succeeds(monkeypatch):
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db: "7001234567",
    )
    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_user_id_by_phone",
        lambda db, phone: "user-123",
    )

    context = selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)

    assert context.phone == "7001234567"
    assert context.user_id == "user-123"


def test_select_or_skip_skips_when_selection_fails(monkeypatch):
    selector = MobileTestUserSelector(db=object())

    monkeypatch.setattr(
        "src.repositories.mobile_test_users_repository.get_phone_for_potential_user",
        lambda db: None,
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
