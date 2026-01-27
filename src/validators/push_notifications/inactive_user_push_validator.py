"""
Валидаторы для push-уведомлений о неактивных пользователях.

Проверяет, что push-уведомления отправлены пользователям,
которые купили абонемент, но не были в клубе определенное время.
"""
from datetime import timedelta
from pprint import pprint
import pytest_check as check
from src.utils.check_helpers import log_check
from src.utils.debug_utils import log_function_call
from src.repositories.notifications_repository import get_user_ids_with_welcome_message
from src.repositories.subscriptions_repository import get_new_subscriptions
from src.repositories.subscriptions_repository import find_users_with_active_subscription
from src.repositories.accesscontrols_repository import get_user_access_stats


def _get_inactive_users_notification(db, description, title, text, days, limit):
    """
    Базовая функция для получения уведомления о неактивных пользователях.
    Использует ту же логику, что и get_user_ids_with_welcome_message.
    """
    return get_user_ids_with_welcome_message(
        db=db,
        description=description,
        title=title,
        text=text,
        days=days,
        limit=limit
    )


@log_function_call
def _check_inactive_user_push(
    db,
    weeks_inactive: int,
    expected_title: str,
    expected_text: str,
    description: str,
    days: int = 7,
    limit: int = 1
):
    """
    Базовая функция для проверки push-уведомлений о неактивных пользователях.
    
    Args:
        db: База данных MongoDB
        weeks_inactive: Количество недель неактивности (1, 2, 4, 8)
        expected_title: Ожидаемый заголовок уведомления
        expected_text: Ожидаемый текст уведомления
        description: Описание для поиска уведомления в БД
        days: Период поиска уведомлений (по умолчанию 7 дней)
        limit: Лимит уведомлений (по умолчанию 1)
    
    Returns:
        bool: True если проверка прошла успешно, False иначе
    """
    print(f"\n=== CHECK: Inactive User Push ({weeks_inactive} недель) ===")
    
    # DEBUG: Проверяем все пуши за период
    from datetime import datetime
    col = db["notifications"]
    today = datetime.now()
    time_ago = today - timedelta(days=days)
    
    query = {
        "created_at": {"$gte": time_ago},
        "title": {"$regex": expected_title, "$options": "i"},
        "description": {"$regex": description, "$options": "i"},
    }
    all_pushes = list(col.find(query, {"created_at": 1, "_id": 1}).sort("created_at", -1))
    
    if len(all_pushes) > 1:
        print(f"\n🔍 DEBUG: Найдено {len(all_pushes)} пушей за последние {days} дней:")
        for idx, push in enumerate(all_pushes[:5], 1):
            print(f"   {idx}. {push['created_at']} (ID: {push['_id']})")
    
    # ---------- 1️⃣ Получаем уведомление ----------
    user_ids, created_at, title, text = _get_inactive_users_notification(
        db=db,
        description=description,
        title=expected_title,
        text=expected_text,
        days=days,
        limit=limit
    )
    
    if not created_at:
        print("⚠️ Уведомление не найдено.")
        check.is_true(False, "Уведомление не найдено.")
        return False
    
    print(f"🕓 Дата пуша: {created_at}")
    print(f"👥 Получателей в пуше: {len(user_ids)}")
    
    # ---------- 2️⃣ Проверка содержимого ----------
    print("\n1️⃣ Проверка содержимого пуша")
    log_check("title", title, expected_title)
    log_check("text", text, expected_text)
    
    # ---------- 3️⃣ Находим пользователей с подписками, которые не были в клубе N недель ----------
    print(f"\n2️⃣ Поиск пользователей с подписками, не посещавших клуб {weeks_inactive} недель")
    
    # Импорты для новой логики
    from src.repositories.subscriptions_repository import get_new_subscriptions_with_dates
    from src.repositories.accesscontrols_repository import get_users_without_entries_since_subscription
    from bson import ObjectId
    
    # Определяем период поиска подписок (примерно N недель назад ±2 дня)
    days_back = weeks_inactive * 7
    subscription_target_date = created_at - timedelta(days=days_back)
    
    # Ищем подписки в окне ±2 дня от целевой даты
    print(f"🎯 Целевая дата покупки подписки: ~{subscription_target_date.strftime('%Y-%m-%d')} (±2 дня)")
    
    # Получаем подписки с датами: {user_id: created_at}
    user_subscriptions_dict = get_new_subscriptions_with_dates(
        db, 
        subscription_target_date + timedelta(days=2),  # +2 дня от целевой даты
        days=4  # окно в 4 дня (±2 дня)
    )
    
    if not user_subscriptions_dict:
        start = (subscription_target_date - timedelta(days=2)).strftime('%Y-%m-%d')
        end = (subscription_target_date + timedelta(days=2)).strftime('%Y-%m-%d')
        print(f"⚠️ Не найдено пользователей с подписками за период {start} - {end}.")
        check.is_true(False, f"Не найдено пользователей с подписками")
        return False
    
    print(f"📦 Найдено пользователей с подписками: {len(user_subscriptions_dict)}")
    
    # DEBUG: Проверка нескольких пользователей
    debug_users = [
        ("645f8fbc9730060021da720c", ObjectId("645f8fbc9730060021da720c")),
        ("673643932074420245f5650d", ObjectId("673643932074420245f5650d")),
        ("6594dbe792bf1100766d54b6", ObjectId("6594dbe792bf1100766d54b6"))
    ]
    
    for debug_user_str, debug_user_obj in debug_users:
        if debug_user_obj not in user_subscriptions_dict:
            continue
        print(f"\n🔍 DEBUG для пользователя {debug_user_str}:")
        
        # Проверяем последний вход
        access_col = db["accesscontrols"]
        last_entry = access_col.find_one(
            {"user": debug_user_obj, "time": {"$lte": created_at}},
            {"time": 1},
            sort=[("time", -1)]
        )
        if last_entry:
            last_time = last_entry.get("time")
            days_since = (created_at - last_time).days if last_time else None
            print(f"   Последний вход: {last_time} ({days_since} дней назад)")
        else:
            print(f"   Последний вход: не найден")
    
    # Оригинальный DEBUG
    debug_user_obj = ObjectId("645f8fbc9730060021da720c")
    debug_user_str = "645f8fbc9730060021da720c"
    if debug_user_obj in user_subscriptions_dict:
        sub_date = user_subscriptions_dict[debug_user_obj]
        print(f"🔍 DEBUG: Пользователь {debug_user_str} ЕСТЬ в списке (подписка куплена {sub_date})")
    else:
        print(f"🔍 DEBUG: Пользователь {debug_user_str} НЕТ в списке с подписками")
    
    # Проверяем, что у них активные подписки СЕЙЧАС
    user_ids_list = list(user_subscriptions_dict.keys())
    active_user_ids = find_users_with_active_subscription(db, user_ids_list)
    
    # Фильтруем только активных пользователей
    active_user_subscriptions = {
        uid: created_at 
        for uid, created_at in user_subscriptions_dict.items() 
        if uid in active_user_ids
    }
    
    print(f"🟢 Пользователей с активными подписками: {len(active_user_subscriptions)}")
    
    # DEBUG: Проверка активной подписки
    if debug_user_obj in active_user_subscriptions:
        print(f"🔍 DEBUG: Пользователь {debug_user_str} ЕСТЬ в списке с активными подписками")
    else:
        print(f"🔍 DEBUG: Пользователь {debug_user_str} НЕТ в списке с активными подписками")
    
    # ---------- 4️⃣ Проверка отсутствия входов ----------
    print(f"\n3️⃣ Проверка входов клиентов (с момента покупки подписки до даты пуша)")
    
    # Определяем диапазон последнего входа для этого типа пуша
    # Для пуша "1 неделя":
    #   - минимум: 7 дней назад (если был 5 дней назад - еще не прошла неделя)
    #   - максимум: 14 дней назад (если был месяц назад - это уже другой пуш)
    min_last_entry_days = weeks_inactive * 7      # не менее N недель назад
    max_last_entry_days = weeks_inactive * 7 * 2  # не более 2N недель назад
    
    print(f"🔍 Диапазон последнего входа: от {min_last_entry_days} до {max_last_entry_days} дней назад")
    
    # Используем новую функцию: проверяем входы для каждого пользователя 
    # с момента покупки его подписки
    users_without_entries = get_users_without_entries_since_subscription(
        db=db,
        user_subscriptions=active_user_subscriptions,
        end_date=created_at,
        min_last_entry_days=min_last_entry_days,
        max_last_entry_days=max_last_entry_days
    )
    
    print(f"🚫 Пользователей без входов: {len(users_without_entries)}")
    
    # DEBUG: Проверка входов для конкретного пользователя
    if debug_user_obj in users_without_entries:
        print(f"🔍 DEBUG: Пользователь {debug_user_str} НЕ был в клубе (должен получить пуш)")
    else:
        print(f"🔍 DEBUG: Пользователь {debug_user_str} БЫЛ в клубе (не должен получить пуш)")
    
    if len(users_without_entries) > 5:
        print("\n🔍 Первые 5 пользователей без входов:")
        pprint(users_without_entries[:5])
    
    # ---------- 5️⃣ Сравнение составов списков ----------
    print("\n4️⃣ Сравнение составов списков")
    
    push_set = set(user_ids)
    db_set = {str(uid) for uid in users_without_entries}
    
    # DEBUG: Проверка конкретного пользователя
    debug_user = "645f8fbc9730060021da720c"
    if debug_user in push_set:
        print(f"\n🔍 DEBUG: Пользователь {debug_user} ЕСТЬ в пуше от {created_at}")
    else:
        print(f"\n🔍 DEBUG: Пользователь {debug_user} НЕТ в пуше от {created_at}")
    
    if debug_user in db_set:
        print(f"🔍 DEBUG: Пользователь {debug_user} должен был получить пуш (есть в db_set)")
    else:
        print(f"🔍 DEBUG: Пользователь {debug_user} НЕ должен был получить пуш (нет в db_set)")
    
    missing_in_push = db_set - push_set  # должны были получить, но не получили
    extra_in_push = push_set - db_set    # получили, но не должны были
    matched = db_set & push_set           # совпали (правильные пользователи)
    
    print(f"📦 Пользователей в пуше: {len(push_set)}")
    print(f"🧍 Пользователей без входов после покупки: {len(db_set)}")
    print(f"✅ Совпавших пользователей: {len(matched)}")
    print(f"⚠️ Не получили пуш (missing): {len(missing_in_push)}")
    print(f"⚠️ Получили лишние (extra): {len(extra_in_push)}")
    
    # Примеры для наглядности
    if matched:
        print("\n✅ Примеры совпавших пользователей (первые 10):")
        pprint(list(matched)[:10])
    
    if missing_in_push:
        print("\n⚠️ Примеры пользователей, которые не получили пуш, хотя должны были:")
        pprint(list(missing_in_push)[:10])
    
    if extra_in_push:
        print("\n⚠️ Примеры пользователей, которые получили пуш, хотя не должны были:")
        pprint(list(extra_in_push)[:10])
    
    # Логическая проверка
    check.is_true(
        not missing_in_push and not extra_in_push,
        f"❌ Несовпадения в списках пользователей: "
        f"{len(missing_in_push)} отсутствуют, {len(extra_in_push)} лишних."
    )
    
    return True


