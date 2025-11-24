import pymongo
import pprint
from datetime import datetime, timedelta
from collections import Counter
from bson import ObjectId
from src.utils.debug_utils import log_function_call

@log_function_call
def find_users_with_active_subscription(db, user_ids):
    """
    🟢 Возвращает пользователей из списка user_ids, у которых есть активная подписка.
    Условие: isActive = True, isDeleted = False.
    """
    subs_col = db["usersubscriptions"]

    subs = list(subs_col.find(
        {
            "user": {"$in": user_ids},
            "isActive": True,
            "isDeleted": False
        },
        {"user": 1}
    ))

    active_user_ids = {s["user"] for s in subs}
    print(f"🟢 Активные подписки найдены у {len(active_user_ids)} пользователей.")

    return active_user_ids
@log_function_call
def get_new_subscriptions(db, target_date, days=7):
  

    """
    🔍 Возвращает всех пользователей, у которых появилась подписка за последние `days` дней
    относительно даты target_date.
    (включает и тех, у кого это не первая подписка)
    """
    subs_col = db["usersubscriptions"]

    start_date = target_date - timedelta(days=days)
    end_date = target_date
    print(f"📅 ===Поиск всех новых абонементов с {start_date} по {end_date} ===")
    # Ищем подписки, созданные за период
    new_subs = list(subs_col.find(
        {
            "isDeleted": False,
            "created_at": {"$gte": start_date, "$lte": end_date},
            "kid": {"$exists": False},
            "$expr": {
                "$gt": [
                    {"$divide": [{"$subtract": ["$endDate", "$startDate"]}, 1000 * 60 * 60 * 24]},
                    1  # больше 1 дня
                ]
            }
        },
        {"_id": 1, "user": 1, "startDate": 1, "endDate": 1, "created_at": 1}
    ))


    print(f"🔎 Найдено новых подписок: {len(new_subs)}")

    # Пользователи с несколькими подписками
    """
    repeated_users = [user for user, count in user_counts.items() if count > 1]

    if repeated_users:
        print(f"⚠️ Найдено {len(repeated_users)} пользователей с повторными подписками за неделю:")
        pprint.pprint(repeated_users[:20])  # первые 20 для примера
    else:
        print("✅ Повторяющихся пользователей за этот период нет.")
    """
    # Возвращаем уникальные user_id
    new_user_ids = {s["user"] for s in new_subs}
    print(f"👥 Уникальных пользователей: {len(new_user_ids)}")
    

    return list(new_user_ids)

@log_function_call
def get_first_time_subscribers(db, target_date, days=7):
    """
    🆕 Возвращает пользователей, у которых появилась первая подписка за последние `days` дней
    относительно даты target_date.
    Исключает тех, у кого были подписки раньше.
    """
    users_col = db["users"]
    subs_col = db["usersubscriptions"]

    print("\n=== Поиск: у кого первый абонемент ===")

    # 1️⃣ Получаем всех, кто купил подписку за неделю
    new_user_ids = set(get_new_subscriptions(db, target_date, days))
    if not new_user_ids:
        print("⚠️ За этот период не найдено новых подписок.")
        return []

    start_date = target_date - timedelta(days=days)

    # 2️⃣ Проверяем, были ли подписки ранее
    old_subs = list(subs_col.find(
        {
            "user": {"$in": list(new_user_ids)},
            "created_at": {"$lt": start_date},
            "isDeleted": False
        },
        {"user": 1}
    ))

    old_user_ids = {s["user"] for s in old_subs}
    truly_new_user_ids = new_user_ids - old_user_ids

    print(f"🧹 Исключено пользователей с предыдущими подписками: {len(old_user_ids)}")
    print(f"✅ Осталось пользователей с первой подпиской: {len(truly_new_user_ids)}")

    # 3️⃣ Получаем данные пользователей
    users = list(users_col.find(
        {"_id": {"$in": list(truly_new_user_ids)}},
        {"_id": 1, "name": 1, "email": 1, "created_at": 1}
    ))

    # print(f"📊 Подробности по первым 10 пользователям:")
    # pprint.pprint(users[:10])
    return users

  


def find_last_10_subscriptions_with_big_gap(db, months=3):
    """
    🔍 Находит последние 10 подписок, у которых разница между created_at и startDate > N месяцев.
    """
    subs_col = db["usersubscriptions"]

    # 1️⃣ Рассчитываем разницу в миллисекундах (примерно 30 дней в месяце)
    days = months * 30
    ms_threshold = days * 24 * 60 * 60 * 1000  # миллисекунды

    print(f"📅 Поиск последних 10 подписок с разницей > {days} дней между created_at и startDate")

    # 2️⃣ Агрегация
    pipeline = [
        {
            "$addFields": {
                "diffMs": {"$subtract": ["$startDate", "$created_at"]}
            }
        },
        {
            "$match": {
                "diffMs": {"$gt": ms_threshold},
                "isDeleted": False
            }
        },
        {
            "$project": {
                "_id": 1,
                "user": 1,
                "created_at": 1,
                "startDate": 1,
                "diffDays": {"$divide": ["$diffMs", 1000 * 60 * 60 * 24]}
            }
        },
        {"$sort": {"created_at": -1}},  # последние по дате создания
        {"$limit": 100}
    ]

    # 3️⃣ Выполняем запрос
    results = list(subs_col.aggregate(pipeline))
    print(f"🔎 Найдено подписок с разницей > {days} дней: {len(results)}")

    if results:
        print("\n📋 Последние 10 подписок с большой разницей дат:")
        for r in results:
            print(
                f"🆔 {r['_id']} | {r['user']} | "
                f"created_at={r['created_at']} | startDate={r['startDate']} | "
                f"⏱ {round(r['diffDays'])} дней"
            )
    else:
        print("⚠️ Подписок с такой разницей не найдено.")

    return results