"""
Хелперы для проверок экрана профиля.
"""

from typing import TYPE_CHECKING, Any

from src.repositories.users_repository import get_user_display_info_by_phone

if TYPE_CHECKING:
    from src.pages.mobile.profile.profile_page import ProfilePage


def assert_profile_matches_potential_user(db: Any, profile_page: "ProfilePage") -> None:
    """
    Сравнивает имя и телефон на экране профиля с данными того же пользователя в БД (по номеру с экрана).
    """
    phone_ui = profile_page.get_displayed_phone()
    assert phone_ui, "На экране профиля не удалось получить номер телефона"
    user_info = get_user_display_info_by_phone(db, phone_ui)
    assert user_info, f"В БД не найден пользователь с номером с экрана: {phone_ui}"

    print(
        f"Данные из БД: телефон {user_info['phone_display']}, "
        f"роль {user_info['role']}, имя {user_info['firstName'] or user_info['fullName'] or '—'}"
    )

    profile_page.assert_profile_data_matches_db(
        user_info["firstName"],
        user_info["phone_display"],
    )

