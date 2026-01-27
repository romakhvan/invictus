"""
Скрипт для отладки и тестирования отдельных функций.
Запуск: python debug_script.py
"""

import pymongo
from datetime import datetime
from src.config.db_config import MONGO_URI_PROD, MONGO_URI_STAGE, DB_NAME
from src.repositories.users_repository import find_users_with_birthday, find_users_without_gender

# ========== КОНФИГУРАЦИЯ ==========
ENVIRONMENT = 'prod'  # 'prod' или 'stage'
# ==================================

def main():
    # Подключаемся к БД
    mongo_uri = MONGO_URI_PROD if ENVIRONMENT == 'prod' else MONGO_URI_STAGE
    env_name = ENVIRONMENT.upper()
    
    print(f"Connecting to MongoDB {env_name}...")
    client = pymongo.MongoClient(mongo_uri)
    db = client[DB_NAME]
    
    try:
        find_users_without_gender(db, datetime(2026, 1, 1))
        find_users_with_birthday(db, datetime(2026, 1, 1))
    finally:
        print(f"\nClosing MongoDB {env_name} connection.")
        client.close()

if __name__ == '__main__':
    main()
