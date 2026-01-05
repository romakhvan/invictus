import pytest_check as check
from src.validators.notifications_checker import check_welcome_push


def test_welcome_push_with_new_subscriptions(db):
    """
    👋 Проверяет пуш 'Добро пожаловать':
    - Заголовок и текст соответствуют шаблону;
    - Пользователи действительно купили абонемент в этот день;
    - Количество получателей совпадает с количеством покупок.
    """
    print("\n=== TEST: Welcome Push ===")
    assert check_welcome_push(db), "❌ Push 'Добро пожаловать' не прошёл проверку"
