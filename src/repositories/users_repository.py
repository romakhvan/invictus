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
    print(f"[INFO] Найдено пользователей с ДР {target_day:02d}.{target_month:02d}: {len(birthday_users)}")

    return birthday_users

def user_exists_by_phone(db, phone_digits: str) -> bool:
    """
    Проверяет, есть ли в БД пользователь с указанным номером телефона.
    phone_digits: 10 цифр без кода страны (например "7001234564").
    Возвращает True, если пользователь найден.
    """
    users_col = db["users"]
    digits_only = "".join(c for c in phone_digits if c.isdigit())
    if len(digits_only) < 10:
        return False
    # Варианты хранения: +77001234564, 77001234564, 7001234564
    suffix = digits_only[-10:]  # последние 10 цифр
    variants = [
        suffix,
        "7" + suffix,
        "+7" + suffix,
    ]
    query = {"$or": [
        {"phone": {"$in": variants}},
        {"phoneNumber": {"$in": variants}},
    ]}
    return users_col.count_documents(query) > 0


def _normalize_phone_to_10_digits(phone_value) -> str | None:
    """Извлекает 10 цифр номера из значения phone/phoneNumber в БД."""
    if phone_value is None:
        return None
    digits = "".join(c for c in str(phone_value) if c.isdigit())
    if len(digits) < 10:
        return None
    return digits[-10:]


def get_phone_for_potential_user(db) -> str | None:
    """
    Возвращает номер телефона (10 цифр) любого пользователя с role: 'potential'.

    Используется для тестов навигации: вход под существующим потенциальным клиентом
    без прохождения онбординга. Если таких пользователей нет — возвращает None.
    """
    users_col = db["users"]
    user = users_col.find_one(
        {"role": "potential"},
        {"phone": 1, "phoneNumber": 1},
        sort=[("_id", -1)],
    )
    if not user:
        return None
    raw = user.get("phone") or user.get("phoneNumber")
    return _normalize_phone_to_10_digits(raw)


def get_available_test_phone(
    db,
    base_phone: str = "7001234564",
    max_attempts: int = 100,
) -> str | None:
    """
    Ищет номер телефона (10 цифр), которого ещё нет в БД.
    Перебирает base_phone, base_phone+1, +2, ... до max_attempts.
    Возвращает первый свободный номер или None, если не найден.
    """
    digits_only = "".join(c for c in base_phone if c.isdigit())
    if len(digits_only) < 10:
        return None
    base = int(digits_only[-10:])  # последние 10 цифр как число
    prefix = digits_only[:-10] if len(digits_only) > 10 else ""
    for i in range(max_attempts):
        candidate = (base + i) % 10**10
        phone_str = f"{prefix}{candidate:010d}"[-10:]
        if not user_exists_by_phone(db, phone_str):
            return phone_str
    return None


def find_users_without_gender(db, created_at):
    """
    🎂 Возвращает пользователей, у которых нет пола
    """
    users_col = db["users"]
    query = {
        "created_at": {"$gte": created_at},
        "gender": {"$exists": False},
        "role": {"$nin": ["potential", "guest"]}
    }
    projection = {"_id": 1, "fullName": 1}
    users_without_gender = list(users_col.find(query, projection))
    print(f"[INFO] Найдено пользователей без пола: {len(users_without_gender)}")
    return users_without_gender