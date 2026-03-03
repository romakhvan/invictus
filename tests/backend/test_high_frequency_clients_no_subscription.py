"""
Тест для анализа клиентов с высокой частотой посещений без абонемента.
"""
import pytest
import psycopg2
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


def test_daily_access_users_count(pg_conn):
    """
    Получает количество уникальных пользователей,
    у которых был вход за последние 24 часа.
    """
    cursor = pg_conn.cursor()
    
    # SQL-запрос для подсчета уникальных пользователей за последние сутки
    query = """
        SELECT COUNT(DISTINCT "user") as users_count
        FROM mongo.accesscontrols
        WHERE created_at >= NOW() - INTERVAL '1 day';
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    users_count = result[0] if result else 0
    
    print(f"\n=== Количество пользователей с входом за последние 24 часа: {users_count} ===")
    
    cursor.close()
    
    assert users_count >= 0, "Количество пользователей не может быть отрицательным"


def test_recent_access_sample(pg_conn):
    """
    Показывает примеры последних записей из accesscontrols за сутки.
    """
    cursor = pg_conn.cursor()
    
    query = """
        SELECT 
            "user",
            created_at,
            type,
            access_type,
            user_full_name
        FROM mongo.accesscontrols
        WHERE created_at >= NOW() - INTERVAL '1 day'
        ORDER BY created_at DESC
        LIMIT 10;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"\n=== Последние 10 записей за сутки ===")
    for row in results:
        print(f"User: {row[0]}, Name: {row[4]}, Time: {row[1]}, Type: {row[2]}, Access: {row[3]}")
    
    cursor.close()
