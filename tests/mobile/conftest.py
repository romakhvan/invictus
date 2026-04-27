"""
Конфигурация фикстур для mobile тестов.
Mobile тесты используют STAGE окружение.
"""

import os
import pytest
import pymongo
import time
from contextlib import contextmanager

from src.config.db_config import MONGO_URI_STAGE, DB_NAME
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)
from tests.mobile.helpers.session_helpers import (
    ensure_coach_user_on_home_screen,
    ensure_test_user_session,
    ensure_member_user_on_home_screen,
    ensure_new_user_on_home_screen,
    ensure_rabbit_hole_user_on_home_screen,
    ensure_subscribed_user_on_home_screen,
)


def _mobile_ui_logs_enabled() -> bool:
    return os.getenv("MOBILE_UI_LOGS") == "1"


def _mobile_ui_log(message: str) -> None:
    if _mobile_ui_logs_enabled():
        print(f"[mobile-ui] {message}", flush=True)


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


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB STAGE.
    Используется для всех mobile тестов.
    """
    print("\n🔌 Connecting to MongoDB STAGE...")
    with _mobile_ui_timing("create MongoDB STAGE client"):
        client = pymongo.MongoClient(MONGO_URI_STAGE)
        db = client[DB_NAME]
        db.command("ping")
    yield db
    print("\n🧹 Closing Mongo STAGE connection.")
    with _mobile_ui_timing("close MongoDB STAGE client"):
        client.close()


# ==================== Автоматический трекинг времени выполнения ====================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Сохраняем время начала теста."""
    _mobile_ui_log(f"PYTEST SETUP START {item.nodeid}")
    item.test_start_time = time.time()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Логируем границу между setup fixtures и телом mobile-теста."""
    _mobile_ui_log(f"PYTEST CALL START {item.nodeid}")
    outcome = yield
    _mobile_ui_log(f"PYTEST CALL DONE {item.nodeid}")
    return outcome


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Выводим время выполнения теста после его завершения."""
    outcome = yield
    report = outcome.get_result()
    
    # Выводим время только после завершения фазы выполнения теста
    if report.when == "call" and hasattr(item, 'test_start_time'):
        execution_time = time.time() - item.test_start_time
        
        if report.passed:
            print(f"\n✅ ТЕСТ ПРОЙДЕН")
        elif report.failed:
            print(f"\n❌ ТЕСТ ПРОВАЛЕН")
        elif report.skipped:
            print(f"\n⏭️  ТЕСТ ПРОПУЩЕН")
        
        print(f"⏱️  Время выполнения: {execution_time:.2f} сек ({execution_time/60:.2f} мин)")


# ==================== Фикстуры с параметрами командной строки ====================

@pytest.fixture(scope="session")
def onboarding_phone(request):
    """Номер телефона для теста онбординга (передаётся через --onboarding-phone)."""
    return request.config.getoption("--onboarding-phone")


@pytest.fixture(scope="session")
def onboarding_phone_kg(request):
    """Номер телефона (без кода +996) для теста онбординга клиента из Кыргызстана (--onboarding-phone-kg)."""
    return request.config.getoption("--onboarding-phone-kg")


# ==================== Общие фикстуры для всех mobile тестов ====================

@pytest.fixture
def new_user_on_home(mobile_driver, db):
    """Драйвер на главной в состоянии NEW_USER."""
    with _mobile_ui_timing("fixture new_user_on_home setup"):
        ensure_new_user_on_home_screen(mobile_driver, db)
    _mobile_ui_log("READY fixture new_user_on_home")
    yield mobile_driver


@pytest.fixture
def subscribed_user_on_home(mobile_driver, db):
    """Драйвер на главной в состоянии SUBSCRIBED."""
    with _mobile_ui_timing("fixture subscribed_user_on_home setup"):
        ensure_subscribed_user_on_home_screen(mobile_driver, db)
    _mobile_ui_log("READY fixture subscribed_user_on_home")
    yield mobile_driver


@pytest.fixture
def member_user_on_home(mobile_driver, db):
    """Драйвер на главной в состоянии MEMBER."""
    with _mobile_ui_timing("fixture member_user_on_home setup"):
        ensure_member_user_on_home_screen(mobile_driver, db)
    _mobile_ui_log("READY fixture member_user_on_home")
    yield mobile_driver


@pytest.fixture
def rabbit_hole_user_on_home(mobile_driver, db):
    """Драйвер на главной в состоянии RABBIT_HOLE."""
    with _mobile_ui_timing("fixture rabbit_hole_user_on_home setup"):
        ensure_rabbit_hole_user_on_home_screen(mobile_driver, db)
    _mobile_ui_log("READY fixture rabbit_hole_user_on_home")
    yield mobile_driver


@pytest.fixture
def coach_user_on_home(mobile_driver, db):
    """Драйвер, авторизованный coach-пользователем. Пока flow может завершиться skip."""
    with _mobile_ui_timing("fixture coach_user_on_home setup"):
        ensure_coach_user_on_home_screen(mobile_driver, db)
    _mobile_ui_log("READY fixture coach_user_on_home")
    yield mobile_driver


@pytest.fixture
def potential_user_on_main_screen(mobile_driver, db, potential_user_context):
    """Драйвер на главной под пользователем role=potential."""
    with _mobile_ui_timing("fixture potential_user_on_main_screen setup"):
        ensure_new_user_on_home_screen(mobile_driver, db, context=potential_user_context)
    _mobile_ui_log("READY fixture potential_user_on_main_screen")
    yield mobile_driver


@pytest.fixture
def potential_user_context(db):
    """Контекст существующего potential-пользователя для mobile smoke-flow."""
    selector = MobileTestUserSelector(db)
    return selector.select_or_skip(MobileTestUserScenario.POTENTIAL_USER)


@pytest.fixture
def potential_user_session(mobile_driver, db, potential_user_context):
    """РђРІС‚РѕСЂРёР·РѕРІР°РЅРЅС‹Р№ potential-РїРѕР»СЊР·РѕРІР°С‚РµР»СЊ СЃ РґРѕСЃС‚СѓРїРЅС‹Рј shell/tabbar."""
    with _mobile_ui_timing("fixture potential_user_session setup"):
        nav = ensure_test_user_session(mobile_driver, db, potential_user_context)
    _mobile_ui_log("READY fixture potential_user_session")
    yield nav


@pytest.fixture
def authorized_potential_user(mobile_driver, db, potential_user_context):
    """Авторизованный potential-пользователь на главной (алиас для auth-тестов)."""
    ensure_test_user_session(mobile_driver, db, potential_user_context)
    yield mobile_driver


# ==================== Интерактивное меню после выбранных тестов ====================
# Меню вызывается в teardown фикстуры appium_driver (tests/conftest.py), когда
# тест помечен @pytest.mark.interactive_mobile или передан --keepalive.
# Так сессия не закрывается до выхода из меню — команды 1–9 работают.
