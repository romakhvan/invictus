from types import SimpleNamespace
from datetime import datetime

import pytest

from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    TestUserContext as MobileUserContext,
)
from tests.mobile.flows.rabbit_hole import new_client_buy_rh


def test_resolve_user_id_prefers_context_value(monkeypatch):
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        user_id="user-123",
    )

    assert new_client_buy_rh._resolve_user_id(context, object()) == "user-123"


def test_resolve_user_id_requires_context_user_id(monkeypatch):
    context = MobileUserContext(
        scenario=MobileTestUserScenario.POTENTIAL_USER,
        phone="7001234567",
        user_id=None,
    )

    with pytest.raises(ValueError, match="user_id"):
        new_client_buy_rh._resolve_user_id(context, object())


def test_payment_transaction_since_uses_utc_clock():
    now_utc = datetime(2026, 4, 21, 10, 26, 46)

    assert new_client_buy_rh._payment_transaction_since(now_utc=now_utc) == datetime(
        2026, 4, 21, 10, 26, 41
    )


def test_assert_rabbit_hole_success_page_checks_expected_reward(monkeypatch):
    calls = []

    class FakeSuccessPage:
        def __init__(self, driver):
            calls.append(("init", driver))

        def wait_loaded(self):
            calls.append(("wait_loaded", None))
            return self

        def assert_reward_text_visible(self, reward_text):
            calls.append(("assert_reward", reward_text))

        def click_go_to_main(self):
            calls.append(("click_go_to_main", None))

    class FakeHomePage:
        def __init__(self, driver):
            calls.append(("home_init", driver))

        def wait_loaded(self):
            calls.append(("home_wait_loaded", None))
            return self

        def get_current_home_state(self):
            calls.append(("get_current_home_state", None))
            return new_client_buy_rh.HomeState.RABBIT_HOLE

    monkeypatch.setattr(new_client_buy_rh, "SuccessPage", FakeSuccessPage, raising=False)
    monkeypatch.setattr(new_client_buy_rh, "HomePage", FakeHomePage, raising=False)

    new_client_buy_rh._assert_rabbit_hole_success_page(driver="driver")

    assert calls == [
        ("init", "driver"),
        ("wait_loaded", None),
        ("assert_reward", "3 посещения в Invictus GO"),
        ("click_go_to_main", None),
        ("home_init", "driver"),
        ("home_wait_loaded", None),
        ("get_current_home_state", None),
    ]


def test_assert_rabbit_hole_success_page_requires_rabbit_hole_home(monkeypatch):
    class FakeSuccessPage:
        def __init__(self, driver):
            pass

        def wait_loaded(self):
            return self

        def assert_reward_text_visible(self, reward_text):
            pass

        def click_go_to_main(self):
            pass

    class FakeHomePage:
        def __init__(self, driver):
            pass

        def wait_loaded(self):
            return self

        def get_current_home_state(self):
            return new_client_buy_rh.HomeState.NEW_USER

    monkeypatch.setattr(new_client_buy_rh, "SuccessPage", FakeSuccessPage, raising=False)
    monkeypatch.setattr(new_client_buy_rh, "HomePage", FakeHomePage, raising=False)

    with pytest.raises(AssertionError, match="RABBIT_HOLE"):
        new_client_buy_rh._assert_rabbit_hole_success_page(driver="driver")


def test_rabbit_hole_flow_uses_selector_for_potential_user(monkeypatch):
    selected = []
    auth_calls = []

    class StopFlow(Exception):
        pass

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.POTENTIAL_USER,
                phone="7001234567",
                user_id="user-123",
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    fake_driver = SimpleNamespace(current_package=new_client_buy_rh.MOBILE_APP_PACKAGE)

    monkeypatch.setattr(new_client_buy_rh, "MobileTestUserSelector", FakeSelector, raising=False)
    monkeypatch.setattr(
        new_client_buy_rh,
        "authorize_user",
        lambda driver, wait, phone, expected_state=None: auth_calls.append((driver, phone, expected_state))
        or (_ for _ in ()).throw(StopFlow()),
    )

    try:
        new_client_buy_rh.test_new_client_buys_rabbit_hole(
            mobile_driver=fake_driver,
            db=object(),
        )
    except StopFlow:
        pass
    else:
        raise AssertionError("Expected flow to stop immediately after authorize_user.")

    assert selected == [(MobileTestUserScenario.POTENTIAL_USER, None)]
    assert auth_calls == [(fake_driver, "7001234567", new_client_buy_rh.HomeState.NEW_USER)]


