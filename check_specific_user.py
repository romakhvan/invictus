"""
Скрипт для анализа конкретного клиента.
"""
import psycopg2
from src.config.db_config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_DATABASE
)


def main():
    print(f"Подключение к PostgreSQL...")
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DATABASE
    )
    
    cursor = conn.cursor()
    
    user_id = '66920cb8e498f711eb1eaf55'
    
    # Информация о клиенте
    print(f"\n=== Анализ клиента: {user_id} ===\n")
    
    query = """
        SELECT 
            DATE(ac.created_at) as visit_date,
            COUNT(*) as visits_count,
            STRING_AGG(DISTINCT ac.club || ' (' || COALESCE(c.name, 'Unknown') || ')', ', ') as clubs_visited,
            STRING_AGG(TO_CHAR(ac.created_at, 'HH24:MI:SS'), ', ' ORDER BY ac.created_at) as visit_times
        FROM mongo.accesscontrols ac
        LEFT JOIN mongo.clubs c ON ac.club = c.id
        WHERE ac."user" = %s
            AND ac.created_at >= NOW() - INTERVAL '30 day'
            AND ac.type = 'enter'
            AND (ac.err IS NULL OR ac.err = '')
        GROUP BY DATE(ac.created_at)
        ORDER BY visits_count DESC, visit_date DESC
        LIMIT 10;
    """
    
    cursor.execute(query, (user_id,))
    results = cursor.fetchall()
    
    if results:
        print("Даты с максимальным количеством входов:")
        print("-" * 100)
        for row in results:
            visit_date, visits_count, clubs, times = row
            print(f"\nДата: {visit_date}")
            print(f"Количество входов: {visits_count}")
            print(f"Клубы: {clubs}")
            print(f"Время входов: {times}")
    else:
        print("Нет данных за последние 30 дней")
    
    cursor.close()
    conn.close()
    print("\n\nГотово!")


if __name__ == "__main__":
    main()
