"""
Проверки переключения табов «Все возможности» / «Расписание» в разделе «Записи».
"""

import pytest

from src.pages.mobile.bookings.bookings_page import BookingsPage
from src.pages.mobile.home import HomePage, HomeState

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
def test_bookings_tab_switch_to_schedule_and_back(
    potential_user_on_main_screen: "Remote",
):
    """
    Переключение между табами «Все возможности» и «Расписание» скрывает и
    восстанавливает список секций.
    """
    driver = potential_user_on_main_screen

    home = HomePage(driver).wait_loaded()
    assert home.get_current_home_state() == HomeState.NEW_USER
    bookings: BookingsPage = home.nav.open_bookings()

    bookings.switch_to_schedule_tab()
    bookings.switch_to_all_activities_tab()
