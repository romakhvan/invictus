import pytest
import pymongo
import pytest_check as check
from collections import Counter
from datetime import timedelta

from src.repositories.rabbitholev2_repository import get_all_rabbitholev2_subscriptions_last_14_days
from src.config.db_config import MONGO_URI_PROD, MONGO_URI_STAGE, DB_NAME


# ========== КОНФИГУРАЦИЯ ОКРУЖЕНИЯ ==========
# Выберите окружение базы данных: 'prod' или 'stage'
ENVIRONMENT = 'prod'  # 'prod' или 'stage'
# ============================================


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB.
    Окружение определяется переменной ENVIRONMENT.
    """
    mongo_uri = MONGO_URI_PROD if ENVIRONMENT == 'prod' else MONGO_URI_STAGE
    env_name = ENVIRONMENT.upper()
    
    print(f"\nConnecting to MongoDB {env_name}...")
    client = pymongo.MongoClient(mongo_uri)
    db = client[DB_NAME]
    yield db
    print(f"\nClosing Mongo {env_name} connection.")
    client.close()



def test_rabbitholev2_users_with_subscriptions_sample(db):
    """
    🧪 Проверка пользователей с подписками, где разница между startDate и endDate больше 12 месяцев.
    Выводит только первые 5 примеров.
    """
    print("\n" + "=" * 80)
    print("ТЕСТ: Пользователи с подписками (длительность > 12 месяцев)")
    print("=" * 80)
    
    # Получаем все записи за последние 14 дней
    results = get_all_rabbitholev2_subscriptions_last_14_days(db, days=14)
    
    if not results:
        print("\n⚠️ Записи не найдены за последние 14 дней")
        return
    
    # Фильтруем записи с подписками, где разница между endDate и startDate больше 12 месяцев
    twelve_months = timedelta(days=370)  # 12 месяцев = 367 дней
    filtered_records = []
    
    for r in results:
        subscriptions = r.get("subscriptions", [])
        if subscriptions:
            # Проверяем, есть ли подписки с длительностью больше 12 месяцев
            matching_subs = []
            for sub in subscriptions:
                start_date = sub.get("startDate")
                end_date = sub.get("endDate")
                
                # Проверяем, что обе даты присутствуют
                if start_date and end_date:
                    # Вычисляем разницу между датами
                    duration = end_date - start_date
                    if duration > twelve_months:
                        matching_subs.append(sub)
            
            if matching_subs:
                # Создаем копию записи только с подписками, соответствующими фильтру
                filtered_record = r.copy()
                filtered_record["subscriptions"] = matching_subs
                filtered_records.append(filtered_record)
    
    if filtered_records:
        print(f"\n✅ Найдено {len(filtered_records)} записей с подписками (длительность > 12 месяцев)")
        print(f"   Показываем первые 5 примеров:\n")
        
        # Выводим только первые 5 записей
        from src.repositories.rabbitholev2_repository import display_rabbitholev2_subscriptions
        display_rabbitholev2_subscriptions(filtered_records[:5])
        
        if len(filtered_records) > 5:
            print(f"\n   ... и еще {len(filtered_records) - 5} записей")
    else:
        print(f"\n⚠️ Записи с подписками длительностью > 12 месяцев не найдены")

