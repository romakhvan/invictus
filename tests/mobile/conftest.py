"""
Конфигурация фикстур для mobile тестов.
Mobile тесты используют STAGE окружение.
"""

import pytest
import pymongo
import time
from src.config.db_config import MONGO_URI_STAGE, DB_NAME
from src.repositories.users_repository import get_phone_for_potential_user
from tests.mobile.helpers.onboarding_helpers import run_auth_to_main


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


@pytest.fixture
def potential_user_on_main_screen(mobile_driver, db):
    """
    Драйвер на главном экране в состоянии NEW_USER под существующим пользователем (role: potential).

    Только вход: превью → ввод телефона → SMS-код → главная. Без онбординга.
    Требует в БД пользователя с role: 'potential' и полем firstName.
    """
    phone = get_phone_for_potential_user(db)
    if not phone:
        pytest.skip(
            "В БД нет пользователя с role: 'potential' и полем firstName. "
            "Создайте такого пользователя (например, пройдите онбординг в отдельном тесте)."
        )
    run_auth_to_main(mobile_driver, phone)
    yield mobile_driver


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

