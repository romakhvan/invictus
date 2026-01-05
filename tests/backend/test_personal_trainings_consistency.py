"""
Тест на консистентность количества персональных тренировок клиента
в разных коллекциях MongoDB.
"""

import pytest
import pymongo
from src.utils.repository_helpers import get_collection
from src.config.db_config import MONGO_URI_PROD, DB_NAME


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB PROD.
    """
    print("\nConnecting to MongoDB PROD...")
    client = pymongo.MongoClient(MONGO_URI_PROD)
    db = client[DB_NAME]
    yield db
    print("\nClosing Mongo PROD connection.")
    client.close()


def test_personal_trainings_count_consistency_last_20(db):
    """
    Проверяет консистентность количества персональных тренировок
    для всех записей userserviceproducts за последние 2 дня.
    
    Сравнивает:
    1. count в userserviceproducts
    2. количество активных неиспользованных билетов в trainingtickets
    3. currentCount в последней записи userserviceproductshistories
    """
    print("\n" + "=" * 80)
    print("ПРОВЕРКА КОНСИСТЕНТНОСТИ ПЕРСОНАЛЬНЫХ ТРЕНИРОВОК")
    print("Анализ записей за последние 2 дня")
    print("=" * 80)
    
    # Шаг 1: Получаем последние 20 записей из userserviceproducts
    # где initialCount != count (уже были использованы тренировки)
    usp_col = get_collection(db, "userserviceproducts")
    
    from datetime import datetime, timedelta

    # Определяем период: последние 2 дня
    now = datetime.now()
    two_days_ago = now - timedelta(days=7)

    print(f"\nПериод проверки:")
    print(f"  С: {two_days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  По: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    latest_usps = list(
        usp_col.find({
            "isDeleted": False,
            "updated_at": {"$gte": two_days_ago}
        }).sort("updated_at", -1)
    )
    
    print(f"\nПолучено записей userserviceproducts: {len(latest_usps)}")
    
    if not latest_usps:
        print("Нет записей для проверки")
        return
    
    # Шаг 2: BATCH получение данных (оптимизация)
    tt_col = get_collection(db, "trainingtickets")
    hist_col = get_collection(db, "userserviceproductshistories")
    
    # Собираем все ID для batch-запроса
    usp_ids = [usp['_id'] for usp in latest_usps]
    
    print("\nПолучение данных из trainingtickets (batch)...")
    # Получаем количество билетов для всех userServiceProduct за один запрос
    tickets_pipeline = [
        {
            "$match": {
                "userServiceProduct": {"$in": usp_ids},
                "isUsed": False,
                "status": "active",
                "isDeleted": False
            }
        },
        {
            "$group": {
                "_id": "$userServiceProduct",
                "count": {"$sum": 1}
            }
        }
    ]
    tickets_counts = {doc['_id']: doc['count'] for doc in tt_col.aggregate(tickets_pipeline)}
    
    print("Получение данных из userserviceproductshistories (batch)...")
    # Получаем последние записи истории для всех userServiceProduct
    history_pipeline = [
        {
            "$match": {
                "userServiceProduct": {"$in": usp_ids}
            }
        },
        {
            "$sort": {"created_at": -1}
        },
        {
            "$group": {
                "_id": "$userServiceProduct",
                "lastRecord": {"$first": "$$ROOT"}
            }
        }
    ]
    history_counts = {
        doc['_id']: doc['lastRecord'].get('currentCount', 'N/A') 
        for doc in hist_col.aggregate(history_pipeline)
    }
    
    print("Анализ данных...")
    # Шаг 3: Анализируем результаты
    results = []
    
    for idx, usp in enumerate(latest_usps, start=1):
        usp_id = usp['_id']
        user_id = usp['user']
        initial_count = usp.get('initialCount', 'N/A')
        count = usp.get('count', 'N/A')
        updated_at = usp.get('updated_at', 'N/A')
        
        tickets_count = tickets_counts.get(usp_id, 0)
        hist_count = history_counts.get(usp_id, 'N/A')
        
        # Проверяем консистентность
        status = "OK"
        if count != 'N/A' and tickets_count != count:
            status = "FAIL"
        if count != 'N/A' and hist_count != 'N/A' and hist_count != count:
            status = "FAIL"
        if tickets_count != 'N/A' and hist_count != 'N/A' and tickets_count != hist_count:
            status = "FAIL"
        
        results.append({
            'idx': idx,
            'usp_id': str(usp_id),
            'user_id': str(user_id),
            'initial_count': initial_count,
            'count': count,
            'tickets_count': tickets_count,
            'hist_count': hist_count,
            'status': status,
            'updated_at': updated_at
        })
    
    # Статистика общая
    failed_count = sum(1 for r in results if r['status'] == 'FAIL')
    ok_count = sum(1 for r in results if r['status'] == 'OK')
    
    print(f"\nОбщая статистика:")
    print(f"  Всего проверено записей: {len(results)}")
    print(f"  OK:   {ok_count}")
    print(f"  FAIL: {failed_count}")
    
    # Выводим только записи с расхождениями
    if failed_count > 0:
        failed_records = [r for r in results if r['status'] == 'FAIL']
        
        print("\n" + "=" * 165)
        print("ЗАПИСИ С РАСХОЖДЕНИЯМИ:")
        print("=" * 165)
        print(f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} {'Tickets':<8} {'Hist':<5} {'Status':<7} {'Updated At':<22}")
        print("=" * 165)
        
        for r in failed_records:
            updated_str = r['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if r['updated_at'] != 'N/A' else 'N/A'
            
            print(f"{r['idx']:<4} {r['usp_id']:<26} {r['user_id']:<26} "
                  f"{str(r['initial_count']):<5} {str(r['count']):<6} "
                  f"{str(r['tickets_count']):<8} {str(r['hist_count']):<5} "
                  f"{r['status']:<7} {updated_str:<22}")
        
        print("=" * 165)
    else:
        print("\nВсе данные консистентны! Расхождений не обнаружено.")
    
    print("=" * 165)
    
    # Проверка: не должно быть расхождений
    assert failed_count == 0, f"Обнаружено {failed_count} записей с расхождениями данных между таблицами"

