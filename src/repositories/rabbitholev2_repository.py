from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import get_collection
from src.utils.id_utils import normalize_object_ids


@log_function_call
def get_rabbitholev2_subscriptions_by_user(
    db,
    user_id: Any,
    days: int = 14
) -> List[Dict[str, Any]]:
    """
    Получает записи из rabbitholev2 созданные за последние N дней для указанного пользователя,
    и находит связанные usersubscriptions.
    
    Args:
        db: База данных MongoDB
        user_id: ID пользователя
        days: Количество дней для поиска (по умолчанию 14)
    
    Returns:
        Список словарей с информацией о подписках:
        {
            "rabbithole_id": str,
            "rabbithole_created_at": datetime,
            "subscriptions": [
                {
                    "id": str,
                    "startDate": datetime,
                    "endDate": datetime,
                    "createdAt": datetime,
                    "subscriptionId": str,
                    "purchasedPrice": float
                }
            ]
        }
    """
    rabbithole_col = get_collection(db, "rabbitholev2")
    subs_col = get_collection(db, "usersubscriptions")
    
    # Нормализуем user_id
    normalized_ids = normalize_object_ids([user_id])
    if not normalized_ids:
        print(f"⚠️ Не удалось нормализовать user_id: {user_id}")
        return []
    
    user_object_id = normalized_ids[0]
    
    # Ищем записи в rabbitholev2 за последние N дней
    start_date = datetime.now() - timedelta(days=days)
    
    query = {
        "user": user_object_id,
        "created_at": {"$gte": start_date}
    }
    
    rabbithole_docs = list(rabbithole_col.find(query).sort("created_at", -1))
    
    if not rabbithole_docs:
        print(f"\n❌ Записи в rabbitholev2 для user_id {user_id} за последние {days} дней не найдены")
        return []
    
    print(f"\n✅ Найдено {len(rabbithole_docs)} записей в rabbitholev2 для user_id {user_id}")
    
    # Для каждого user_id ищем usersubscriptions
    subscriptions = list(subs_col.find({
        "user": user_object_id,
        "isDeleted": False
    }))
    
    print(f"✅ Найдено {len(subscriptions)} подписок для user_id {user_id}")
    
    # Формируем результат
    result = []
    for rh_doc in rabbithole_docs:
        subscriptions_data = []
        for sub in subscriptions:
            subscriptions_data.append({
                "id": str(sub.get("_id", "")),
                "startDate": sub.get("startDate"),
                "endDate": sub.get("endDate"),
                "createdAt": sub.get("created_at"),  # В usersubscriptions используется created_at
                "subscriptionId": str(sub.get("subscriptionId", "")) if sub.get("subscriptionId") else None,
                "purchasedPrice": sub.get("purchasedPrice")
            })
        
        result.append({
            "rabbithole_id": str(rh_doc.get("_id", "")),
            "rabbithole_created_at": rh_doc.get("created_at"),
            "user_id": str(user_id),
            "subscriptions": subscriptions_data
        })
    
    return result


@log_function_call
def get_all_rabbitholev2_subscriptions_last_14_days(
    db,
    days: int = 14
) -> List[Dict[str, Any]]:
    """
    Получает все записи из rabbitholev2 созданные за последние N дней,
    и для каждого user находит связанные usersubscriptions.
    
    Args:
        db: База данных MongoDB
        days: Количество дней для поиска (по умолчанию 14)
    
    Returns:
        Список словарей с информацией о подписках для каждого пользователя
    """
    rabbithole_col = get_collection(db, "rabbitholev2")
    subs_col = get_collection(db, "usersubscriptions")
    
    # Ищем записи в rabbitholev2 за последние N дней
    start_date = datetime.now() - timedelta(days=days)
    
    query = {
        "created_at": {"$gte": start_date}
    }
    
    rabbithole_docs = list(rabbithole_col.find(query).sort("created_at", -1))
    
    if not rabbithole_docs:
        print(f"\n❌ Записи в rabbitholev2 за последние {days} дней не найдены")
        return []
    
    print(f"\n✅ Найдено {len(rabbithole_docs)} записей в rabbitholev2 за последние {days} дней")
    
    # Собираем уникальные user_id
    user_ids = set()
    for doc in rabbithole_docs:
        user = doc.get("user")
        if user:
            user_ids.add(user)
    
    print(f"✅ Найдено {len(user_ids)} уникальных пользователей")
    
    # Для каждого user_id ищем usersubscriptions
    subscriptions_by_user = {}
    if user_ids:
        subscriptions = list(subs_col.find({
            "user": {"$in": list(user_ids)},
            "isDeleted": False
        }))
        
        # Группируем подписки по пользователям
        for sub in subscriptions:
            user = sub.get("user")
            if user not in subscriptions_by_user:
                subscriptions_by_user[user] = []
            subscriptions_by_user[user].append(sub)
    
    # Формируем результат
    result = []
    for rh_doc in rabbithole_docs:
        user = rh_doc.get("user")
        if not user:
            continue
        
        subscriptions_data = []
        if user in subscriptions_by_user:
            for sub in subscriptions_by_user[user]:
                subscriptions_data.append({
                    "id": str(sub.get("_id", "")),
                    "startDate": sub.get("startDate"),
                    "endDate": sub.get("endDate"),
                    "createdAt": sub.get("created_at"),
                    "subscriptionId": str(sub.get("subscriptionId", "")) if sub.get("subscriptionId") else None,
                    "purchasedPrice": sub.get("purchasedPrice")
                })
        
        result.append({
            "rabbithole_id": str(rh_doc.get("_id", "")),
            "rabbithole_created_at": rh_doc.get("created_at"),
            "user_id": str(user),
            "subscriptions": subscriptions_data
        })
    
    return result


def display_rabbitholev2_subscriptions(result: List[Dict[str, Any]]):
    """
    Выводит информацию о найденных подписках в удобном формате.
    
    Args:
        result: Результат работы get_rabbitholev2_subscriptions_by_user или 
                get_all_rabbitholev2_subscriptions_last_14_days
    """
    if not result:
        print("\n❌ Нет данных для отображения")
        return
    
    print("\n" + "=" * 80)
    print("Результаты поиска подписок")
    print("=" * 80)
    
    for i, item in enumerate(result, 1):
        print(f"\n📋 Запись #{i}")
        print(f"   RabbitHole ID: {item.get('rabbithole_id')}")
        print(f"   User ID: {item.get('user_id')}")
        print(f"   RabbitHole created_at: {item.get('rabbithole_created_at')}")
        
        subscriptions = item.get("subscriptions", [])
        if subscriptions:
            print(f"   Подписок найдено: {len(subscriptions)}")
            for j, sub in enumerate(subscriptions, 1):
                print(f"\n   Подписка #{j}:")
                print(f"      id: {sub.get('id')}")
                print(f"      startDate: {sub.get('startDate')}")
                print(f"      endDate: {sub.get('endDate')}")
                print(f"      createdAt: {sub.get('createdAt')}")
                print(f"      subscriptionId: {sub.get('subscriptionId')}")
                print(f"      purchasedPrice: {sub.get('purchasedPrice')}")
        else:
            print(f"   ⚠️ Подписки не найдены")
        print()

