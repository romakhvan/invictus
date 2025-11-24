from src.utils.check_helpers import log_check
from src.repositories.notifications_repository import get_user_ids_with_birthday_message
from src.repositories.notifications_repository import get_user_ids_with_welcome_message
from src.repositories.subscriptions_repository import get_first_time_subscribers
from src.repositories.subscriptions_repository import find_users_with_active_subscription
from src.repositories.users_repository import  find_users_with_birthday
import pytest_check as check
from src.utils.debug_utils import debug_print
from src.utils.debug_utils import log_function_call
from src.repositories.accesscontrols_repository import get_user_access_stats
import pprint

@log_function_call
def find_users_with_birthday_and_subscription(db, target_date):

    """
    🎂 Возвращает пользователей, у которых ДР совпадает с target_date
    и есть активная подписка.
    """
    birthday_users = find_users_with_birthday(db, target_date)
    if not birthday_users:
        print("⚠️ Пользователи с ДР не найдены.")
        return []

    user_ids = [u["_id"] for u in birthday_users]
    active_user_ids = find_users_with_active_subscription(db, user_ids)

    result = [u for u in birthday_users if u["_id"] in active_user_ids]
    print(f"🎉 Пользователей с ДР и активной подпиской: {len(result)}")
    return result

@log_function_call
def check_birthday_push(db, days=7, limit=1):
    """
    🎂 Проверяет, что пуш 'С днём рождения 💛' отправлен пользователям
    с активной подпиской на момент отправки.
    """
    print("\n=== CHECK: Birthday Push Validation ===")

    expected_title = "С днём рождения 💛"
    expected_text = "Сегодня самое время сказать спасибо за то, что вы с нами!"

    # ---------- 1️⃣ Получаем уведомление ----------
    user_ids, created_at, title, text = get_user_ids_with_birthday_message(
        db=db,
        search_text="День рождения когда есть абонемент",
        days=days,
        limit=limit
    )

    if not created_at:
        print("⚠️ Уведомление не найдено.")
        return False

    print(f"🕓 Дата пуша: {created_at}")

    # ---------- 2️⃣ Проверка содержимого ----------
    print("\n1️⃣ Проверка содержимого пуша")
    log_check("title", title, expected_title)
    log_check("text", text, expected_text)

    # ---------- 3️⃣ Проверка соответствия получателей ----------
    print("\n2️⃣ Проверка соответствия получателей")
    users = find_users_with_birthday_and_subscription(db, created_at)

    total_push = len(user_ids)
    total_db = len(users)

    print(f"📦 Пользователей в пуше: {total_push}")
    print(f"🧍 Пользователей с ДР и активной подпиской: {total_db}")

    check.is_true(total_db > 0, f"⚠️ Не найдено активных пользователей с ДР {created_at.strftime('%d-%m')}.")

    check.equal(
        total_db,
        total_push,
        f"❌ Количество пользователей в пуше ({total_push}) не совпадает с количеством активных ({total_db})."
    )

    # ---------- 4️⃣ Сравнение составов списков ----------
    print("\n3️⃣ Сравнение составов списков")

    push_set = set(user_ids)
    db_set = {str(u["_id"]) for u in users}

    missing_in_push = db_set - push_set
    extra_in_push = push_set - db_set

    if not missing_in_push and not extra_in_push:
        print("✅ Списки пользователей полностью совпадают.")
    else:
        if missing_in_push:
            print(f"⚠️ {len(missing_in_push)} пользователей не получили пуш, хотя должны были:")
            print(list(missing_in_push)[:10])
        if extra_in_push:
            print(f"⚠️ {len(extra_in_push)} пользователей получили пуш, хотя не должны были:")
            print(list(extra_in_push)[:10])

        check.is_true(
            not missing_in_push and not extra_in_push,
            f"❌ Несовпадения в списках пользователей: "
            f"{len(missing_in_push)} отсутствуют, {len(extra_in_push)} лишних."
        )
    return True

