from types import SimpleNamespace

from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    TestUserContext as MobileUserContext,
)
from tests.mobile.onboarding import test_client_onboarding_kyrgyzstan


def test_kyrgyzstan_onboarding_flow_uses_selector_for_phone_choice(monkeypatch):
    selected = []
    run_calls = []

    class FakeSelector:
        def __init__(self, db):
            self.db = db

        def select(self, scenario, override_phone=None):
            selected.append((scenario, override_phone))
            return MobileUserContext(
                scenario=MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER,
                phone="700000001",
                is_new_user=True,
                country_code="+996",
            )

        def select_or_skip(self, scenario, override_phone=None):
            return self.select(scenario, override_phone=override_phone)

    fake_home = SimpleNamespace(
        get_current_home_state=lambda: HomeState.NEW_USER,
        get_content=lambda: SimpleNamespace(assert_ui=lambda: None),
    )
    fake_driver = SimpleNamespace(current_package=test_client_onboarding_kyrgyzstan.MOBILE_APP_PACKAGE)

    monkeypatch.setattr(
        test_client_onboarding_kyrgyzstan,
        "MobileTestUserSelector",
        FakeSelector,
        raising=False,
    )
    monkeypatch.setattr(
        test_client_onboarding_kyrgyzstan,
        "run_full_onboarding_to_main",
        lambda driver, phone, country_name=None: run_calls.append((driver, phone, country_name)) or fake_home,
    )

    test_client_onboarding_kyrgyzstan.test_new_client_onboarding_kyrgyzstan_full_flow(
        mobile_driver=fake_driver,
        db=object(),
        onboarding_phone_kg="700000099",
    )

    assert selected == [(MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER, "700000099")]
    assert run_calls == [(fake_driver, "700000001", "Кыргызстан")]
