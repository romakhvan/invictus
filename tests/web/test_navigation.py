"""
Тесты навигации по сайту invictus.kz
"""

import pytest
from playwright.sync_api import Page
from src.pages.web.home_page import HomePage
from src.pages.web.clubs_page import ClubsPage
from src.pages.web.auth_page import AuthPage


@pytest.mark.web
@pytest.mark.smoke
def test_nav_clubs_link(web_page: Page):
    """Ссылка 'Клубтар' в навигации ведёт на /clubs."""
    page = HomePage(web_page)
    page.open()
    page.click_clubs_nav()
    web_page.wait_for_load_state("networkidle")
    assert "/clubs" in page.get_current_url(), "Навигация на /clubs не сработала"
    clubs_page = ClubsPage(web_page)
    assert clubs_page.is_loaded(), "Страница клубов не загрузилась"


@pytest.mark.web
@pytest.mark.smoke
def test_nav_trainings_link(web_page: Page):
    """Ссылка 'Жаттығулар' в навигации ведёт на /group-trainings."""
    page = HomePage(web_page)
    page.open()
    page.click_trainings_nav()
    web_page.wait_for_load_state("networkidle")
    assert "/group-trainings" in page.get_current_url(), "Навигация на /group-trainings не сработала"


@pytest.mark.web
@pytest.mark.smoke
def test_nav_login_link(web_page: Page):
    """Ссылка 'Кіру' ведёт на страницу авторизации /auth."""
    page = HomePage(web_page)
    page.open()
    page.click_login()
    web_page.wait_for_load_state("networkidle")
    assert "/auth" in page.get_current_url(), "Навигация на /auth не сработала"
    auth_page = AuthPage(web_page)
    assert auth_page.is_loaded(), "Страница авторизации не загрузилась"


@pytest.mark.web
def test_logo_click_returns_home(web_page: Page):
    """Клик по логотипу возвращает на главную страницу."""
    clubs_page = ClubsPage(web_page)
    clubs_page.open()
    web_page.click("header a[href*='/']:first-child, header a[href='/']")
    web_page.wait_for_load_state("networkidle")
    url = web_page.url.rstrip("/")
    assert url == "https://invictus.kz", f"Логотип не ведёт на главную, URL: {url}"


@pytest.mark.web
@pytest.mark.parametrize("nav_link,expected_path", [
    ("a[href*='/personal-trainings']", "/personal-trainings"),
    ("a[href*='/shop']", "/shop"),
    ("a[href*='/franchise']", "/franchise"),
    ("a[href*='/about-us']", "/about-us"),
])
def test_all_nav_links_navigate(web_page: Page, nav_link: str, expected_path: str):
    """Все ссылки основной навигации ведут на корректные страницы."""
    page = HomePage(web_page)
    page.open()
    web_page.click(f"nav[aria-label='Main navigation'] {nav_link}")
    web_page.wait_for_load_state("networkidle")
    assert expected_path in web_page.url, \
        f"Ожидался путь {expected_path}, получен URL: {web_page.url}"


@pytest.mark.web
def test_footer_instagram_link(web_page: Page):
    """Ссылка на Instagram в футере присутствует."""
    page = HomePage(web_page)
    page.open()
    web_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    assert page.is_visible(page.FOOTER_INSTAGRAM), "Ссылка Instagram в футере не найдена"


@pytest.mark.web
def test_clubs_from_footer(web_page: Page):
    """Ссылка 'Invictus Fitness' в футере ведёт на /clubs?type=Fitness."""
    page = HomePage(web_page)
    page.open()
    web_page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    web_page.click("footer a[href*='type=Fitness'], [role='contentinfo'] a[href*='type=Fitness']")
    web_page.wait_for_load_state("networkidle")
    assert "type=Fitness" in web_page.url, f"Ожидался параметр type=Fitness, URL: {web_page.url}"
