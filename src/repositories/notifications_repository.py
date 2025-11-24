from datetime import datetime, timedelta



def get_user_ids_with_birthday_message(db, search_text, days, limit):
    """
    Возвращает пользователей, дату создания, title и text уведомления.
    """
    col = db["notifications"]
    today = datetime.now()
    time_ago = today - timedelta(days=days)

    query = {
        "created_at": {"$gte": time_ago},
        "description": {"$regex": search_text, "$options": "i"},
    }

    projection = {
        "_id": 1,
        "created_at": 1,
        "description": 1,
        "title": 1,
        "text": 1,
        "toUsers": 1,
        "type": 1,
        "reqPath": 1
    }

    docs = list(col.find(query, projection).sort("created_at", -1).limit(limit))
    if not docs:
        return [], None, None, None

    doc = docs[0]

    # не выводим toUsers, чтобы не засорять консоль
    doc_for_print = dict(doc)
    doc_for_print.pop("toUsers", None)
    # pprint.pprint(doc_for_print, sort_dicts=False, width=120)

    user_ids = [str(uid) for uid in doc.get("toUsers", [])]
    created_at = doc.get("created_at")
    title = doc.get("title")
    text = doc.get("text")

    return user_ids, created_at, title, text


def get_user_ids_with_welcome_message(db, description, title, text, days, limit):

    # 1️⃣ Берём коллекцию уведомлений
    col = db["notifications"]

    # 2️⃣ Определяем период поиска: от N дней назад до текущего момента
    today = datetime.now()
    time_ago = today - timedelta(days=days)

    # 3️⃣ Формируем фильтр для MongoDB
    query = {
        "created_at": {"$gte": time_ago},               # за последние N дней
        "title": {"$regex": title, "$options": "i"},  # текст содержит фразу (регистронезависимо)
        "description": {"$regex": description, "$options": "i"},  # текст содержит фразу (регистронезависимо)
    }

    # 4️⃣ Ограничиваем возвращаемые поля (чтобы не тянуть весь документ)
    projection = {
        "_id": 1,
        "created_at": 1,
        "description": 1,
        "title": 1,
        "text": 1,
        "toUsers": 1,
        "type": 1,
        "reqPath": 1
    }

    # 5️⃣ Выполняем запрос:
    #     - сортируем по убыванию даты (последние уведомления первыми),
    #     - ограничиваем количество найденных документов.
    docs = list(col.find(query, projection).sort("created_at", -1).limit(limit))

    # 6️⃣ Если уведомлений нет — возвращаем пустые значения
    if not docs:
        return [], None

    # 7️⃣ Берём первый документ (самое свежее уведомление)
    doc = docs[0]

    # 8️⃣ Извлекаем список пользователей и дату создания
    user_ids = [str(uid) for uid in doc.get("toUsers", [])]  # ObjectId → string
    created_at = doc.get("created_at")

    return user_ids, created_at, title, text