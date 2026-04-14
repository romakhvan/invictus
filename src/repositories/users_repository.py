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

def get_user_role_by_phone(db, phone_from_ui: str):
    """
    Возвращает роль пользователя по номеру телефона (как отображается в UI или 10 цифр).

    phone_from_ui: номер с экрана (например "+7 700 123 45 64") или 10 цифр.
    Возвращает значение поля role из БД или None, если пользователь не найден.
    """
    phone_10 = _normalize_phone_to_10_digits(phone_from_ui)
    if not phone_10:
        return None
    users_col = db["users"]
    variants = [phone_10, "7" + phone_10, "+7" + phone_10]
    query = {"$or": [
        {"phone": {"$in": variants}},
        {"phoneNumber": {"$in": variants}},
    ]}
    user = users_col.find_one(query, {"role": 1})
    return user.get("role") if user else None


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


def _format_phone_for_display(phone_10_digits: str) -> str:
    """Форматирует 10 цифр номера в вид как в UI: +7 XXX XXX XX XX."""
    digits = "".join(c for c in phone_10_digits if c.isdigit())[-10:]
    if len(digits) != 10:
        return phone_10_digits
    return f"+7 {digits[0:3]} {digits[3:6]} {digits[6:8]} {digits[8:10]}"


# Условие выбора пользователя для тестов навигации (NEW_USER): potential с заполненным firstName
POTENTIAL_USER_QUERY = {
    "role": "potential",
    "firstName": {"$exists": True, "$ne": ""},
}


def get_phone_for_potential_user(db) -> str | None:
    """
    Возвращает номер телефона (10 цифр) пользователя с role: 'potential' и полем firstName.

    Используется для тестов навигации: вход под существующим потенциальным клиентом
    без прохождения онбординга. Если таких пользователей нет — возвращает None.
    """
    users_col = db["users"]
    user = users_col.find_one(
        POTENTIAL_USER_QUERY,
        {"phone": 1, "phoneNumber": 1},
        sort=[("_id", -1)],
    )
    if not user:
        return None
    raw = user.get("phone") or user.get("phoneNumber")
    return _normalize_phone_to_10_digits(raw)


def _get_phone_for_user_id(db, user_id) -> str | None:
    """Возвращает номер телефона пользователя по его _id."""
    if user_id is None:
        return None

    users_col = db["users"]
    user = users_col.find_one({"_id": user_id}, {"phone": 1, "phoneNumber": 1})
    if not user:
        return None

    raw = user.get("phone") or user.get("phoneNumber")
    return _normalize_phone_to_10_digits(raw)


def get_phone_for_active_subscription_user(db) -> str | None:
    """
    Возвращает телефон пользователя с активной подпиской.

    Подходит для подготовки состояния HomeState.SUBSCRIBED.
    """
    subscription = db["usersubscriptions"].find_one(
        {
            "isActive": True,
            "isDeleted": False,
            "kid": {"$exists": False},
        },
        {"user": 1},
        sort=[("_id", -1)],
    )
    if not subscription:
        return None
    return _get_phone_for_user_id(db, subscription.get("user"))


def get_phone_for_active_service_product_user(db) -> str | None:
    """
    Возвращает телефон пользователя с активным service product.

    Используется как best-effort кандидат для состояния HomeState.MEMBER.
    """
    service_product = db["userserviceproducts"].find_one(
        {
            "isActive": True,
            "isDeleted": False,
            "child": {"$exists": False},
        },
        {"user": 1},
        sort=[("_id", -1)],
    )
    if not service_product:
        return None
    return _get_phone_for_user_id(db, service_product.get("user"))


def get_phone_for_coach_user(db) -> str | None:
    """
    Возвращает телефон пользователя, у которого есть запись в коллекции coaches.

    Используется для подготовки coach-сценариев, если приложение показывает выбор режима.
    """
    coach = db["coaches"].find_one(
        {
            "isDeleted": False,
            "user": {"$exists": True},
        },
        {"user": 1},
        sort=[("_id", -1)],
    )
    if not coach:
        return None
    return _get_phone_for_user_id(db, coach.get("user"))


def get_user_display_info_by_phone(db, phone_from_ui: str) -> dict | None:
    """
    Возвращает имя и номер в формате для UI по номеру телефона (как на экране).

    Используется для сверки профиля: данные на экране сравниваются с тем же пользователем в БД.
    Возвращает None, если пользователь с таким номером не найден.
    """
    phone_10 = _normalize_phone_to_10_digits(phone_from_ui)
    if not phone_10:
        return None
    users_col = db["users"]
    variants = [phone_10, "7" + phone_10, "+7" + phone_10]
    query = {"$or": [
        {"phone": {"$in": variants}},
        {"phoneNumber": {"$in": variants}},
    ]}
    user = users_col.find_one(query, {"fullName": 1, "firstName": 1, "role": 1, "phone": 1, "phoneNumber": 1})
    if not user:
        return None
    raw_phone = user.get("phone") or user.get("phoneNumber")
    phone_10 = _normalize_phone_to_10_digits(raw_phone)
    return {
        "fullName": (user.get("fullName") or "").strip(),
        "firstName": (user.get("firstName") or "").strip(),
        "role": (user.get("role") or "").strip(),
        "phone_display": _format_phone_for_display(phone_10) if phone_10 else "",
    }


def get_potential_user_display_info(db) -> dict | None:
    """
    Возвращает имя и номер телефона в формате для сравнения с UI профиля.

    Выбирается пользователь с role: 'potential' и полем firstName (последний по _id).
    Для сверки по номеру с экрана используйте get_user_display_info_by_phone(db, phone_ui).
    Возвращает None, если подходящего пользователя нет.
    """
    users_col = db["users"]
    user = users_col.find_one(
        POTENTIAL_USER_QUERY,
        {"fullName": 1, "firstName": 1, "phone": 1, "phoneNumber": 1},
        sort=[("_id", -1)],
    )
    if not user:
        return None
    raw_phone = user.get("phone") or user.get("phoneNumber")
    phone_10 = _normalize_phone_to_10_digits(raw_phone)
    return {
        "fullName": (user.get("fullName") or "").strip(),
        "firstName": (user.get("firstName") or "").strip(),
        "phone_display": _format_phone_for_display(phone_10) if phone_10 else "",
    }


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
