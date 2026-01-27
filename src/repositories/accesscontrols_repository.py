from collections import Counter
from pprint import pprint
from src.utils.debug_utils import log_function_call
from datetime import datetime, timedelta

@log_function_call
def get_user_access_stats(
    db,
    user_ids,
    start_date=None,
    end_date=None,
    include_subscriptions_only=False,
    mode="count"
):
    access_col = db["accesscontrols"]
    
    # Если start_date не передан, но передан end_date, используем 7 дней по умолчанию
    if start_date is None and end_date is not None:
        start_date = end_date - timedelta(days=7)

    if not user_ids:
        print("⚠️ Список пользователей пуст.")
        return {} if mode == "count" else []

    query = {"user": {"$in": user_ids}}
    if include_subscriptions_only:
        query["accessType"] = "subscription"

    if start_date or end_date:
        query["time"] = {}
        if start_date:
            query["time"]["$gte"] = start_date
        if end_date:
            query["time"]["$lte"] = end_date

    print(f"[CHECK] Проверка входов с {start_date or 'начала времён'} по {end_date or 'сейчас'}")
    print(f"[INFO] Пользователей: {len(user_ids)}")

    entries = list(access_col.find(query, {"_id": 1, "user": 1, "time": 1}))
    print(f"[INFO] Найдено входов: {len(entries)}")

    if mode == "count":
        user_counts = Counter(str(e["user"]) for e in entries)
        pprint(dict(user_counts))
        return dict(user_counts)

    
    users_with_entries = {e["user"] for e in entries}
    users_without_entries = [u for u in user_ids if u not in users_with_entries]


    print(f"[OK] Пользователей с входами: {len(users_with_entries)}")
    print(f"[INFO] Пользователей без входов: {len(users_without_entries)}")

    if mode == "users_with_entries":
        return list(users_with_entries)
    elif mode == "users_without_entries":
        return list(users_without_entries)
    else:
        raise ValueError("[ERROR] mode должен быть одним из: 'count', 'users_with_entries', 'users_without_entries'")


@log_function_call
def get_users_without_entries_since_subscription(
    db, 
    user_subscriptions, 
    end_date, 
    min_last_entry_days=None,
    max_last_entry_days=None
):
    """
    Проверяет, какие пользователи НЕ были в клубе с момента покупки подписки.
    
    Args:
        db: База данных MongoDB
        user_subscriptions: dict {user_id: created_at} - пользователи и даты покупки подписок
        end_date: Конечная дата проверки (обычно дата отправки пуша)
        min_last_entry_days: Минимальное количество дней с последнего входа
                            Исключает пользователей, которые были в клубе слишком недавно
        max_last_entry_days: Максимальное количество дней с последнего входа
                            Исключает пользователей, которые не были в клубе слишком долго
    
    Returns:
        list: Список user_id пользователей без входов
    """
    access_col = db["accesscontrols"]
    
    if not user_subscriptions:
        print("[WARNING] Список пользователей с подписками пуст.")
        return []
    
    print(f"[CHECK] Проверка входов для каждого пользователя с момента покупки подписки до {end_date}")
    if min_last_entry_days:
        print(f"[FILTER] Фильтр: последний вход не менее {min_last_entry_days} дней назад")
    if max_last_entry_days:
        print(f"[FILTER] Фильтр: последний вход не более {max_last_entry_days} дней назад")
    print(f"[INFO] Пользователей для проверки: {len(user_subscriptions)}")
    
    users_without_entries = []
    users_with_entries = []
    users_too_long_inactive = []
    users_too_recently_active = []
    
    # Проверяем каждого пользователя индивидуально
    for user_id, subscription_date in user_subscriptions.items():
        # 1. Проверяем входы с момента покупки подписки
        query_since_sub = {
            "user": user_id,
            "time": {
                "$gte": subscription_date,
                "$lte": end_date
            }
        }
        
        entry_since_sub = access_col.find_one(query_since_sub, {"_id": 1})
        
        if entry_since_sub is not None:
            # Был в клубе после покупки подписки
            users_with_entries.append(user_id)
            continue
        
        # 2. Если указаны фильтры по последнему входу, проверяем
        if min_last_entry_days or max_last_entry_days:
            # Ищем последний вход пользователя (в любое время)
            last_entry = access_col.find_one(
                {"user": user_id, "time": {"$lte": end_date}},
                {"time": 1},
                sort=[("time", -1)]
            )
            
            if last_entry:
                last_entry_time = last_entry.get("time")
                
                if last_entry_time:
                    days_since_last_entry = (end_date - last_entry_time).days
                    
                    # Проверка: последний вход был слишком недавно
                    if min_last_entry_days and days_since_last_entry < min_last_entry_days:
                        users_too_recently_active.append(user_id)
                        continue
                    
                    # Проверка: последний вход был слишком давно
                    if max_last_entry_days and days_since_last_entry > max_last_entry_days:
                        users_too_long_inactive.append(user_id)
                        continue
        
        # Пользователь не был после покупки подписки и прошел все фильтры
        users_without_entries.append(user_id)
    
    print(f"✅ Пользователей с входами (после покупки): {len(users_with_entries)}")
    print(f"🚫 Пользователей без входов: {len(users_without_entries)}")
    
    if min_last_entry_days:
        print(f"⏰ Исключено: последний вход < {min_last_entry_days} дней назад (слишком недавно): {len(users_too_recently_active)}")
    if max_last_entry_days:
        print(f"⏰ Исключено: последний вход > {max_last_entry_days} дней назад (слишком давно): {len(users_too_long_inactive)}")
    
    return users_without_entries
