from dataclasses import dataclass
from enum import Enum
import os
import time
from contextlib import contextmanager

import pytest

from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_cache import MobileTestUsersCache
from src.repositories.users_repository import (
    get_available_test_phone,
    get_phone_for_active_service_product_user,
    get_phone_for_active_rabbit_hole_user,
    get_phone_for_active_subscription_user,
    get_phone_for_coach_user,
    get_phone_for_potential_user,
    get_user_id_by_phone,
    validate_coach_test_user,
    validate_member_test_user,
    validate_potential_test_user,
    validate_rabbit_hole_test_user,
    validate_subscribed_test_user,
)


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


class MobileTestUserScenario(Enum):
    ONBOARDING_NEW_USER = "onboarding_new_user"
    POTENTIAL_USER = "potential_user"
    SUBSCRIBED_USER = "subscribed_user"
    MEMBER_USER = "member_user"
    COACH_USER = "coach_user"
    RABBIT_HOLE_USER = "rabbit_hole_user"
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
    CACHEABLE_SCENARIOS = {
        MobileTestUserScenario.POTENTIAL_USER,
        MobileTestUserScenario.SUBSCRIBED_USER,
        MobileTestUserScenario.MEMBER_USER,
        MobileTestUserScenario.COACH_USER,
        MobileTestUserScenario.RABBIT_HOLE_USER,
    }

    def __init__(self, db, cache: MobileTestUsersCache | None = None):
        self.db = db
        self.cache = cache or MobileTestUsersCache()

    def select(
        self,
        scenario: MobileTestUserScenario,
        override_phone: str | None = None,
    ) -> TestUserContext:
        if scenario in self.CACHEABLE_SCENARIOS:
            return self._select_cached_existing_user(scenario)
        if scenario == MobileTestUserScenario.ONBOARDING_NEW_USER:
            return self._select_onboarding_new_user(override_phone=override_phone)
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
        with _mobile_ui_timing(f"select_or_skip {scenario.name}"):
            try:
                return self.select(scenario=scenario, override_phone=override_phone)
            except ValueError as exc:
                pytest.skip(str(exc))

    def _select_cached_existing_user(self, scenario: MobileTestUserScenario) -> TestUserContext:
        category = scenario.name
        users = self.cache.get_category_users(category)
        invalid_user_ids = {
            user.get("user_id")
            for user in users
            if user.get("status") == "invalid" and user.get("user_id")
        }

        for entry in reversed(users):
            if entry.get("status") != "valid":
                continue
            valid, reason = validate_cached_test_user(self.db, scenario, entry)
            if valid:
                _mobile_ui_log(f"cache hit {category}")
                return self._context_from_cache_entry(scenario, entry)
            self.cache.mark_invalid(category, str(entry.get("user_id")), reason or "cached user is invalid")
            invalid_user_ids.add(entry.get("user_id"))
            _mobile_ui_log(f"cache invalid {category}: {reason}")

        _mobile_ui_log(f"cache miss {category}")
        if invalid_user_ids:
            _mobile_ui_log(f"cache excluded invalid users {category}: {len(invalid_user_ids)}")
        context = self._select_existing_candidate_for_scenario(
            scenario,
            excluded_user_ids={user_id for user_id in invalid_user_ids if user_id},
        )
        self.cache.append_valid_user(
            category,
            phone=context.phone,
            user_id=str(context.user_id),
            expected_home_state=context.expected_home_state.value if context.expected_home_state else None,
            role=context.role,
        )
        _mobile_ui_log(f"cache append {category}")
        return context

    def _context_from_cache_entry(
        self,
        scenario: MobileTestUserScenario,
        entry: dict,
    ) -> TestUserContext:
        expected_state_value = entry.get("expected_home_state")
        expected_home_state = HomeState(expected_state_value) if expected_state_value else None
        return TestUserContext(
            scenario=scenario,
            phone=str(entry.get("phone") or ""),
            user_id=str(entry.get("user_id") or ""),
            role=entry.get("role"),
            expected_home_state=expected_home_state,
            is_new_user=False,
            selection_source="cache",
            description=f"Cached mobile test user for scenario {scenario.name}.",
        )

    def _select_existing_candidate_for_scenario(
        self,
        scenario: MobileTestUserScenario,
        excluded_user_ids: set | None = None,
    ) -> TestUserContext:
        if scenario == MobileTestUserScenario.POTENTIAL_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_potential_user(self.db, excluded_user_ids=excluded_user_ids),
                expected_home_state=HomeState.NEW_USER,
                role="potential",
            )
        if scenario == MobileTestUserScenario.SUBSCRIBED_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_active_subscription_user(self.db, excluded_user_ids=excluded_user_ids),
                expected_home_state=HomeState.SUBSCRIBED,
            )
        if scenario == MobileTestUserScenario.MEMBER_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_active_service_product_user(self.db, excluded_user_ids=excluded_user_ids),
                expected_home_state=HomeState.MEMBER,
            )
        if scenario == MobileTestUserScenario.RABBIT_HOLE_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_active_rabbit_hole_user(self.db, excluded_user_ids=excluded_user_ids),
                expected_home_state=HomeState.RABBIT_HOLE,
            )
        if scenario == MobileTestUserScenario.COACH_USER:
            return self._select_existing_candidate(
                scenario=scenario,
                phone=get_phone_for_coach_user(self.db, excluded_user_ids=excluded_user_ids),
            )
        raise ValueError(f"Unsupported cached mobile test user scenario: {scenario!r}")

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


def _mobile_ui_log(message: str) -> None:
    if _mobile_ui_logs_enabled():
        print(f"[mobile-ui] {message}", flush=True)


# Валидация пользователей в рамках одной pytest-сессии не повторяется:
# состояние тестового пользователя за время сессии не меняется.
_session_validation_cache: dict[str, tuple[bool, str | None]] = {}


def validate_cached_test_user(
    db,
    scenario: MobileTestUserScenario,
    entry: dict,
) -> tuple[bool, str | None]:
    user_id = entry.get("user_id")
    phone = entry.get("phone")
    if not user_id or not phone:
        return False, "cache entry has no user_id or phone"

    session_key = f"{scenario.name}:{user_id}:{phone}"
    if session_key in _session_validation_cache:
        return _session_validation_cache[session_key]

    if scenario == MobileTestUserScenario.POTENTIAL_USER:
        result = validate_potential_test_user(db, user_id, phone)
    elif scenario == MobileTestUserScenario.SUBSCRIBED_USER:
        result = validate_subscribed_test_user(db, user_id, phone)
    elif scenario == MobileTestUserScenario.MEMBER_USER:
        result = validate_member_test_user(db, user_id, phone)
    elif scenario == MobileTestUserScenario.RABBIT_HOLE_USER:
        result = validate_rabbit_hole_test_user(db, user_id, phone)
    elif scenario == MobileTestUserScenario.COACH_USER:
        result = validate_coach_test_user(db, user_id, phone)
    else:
        return False, f"scenario {scenario.name} is not cacheable"

    if result[0]:
        _session_validation_cache[session_key] = result
    return result
