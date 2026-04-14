"""
Проверки entrypoints в табе «Записи».

Сценарий: главная (NEW_USER) → таб «Записи» → клик по секции → открывается ожидаемая страница.
"""

from typing import TYPE_CHECKING, Type

import pytest

from src.pages.mobile.bookings.bookings_page import BookingsPage
from src.pages.mobile.bookings.doctors_schedule_page import DoctorsSchedulePage
from src.pages.mobile.bookings.events_bookings_page import EventsBookingsPage
from src.pages.mobile.bookings.faq_bookings_page import FaqBookingsPage
from src.pages.mobile.bookings.group_bookings_page import GroupBookingsPage
from src.pages.mobile.bookings.personal_bookings_page import PersonalBookingsPage
from src.pages.mobile.home import HomePage, HomeState

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
@pytest.mark.parametrize(
    "entrypoint_method,ExpectedPage",
    [
        ("open_personal_section", PersonalBookingsPage),
        ("open_group_section", GroupBookingsPage),
        ("open_doctors_section", DoctorsSchedulePage),
        ("open_events_section", EventsBookingsPage),
        ("open_faq_section", FaqBookingsPage),
    ],
    ids=[
        "personal",
        "group",
        "doctors",
        "events",
        "faq",
    ],
)
def test_bookings_entrypoints_open_expected_page(
    potential_user_on_main_screen: "Remote",
    entrypoint_method: str,
    ExpectedPage: Type,
):
    """
    С таба «Записи» по entrypoint секции открывается ожидаемая страница.
    """
    driver = potential_user_on_main_screen

    # Гарантируем, что находимся на главной в состоянии NEW_USER.
    home = HomePage(driver).wait_loaded()
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "Ожидалось состояние NEW_USER. Фикстура potential_user_on_main_screen "
        "должна обеспечивать вход под potential."
    )

    # Переход в таб «Записи» через нижнюю навигацию.
    bookings = home.nav.open_bookings()
    assert isinstance(bookings, BookingsPage)

    # Вызов entrypoint и проверка типа целевой страницы.
    print(
        f"▶️ Проверка entrypoint '{entrypoint_method}' в табе 'Записи' "
        f"→ ожидаемая страница {ExpectedPage.__name__}"
    )
    open_fn = getattr(bookings, entrypoint_method)
    page = open_fn()
    print(f"ℹ️ Entrypoint '{entrypoint_method}' вернул объект: {type(page).__name__}")

    assert isinstance(page, ExpectedPage), (
        f"Entrypoint '{entrypoint_method}' открыл {type(page).__name__}, "
        f"ожидался {ExpectedPage.__name__}."
    )
    print(
        f"✅ Entrypoint '{entrypoint_method}' в табе 'Записи' успешно открыл страницу "
        f"{ExpectedPage.__name__}"
    )
