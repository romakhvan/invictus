from datetime import datetime, timedelta
import re


def _aggregate_batch_users(col, query, projection, description_label="пуша"):
    """
    Находит самый свежий документ по query, затем берёт все языковые варианты
    того же батча (±2 часа) и агрегирует toUsers по ним.

    Возвращает (user_ids, created_at, title, text) или ([], None, None, None).
    """
    # Самый свежий документ → определяет время батча
    latest = col.find_one(query, projection, sort=[("created_at", -1)])
    if not latest:
        return [], None, None, None

    batch_time = latest["created_at"]
    window_start = batch_time - timedelta(hours=2)
    window_end = batch_time + timedelta(hours=2)

    # Все языковые версии одного батча
    batch_query = dict(query)
    batch_query["created_at"] = {"$gte": window_start, "$lte": window_end}
    docs = list(col.find(batch_query, projection))

    all_user_ids = set()
    for d in docs:
        for uid in d.get("toUsers", []):
            all_user_ids.add(str(uid))

    descriptions = ", ".join(d.get("description", "") for d in docs)
    print(f"[INFO] Языковых версий {description_label}: {len(docs)} ({descriptions})")
    print(f"[INFO] Итого уникальных получателей: {len(all_user_ids)}")

    return list(all_user_ids), batch_time, latest.get("title"), latest.get("text")


def _build_regex_condition(value: str) -> dict:
    """
    Строит Mongo regex condition.
    `regex:<pattern>` трактуется как намеренный regex, все остальные строки экранируются как literal.
    """
    pattern = value[len("regex:"):] if isinstance(value, str) and value.startswith("regex:") else re.escape(value)
    return {"$regex": pattern, "$options": "i"}


def get_user_ids_with_birthday_message(db, search_text, days, limit):
    """
    Возвращает пользователей, дату создания, title и text уведомления.
    Агрегирует toUsers по всем языковым версиям одного батча ([RU], [KY], [EN] и т.д.).
    """
    col = db["notifications"]
    time_ago = datetime.now() - timedelta(days=days)

    query = {
        "created_at": {"$gte": time_ago},
        "description": _build_regex_condition(search_text),
    }
    projection = {"_id": 1, "created_at": 1, "description": 1, "title": 1, "text": 1, "toUsers": 1}

    return _aggregate_batch_users(col, query, projection, description_label="birthday пуша")


def get_user_ids_with_welcome_message(db, description, title, text, days, limit):
    """
    Возвращает пользователей, дату создания, title и text уведомления.
    Агрегирует toUsers по всем языковым версиям одного батча ([RU], [EN], [KK] и т.д.).
    """
    col = db["notifications"]

    time_ago = datetime.now() - timedelta(days=days)

    query = {"created_at": {"$gte": time_ago}}

    if description:
        query["description"] = _build_regex_condition(description)
    if title:
        query["title"] = _build_regex_condition(title)
    if text:
        query["text"] = _build_regex_condition(text)

    projection = {"_id": 1, "created_at": 1, "description": 1, "title": 1, "text": 1, "toUsers": 1}

    return _aggregate_batch_users(col, query, projection, description_label="welcome/inactive пуша")