@log_function_call
def check_inactive_user_push_1_week(db, days=7, limit=1):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 1 неделю.
    """
    return _check_inactive_user_push(
        db=db,
        weeks_inactive=1,
        expected_title="Имя, мы уже скучаем по тебе!",
        expected_text=(
            "Прошла всего неделя, но зал будто опустел.\n"
            "Зайди хотя бы на 20 минут — и твой день станет лучше."
        ),
        description="1 неделя отсутствия",
        days=days,
        limit=limit
    )


@log_function_call
def check_inactive_user_push_2_weeks(db, days=7, limit=1):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 2 недели.
    """
    return _check_inactive_user_push(
        db=db,
        weeks_inactive=2,
        expected_title="Купил абонемент, но не приходит в клуб 2 недели",
        expected_text="",  # TODO: добавить ожидаемый текст
        description="Купил абонемент, но не приходит в клуб 2 недели",
        days=days,
        limit=limit
    )


@log_function_call
def check_inactive_user_push_4_weeks(db, days=7, limit=1):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 4 недели.
    """
    return _check_inactive_user_push(
        db=db,
        weeks_inactive=4,
        expected_title="Купил абонемент, но не приходит в клуб 4 недели",
        expected_text="",  # TODO: добавить ожидаемый текст
        description="Купил абонемент, но не приходит в клуб 4 недели",
        days=days,
        limit=limit
    )


@log_function_call
def check_inactive_user_push_8_weeks(db, days=7, limit=1):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 8 недель.
    """
    return _check_inactive_user_push(
        db=db,
        weeks_inactive=8,
        expected_title="Купил абонемент, но не приходит в клуб 8 недель",
        expected_text="",  # TODO: добавить ожидаемый текст
        description="Купил абонемент, но не приходит в клуб 8 недель",
        days=days,
        limit=limit
    )
