from src.repositories.notifications_repository import get_user_ids_with_birthday_message
from src.repositories.subscriptions_repository import find_users_with_active_subscription
from src.repositories.users_repository import find_users_with_birthday
from src.utils.debug_utils import log_function_call
from src.validators.push_notifications.base import PushValidationConfig, validate_push


@log_function_call
def find_users_with_birthday_and_subscription(db, target_date):
    """
    🎂 Возвращает пользователей, у которых ДР совпадает с target_date
    и есть активная подписка.
    """
    birthday_users = find_users_with_birthday(db, target_date)
    if not birthday_users:
        print("[WARNING] Пользователи с ДР не найдены.")
        return []

    user_ids = [u["_id"] for u in birthday_users]
    active_user_ids = find_users_with_active_subscription(db, user_ids)

    result = [u for u in birthday_users if u["_id"] in active_user_ids]
    print(f"[RESULT] Пользователей с ДР и активной подпиской: {len(result)}")
    return result


@log_function_call
def check_birthday_push(db, days=7, limit=1):
    """
    🎂 Проверяет, что birthday push отправлен пользователям
    с активной подпиской на момент отправки.
    """
    config = PushValidationConfig(
        name="Birthday Push Validation",
        expected_title=(
            "{{name}}, с днём рождения 💛",
            "{{name}}, happy birthday💛",
        ),
        expected_text=(
            "Сегодня самое время сказать спасибо за то, что вы с нами! Здоровья и побед!",
            "Today is the perfect time to say thank you for being with us! Wishing you health and victories!",
        ),
        fetch_function=get_user_ids_with_birthday_message,
        get_recipients_function=find_users_with_birthday_and_subscription,
        fetch_kwargs={"search_text": "День рождения когда есть абонемент"},
        description="Проверка пуша с днём рождения для пользователей с активной подпиской"
    )
    
    return validate_push(db, config, days, limit)
