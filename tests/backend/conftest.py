"""
Конфигурация фикстур для backend тестов.

CLI-параметры:
  --backend-env   prod | stage   (по умолчанию: prod)
  --period-days   целое число    (по умолчанию: 7)

Оба параметра автоматически попадают в Allure-отчёт для каждого теста.
"""

import pytest
import pymongo
import allure
from datetime import datetime, timedelta
from src.config.db_config import MONGO_URI_STAGE, MONGO_URI_PROD, DB_NAME



@pytest.fixture(scope="session")
def backend_env(request):
    """Окружение БД, заданное через --backend-env."""
    return request.config.getoption("--backend-env")


@pytest.fixture(scope="session")
def period_days(request):
    """Период анализа в днях, заданный через --period-days."""
    return request.config.getoption("--period-days")


@pytest.fixture(scope="session")
def db(backend_env):
    """
    Фикстура для подключения к MongoDB.
    Окружение задаётся через --backend-env (по умолчанию: prod).
    """
    mongo_uri = MONGO_URI_PROD if backend_env == "prod" else MONGO_URI_STAGE
    env_name = backend_env.upper()

    print(f"\nConnecting to MongoDB {env_name}...")
    client = pymongo.MongoClient(mongo_uri)
    database = client[DB_NAME]
    yield database
    print(f"\nClosing Mongo {env_name} connection.")
    client.close()


@pytest.fixture(scope="session")
def prod_db():
    """
    Фикстура для явного подключения к MongoDB PROD.
    Используется в тестах, которым всегда нужен PROD независимо от --backend-env.
    """
    print("\nConnecting to MongoDB PROD...")
    client = pymongo.MongoClient(MONGO_URI_PROD)
    database = client[DB_NAME]
    yield database
    print("\nClosing Mongo PROD connection.")
    client.close()


@pytest.fixture(autouse=True)
def attach_test_period(backend_env, period_days):
    """
    Автоматически добавляет в Allure-отчёт окружение и период анализа
    для каждого backend теста.
    """
    now = datetime.now()
    period_start = now - timedelta(days=period_days)

    allure.dynamic.parameter("Окружение", backend_env.upper())
    allure.dynamic.parameter("Период анализа", f"последние {period_days} дней")
    allure.dynamic.parameter(
        "Диапазон дат",
        f"{period_start.strftime('%Y-%m-%d')} — {now.strftime('%Y-%m-%d')}",
    )
