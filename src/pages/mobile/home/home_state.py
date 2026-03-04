"""
Состояния главного экрана в зависимости от типа пользователя.
"""

from enum import Enum


class HomeState(Enum):
    """Тип контента на главном экране после входа."""

    NEW_USER = "new_user"  # приглашение заполнить профиль / онбординг
    SUBSCRIBED = "subscribed"  # клиент с подпиской
    MEMBER = "member"  # клиент с абонементом
    UNKNOWN = "unknown"  # не удалось определить
