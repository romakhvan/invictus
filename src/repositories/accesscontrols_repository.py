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

    print(f"📅 Проверка входов с {start_date or 'начала времён'} по {end_date or 'сейчас'}")
    print(f"👥 Пользователей: {len(user_ids)}")

    entries = list(access_col.find(query, {"_id": 1, "user": 1, "time": 1}))
    print(f"🔎 Найдено входов: {len(entries)}")

    if mode == "count":
        user_counts = Counter(str(e["user"]) for e in entries)
        pprint(dict(user_counts))
        return dict(user_counts)

    
    users_with_entries = {e["user"] for e in entries}
    users_without_entries = [u for u in user_ids if u not in users_with_entries]


    print(f"✅ Пользователей с входами: {len(users_with_entries)}")
    print(f"🚫 Пользователей без входов: {len(users_without_entries)}")

    if mode == "users_with_entries":
        return list(users_with_entries)
    elif mode == "users_without_entries":
        return list(users_without_entries)
    else:
        raise ValueError("❌ mode должен быть одним из: 'count', 'users_with_entries', 'users_without_entries'")
