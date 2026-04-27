from bson import ObjectId

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

def get_user_id_by_phone(db, phone_from_ui: str):
    """
    Возвращает _id пользователя по номеру телефона (как отображается в UI или 10 цифр).

    Возвращает None, если пользователь не найден.
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
    user = users_col.find_one(query, {"_id": 1})
    return user.get("_id") if user else None


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


def _object_id_or_none(value):
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    return None


def _identity_values(value) -> list:
    values = []
    if value is not None:
        values.append(value)
    object_id = _object_id_or_none(value)
    if object_id is not None and object_id not in values:
        values.append(object_id)
    return values


def _identity_query(field_name: str, value) -> dict:
    values = _identity_values(value)
    if not values:
        return {field_name: value}
    return {field_name: {"$in": values}}


def _linked_user_query(user_id) -> dict:
    values = _identity_values(user_id)
    return {"$or": [{"user": {"$in": values}}, {"userId": {"$in": values}}]}


def _is_excluded_user_id(user_id, excluded_user_ids) -> bool:
    excluded = {str(value) for value in excluded_user_ids or () if value is not None}
    return str(user_id) in excluded


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


def get_phone_for_potential_user(db, excluded_user_ids=None) -> str | None:
    """
    Возвращает номер телефона (10 цифр) пользователя с role: 'potential',
    заполненным firstName и записью в usermetadatas.

    Используется для тестов навигации: вход под существующим потенциальным клиентом
    без прохождения онбординга. Если таких пользователей нет — возвращает None.
    """
    users_col = db["users"]
    usermetadatas_col = db["usermetadatas"]
    excluded_user_ids = set(excluded_user_ids or ())

    candidate_cursor = users_col.find(
        POTENTIAL_USER_QUERY,
        {"phone": 1, "phoneNumber": 1},
        sort=[("_id", -1)],
    )

    batch: list[dict] = []
    for user in candidate_cursor:
        if user.get("_id") and not _is_excluded_user_id(user.get("_id"), excluded_user_ids):
            batch.append(user)
        if len(batch) >= 100:
            phone = _select_potential_user_phone_from_batch(db, batch, usermetadatas_col)
            if phone:
                return phone
            batch = []

    if batch:
        return _select_potential_user_phone_from_batch(db, batch, usermetadatas_col)

    return None


def _select_potential_user_phone_from_batch(
    db,
    users: list[dict],
    usermetadatas_col,
) -> str | None:
    user_ids = [user["_id"] for user in users if user.get("_id")]
    if not user_ids:
        return None

    metadata_user_ids = _linked_user_ids(
        usermetadatas_col.find(
            {"$or": [{"user": {"$in": user_ids}}, {"userId": {"$in": user_ids}}]},
            {"user": 1, "userId": 1},
        )
    )
    if not metadata_user_ids:
        return None

    related_user_ids = set()
    for collection_name in (
        "rabbitholev2",
        "visits",
        "usersubscriptions",
        "accesscontrols",
    ):
        related_user_ids.update(
            _linked_user_ids(
                db[collection_name].find(
                    {
                        "$or": [
                            {"user": {"$in": user_ids}},
                            {"userId": {"$in": user_ids}},
                        ]
                    },
                    {"user": 1, "userId": 1},
                )
            )
        )

    for user in users:
        user_id = user.get("_id")
        if user_id not in metadata_user_ids or user_id in related_user_ids:
            continue
        raw = user.get("phone") or user.get("phoneNumber")
        phone = _normalize_phone_to_10_digits(raw)
        if phone:
            return phone

    return None


def _linked_user_ids(docs) -> set:
    user_ids = set()
    for doc in docs:
        for field in ("user", "userId"):
            value = doc.get(field)
            if value is not None:
                user_ids.add(value)
    return user_ids


def _has_related_user_records(db, user_id, collection_names: tuple[str, ...]) -> bool:
    query = {"$or": [{"user": user_id}, {"userId": user_id}]}
    for collection_name in collection_names:
        if db[collection_name].count_documents(query) > 0:
            return True
    return False


def _user_phone_matches(db, user_id, phone: str) -> tuple[bool, str | None]:
    user = db["users"].find_one(
        _identity_query("_id", user_id),
        {"phone": 1, "phoneNumber": 1, "role": 1, "firstName": 1},
    )
    if not user:
        return False, "user not found"
    expected_phone = _normalize_phone_to_10_digits(phone)
    actual_phone = _normalize_phone_to_10_digits(user.get("phone") or user.get("phoneNumber"))
    if expected_phone and actual_phone != expected_phone:
        return False, "phone mismatch"
    return True, None


def validate_potential_test_user(db, user_id, phone: str) -> tuple[bool, str | None]:
    user = db["users"].find_one(
        _identity_query("_id", user_id),
        {"phone": 1, "phoneNumber": 1, "role": 1, "firstName": 1},
    )
    if not user:
        return False, "user not found"
    expected_phone = _normalize_phone_to_10_digits(phone)
    actual_phone = _normalize_phone_to_10_digits(user.get("phone") or user.get("phoneNumber"))
    if expected_phone and actual_phone != expected_phone:
        return False, "phone mismatch"
    if user.get("role") != "potential":
        return False, "role is not potential"
    if not (user.get("firstName") or "").strip():
        return False, "firstName is empty"

    metadata = db["usermetadatas"].find_one(_linked_user_query(user_id), {"_id": 1})
    if not metadata:
        return False, "usermetadatas record not found"

    for collection_name in ("rabbitholev2", "visits", "usersubscriptions", "accesscontrols"):
        if db[collection_name].find_one(_linked_user_query(user_id), {"_id": 1}):
            return False, f"{collection_name} related record exists"

    return True, None


def validate_subscribed_test_user(db, user_id, phone: str) -> tuple[bool, str | None]:
    phone_ok, reason = _user_phone_matches(db, user_id, phone)
    if not phone_ok:
        return False, reason
    subscription = db["usersubscriptions"].find_one(
        {
            "user": {"$in": _identity_values(user_id)},
            "isActive": True,
            "isDeleted": False,
            "kid": {"$exists": False},
        },
        {"_id": 1},
    )
    return (True, None) if subscription else (False, "active subscription not found")


def validate_member_test_user(db, user_id, phone: str) -> tuple[bool, str | None]:
    phone_ok, reason = _user_phone_matches(db, user_id, phone)
    if not phone_ok:
        return False, reason
    service_product = db["userserviceproducts"].find_one(
        {
            "user": {"$in": _identity_values(user_id)},
            "isActive": True,
            "isDeleted": False,
            "child": {"$exists": False},
        },
        {"_id": 1},
    )
    return (True, None) if service_product else (False, "active service product not found")


def validate_rabbit_hole_test_user(db, user_id, phone: str) -> tuple[bool, str | None]:
    phone_ok, reason = _user_phone_matches(db, user_id, phone)
    if not phone_ok:
        return False, reason
    visits_count = db["visits"].count_documents(
        {
            "user": {"$in": _identity_values(user_id)},
            "type": "visit",
            "source": "rabbit",
            "isActive": True,
            "isDeleted": False,
            "isExpired": False,
        }
    )
    if visits_count < 3:
        return False, "less than 3 active rabbit visits"
    active_subscription_count = db["usersubscriptions"].count_documents(
        {
            "user": {"$in": _identity_values(user_id)},
            "isActive": True,
            "isDeleted": False,
        }
    )
    if active_subscription_count:
        return False, "active subscription exists"
    return True, None


def validate_coach_test_user(db, user_id, phone: str) -> tuple[bool, str | None]:
    phone_ok, reason = _user_phone_matches(db, user_id, phone)
    if not phone_ok:
        return False, reason
    coach = db["coaches"].find_one(
        {
            "user": {"$in": _identity_values(user_id)},
            "isDeleted": False,
        },
        {"_id": 1},
    )
    return (True, None) if coach else (False, "coach record not found")


def _get_phone_for_user_id(db, user_id) -> str | None:
    """Возвращает номер телефона пользователя по его _id."""
    if user_id is None:
        return None

    users_col = db["users"]
    user = users_col.find_one(_identity_query("_id", user_id), {"phone": 1, "phoneNumber": 1})
    if not user:
        return None

    raw = user.get("phone") or user.get("phoneNumber")
    return _normalize_phone_to_10_digits(raw)


def get_phone_for_active_subscription_user(db, excluded_user_ids=None) -> str | None:
    """
    Возвращает телефон пользователя с активной подпиской.

    Подходит для подготовки состояния HomeState.SUBSCRIBED.
    """
    excluded_user_ids = set(excluded_user_ids or ())
    subscriptions = db["usersubscriptions"].find(
        {
            "isActive": True,
            "isDeleted": False,
            "kid": {"$exists": False},
        },
        {"user": 1},
        sort=[("_id", -1)],
    )
    for subscription in subscriptions:
        user_id = subscription.get("user")
        if _is_excluded_user_id(user_id, excluded_user_ids):
            continue
        phone = _get_phone_for_user_id(db, user_id)
        if phone:
            return phone
    return None


def get_phone_for_active_service_product_user(db, excluded_user_ids=None) -> str | None:
    """
    Возвращает телефон пользователя с активным service product.

    Используется как best-effort кандидат для состояния HomeState.MEMBER.
    """
    excluded_user_ids = set(excluded_user_ids or ())
    service_products = db["userserviceproducts"].find(
        {
            "isActive": True,
            "isDeleted": False,
            "child": {"$exists": False},
        },
        {"user": 1},
        sort=[("_id", -1)],
    )
    for service_product in service_products:
        user_id = service_product.get("user")
        if _is_excluded_user_id(user_id, excluded_user_ids):
            continue
        phone = _get_phone_for_user_id(db, user_id)
        if phone:
            return phone
    return None


def get_phone_for_coach_user(db, excluded_user_ids=None) -> str | None:
    """
    Возвращает телефон пользователя, у которого есть запись в коллекции coaches.

    Используется для подготовки coach-сценариев, если приложение показывает выбор режима.
    """
    excluded_user_ids = set(excluded_user_ids or ())
    coaches = db["coaches"].find(
        {
            "isDeleted": False,
            "user": {"$exists": True},
        },
        {"user": 1},
        sort=[("_id", -1)],
    )
    for coach in coaches:
        user_id = coach.get("user")
        if _is_excluded_user_id(user_id, excluded_user_ids):
            continue
        phone = _get_phone_for_user_id(db, user_id)
        if phone:
            return phone
    return None


def get_phone_for_active_rabbit_hole_user(db, excluded_user_ids=None) -> str | None:
    """
    Возвращает телефон пользователя с 3 активными Rabbit Hole visits и без активной подписки.

    Подходит для подготовки состояния HomeState.RABBIT_HOLE.
    """
    visits_col = db["visits"]
    subscriptions_col = db["usersubscriptions"]
    excluded_user_ids = set(excluded_user_ids or ())

    query = {
        "type": "visit",
        "source": "rabbit",
        "isActive": True,
        "isDeleted": False,
        "isExpired": False,
        "user": {"$exists": True},
    }
    projection = {"user": 1, "created_at": 1}

    counts_by_user = {}
    ordered_user_ids = []
    for visit in visits_col.find(query, projection).sort("created_at", -1):
        user_id = visit.get("user")
        if user_id is None:
            continue
        if user_id not in counts_by_user:
            counts_by_user[user_id] = 0
            ordered_user_ids.append(user_id)
        counts_by_user[user_id] += 1

    for user_id in ordered_user_ids:
        if _is_excluded_user_id(user_id, excluded_user_ids):
            continue
        if counts_by_user[user_id] < 3:
            continue
        active_subscription_count = subscriptions_col.count_documents(
            {
                "user": user_id,
                "isActive": True,
                "isDeleted": False,
            }
        )
        if active_subscription_count:
            continue
        phone = _get_phone_for_user_id(db, user_id)
        if phone:
            return phone

    return None


def get_user_display_info_by_user_id(db, user_id) -> dict | None:
    """
    Возвращает имя и номер в формате для UI по user_id.

    Используется, когда user_id уже известен и не нужно повторно искать пользователя по номеру.
    Возвращает None, если пользователь не найден.
    """
    if user_id is None:
        return None

    users_col = db["users"]
    user = users_col.find_one(
        _identity_query("_id", user_id),
        {"fullName": 1, "firstName": 1, "role": 1, "phone": 1, "phoneNumber": 1},
    )
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
