"""
Тесты для push-уведомлений о неактивных пользователях.
"""
import pytest_check as check
from src.validators.push_notifications.inactive_user_push_validator import (
    check_inactive_user_push_1_week,
    check_inactive_user_push_2_weeks,
    check_inactive_user_push_4_weeks,
    check_inactive_user_push_8_weeks,
)

def test_inactive_user_push_1_week(db):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 1 неделю.
    """
    print("\n=== TEST: Inactive User Push (1 week) ===")
    assert check_inactive_user_push_1_week(db), "❌ Push '1 неделя' не прошёл проверку"


def test_inactive_user_push_2_weeks(db):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 2 недели.
    """
    print("\n=== TEST: Inactive User Push (2 weeks) ===")
    assert check_inactive_user_push_2_weeks(db), "❌ Push '2 недели' не прошёл проверку"


def test_inactive_user_push_4_weeks(db):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 4 недели.
    """
    print("\n=== TEST: Inactive User Push (4 weeks) ===")
    assert check_inactive_user_push_4_weeks(db), "❌ Push '4 недели' не прошёл проверку"


def test_inactive_user_push_8_weeks(db):
    """
    🚫 Проверяет push-уведомление для пользователей,
    которые купили абонемент, но не были в клубе 8 недель.
    """
    print("\n=== TEST: Inactive User Push (8 weeks) ===")
    assert check_inactive_user_push_8_weeks(db), "❌ Push '8 недель' не прошёл проверку"









