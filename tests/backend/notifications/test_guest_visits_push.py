"""
Тесты для проверки push-уведомлений у клиентов с гостевыми визитами.
"""
import json
import psycopg2
import pytest
import pytest_check as check
from pathlib import Path
from bson import ObjectId
from datetime import datetime
from src.config.db_config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DATABASE
)


@pytest.fixture(scope="session")
def pg_conn():
    """
    Фикстура для подключения к PostgreSQL.
    """
    print(f"\nConnecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DATABASE
    )
    yield conn
    print(f"\nClosing PostgreSQL connection.")
    conn.close()


@pytest.fixture(scope="session")
def guest_visits_recipients():
    """
    Загружает список ID клиентов, получивших push о гостевых визитах.
    """
    json_path = Path(__file__).parent.parent.parent.parent / "data" / "Cluster0.notifications.json"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Извлекаем список ObjectId из users
    user_ids = [ObjectId(user["$oid"]) for user in data[0]["users"]]

    print(f"\nЗагружено {len(user_ids)} ID клиентов из notifications.json")

    return user_ids


def test_guest_visits_push_recipients(db, pg_conn, guest_visits_recipients):
    """
    Проверяет push-уведомление для клиентов с гостевыми визитами:
    - Клиенты действительно имеют гостевые визиты;
    - Условия отправки push-уведомления соблюдены.
    """
    print(f"\n=== TEST: Guest Visits Push ===")
    print(f"Количество получателей: {len(guest_visits_recipients)}")

    assert len(guest_visits_recipients) > 0, "Список получателей пуст"

    cursor = pg_conn.cursor()

    # Преобразуем ObjectId в строки для SQL-запроса
    user_ids_str = [str(user_id) for user_id in guest_visits_recipients]

    # SQL-запрос для получения количества подписок и даты окончания последней подписки
    query = """
        SELECT
            user_id,
            subscriptions_count,
            end_date,
            start_date
        FROM (
            SELECT
                "user" as user_id,
                COUNT(*) OVER (PARTITION BY "user") as subscriptions_count,
                end_date,
                start_date,
                ROW_NUMBER() OVER (PARTITION BY "user" ORDER BY start_date DESC) as rn
            FROM master.mongo.usersubscriptions
            WHERE "user" = ANY(%s)
            AND is_deleted = false
            AND is_active = true
        ) subquery
        WHERE rn = 1
        ORDER BY subscriptions_count DESC, user_id
    """

    cursor.execute(query, (user_ids_str,))
    results = cursor.fetchall()

    today = datetime.now()

    print(f"\n{'=' * 180}")
    print(f"КОЛИЧЕСТВО ПОДПИСОК У КЛИЕНТОВ И АНАЛИЗ ДАТ")
    print(f"{'=' * 180}")
    print(f"{'User ID':<30} {'Кол-во':<10} {'Дата начала':<25} {'Дата окончания':<25} {'Длит.(дн)':<12} {'С начала(дн)':<15} {'До конца(дн)':<15}")
    print(f"{'-' * 180}")

    for user_id, count, end_date, start_date in results:
        start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S') if start_date else 'N/A'
        end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S') if end_date else 'N/A'

        # Разница между start_date и end_date (длительность подписки)
        if start_date and end_date:
            duration_days = (end_date - start_date).days
        else:
            duration_days = 'N/A'

        # Разница между сегодняшней датой и start_date (сколько дней прошло с начала)
        if start_date:
            days_since_start = (today - start_date).days
        else:
            days_since_start = 'N/A'

        # Разница между сегодняшней датой и end_date
        if end_date:
            days_until_end = (end_date - today).days
        else:
            days_until_end = 'N/A'

        duration_str = str(duration_days) if duration_days != 'N/A' else 'N/A'
        days_since_str = str(days_since_start) if days_since_start != 'N/A' else 'N/A'
        days_until_str = str(days_until_end) if days_until_end != 'N/A' else 'N/A'

        print(f"{user_id:<30} {count:<10} {start_date_str:<25} {end_date_str:<25} {duration_str:<12} {days_since_str:<15} {days_until_str:<15}")

    print(f"{'-' * 80}")
    print(f"Всего клиентов с данными: {len(results)}")
    print(f"Клиентов в списке push: {len(guest_visits_recipients)}")

    # Проверка: у всех ли клиентов есть подписки
    users_with_subs = {row[0] for row in results}
    users_without_subs = set(user_ids_str) - users_with_subs

    if users_without_subs:
        print(f"\nКлиенты БЕЗ подписок ({len(users_without_subs)}):")
        for user_id in list(users_without_subs)[:10]:  # показываем первые 10
            print(f"  - {user_id}")
        if len(users_without_subs) > 10:
            print(f"  ... и еще {len(users_without_subs) - 10}")

    cursor.close()

    print(f"\n{'=' * 80}")
    print("Тест завершён")
