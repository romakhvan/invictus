from src.utils.debug_utils import log_function_call

@log_function_call
def find_users_with_birthday(db, target_date):
    """
    🎂 Возвращает пользователей, у которых день рождения совпадает с указанной датой (день и месяц).
    """
    users_col = db["users"]

    target_day = target_date.day
    target_month = target_date.month

    birthday_query = {
        "$expr": {
            "$and": [
                {"$eq": [{"$dayOfMonth": "$birthDate"}, target_day]},
                {"$eq": [{"$month": "$birthDate"}, target_month]},
            ]
        }
    }

    projection = {"_id": 1, "birthDate": 1, "fullName": 1}

    birthday_users = list(users_col.find(birthday_query, projection))
    print(f"🎂 Найдено пользователей с ДР {target_day:02d}.{target_month:02d}: {len(birthday_users)}")

    return birthday_users