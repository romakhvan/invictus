"""
Хелперы для проверок экрана профиля.
"""

from typing import TYPE_CHECKING, Any

from src.repositories.users_repository import get_user_display_info_by_user_id

if TYPE_CHECKING:
    from src.pages.mobile.profile.profile_page import ProfilePage


def assert_profile_matches_test_user(
    db: Any,
    profile_page: "ProfilePage",
    context=None,
) -> None:
    """
    Сравнивает имя и телефон на экране профиля с данными пользователя в БД.

    Требует context с user_id и использует его как единственный путь поиска.
    """
    phone_ui = profile_page.get_displayed_phone()
    assert phone_ui, "На экране профиля не удалось получить номер телефона"

    if not context or not getattr(context, "user_id", None):
        raise ValueError(
            "assert_profile_matches_potential_user требует context с user_id."
        )

    user_info = get_user_display_info_by_user_id(db, context.user_id)

    assert user_info, f"В БД не найден пользователь для user_id: {context.user_id}"

    print(
        f"Данные из БД: телефон {user_info['phone_display']}, "
        f"роль {user_info['role']}, имя {user_info['firstName'] or user_info['fullName'] or '—'}"
    )

    profile_page.assert_profile_data_matches_db(
        user_info["firstName"],
        user_info["phone_display"],
    )


def assert_profile_matches_potential_user(
    db: Any,
    profile_page: "ProfilePage",
    context=None,
) -> None:
    """Compatibility wrapper for existing potential-user checks."""
    assert_profile_matches_test_user(db, profile_page, context=context)