@log_function_call
def check_welcome_push(db, days=7, limit=1):
    """
    👋 Проверяет, что пуш 'Добро пожаловать' отправлен пользователям,
    которые купили абонемент впервые и ещё не были в клубе после покупки.
    """
    print("\n=== CHECK: Welcome Push Validation ===")

    # ---------- 1️⃣ Проверка содержимого ----------
    expected_title = "Добро пожаловать в Invictus 🏃"
    expected_text = "Столько всего впереди, а мы поможем на каждом этапе. Счастливого погружения!"

    user_ids, created_at, title, text = get_user_ids_with_welcome_message(
        db=db,
        description="Купил абонемент",
        title=expected_title,
        text=expected_text,
        days=days,
        limit=limit
    )

    if not created_at:
        print("⚠️ Уведомление не найдено.")
        check.is_true(False, "Уведомление не найдено.")
        return False

    total_in_push = len(user_ids)

    print("\n1️⃣ Проверка содержимого пуша")
    print(f"🕓 Дата пуша: {created_at}")
    print(f"👥 Получателей: {total_in_push}")

    log_check("title", title, expected_title)
    log_check("text", text, expected_text)

    # ---------- 2️⃣ Проверка получателей ----------
    print("\n2️⃣ Проверка соответствия получателей")

    users_with_first_subscription = get_first_time_subscribers(db, created_at)

    
    total_db = len(users_with_first_subscription)

    check.is_true(total_db > 0, f"⚠️ Не найдено новых подписчиков на {created_at.strftime('%d-%m-%Y')}.")
    

    # ---------- 2️⃣.1 Проверка отсутствия входов ----------
    print("\n2️⃣.1 Проверка входов клиентов после покупки абонемента")

 

    user_ids_db = [u["_id"] for u in users_with_first_subscription]
    users_without_entries = get_user_access_stats(
        db=db,
        user_ids=user_ids_db,
        end_date=created_at,
        mode="users_without_entries"
    )

    print("\n🔍 Первые 5 пользователей из функции get_user_access_stats:")
    pprint.pprint(users_without_entries[:5])  # выводим только первые 5 элементов

    # 🔹 Берём только тех, кто не был в клубе после покупки
    users_without_entries = [
        u for u in users_with_first_subscription if u["_id"] in users_without_entries
    ]

    print("\n🚪 Первые 5 пользователей без входов после покупки:")
    pprint.pprint(users_without_entries[:5])  # выводим только первые 5 элементов

    push_set = set(user_ids)
    db_set = {str(u["_id"]) for u in users_without_entries} 
    # print("\n🚪 db_set:")
    # pprint.pprint(db_set)



    print(f"📦 Пользователей в пуше: {len(push_set)}")
    print(f"🧍 Пользователей без входов после покупки: {len(db_set)}")


    total_without_entries = len(users_without_entries)
    print(f"🚪 Пользователей без входов после покупки: {total_without_entries}")

     # ---------- 3️⃣ Сравнение составов списков ----------
    print("\n3️⃣ Сравнение составов списков")

    missing_in_push = db_set - push_set  # должны были получить, но не получили
    extra_in_push = push_set - db_set    # получили, но не должны были
    matched = db_set & push_set          # совпали (правильные пользователи)

    print(f"✅ Совпавших пользователей: {len(matched)}")
    print(f"⚠️ Не получили пуш (missing): {len(missing_in_push)}")
    print(f"⚠️ Получили лишние (extra): {len(extra_in_push)}")

    # 🔹 Примеры для наглядности
    if matched:
        print("\n✅ Примеры совпавших пользователей (первые 10):")
        pprint.pprint(list(matched)[:10])

    if missing_in_push:
        print("\n⚠️ Примеры пользователей, которые не получили пуш, хотя должны были:")
        pprint.pprint(list(missing_in_push)[:10])

    if extra_in_push:
        print("\n⚠️ Примеры пользователей, которые получили пуш, хотя не должны были:")
        pprint.pprint(list(extra_in_push)[:10])

    # 🔹 Логическая проверка (pytest-check)
    check.is_true(
        not missing_in_push and not extra_in_push,
        f"❌ Несовпадения в списках пользователей: "
        f"{len(missing_in_push)} отсутствуют, {len(extra_in_push)} лишних."
    )


    return True