def test_assert_rabbit_visits_created_requires_three_visits(monkeypatch):
    visits = [{"_id": "visit-1"}, {"_id": "visit-2"}, {"_id": "visit-3"}]
    calls = []

    monkeypatch.setattr(
        new_client_buy_rh,
        "get_recent_rabbit_visits_by_user",
        lambda db, *, user_id, since, limit: calls.append((db, user_id, since, limit)) or visits,
    )

    result = new_client_buy_rh._assert_rabbit_visits_created(
        db="db",
        user_id="user-123",
        since=datetime(2026, 4, 21, 10, 26, 36),
    )

    assert result == visits
    assert calls == [("db", "user-123", datetime(2026, 4, 21, 10, 26, 36), 3)]


def test_assert_rabbitholev2_subscription_created_requires_record(monkeypatch):
    records = [
        {
            "rabbithole_id": "rh-1",
            "subscriptions": [],
        }
    ]
    calls = []

    monkeypatch.setattr(
        new_client_buy_rh,
        "get_rabbitholev2_subscriptions_by_user",
        lambda db, user_id, days: calls.append((db, user_id, days)) or records,
    )

    result = new_client_buy_rh._assert_rabbitholev2_subscription_created(
        db="db",
        user_id="user-123",
    )

    assert result == records
    assert calls == [("db", "user-123", 1)]


def test_assert_rabbitholev2_subscription_created_fails_without_record(monkeypatch):
    monkeypatch.setattr(
        new_client_buy_rh,
        "get_rabbitholev2_subscriptions_by_user",
        lambda db, user_id, days: [],
    )

    with pytest.raises(AssertionError, match="rabbitholev2"):
        new_client_buy_rh._assert_rabbitholev2_subscription_created(
            db="db",
            user_id="user-123",
        )


def test_wait_recent_transaction_by_user_polls_until_transaction_appears(monkeypatch):
    calls = []
    responses = [
        [],
        [{"_id": "transaction-1"}],
    ]

    monkeypatch.setattr(
        new_client_buy_rh,
        "get_recent_transaction_by_user",
        lambda db, *, user_id, since, expected_amount, limit: calls.append(
            (db, user_id, since, expected_amount, limit)
        )
        or responses.pop(0),
    )
    monkeypatch.setattr(new_client_buy_rh.time, "sleep", lambda seconds: None)

    result = new_client_buy_rh._wait_recent_transaction_by_user(
        db="db",
        user_id="user-123",
        since=datetime(2026, 4, 21, 10, 26, 36),
        expected_amount="2 990 ₸",
        timeout_seconds=2,
        poll_interval_seconds=1,
    )

    assert result == [{"_id": "transaction-1"}]
    assert len(calls) == 2


def test_assert_rabbit_visits_created_polls_until_three_visits(monkeypatch):
    calls = []
    responses = [
        [{"_id": "visit-1"}],
        [{"_id": "visit-1"}, {"_id": "visit-2"}, {"_id": "visit-3"}],
    ]

    monkeypatch.setattr(
        new_client_buy_rh,
        "get_recent_rabbit_visits_by_user",
        lambda db, *, user_id, since, limit: calls.append((db, user_id, since, limit))
        or responses.pop(0),
    )
    monkeypatch.setattr(new_client_buy_rh.time, "sleep", lambda seconds: None)

    result = new_client_buy_rh._assert_rabbit_visits_created(
        db="db",
        user_id="user-123",
        since=datetime(2026, 4, 21, 10, 26, 36),
        timeout_seconds=2,
        poll_interval_seconds=1,
    )

    assert result == [{"_id": "visit-1"}, {"_id": "visit-2"}, {"_id": "visit-3"}]
    assert len(calls) == 2


def test_assert_rabbit_visits_created_fails_when_less_than_three(monkeypatch):
    monkeypatch.setattr(
        new_client_buy_rh,
        "get_recent_rabbit_visits_by_user",
        lambda db, *, user_id, since, limit: [{"_id": "visit-1"}],
    )

    with pytest.raises(AssertionError, match="Ожидалось 3 купленных visit"):
        new_client_buy_rh._assert_rabbit_visits_created(
            db="db",
            user_id="user-123",
            since=datetime(2026, 4, 21, 10, 26, 36),
            timeout_seconds=0,
        )
