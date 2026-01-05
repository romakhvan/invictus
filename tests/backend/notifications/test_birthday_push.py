import pytest_check as check
from src.validators.notifications_checker import check_birthday_push


def test_birthday_push_with_active_users(db):
    """
    Тест проверяет, что пуш с поздравлением 'С днём рождения 💛'
    отправлен только пользователям с активной подпиской.
    """
    print("=== TEST: Birthday Push ===")

    # 🔹 Выполняем основную проверку
    check_birthday_push(db)