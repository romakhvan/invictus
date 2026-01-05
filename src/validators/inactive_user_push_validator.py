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
    
    # Получаем всех пользователей с новыми подписками за период
    days_back = weeks_inactive * 7
    subscription_date = created_at - timedelta(days=days_back)
    
    users_with_subscriptions = get_new_subscriptions(db, subscription_date, days=days_back)
    
    if not users_with_subscriptions:
        print(f"⚠️ Не найдено пользователей с подписками за период {days_back} дней до пуша.")
        check.is_true(False, f"Не найдено пользователей с подписками")
        return False
    
    print(f"📦 Найдено пользователей с подписками: {len(users_with_subscriptions)}")
    
    # Проверяем, что у них активные подписки
    active_user_ids = find_users_with_active_subscription(db, users_with_subscriptions)
    users_with_active_subs = [uid for uid in users_with_subscriptions if uid in active_user_ids]
    
    print(f"🟢 Пользователей с активными подписками: {len(users_with_active_subs)}")
    
    # ---------- 4️⃣ Проверка отсутствия входов ----------
    print(f"\n3️⃣ Проверка входов клиентов (не были в клубе {weeks_inactive} недель)")
    
    users_without_entries = get_user_access_stats(
        db=db,
        user_ids=users_with_active_subs,
        end_date=created_at,
        mode="users_without_entries"
    )
    
    print(f"🚫 Пользователей без входов: {len(users_without_entries)}")
    
    if len(users_without_entries) > 5:
        print("\n🔍 Первые 5 пользователей без входов:")
        pprint.pprint(users_without_entries[:5])
    
    # ---------- 5️⃣ Сравнение составов списков ----------
    print("\n4️⃣ Сравнение составов списков")
    
    push_set = set(user_ids)
    db_set = {str(uid) for uid in users_without_entries}
    
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
        pprint.pprint(list(matched)[:10])
    
    if missing_in_push:
        print("\n⚠️ Примеры пользователей, которые не получили пуш, хотя должны были:")
        pprint.pprint(list(missing_in_push)[:10])
    
    if extra_in_push:
        print("\n⚠️ Примеры пользователей, которые получили пуш, хотя не должны были:")
        pprint.pprint(list(extra_in_push)[:10])
    
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
        expected_title="Купил первый абонемент, но не приходит в клуб 1 неделю",
        expected_text="",  # TODO: добавить ожидаемый текст
        description="Купил абонемент, но не приходит в клуб 1 неделю",
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









