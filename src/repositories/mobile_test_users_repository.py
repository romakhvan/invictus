from dataclasses import dataclass
from enum import Enum

import pytest

from src.pages.mobile.home import HomeState
from src.repositories.users_repository import (
    get_available_test_phone,
    get_phone_for_active_service_product_user,
    get_phone_for_active_subscription_user,
    get_phone_for_coach_user,
    get_phone_for_potential_user,
    get_user_id_by_phone,
)


class MobileTestUserScenario(Enum):
    ONBOARDING_NEW_USER = "onboarding_new_user"
    POTENTIAL_USER = "potential_user"
    SUBSCRIBED_USER = "subscribed_user"
    MEMBER_USER = "member_user"
    COACH_USER = "coach_user"
    KYRGYZSTAN_ONBOARDING_NEW_USER = "kyrgyzstan_onboarding_new_user"


@dataclass(frozen=True)
class TestUserContext:
    scenario: MobileTestUserScenario
    phone: str
    user_id: str | None = None
    role: str | None = None
    expected_home_state: HomeState | None = None
    country_code: str | None = None
    is_new_user: bool = False
    selection_source: str = "unknown"
    description: str = ""


class MobileTestUserSelector:
    DEFAULT_ONBOARDING_BASE_PHONE = "77781000001"
    DEFAULT_MAX_PHONE_ATTEMPTS = 100

    def __init__(self, db):
        self.db = db

    def select(
        self,
        scenario: MobileTestUserScenario,
        override_phone: str | None = None,
    ) -> TestUserContext:
        if scenario == MobileTestUserScenario.ONBOARDING_NEW_USER:
            return self._select_onboarding_new_user(override_phone=override_phone)
        if scenario == MobileTestUserScenario.POTENTIAL_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_potential_user(self.db),
                expected_home_state=HomeState.NEW_USER,
                role="potential",
            )
        if scenario == MobileTestUserScenario.SUBSCRIBED_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_active_subscription_user(self.db),
                expected_home_state=HomeState.SUBSCRIBED,
            )
        if scenario == MobileTestUserScenario.MEMBER_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_active_service_product_user(self.db),
                expected_home_state=HomeState.MEMBER,
            )
        if scenario == MobileTestUserScenario.COACH_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_coach_user(self.db),
            )
        if scenario == MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER:
            return self._select_kyrgyzstan_onboarding_new_user(
                override_phone=override_phone,
            )
        raise ValueError(f"Unsupported mobile test user scenario: {scenario!r}")

    def select_or_skip(
        self,
        scenario: MobileTestUserScenario,
        override_phone: str | None = None,
    ) -> TestUserContext:
        try:
            return self.select(scenario=scenario, override_phone=override_phone)
        except ValueError as exc:
            pytest.skip(str(exc))

    def _select_onboarding_new_user(
        self,
        override_phone: str | None = None,
    ) -> TestUserContext:
        if override_phone:
            return TestUserContext(
                scenario=MobileTestUserScenario.ONBOARDING_NEW_USER,
                phone=override_phone,
                country_code="+7",
                is_new_user=True,
                selection_source="override",
                description="Новый пользователь для онбординга из CLI override.",
            )

        phone = get_available_test_phone(
            self.db,
            base_phone=self.DEFAULT_ONBOARDING_BASE_PHONE,
            max_attempts=self.DEFAULT_MAX_PHONE_ATTEMPTS,
        )
        if not phone:
            raise ValueError(
                "Не удалось подобрать телефон для сценария "
                "ONBOARDING_NEW_USER: свободный номер не найден."
            )
        return TestUserContext(
            scenario=MobileTestUserScenario.ONBOARDING_NEW_USER,
            phone=phone,
            country_code="+7",
            is_new_user=True,
            selection_source="generated_free_phone",
            description="Новый пользователь для онбординга с автоматически найденным номером.",
        )

    def _select_kyrgyzstan_onboarding_new_user(
        self,
        override_phone: str | None = None,
    ) -> TestUserContext:
        if not override_phone:
            raise ValueError(
                "Не удалось подобрать телефон для сценария "
                "KYRGYZSTAN_ONBOARDING_NEW_USER: требуется override_phone."
            )
        return TestUserContext(
            scenario=MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER,
            phone=override_phone,
            country_code="+996",
            is_new_user=True,
            selection_source="override",
            description="Новый пользователь для онбординга Кыргызстана из CLI override.",
        )

    def _select_existing_candidate(
        self,
        scenario: MobileTestUserScenario,
        phone: str | None,
        expected_home_state: HomeState | None = None,
        role: str | None = None,
    ) -> TestUserContext:
        if not phone:
            raise ValueError(
                f"Не удалось подобрать телефон для сценария {scenario.name}: "
                "подходящий кандидат не найден."
            )
        user_id = get_user_id_by_phone(self.db, phone)
        if not user_id:
            raise ValueError(
                f"Не удалось определить user_id для сценария {scenario.name}: "
                f"пользователь с телефоном {phone} не найден."
            )
        return TestUserContext(
            scenario=scenario,
            phone=phone,
            user_id=user_id,
            role=role,
            expected_home_state=expected_home_state,
            is_new_user=False,
            selection_source="db_lookup",
            description=f"Существующий пользователь для сценария {scenario.name}.",
        )
