"""
Тесты главной страницы invictus.kz
"""

import pytest
from playwright.sync_api import Page
from src.pages.web.home_page import HomePage


@pytest.mark.web
@pytest.mark.smoke
def test_home_page_loads(web_page: Page):
    """Главная страница загружается и содержит основной заголовок."""
    page = HomePage(web_page)
    page.open()
    assert page.is_loaded(), "Главная страница не загрузилась"
    heading = page.get_hero_heading_text()
    assert "Invictus" in heading, f"Неожиданный заголовок: {heading}"


@pytest.mark.web
@pytest.mark.smoke
def test_navigation_links_present(web_page: Page):
    """Все основные ссылки навигации присутствуют на главной странице."""
    page = HomePage(web_page)
    page.open()

    assert page.is_visible(page.NAV_CLUBS), "Ссылка 'Клубтар' не найдена"
    assert page.is_visible(page.NAV_TRAININGS), "Ссылка 'Жаттығулар' не найдена"
    assert page.is_visible(page.NAV_COACHES), "Ссылка 'Жаттықтырушылар' не найдена"
    assert page.is_visible(page.NAV_STORE), "Ссылка 'Store' не найдена"
    assert page.is_visible(page.NAV_FRANCHISE), "Ссылка 'Франшиза' не найдена"
    assert page.is_visible(page.NAV_ABOUT), "Ссылка 'Біз туралы' не найдена"


@pytest.mark.web
@pytest.mark.smoke
def test_login_link_present(web_page: Page):
    """Кнопка 'Кіру' (войти) присутствует в шапке."""
    page = HomePage(web_page)
    page.open()
    assert page.is_visible(page.LOGIN_LINK), "Кнопка входа не найдена"


@pytest.mark.web
def test_club_type_sections_visible(web_page: Page):
    """Секции Fitness, GO, Girls, Kids отображаются на главной."""
    page = HomePage(web_page)
    page.open()

    assert page.is_visible(page.FITNESS_SECTION_HEADING), "Секция Invictus Fitness не найдена"
    assert page.is_visible(page.GO_SECTION_HEADING), "Секция Invictus GO не найдена"
    assert page.is_visible(page.GIRLS_SECTION_HEADING), "Секция Invictus Girls не найдена"
    assert page.is_visible(page.KIDS_SECTION_HEADING), "Секция Invictus Kids не найдена"


@pytest.mark.web
def test_choose_club_links_present(web_page: Page):
    """Ссылки 'Клубты таңдау' для каждого типа клуба присутствуют."""
    page = HomePage(web_page)
    page.open()

    assert page.is_visible(page.CHOOSE_CLUB_FITNESS), "Ссылка выбора Fitness клуба не найдена"
    assert page.is_visible(page.CHOOSE_CLUB_GO), "Ссылка выбора GO клуба не найдена"
    assert page.is_visible(page.CHOOSE_CLUB_GIRLS), "Ссылка выбора Girls клуба не найдена"


@pytest.mark.web
def test_footer_visible(web_page: Page):
    """Футер с копирайтом отображается."""
    page = HomePage(web_page)
    page.open()
    page.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    assert page.is_footer_visible(), "Футер не найден"


@pytest.mark.web
def test_hero_cta_buttons_present(web_page: Page):
    """Hero-секция содержит CTA-кнопки."""
    page = HomePage(web_page)
    page.open()

    assert page.is_visible(page.HERO_BUY_SUBSCRIPTION), "Кнопка 'Абонемент сатып алу' не найдена"
    assert page.is_visible(page.HERO_LEAVE_REQUEST), "Кнопка 'Өтінім қалдыру' не найдена"
