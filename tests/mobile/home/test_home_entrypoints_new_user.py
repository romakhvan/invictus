"""
Проверки открытия модулей приложения с главной страницы (NEW_USER).

Один параметризованный тест: главная (NEW_USER) → клик по entrypoint → проверка целевой страницы.
"""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.pages.mobile.bonuses.bonuses_page import BonusesPage
from src.pages.mobile.clubs.clubs_page import ClubsPage
from src.pages.mobile.clubs.club_details_page import ClubDetailsPage
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.home.content import HomeNewUserContent
from src.pages.mobile.notifications.notifications_page import NotificationsPage
from src.pages.mobile.products.gym_buddy_page import GymBuddyPage
from src.pages.mobile.products.health_page import HealthPage
from src.pages.mobile.products.store_page import StorePage

# @pytest.mark.interactive_mobile
@pytest.mark.mobile
@pytest.mark.parametrize(
    "entrypoint_method,ExpectedPage",
    [
        ("open_clubs", ClubsPage),
        ("open_gym_buddy", GymBuddyPage),
        ("open_bonuses", BonusesPage),
        ("open_notifications", NotificationsPage),
        ("open_health", HealthPage),
        ("open_store", StorePage),
        ("open_first_club_card", ClubDetailsPage),
    ],
    ids=[
        "clubs",
        "gym_buddy",
        "bonuses",
        "notifications_icon",
        "health_banner",
        "store",
        "club_card_details",
    ],
)
def test_home_new_user_entrypoint_opens_page(
    potential_user_on_main_screen: "Remote",
    entrypoint_method: str,
    ExpectedPage: type,
):
    """
    С главной (NEW_USER) по entrypoint открывается ожидаемая страница.
    Фикстура potential_user_on_main_screen гарантирует вход под new user (potential)
    и сверку профиля с БД; при другой роли тест пропускается или падает на assert.
    Параметры: метод контента (open_*), класс ожидаемой страницы.
    """
    driver = potential_user_on_main_screen

    home = HomePage(driver).wait_loaded()
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "Ожидалось состояние NEW_USER. Фикстура должна обеспечивать вход под potential."
    )

    content = home.get_content()
    print(
        f"▶️ Проверка entrypoint '{entrypoint_method}' → ожидаемая страница {ExpectedPage.__name__}"
    )
    open_fn = getattr(content, entrypoint_method)
    page = open_fn()

    assert isinstance(page, ExpectedPage)
    print(
        f"✅ Entrypoint '{entrypoint_method}' успешно открыл страницу {ExpectedPage.__name__}"
    )


@pytest.mark.interactive_mobile
@pytest.mark.mobile
def test_home_new_user_rabbit_hole_opens_overlay(
    potential_user_on_main_screen: "Remote",
):
    """
    С главной (NEW_USER) по акционному баннеру Rabbit Hole («10 ДНЕЙ...» / «Расскажите подробнее!»)
    открывается оверлей поверх главного экрана, без перехода на отдельную страницу.
    """
    driver = potential_user_on_main_screen

    home = HomePage(driver).wait_loaded()
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "Ожидалось состояние NEW_USER. Фикстура должна обеспечивать вход под potential."
    )

    content = home.get_content()
    assert isinstance(content, HomeNewUserContent)

    # Клик по кликабельному контейнеру оффера «10 ДНЕЙ...» с content-desc 'Расскажите подробнее!'
    content.click_tell_more()

    # Баннер открывается как оверлей: заголовок оффера и кнопка «Купить за 2 990 ₸».
    assert content.is_visible(
        content.OFFER_TITLE
    ), "Ожидалось, что после клика по «Расскажите подробнее!» появится оверлей оффера с заголовком «10 ДНЕЙ...»"
    assert content.is_visible(
        content.RABBIT_HOLE_BUY_BTN, timeout=15
    ), "Ожидалось, что в оверлее Rabbit Hole появится кнопка «Купить»"
    print("✅ Оверлей Rabbit Hole открыт: заголовок оффера и кнопка «Купить» отображаются")
