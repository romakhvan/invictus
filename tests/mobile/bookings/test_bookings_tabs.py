"""
Проверки переключения табов «Все возможности» / «Записи» в разделе «Записи».
"""

import pytest

from src.pages.mobile.bookings.bookings_page import BookingsPage

@pytest.mark.mobile
def test_bookings_tab_switch_to_records_and_back(
    potential_user_session,
):
    """
    Переключение между табами «Все возможности» и «Записи» скрывает и
    восстанавливает список секций.
    """
    bookings: BookingsPage = potential_user_session.open_bookings()

    bookings.switch_to_schedule_tab()
    bookings.switch_to_all_activities_tab()
