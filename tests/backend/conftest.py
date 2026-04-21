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

NOTIFICATIONS_TZ_URL = (
    "https://docs.google.com/spreadsheets/d/1SyKGftlBC7CbeZsR8jBC3jqbzRZRYV6SgvF7BFLC6aw/edit?gid=0#gid=0"
)

BACKEND_MONITORING_PATHS = {
    "tests/backend/payments/test_recent_transactions.py",
    "tests/backend/payments/test_webkassa_monitoring.py",
    "tests/backend/payments/bonuses/test_bonus_usage_distribution.py",
    "tests/backend/guest_visits/test_guest_visit_actions_monitoring.py",
    "tests/backend/guest_visits/test_guest_visits_monitoring.py",
}

BACKEND_RESEARCH_PATHS = {
    "tests/backend/test_high_frequency_clients_no_subscription.py",
    "tests/backend/test_statistics_2025.py",
}


def _normalized_backend_path(item) -> str | None:
    """Возвращает нормализованный относительный путь backend-теста."""
    raw_path = getattr(item, "path", None) or str(item.fspath)
    normalized = str(raw_path).replace("\\", "/").lower()
    prefix = "tests/backend/"
    prefix_index = normalized.find(prefix)
    if prefix_index == -1:
        return None
    return normalized[prefix_index:]


def _has_marker(item, marker_name: str) -> bool:
    """Проверяет, есть ли у элемента нужный marker."""
    return any(marker.name == marker_name for marker in item.iter_markers())


def pytest_collection_modifyitems(items):
    """
    Централизованно классифицирует backend-сценарии по типам.

    Пока структура каталогов не разрезана на checks/monitoring/research,
    держим явный реестр здесь, чтобы marker-ы были консистентны для запуска
    и документации.
    """
    for item in items:
        relative_path = _normalized_backend_path(item)
        if relative_path is None:
            continue

        if not _has_marker(item, "backend"):
            item.add_marker(pytest.mark.backend)

        if relative_path in BACKEND_MONITORING_PATHS:
            if not _has_marker(item, "backend_monitoring"):
                item.add_marker(pytest.mark.backend_monitoring)
            continue

        if relative_path in BACKEND_RESEARCH_PATHS:
            if not _has_marker(item, "backend_research"):
                item.add_marker(pytest.mark.backend_research)
            continue

        if not _has_marker(item, "backend_check"):
            item.add_marker(pytest.mark.backend_check)


def pytest_addoption(parser):
    """Регистрирует backend-специфичные CLI-опции только для backend suite."""
    parser.addoption(
        "--backend-env",
        default="prod",
        choices=["prod", "stage"],
        help="Окружение MongoDB для backend тестов (prod или stage). По умолчанию: prod",
    )
    parser.addoption(
        "--period-days",
        type=int,
        default=7,
        help="Период анализа в днях для backend тестов. По умолчанию: 7",
    )



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


@pytest.fixture(autouse=True)
def attach_notifications_tz_link(request):
    """
    Добавляет ссылку на ТЗ по уведомлениям во все backend-тесты из папки notifications.
    """
    relative_path = _normalized_backend_path(request.node)
    if relative_path and relative_path.startswith("tests/backend/notifications/"):
        allure.dynamic.link(
            NOTIFICATIONS_TZ_URL,
            name="ТЗ по уведомлениям",
            link_type="documentation",
        )
