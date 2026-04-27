"""Checks entrypoints in the Bookings tab."""

from typing import TYPE_CHECKING, Type

import pytest

from src.pages.mobile.bookings.bookings_page import BookingsPage
from src.pages.mobile.bookings.doctors_schedule_page import DoctorsSchedulePage
from src.pages.mobile.bookings.events_bookings_page import EventsBookingsPage
from src.pages.mobile.bookings.faq_bookings_page import FaqBookingsPage
from src.pages.mobile.bookings.group_bookings_page import GroupBookingsPage
from src.pages.mobile.bookings.personal_bookings_page import PersonalBookingsPage
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)
from tests.mobile.helpers.session_helpers import ensure_test_user_session

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
@pytest.mark.parametrize(
    "user_scenario,entrypoint_method,ExpectedPage",
    [
        (MobileTestUserScenario.POTENTIAL_USER, "open_personal_section", PersonalBookingsPage),
        (MobileTestUserScenario.POTENTIAL_USER, "open_group_section", GroupBookingsPage),
        (MobileTestUserScenario.POTENTIAL_USER, "open_doctors_section", DoctorsSchedulePage),
        (MobileTestUserScenario.POTENTIAL_USER, "open_events_section", EventsBookingsPage),
        (MobileTestUserScenario.POTENTIAL_USER, "open_faq_section", FaqBookingsPage),
        (MobileTestUserScenario.RABBIT_HOLE_USER, "open_personal_section", PersonalBookingsPage),
        (MobileTestUserScenario.RABBIT_HOLE_USER, "open_group_section", GroupBookingsPage),
        (MobileTestUserScenario.RABBIT_HOLE_USER, "open_doctors_section", DoctorsSchedulePage),
        (MobileTestUserScenario.RABBIT_HOLE_USER, "open_events_section", EventsBookingsPage),
        (MobileTestUserScenario.RABBIT_HOLE_USER, "open_faq_section", FaqBookingsPage),
    ],
    ids=[
        "new_user-personal",
        "new_user-group",
        "new_user-doctors",
        "new_user-events",
        "new_user-faq"
    ],
)
def test_bookings_entrypoints_open_expected_page(
    mobile_driver,
    db,
    user_scenario: MobileTestUserScenario,
    entrypoint_method: str,
    ExpectedPage: Type,
):
    """A Bookings section entrypoint opens the expected page."""
    driver: "Remote" = mobile_driver
    context = MobileTestUserSelector(db).select_or_skip(user_scenario)

    nav = ensure_test_user_session(driver, db, context)
    bookings = nav.open_bookings()
    assert isinstance(bookings, BookingsPage)

    print(
        f"▶️ Проверка entrypoint '{entrypoint_method}' в табе 'Записи' "
        f"→ ожидаемая страница {ExpectedPage.__name__}"
    )
    page = getattr(bookings, entrypoint_method)()
    print(f"ℹ️ Entrypoint '{entrypoint_method}' вернул объект: {type(page).__name__}")

    assert isinstance(page, ExpectedPage), (
        f"Entrypoint '{entrypoint_method}' открыл {type(page).__name__}, "
        f"ожидался {ExpectedPage.__name__}."
    )
    print(
        f"✅ Entrypoint '{entrypoint_method}' в табе 'Записи' успешно открыл страницу "
        f"{ExpectedPage.__name__}"
    )
