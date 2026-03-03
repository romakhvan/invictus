"""
Конфигурация фикстур для mobile тестов.
Mobile тесты используют STAGE окружение.
"""

import pytest
import pymongo
import time
from src.config.db_config import MONGO_URI_STAGE, DB_NAME


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

