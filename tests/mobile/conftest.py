"""
Конфигурация фикстур для mobile тестов.
Mobile тесты используют STAGE окружение.
"""

import pytest
import pymongo
import time

from src.config.db_config import MONGO_URI_STAGE, DB_NAME
from tests.mobile.helpers.session_helpers import ensure_potential_user_on_main_screen


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB STAGE.
    Используется для всех mobile тестов.
    """
    print("\n🔌 Connecting to MongoDB STAGE...")
    client = pymongo.MongoClient(MONGO_URI_STAGE)
    db = client[DB_NAME]
    yield db
    print("\n🧹 Closing Mongo STAGE connection.")
    client.close()


# ==================== Автоматический трекинг времени выполнения ====================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Сохраняем время начала теста."""
    item.test_start_time = time.time()


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


# ==================== Общие фикстуры для всех mobile тестов ====================

@pytest.fixture
def potential_user_on_main_screen(mobile_driver, db):
    """Драйвер на главной под пользователем role=potential."""
    ensure_potential_user_on_main_screen(mobile_driver, db)
    yield mobile_driver


@pytest.fixture
def authorized_potential_user(mobile_driver, db):
    """Авторизованный potential-пользователь на главной (алиас для auth-тестов)."""
    ensure_potential_user_on_main_screen(mobile_driver, db)
    yield mobile_driver


# ==================== Интерактивное меню после выбранных тестов ====================
# Меню вызывается в teardown фикстуры appium_driver (tests/conftest.py), когда
# тест помечен @pytest.mark.interactive_mobile или передан --keepalive.
# Так сессия не закрывается до выхода из меню — команды 1–9 работают.

