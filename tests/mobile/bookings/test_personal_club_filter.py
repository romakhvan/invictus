from typing import TYPE_CHECKING

import pytest

from src.pages.mobile.home import HomePage, HomeState
from src.repositories.clubs_repository import get_mobile_clubs_by_city
from tests.mobile.helpers.club_filter_assertions import assert_club_cards_match_mongo

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
def test_personal_club_filter_matches_mongo(
    potential_user_on_main_screen: "Remote",
    db,
):
    city_name = "Алматы"

    home = HomePage(potential_user_on_main_screen)
    assert home.get_current_home_state() == HomeState.NEW_USER

    bookings = home.nav.open_bookings()
    personal_page = bookings.open_personal_section()
    personal_page.club_filter.select_city(city_name)

    actual_cards = sorted(personal_page.club_filter.get_all_club_cards(), key=lambda item: item.key)
    expected_cards = get_mobile_clubs_by_city(db, city_name=city_name)

    assert expected_cards, f"В Mongo не найдено клубов для города {city_name}"
    assert_club_cards_match_mongo(actual_cards, expected_cards)
