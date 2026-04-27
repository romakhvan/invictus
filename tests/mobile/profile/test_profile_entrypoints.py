"""Проверяет entrypoints на экране «Профиль»."""

from typing import TYPE_CHECKING, Type

import pytest

from src.pages.mobile.clubs.clubs_page import ClubsPage
from src.pages.mobile.notifications.notifications_page import NotificationsPage
from src.pages.mobile.profile.guest_visits_page import GuestVisitsPage
from src.pages.mobile.profile.partner_discounts_page import PartnerDiscountsPage
from src.pages.mobile.profile.personal_info_page import PersonalInfoPage
from src.pages.mobile.profile.profile_page import ProfilePage
from src.pages.mobile.profile.promo_code_page import PromoCodePage
from src.pages.mobile.profile.trainings_promo_page import TrainingsPromoPage
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)
from tests.mobile.helpers.session_helpers import ensure_test_user_session

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.mark.mobile
@pytest.mark.parametrize(
    "entrypoint_method,ExpectedPage",
    [
        ("open_buy_subscription",  ClubsPage),
        ("open_partner_discounts", PartnerDiscountsPage),
        ("open_add_service",       TrainingsPromoPage),
        ("open_promo_code",        PromoCodePage),
        ("open_guest_visits",      GuestVisitsPage),
        ("open_notifications",     NotificationsPage),
        ("open_personal_info",     PersonalInfoPage),
    ],
    ids=[
        "buy_subscription",
        "partner_discounts",
        "add_service",
        "promo_code",
        "guest_visits",
        "notifications",
        "personal_info",
    ],
)
def test_profile_entrypoints_open_expected_page(
    mobile_driver,
    db,
    entrypoint_method: str,
    ExpectedPage: Type,
):
    """Entrypoint на экране «Профиль» открывает ожидаемую страницу."""
    driver: "Remote" = mobile_driver
    context = MobileTestUserSelector(db).select_or_skip(MobileTestUserScenario.POTENTIAL_USER)

    nav = ensure_test_user_session(driver, db, context)
    profile = nav.open_profile()
    assert isinstance(profile, ProfilePage)

    print(
        f"▶️ Проверка entrypoint '{entrypoint_method}' на экране 'Профиль' "
        f"→ ожидаемая страница {ExpectedPage.__name__}"
    )
    page = getattr(profile, entrypoint_method)()
    print(f"ℹ️ Entrypoint '{entrypoint_method}' вернул объект: {type(page).__name__}")

    assert isinstance(page, ExpectedPage), (
        f"Entrypoint '{entrypoint_method}' открыл {type(page).__name__}, "
        f"ожидался {ExpectedPage.__name__}."
    )
    print(
        f"✅ Entrypoint '{entrypoint_method}' на экране 'Профиль' успешно открыл "
        f"{ExpectedPage.__name__}"
    )
