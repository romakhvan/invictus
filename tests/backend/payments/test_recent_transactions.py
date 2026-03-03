"""
Тест для анализа транзакций с 14:55 по местному времени (исключая source='pos') с группировкой по instalmentType.
"""
import pytest
import pymongo
from datetime import datetime, timedelta, timezone
from collections import defaultdict

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
    
    print(f"\n🔌 Подключение к MongoDB {env_name}...")
    client = pymongo.MongoClient(mongo_uri)
    database = client[DB_NAME]
    
    yield database
    
    print(f"\n🔌 Закрытие соединения с MongoDB {env_name}.")
    client.close()


def test_recent_transactions_grouped_by_instalment_type(db):
    """
    Получает транзакции с 14:55 по местному времени (исключая source='pos') и группирует их по instalmentType.
    """
    from src.utils.repository_helpers import get_collection
    
    col = get_collection(db, "transactions")
    
    # Период: фиксированная дата и время 14:55 03.02.2026 по местному времени (UTC+5 для Алматы)
    # Задаем datetime для 14:55 3 февраля 2026 года и конвертируем в UTC
    start_time_local = datetime(2026, 2, 3, 14, 55, 0)
    # Конвертируем в UTC (минус 5 часов для Алматы)
    start_time_utc = start_time_local - timedelta(hours=5)
    
    query = {
        "created_at": {"$gte": start_time_utc},
        "$or": [
            {"source": {"$exists": False}},  # Транзакции без поля source
            {"source": {"$ne": "pos"}}  # Транзакции, где source != "pos"
        ]
    }
    
    print(f"\n{'=' * 80}")
    print(f"📊 ТРАНЗАКЦИИ С 14:55 С ГРУППИРОВКОЙ ПО instalmentType")
    print(f"{'=' * 80}")
    current_local = datetime.now()
    print(f"Период (местное время): с {start_time_local.strftime('%Y-%m-%d %H:%M:%S')} до {current_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Период (UTC): с {start_time_utc.strftime('%Y-%m-%d %H:%M:%S')} до {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    
    transactions = list(col.find(query).sort("created_at", -1))
    
    print(f"\n✅ Всего транзакций: {len(transactions)}")
    
    if not transactions:
        print("\n⚠️ Транзакции за указанный период не найдены")
        return
    
    # Группировка по instalmentType
    grouped = defaultdict(list)
    
    for trans in transactions:
        instalment_type = trans.get("instalmentType", "Не указан")
        grouped[instalment_type].append(trans)
    
    # Вывод статистики по группам
    print(f"\n{'─' * 80}")
    print(f"📈 ГРУППИРОВКА ПО instalmentType:")
    print(f"{'─' * 80}")
    
    for instalment_type, trans_list in sorted(grouped.items()):
        print(f"\n🔹 {instalment_type}: {len(trans_list)} транзакций")
        
        # Подсчёт статистики по статусам
        statuses = defaultdict(int)
        total_amount = 0
        
        for trans in trans_list:
            status = trans.get("status", "unknown")
            statuses[status] += 1
            total_amount += trans.get("price", 0)
        
        print(f"   Общая сумма: {total_amount} тенге")
        print(f"   Статусы:")
        for status, count in sorted(statuses.items()):
            print(f"      - {status}: {count}")
    
    # Показываем успешные транзакции с productType='recurrent' с группировкой по instalmentType
    print(f"\n{'─' * 80}")
    print(f"✅ УСПЕШНЫЕ ТРАНЗАКЦИИ С productType='recurrent' ПО instalmentType:")
    print(f"{'─' * 80}")
    
    # Фильтруем успешные транзакции с productType='recurrent'
    recurrent_success_transactions = [
        t for t in transactions 
        if t.get("status") == "success" and t.get("productType") == "recurrent"
    ]
    
    if not recurrent_success_transactions:
        print("\n⚠️ Успешных транзакций с productType='recurrent' не найдено")
    else:
        # Группируем по instalmentType
        recurrent_grouped = defaultdict(int)
        for trans in recurrent_success_transactions:
            instalment_type = trans.get("instalmentType", "Не указан")
            recurrent_grouped[instalment_type] += 1
        
        print(f"\n📊 Всего успешных recurrent транзакций: {len(recurrent_success_transactions)}")
        print(f"\n📈 Распределение по instalmentType:")
        
        for instalment_type, count in sorted(recurrent_grouped.items()):
            print(f"   🔹 {instalment_type}: {count} транзакций")
    
    # Показываем только FAIL транзакции с группировкой по instalmentType
    print(f"\n{'─' * 80}")
    print(f"❌ НЕУСПЕШНЫЕ ТРАНЗАКЦИИ (FAIL) ПО instalmentType:")
    print(f"{'─' * 80}")
    
    # Фильтруем только fail транзакции
    fail_transactions = [t for t in transactions if t.get("status") == "fail"]
    
    if not fail_transactions:
        print("\n✅ Неуспешных транзакций не найдено")
    else:
        # Группируем fail транзакции по instalmentType
        fail_grouped = defaultdict(list)
        for trans in fail_transactions:
            instalment_type = trans.get("instalmentType", "Не указан")
            fail_grouped[instalment_type].append(trans)
        
        print(f"\n📊 Всего неуспешных транзакций: {len(fail_transactions)}")
        
        # Выводим по каждому instalmentType
        for instalment_type, trans_list in sorted(fail_grouped.items()):
            print(f"\n{'─' * 80}")
            print(f"🔸 {instalment_type}: {len(trans_list)} неуспешных транзакций")
            print(f"{'─' * 80}")
            
            # Показываем до 5 примеров для каждого типа
            for idx, trans in enumerate(trans_list[:5], 1):
                created_at = trans.get("created_at")
                price = trans.get("price", 0)
                product_type = trans.get("productType", "unknown")
                reason = trans.get("reason", "Не указана")
                
                print(f"\n   #{idx}")
                print(f"      Время: {created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'Не указано'}")
                print(f"      Сумма: {price} тенге")
                print(f"      Тип продукта: {product_type}")
                if reason != "Не указана":
                    print(f"      Причина: {reason}")
            
            if len(trans_list) > 5:
                print(f"\n   ... и ещё {len(trans_list) - 5} транзакций")
    
    print(f"\n{'=' * 80}")
    
    # Проверка
    assert len(transactions) >= 0, "Количество транзакций не может быть отрицательным"
