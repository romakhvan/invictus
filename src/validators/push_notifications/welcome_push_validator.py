from src.repositories.notifications_repository import get_user_ids_with_welcome_message
from src.repositories.subscriptions_repository import get_first_time_subscribers
from src.repositories.accesscontrols_repository import get_user_access_stats
from src.utils.debug_utils import log_function_call
from src.validators.push_notifications.base import PushValidationConfig, validate_push
import pprint


def get_welcome_push_recipients(db, created_at):
    """
    Получает пользователей, которые должны получить welcome push:
    - Купили абонемент впервые
    - Не заходили в клуб неделю после покупки
    
    Args:
        db: подключение к MongoDB
        created_at: дата отправки пуша
    
    Returns:
        Список пользователей, соответствующих критериям
    """
    print("\n[SEARCH] Поиск пользователей с первой подпиской...")
    users_with_first_subscription = get_first_time_subscribers(db, created_at)
    
    total_first_time = len(users_with_first_subscription)
    print(f"[INFO] Найдено пользователей с первой подпиской: {total_first_time}")
    
    if total_first_time == 0:
        return []
    
    # Проверка отсутствия входов после покупки
    print("\n[FILTER] Фильтрация пользователей без входов в клуб после покупки...")
    
    user_ids_db = [u["_id"] for u in users_with_first_subscription]
    user_ids_without_entries = get_user_access_stats(
        db=db,
        user_ids=user_ids_db,
        end_date=created_at,
        mode="users_without_entries"
    )
    
    print(f"\n[INFO] Первые 5 ID пользователей без входов:")
    pprint.pprint(user_ids_without_entries[:5])
    
    # Берём только тех, кто не был в клубе после покупки
    users_without_entries = [
        u for u in users_with_first_subscription if u["_id"] in user_ids_without_entries
    ]
    
    print(f"\n[INFO] Первые 5 пользователей без входов после покупки:")
    pprint.pprint(users_without_entries[:5])
    
    print(f"[RESULT] Итого пользователей для welcome push: {len(users_without_entries)}")
    
    return users_without_entries


@log_function_call
def check_welcome_push(db, days=7, limit=1):
    """
    👋 Проверяет, что пуш 'Добро пожаловать' отправлен пользователям,
    которые купили абонемент впервые и ещё не были в клубе после покупки неделю.
    """
    config = PushValidationConfig(
        name="Welcome Push Validation",
        expected_title="{{name}}, добро пожаловать в Invictus 🏃",
        expected_text="Здесь мы добьемся результата вместе. Ждем на тренировках.",
        fetch_function=get_user_ids_with_welcome_message,
        get_recipients_function=get_welcome_push_recipients,
        fetch_kwargs={
            "description": "Купил первый абонемент, но не приходит в клуб 1 неделю [RU]",
            "title": "{{name}}, добро пожаловать в Invictus 🏃",
            "text": "Здесь мы добьемся результата вместе. Ждем на тренировках."
        },
        description="Проверка welcome push для новых подписчиков без входов в клуб"
    )
    
    return validate_push(db, config, days, limit)
