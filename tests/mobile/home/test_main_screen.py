"""
Smoke-тесты главного экрана в POM-стиле.
"""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.home.content import HomeNewUserContent


@pytest.mark.mobile
@pytest.mark.smoke
def test_main_screen_loaded(new_user_on_home: "Remote"):
    """Главная страница открывается и распознаётся как NEW_USER."""
    home = HomePage(new_user_on_home).wait_loaded()

    assert home.get_current_home_state() == HomeState.NEW_USER
    assert isinstance(home.get_content(), HomeNewUserContent)


@pytest.mark.mobile
@pytest.mark.smoke
def test_main_screen_new_user_content_visible(new_user_on_home: "Remote"):
    """На главной NEW_USER видны ключевые entrypoints и оффер Rabbit Hole."""
    home = HomePage(new_user_on_home).wait_loaded()
    content = home.get_content()

    assert isinstance(content, HomeNewUserContent)
    content.assert_ui()

    assert content.is_visible(content.WANT_BONUSES_BTN), "Ожидалась CTA кнопка бонусов"
    assert content.is_visible(content.TELL_MORE_ENTRYPOINT), "Ожидался entrypoint Rabbit Hole"
    assert content.is_visible(content.CLUBS_BTN), "Ожидалась кнопка перехода в клубы"


@pytest.mark.mobile
@pytest.mark.smoke
def test_main_screen_new_user_negative_assertions(new_user_on_home: "Remote"):
    """На главной NEW_USER не должны детектиться состояния subscribed/member."""
    home = HomePage(new_user_on_home).wait_loaded()
    content = home.get_content()

    assert isinstance(content, HomeNewUserContent)
    assert not content.is_visible(content.RABBIT_HOLE_BUY_BTN, timeout=2), (
        "Кнопка покупки Rabbit Hole не должна быть видна до открытия оффера"
    )

